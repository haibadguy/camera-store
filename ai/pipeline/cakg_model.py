"""
cakg_model.py -- Mô hình CaKG-Rec (docs/cakg_design.md khối 1–6; kế hoạch đăng ký trước docs/reviews/cakg_eval_plan.md).
Viết 14/10/2026. Script huấn luyện: 06_cakg_train.py. Kiểm thử dựng tay: ai/survey/cakg/test_cakg.py.

Ví dụ (thiết kế khối 3–4): người u1 có thân b (có nút trong H), ống l2 có nút trong H, thẻ nhớ C không có:
  ŷ(u1, l2) = z_u1 · z_l2 = β_e(u1)β_e(l2) e_u1·e_l2 + β_h(u1)β_h(l2) h_u1·h_l2   (cả hai phía có h: gộp kênh)
  ŷ(u1, C)  = e_u1 · e_C                                                          (một phía thiếu h: đúng điểm hành vi)

Các khối:
  1. kênh hành vi: LightGCN 3 lớp trên user–item train (như 05b), e_u, e_i ∈ ℝ⁶⁴           — công thức (1), (2)
  2. kênh phần cứng: 2 lớp RGAT (rgat_layer.py) trên đồ thị con H_lõi (build_h), h_v ∈ ℝ⁶⁴  — (3)–(6)
  3. h_u = trung bình h_b trên các thân TRONG TRAIN của u có nút trong H (HỎI 4: chỉ thân)  — (7)
  4. gộp kênh: β_v = softmax_c(qᵀ tanh(W x_{v,c} + b)) trên các kênh CÓ MẶT, z_v = [β_e e_v ; β_h h_v]; cổng theo
     cặp: ŷ = z_uᵀz_i nếu u và i đều có h, ngược lại e_uᵀe_i                                — (8), (9)
  5. L_comp: InfoNCE trên MỌI cặp dương M = 1 (72.720), âm = mọi ống M = 0 ∧ U = 0 của cùng thân, cosine, τ = 0,2,
     lấy trung bình trên cặp dương                                                           — (10)–(12)
  6. L_total = L_BPR + λ1 L_comp + λ2 · ½(‖e_u⁰‖² + ‖e_i⁰‖² + ‖e_j⁰‖²)/|B|                  — (13), (14)

Biến thể v2 (docs/reviews/cakg_v2_plan.md; thêm 16/10/2026; variant = "v1" giữ ĐÚNG mô hình đã chấm test lần 1):
  A "lens_gate":    cổng chỉ mở cho ỐNG có h: ŷ = z_uᵀz_i nếu u có h_u và i là ống có h; mọi sản phẩm khác (kể cả thân)
                    ŷ = e_uᵀe_i. Thân vẫn là nút của H (dựng h_u, L_comp) nhưng không được cộng điểm phần cứng.
  B "loo_hu":       cổng như v1, nhưng lúc HUẤN LUYỆN, cặp dương (u, b) với b là thân của u: h_u tính BỎ chính b
                    (h_u⁻ᵇ = (|B| h_u − h_b)/(|B| − 1)); |B| = 1 thì cổng đóng cho cặp đó. Lúc chấm không đổi (thân của u
                    là item train, đã bị bỏ khỏi ứng viên).
  C "body_hardneg": cổng như v1; mỗi bộ ba (u, i, j) của người có h_u thêm một âm mẫu j2 = thân CÙNG NGÀM với một thân
                    của u mà u chưa có trong train (lấy đều): L_BPR thêm −ln σ(ŷ_ui − ŷ_uj2).
"""

import csv
import json
from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.sparse import load_npz

import common_05 as C
from rgat_layer import HwEncoder

KG = C.DATA_DIR / "kg"
HW_EDGE_CSVS = ["kg_edges_compatible_with.csv", "kg_edges_crops_sensor.csv", "kg_edges_requires_adapter.csv",
                "kg_edges_has_spec_mount.csv", "kg_edges_has_spec_sensor_format.csv", "kg_edges_suitable_for.csv"]
HW_INPUT_FILES = [KG / f for f in HW_EDGE_CSVS] + [KG / "kg_node_index.json"]

# Số đếm của H_lõi phải khớp log run_probe_cakg_20261014_lan1.log / thiết kế khối 2 (cạnh xuôi; rev_ cùng số)
H_LOI_EXPECTED = {"compatible_with": 68_786, "compatible_with_crop_unknown": 1_686, "crops_sensor": 2_248,
                  "requires_adapter": 16_301, "has_spec_mount": 1_570, "has_spec_sensor_format": 1_498,
                  "suitable_for": 1_080}
H_LOI_N_NODES = 1_822
H_LOI_N_ITEMS = 1_788
N_UNSURE_DROPPED = 134          # cạnh has_spec → mount có cờ ngam_khong_chac (HỎI 3: bỏ)


def _rows(name):
    with open(KG / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


@dataclass
class HwGraph:
    """Đồ thị con phần cứng H (không có nút người dùng, không có cạnh interacted_with).
    Nút cục bộ: item [0, n_items_h) theo iid tăng dần, rồi ngàm, khổ, mục đích (thứ tự như kg_node_index.json)."""
    ei: torch.Tensor                 # [2, E]: hàng 0 = nguồn j, hàng 1 = đích i (tin đi j -> i)
    et: torch.Tensor                 # [E] chỉ số quan hệ
    rel_names: list                  # tên 14 (hoặc 12) quan hệ, "rev_" = chiều ngược
    item_loc: dict                   # iid toàn cục -> chỉ số nút cục bộ
    n_nodes: int
    off: dict                        # chỉ số bắt đầu của từng loại nút
    node_names: dict                 # loại nút -> [tên]
    counts: dict = field(default_factory=dict)   # quan hệ xuôi -> số cạnh


def build_h(drop_suitable_for=False):
    """Dựng H_lõi từ kg_edges_*.csv (thiết kế khối 2; không ghi file nào).
      - compatible_with tách theo cờ crop_unknown thành 2 quan hệ; crops_sensor; requires_adapter;
      - has_spec_mount chỉ của thân / ống (src_phu_kien = 0), BỎ 134 cạnh ngam_khong_chac (HỎI 3);
      - has_spec_sensor_format; suitable_for; mỗi quan hệ thêm chiều rev_.
    drop_suitable_for (ablation C8, kế hoạch mục 6): bỏ 2 quan hệ suitable_for / rev_suitable_for, GIỮ NGUYÊN tập nút
    (4 nút mục đích không còn cạnh; ống chỉ có suitable_for thành nút không có cạnh)."""
    comp, crops, radp = _rows("kg_edges_compatible_with.csv"), _rows("kg_edges_crops_sensor.csv"), \
        _rows("kg_edges_requires_adapter.csv")
    hsm, hss, suit = _rows("kg_edges_has_spec_mount.csv"), _rows("kg_edges_has_spec_sensor_format.csv"), \
        _rows("kg_edges_suitable_for.csv")
    with open(KG / "kg_node_index.json", encoding="utf-8") as f:
        nidx = json.load(f)
    names = {"mount": list(nidx["mount"]), "sensor_format": list(nidx["sensor_format"]),
             "usecase": list(nidx["usecase"])}
    nid = {t: {s: k for k, s in enumerate(v)} for t, v in names.items()}
    edges = {k: [] for k in H_LOI_EXPECTED}       # quan hệ xuôi -> [(iid nguồn, (loại đích, chỉ số / iid))]
    for r in comp:
        key = "compatible_with" + ("_crop_unknown" if r["crop_unknown"] == "1" else "")
        edges[key].append((int(r["body_iid"]), ("item", int(r["lens_iid"]))))
    for r in crops:
        edges["crops_sensor"].append((int(r["body_iid"]), ("item", int(r["lens_iid"]))))
    for r in radp:
        edges["requires_adapter"].append((int(r["body_iid"]), ("item", int(r["lens_iid"]))))
    n_unsure = 0
    for r in hsm:
        if r["ngam_khong_chac"] == "1":
            n_unsure += 1
            continue
        if r["src_phu_kien"] != "0":
            continue                                   # phụ kiện: chỉ ở H_pk (không dùng, HỎI 2)
        assert ">" not in r["mount"] and r["item_type"] in ("than", "ong"), r
        edges["has_spec_mount"].append((int(r["iid"]), ("mount", nid["mount"][r["mount"]])))
    assert n_unsure == N_UNSURE_DROPPED, n_unsure
    for r in hss:
        edges["has_spec_sensor_format"].append((int(r["iid"]), ("sensor_format", nid["sensor_format"][r["sensor_format"]])))
    for r in suit:
        edges["suitable_for"].append((int(r["iid"]), ("usecase", nid["usecase"][r["usecase"]])))
    counts = {k: len(v) for k, v in edges.items()}

    items = sorted({s for es in edges.values() for s, _ in es} |
                   {d[1] for es in edges.values() for _, d in es if d[0] == "item"})
    loc = {g: k for k, g in enumerate(items)}
    off = {"item": 0, "mount": len(items)}
    off["sensor_format"] = off["mount"] + len(names["mount"])
    off["usecase"] = off["sensor_format"] + len(names["sensor_format"])
    n = off["usecase"] + len(names["usecase"])
    src, dst, typ, rel_names = [], [], [], []
    for name in H_LOI_EXPECTED:
        if drop_suitable_for and name == "suitable_for":
            continue
        es = edges[name]
        s = [loc[a] for a, _ in es]
        d = [loc[b[1]] if b[0] == "item" else off[b[0]] + b[1] for _, b in es]
        for rev in (False, True):
            rel_names.append(("rev_" if rev else "") + name)
            src += d if rev else s
            dst += s if rev else d
            typ += [len(rel_names) - 1] * len(s)
    return HwGraph(torch.tensor([src, dst], dtype=torch.long), torch.tensor(typ, dtype=torch.long), rel_names, loc, n,
                   off, names, counts)


def user_body_matrix(train, item_type, loc, n_nodes):
    """(7): A_ub [n_users, n_nodes] thưa, A_ub[u, b] = 1/|B_u^H| với b là thân (loại 0) trong train của u CÓ nút trong H.
    Trả về (A_ub, has_hu [n_users] bool, B_u^H {uid: [iid thân]})."""
    rows_, cols, vals, bodies_h = [], [], [], {}
    for u, its in train.items():
        bs = sorted(i for i in its if item_type[i] == 0 and i in loc)
        if not bs:
            continue
        bodies_h[u] = bs
        for b in bs:
            rows_.append(u)
            cols.append(loc[b])
            vals.append(1.0 / len(bs))
    A = torch.sparse_coo_tensor(torch.tensor([rows_, cols]), torch.tensor(vals, dtype=torch.float32),
                                (C.N_USERS, n_nodes)).coalesce()
    has = torch.zeros(C.N_USERS, dtype=torch.bool)
    has[torch.tensor(sorted(bodies_h))] = True
    return A, has, bodies_h


VARIANTS = ("v1", "lens_gate", "loo_hu", "body_hardneg")


def body_mounts():
    """iid thân -> ngàm, từ has_spec_mount (thân, không phụ kiện, không cờ ngam_khong_chac)."""
    out = {}
    for r in _rows("kg_edges_has_spec_mount.csv"):
        if r["item_type"] == "than" and r["src_phu_kien"] == "0" and r["ngam_khong_chac"] == "0":
            out[int(r["iid"])] = r["mount"]
    return out


def same_mount_body_candidates(bodies_h, train, loc):
    """Biến thể C: với mỗi u có h_u, tập thân có nút trong H, CÙNG NGÀM với ít nhất một thân trong B_u^H, KHÔNG có trong
    train của u. Trả về CSR (ptr [N_USERS + 1], idx) theo iid tăng dần; người không có h_u: tập rỗng."""
    mt = body_mounts()
    by_mount = {}
    for b, m in mt.items():
        if b in loc:
            by_mount.setdefault(m, []).append(b)
    ptr, idx = [0], []
    for u in range(C.N_USERS):
        bs = bodies_h.get(u, [])
        cand = sorted({c for b in bs if b in mt for c in by_mount[mt[b]]} - set(train.get(u, ())))
        idx += cand
        ptr.append(len(idx))
    return torch.tensor(ptr, dtype=torch.long), torch.tensor(idx, dtype=torch.long)


def lcomp_tensors(loc):
    """M, U ∈ {0,1}^{537×1033} và chỉ số nút cục bộ của từng hàng (thân) / cột (ống) của M.
    M = 1: cạnh compatible_with + crops_sensor (= common_05.load_body_to_lenses); U: unknown_mask.npz."""
    item_map = json.load(open(C.ITEM_MAP_JSON, encoding="utf-8"))
    b_idx = json.load(open(C.BODY_INDEX, encoding="utf-8"))
    l_idx = json.load(open(C.LENS_INDEX, encoding="utf-8"))
    bg = [item_map[a] for a, _ in sorted(b_idx.items(), key=lambda t: t[1])]
    lg = [item_map[a] for a, _ in sorted(l_idx.items(), key=lambda t: t[1])]
    br = {g: k for k, g in enumerate(bg)}
    lc = {g: k for k, g in enumerate(lg)}
    M = torch.zeros(len(bg), len(lg), dtype=torch.bool)
    for b, ls in C.load_body_to_lenses().items():
        for l in ls:
            M[br[b], lc[l]] = True
    U = torch.as_tensor(load_npz(C.UNKNOWN_NPZ).toarray().astype(bool))
    assert U.shape == M.shape and not bool((M & U).any())
    assert all(g in loc for g in bg) and all(g in loc for g in lg), "thân / ống của M phải có nút trong H"
    return M, U, torch.tensor([loc[g] for g in bg]), torch.tensor([loc[g] for g in lg]), bg, lg


def l_comp(h, M, U, bl, ll, tau):
    """(10)–(12): s(b, l) = cos(h_b, h_l)/τ; với mỗi cặp dương (b, l+): −log e^{s(b,l+)} / (e^{s(b,l+)} +
    Σ_{l−: M=0 ∧ U=0} e^{s(b,l−)}); trung bình trên mọi cặp dương. Cặp U không vào mẫu số (không bị đẩy xa)."""
    hb = F.normalize(h[bl], dim=1)
    hl = F.normalize(h[ll], dim=1)
    S = hb @ hl.T / tau
    neg = ~M & ~U
    lse_neg = torch.logsumexp(S.masked_fill(~neg, -float("inf")), 1)       # log Σ_{l−} exp s(b, l−) theo hàng
    rows_ = M.nonzero()[:, 0]
    s_pos = S[M]                                                            # cùng thứ tự hàng-trước với nonzero()
    return (torch.logaddexp(s_pos, lse_neg[rows_]) - s_pos).mean()


class Fusion(nn.Module):
    """(8)–(9) theo AM-GCN Eq. 8–9: ω_{v,c} = qᵀ tanh(W x_{v,c} + b), W, b, q dùng chung cho 2 kênh của một phía;
    β_v = softmax trên các kênh CÓ MẶT (thiếu h thì β = (1; 0)); z_v = [β_e e_v ; β_h h_v] (ghép, không cộng)."""

    def __init__(self, dim=64, hid=64):
        super().__init__()
        self.W = nn.Linear(dim, hid)
        self.q = nn.Linear(hid, 1, bias=False)
        nn.init.xavier_uniform_(self.W.weight)
        nn.init.zeros_(self.W.bias)
        nn.init.xavier_uniform_(self.q.weight)

    def forward(self, e, h, has_h):
        we = self.q(torch.tanh(self.W(e)))
        wh = self.q(torch.tanh(self.W(h)))
        wh = torch.where(has_h[:, None], wh, torch.full_like(wh, -float("inf")))
        beta = torch.softmax(torch.cat([we, wh], 1), 1)
        hz = torch.where(has_h[:, None], h, torch.zeros_like(h))
        return torch.cat([beta[:, :1] * e, beta[:, 1:] * hz], 1), beta


def gated_score(e_u, e_i, z_u, z_i, gate):
    """(9) từng cặp: z_uᵀz_i nếu gate (cả u và i có h), ngược lại e_uᵀe_i."""
    return torch.where(gate, (z_u * z_i).sum(-1), (e_u * e_i).sum(-1))


def lightgcn_propagate(adj, E0, n_layers):
    """(1)–(2): e = (1/(L+1)) Σ_{l=0..L} Ã^l e⁽⁰⁾, Ã = D^(-1/2) A D^(-1/2) (như 05b)."""
    acc, Ek = E0, E0
    for _ in range(n_layers):
        Ek = torch.sparse.mm(adj, Ek)
        acc = acc + Ek
    return acc / (n_layers + 1)


class CaKGRec(nn.Module):
    def __init__(self, adj, H: HwGraph, A_ub, has_hu, lc, dim=64, n_layers=3, l2=1e-3, lam1=0.1, tau=0.2,
                 variant="v1", item_type=None, hardneg=None):
        """adj: ma trận kề chuẩn hóa user–item train (05b.build_norm_adj); H: build_h(); A_ub, has_hu:
        user_body_matrix(); lc: lcomp_tensors() (M, U, bl, ll, ...). Mọi tensor đặt trên cùng thiết bị trước.
        variant (VARIANTS): "v1" = mô hình test lần 1; item_type (np [N_ITEMS]) bắt buộc với biến thể khác v1;
        hardneg = same_mount_body_candidates() (ptr, idx), bắt buộc với "body_hardneg"."""
        super().__init__()
        assert variant in VARIANTS, variant
        self.variant = variant
        self.adj, self.n_layers, self.l2, self.lam1, self.tau = adj, n_layers, l2, lam1, tau
        self.n_users = C.N_USERS
        self.user_emb = nn.Embedding(C.N_USERS, dim)
        self.item_emb = nn.Embedding(C.N_ITEMS, dim)
        nn.init.xavier_uniform_(self.user_emb.weight)
        nn.init.xavier_uniform_(self.item_emb.weight)
        self.enc = HwEncoder(H.n_nodes, len(H.rel_names), dim)
        self.fu, self.fi = Fusion(dim), Fusion(dim)            # tham số riêng cho phía người / phía sản phẩm
        dev = adj.device
        self.ei, self.et = H.ei.to(dev), H.et.to(dev)
        item_loc = torch.full((C.N_ITEMS,), -1, dtype=torch.long)
        for g, l_ in H.item_loc.items():
            item_loc[g] = l_
        self.item_loc = item_loc.to(dev)
        self.has_hi = self.item_loc >= 0
        self.hidx = torch.nonzero(self.has_hi).view(-1)       # các item có h (tăng dần theo iid)
        self.A_ub, self.has_hu = A_ub.to(dev), has_hu.to(dev)
        # gate_i: sản phẩm mà phần phần cứng được cộng vào điểm (v1, B, C: mọi item có h; A: chỉ ống có h)
        self.gate_i = self.has_hi.clone()
        if variant != "v1":
            it = torch.as_tensor(item_type, device=dev)
            if variant == "lens_gate":
                self.gate_i = self.has_hi & (it == 1)
            self.is_body_h = self.has_hi & (it == 0)
            Ac = self.A_ub.coalesce()
            self.n_bu = torch.bincount(Ac.indices()[0], minlength=C.N_USERS).to(torch.float32)   # |B_u^H|
            self.ub_keys = Ac.indices()[0] * H.n_nodes + Ac.indices()[1]                       # cặp (u, thân ∈ B_u^H)
            self.n_nodes_h = H.n_nodes
        if variant == "body_hardneg":
            self.hn_ptr, self.hn_idx = (t.to(dev) for t in hardneg)
        self.M, self.U, self.bl, self.ll = (t.to(dev) for t in lc[:4])
        self.beta_h_zero = False                               # chỉ để kiểm thử Faithfulness (β_h = 0)
        self._acc = torch.zeros(3, device=dev)                 # tổng BPR, L_comp, số bước trong epoch

    # -- các khối ------------------------------------------------------------
    def behaviour(self):
        Ef = lightgcn_propagate(self.adj, torch.cat([self.user_emb.weight, self.item_emb.weight]), self.n_layers)
        return Ef[:self.n_users], Ef[self.n_users:]

    def hardware(self, ei=None, et=None, A_ub=None):
        """h mọi nút của H, h_u (7) mọi người dùng, α lớp 2. ei / et / A_ub thay được (phản thực tế, khối 8)."""
        h, alpha = self.enc(self.ei if ei is None else ei, self.et if et is None else et)
        hU = torch.sparse.mm(self.A_ub if A_ub is None else A_ub, h)
        return h, hU, alpha

    def fuse(self, eU, eI, h, hU, has_hu=None):
        has_hu = self.has_hu if has_hu is None else has_hu
        hI = h[self.item_loc.clamp(min=0)]
        if self.beta_h_zero:
            has_hu = torch.zeros_like(has_hu)
            has_hi = torch.zeros_like(self.has_hi)
        else:
            has_hi = self.has_hi
        zU, bU = self.fu(eU, hU, has_hu)
        zI, bI = self.fi(eI, hI, has_hi)
        return zU, zI, bU, bI, has_hu, has_hi

    # -- huấn luyện ----------------------------------------------------------
    def pos_user_side(self, u, i, eU, h, hU):
        """Phía người dùng của cặp DƯƠNG (u, i) lúc huấn luyện -> (z_u, cổng phía người). v1, A, C: như lúc chấm.
        B "loo_hu": nếu i là thân của u (i ∈ B_u^H; với cặp dương thật luôn đúng khi i là thân có h) thì h_u bỏ chính i:
        h_u⁻ⁱ = (|B| h_u − h_i)/(|B| − 1); |B| = 1 thì cổng phía người đóng (không còn thân nào)."""
        hu, has_u = hU[u], self.has_hu[u]
        if self.variant == "loo_hu":
            selfb = self.is_body_h[i] & has_u & torch.isin(u * self.n_nodes_h + self.item_loc[i].clamp(min=0),
                                                            self.ub_keys)     # i ∈ B_u^H (kiểm thẳng, không giả định)
            nb = self.n_bu[u]
            hu_loo = (nb[:, None] * hu - h[self.item_loc[i].clamp(min=0)]) / (nb - 1).clamp(min=1)[:, None]
            hu = torch.where(selfb[:, None], hu_loo, hu)
            has_u = has_u & ~(selfb & (nb == 1))
        zu, _ = self.fu(eU[u], hu, has_u)
        return zu, has_u

    def sample_hardneg(self, u):
        """C: j2 lấy đều trong same_mount_body_candidates của u (RNG torch trên thiết bị của mô hình).
        Trả về (j2 [số người có ứng viên], ok [len(u)] bool)."""
        lo, cnt = self.hn_ptr[u], self.hn_ptr[u + 1] - self.hn_ptr[u]
        r = torch.rand(len(u), device=u.device)
        pos = lo + torch.minimum((r * cnt).long(), (cnt - 1).clamp(min=0))
        ok = cnt > 0
        return self.hn_idx[pos[ok]], ok

    def loss(self, u, i, j):
        j2, ok = self.sample_hardneg(u) if self.variant == "body_hardneg" else (None, None)
        eU, eI = self.behaviour()
        h, hU, _ = self.hardware()
        zu, _ = self.fu(eU[u], hU[u], self.has_hu[u])
        if self.variant == "loo_hu":
            zu_pos, has_pos = self.pos_user_side(u, i, eU, h, hU)
        else:
            zu_pos, has_pos = zu, self.has_hu[u]                                 # v1: đúng như code test lần 1
        zi, _ = self.fi(eI[i], h[self.item_loc[i].clamp(min=0)], self.has_hi[i])
        zj, _ = self.fi(eI[j], h[self.item_loc[j].clamp(min=0)], self.has_hi[j])
        s_i = gated_score(eU[u], eI[i], zu_pos, zi, has_pos & self.gate_i[i])
        s_j = gated_score(eU[u], eI[j], zu, zj, self.has_hu[u] & self.gate_i[j])
        bpr_t = F.softplus(-(s_i - s_j))                                         # (13) = −ln σ(ŷ_ui − ŷ_uj)
        reg_hn = 0.0
        if j2 is not None and bool(ok.any()):
            uu = u[ok]
            zj2, _ = self.fi(eI[j2], h[self.item_loc[j2].clamp(min=0)], self.has_hi[j2])
            s_j2 = gated_score(eU[uu], eI[j2], zu[ok], zj2, self.has_hu[uu] & self.gate_i[j2])
            bpr_t = bpr_t + torch.zeros_like(bpr_t).masked_scatter(ok, F.softplus(-(s_i[ok] - s_j2)))
            reg_hn = self.item_emb(j2).pow(2).sum()
        bpr = bpr_t.mean()
        if self.lam1 > 0:
            lc = l_comp(h, self.M, self.U, self.bl, self.ll, self.tau)
        else:
            with torch.no_grad():                                                 # ablation λ1 = 0: chỉ ghi lại
                lc = l_comp(h, self.M, self.U, self.bl, self.ll, self.tau)
        reg = 0.5 * (self.user_emb(u).pow(2).sum() + self.item_emb(i).pow(2).sum()
                     + self.item_emb(j).pow(2).sum() + reg_hn) / len(u)
        self._acc += torch.stack([bpr.detach(), lc.detach(), torch.ones((), device=bpr.device)])
        return bpr + self.lam1 * lc + self.l2 * reg                               # (14)

    def epoch_stats(self):
        a = self._acc.tolist()
        self._acc.zero_()
        return {"bpr": a[0] / a[2], "l_comp": a[1] / a[2]} if a[2] else {}

    # -- chấm điểm -----------------------------------------------------------
    @torch.no_grad()
    def components(self):
        eU, eI = self.behaviour()
        h, hU, alpha = self.hardware()
        zU, zI, bU, bI, has_hu, has_hi = self.fuse(eU, eI, h, hU)
        return {"eU": eU, "eI": eI, "h": h, "hU": hU, "alpha2": alpha, "zU": zU, "zI": zI, "betaU": bU,
                "betaI": bI, "has_hu": has_hu, "has_hi": has_hi, "gate_i": has_hi & self.gate_i}

    @staticmethod
    def make_scorer(c, hidx):
        """score_batch(uids) -> [b, n_items] theo (9): e_uᵀe_i, thay bằng z_uᵀz_i ở các cặp có cổng mở
        (cổng phía sản phẩm = c["gate_i"]: v1 mọi item có h; biến thể A chỉ ống có h)."""
        eU, eIT, zU = c["eU"], c["eI"].T, c["zU"]
        hidx = hidx[c.get("gate_i", c["has_hi"])[hidx]]
        zIhT = c["zI"][hidx].T
        has_hu = c["has_hu"]

        def f(uids):
            S = eU[uids] @ eIT
            g = has_hu[uids]
            if bool(g.any()) and len(hidx):
                S[:, hidx] = torch.where(g[:, None], zU[uids] @ zIhT, S[:, hidx])
            return S
        return f

    @torch.no_grad()
    def score_fn(self):
        return self.make_scorer(self.components(), self.hidx)
