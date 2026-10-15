"""Đo thử bộ nhớ GPU / thời gian cho kế hoạch CaKG-Rec (docs/reviews/cakg_eval_plan.md mục "Tài nguyên").

KHÔNG huấn luyện: trọng số khởi tạo ngẫu nhiên, chỉ forward + backward vài bước (không optimizer.step), không chấm
val / test. Số đo chỉ để ước tính thời gian một epoch, đỉnh bộ nhớ, độ trễ một yêu cầu. Cùng cách đo với
ai/survey/content5/probe_gpu.py (bước khởi động không tính giờ, rồi trung bình N_STEPS bước).

  1. CaKG-Rec một bước: LightGCN 3 lớp (như 05b) + RGAT 2 lớp trên đồ thị con phần cứng H (H_loi: 14 quan hệ;
     H_pk: 20 quan hệ) + gộp kênh có attention + BPR + L_comp (InfoNCE trên toàn bộ 537 × 1.033 cặp); batch 2048.
     RGAT là lớp tự cài RGATLayer (cùng công thức với RGATConv của PyG, kiểm trùng số trên 20.000 cạnh), vì
     RGATConv nhân ma trận W^(r) riêng cho từng cạnh: đo thêm đỉnh bộ nhớ một lớp RGATConv trên toàn H.
     Kiểm hệ số attention lấy ra được (để dùng cho phần giải thích) và tổng theo (nút đích, quan hệ) = 1.
  2. KGAT một bước (bài Wang et al. 2019): đồ thị cộng tác 95.646 nút, 18 quan hệ (bỏ 134 cạnh ngam_khong_chac
     như QĐ 5-4), attention π(h,r,t) = (W_r e_t)ᵀ tanh(W_r e_h + e_r), 3 lớp Bi-Interaction 64-32-16, BPR batch 1024;
     (a) attention tính lại có gradient mỗi bước; (b) attention cố định (không gradient); bước TransR batch 2048.
  3. Độ trễ một yêu cầu: điểm 1 người × 27.940 sản phẩm từ biểu diễn đã tính sẵn, bỏ item train, mặt nạ cứng,
     top-10, dựng đường giải thích cho ống trong top-10; GPU và CPU; 1.000 người ngẫu nhiên, p50 / p95.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/cakg/probe_cakg.py <đường dẫn log mới>
"""
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import psutil
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.sparse import load_npz
from torch_geometric.nn import RGATConv
from torch_geometric.utils import softmax as pyg_softmax

sys.path.insert(0, "ai/pipeline")
sys.path.insert(0, "ai/survey/report")
sys.stdout.reconfigure(encoding="utf-8")
import common_05 as C  # noqa: E402
from report_common import git_state, sha256_file  # noqa: E402

DEV = torch.device("cuda")
D = 64
N_STEPS = 5
KG = "ai/data/kg"
log_lines: list[str] = []


def log(msg: str = "") -> None:
    print(msg, flush=True)
    log_lines.append(msg)


def mib(x):
    return f"{x / 2**20:,.0f} MiB"


def timed(step_fn, n=N_STEPS):
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    step_fn()
    torch.cuda.synchronize()
    t = time.perf_counter()
    for _ in range(n):
        step_fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t) / n, torch.cuda.max_memory_allocated()


def rows(name):
    return list(csv.DictReader(open(f"{KG}/{name}", encoding="utf-8")))


# ── đồ thị con phần cứng ──────────────────────────────────────────────────────

def build_h(with_acc: bool):
    """Trả về (edge_index [2,E] cục bộ, edge_type [E], tên quan hệ, item_global -> chỉ số cục bộ, số nút)."""
    comp, crops, radp = rows("kg_edges_compatible_with.csv"), rows("kg_edges_crops_sensor.csv"), \
        rows("kg_edges_requires_adapter.csv")
    hsm, hss, suit = rows("kg_edges_has_spec_mount.csv"), rows("kg_edges_has_spec_sensor_format.csv"), \
        rows("kg_edges_suitable_for.csv")
    node_index = json.load(open(f"{KG}/kg_node_index.json", encoding="utf-8"))
    edges = defaultdict(list)  # tên quan hệ -> [(item_g, đích)] ; đích = ('item', iid) | (loại, chỉ số)
    for r in comp:
        edges["compatible_with" + ("_crop_unknown" if r["crop_unknown"] == "1" else "")].append(
            (int(r["body_iid"]), ("item", int(r["lens_iid"]))))
    for r in crops:
        edges["crops_sensor"].append((int(r["body_iid"]), ("item", int(r["lens_iid"]))))
    for r in radp:
        edges["requires_adapter"].append((int(r["body_iid"]), ("item", int(r["lens_iid"]))))
    mount_names = sorted({r["mount"] for r in hsm if ">" not in r["mount"]} |
                         {m for r in hsm if ">" in r["mount"] for m in r["mount"].split(">")})
    mount_id = {m: k for k, m in enumerate(mount_names)}
    for r in hsm:
        if r["ngam_khong_chac"] == "1":
            continue                                           # QĐ 5-4: bỏ
        if r["src_phu_kien"] == "0":
            key = "has_spec_mount"
        elif not with_acc:
            continue
        elif r["phia"] == "khong_phai_ngam_chuyen":
            key = "has_spec_mount_phukien"
        else:
            key = f"has_spec_mount_{r['phia']}"
        m = r["mount"]
        if ">" in m:
            a, b = m.split(">")
            m = a if r["phia"] == "phia_ong" else b
        edges[key].append((int(r["iid"]), ("mount", mount_id[m])))
    sf = sorted({r["sensor_format"] for r in hss})
    sf_id = {s: k for k, s in enumerate(sf)}
    for r in hss:
        edges["has_spec_sensor_format"].append((int(r["iid"]), ("sensor_format", sf_id[r["sensor_format"]])))
    uc = sorted({r["usecase"] for r in suit})
    uc_id = {s: k for k, s in enumerate(uc)}
    for r in suit:
        edges["suitable_for"].append((int(r["iid"]), ("usecase", uc_id[r["usecase"]])))
    items = sorted({s for es in edges.values() for s, _ in es} |
                   {d[1] for es in edges.values() for _, d in es if d[0] == "item"})
    loc = {g: k for k, g in enumerate(items)}
    off = {"item": 0, "mount": len(items)}
    off["sensor_format"] = off["mount"] + len(mount_names)
    off["usecase"] = off["sensor_format"] + len(sf)
    n = off["usecase"] + len(uc)
    src, dst, typ, names = [], [], [], []
    for name in sorted(edges):
        es = edges[name]
        s = [loc[a] for a, _ in es]
        d = [loc[b[1]] if b[0] == "item" else off[b[0]] + b[1] for _, b in es]
        for rev in (False, True):
            names.append(("rev_" if rev else "") + name)
            src += d if rev else s
            dst += s if rev else d
            typ += [len(names) - 1] * len(s)
    ei = torch.tensor([src, dst])
    return ei, torch.tensor(typ), names, loc, n, {k: len(v) for k, v in edges.items()}


class HwEncoder(nn.Module):
    """2 lớp RGAT (WIRGAT, logit cộng) + phần tự giữ W_0 h_i (RGATConv của PyG không có), ReLU giữa hai lớp."""

    def __init__(self, n, R):
        super().__init__()
        self.x = nn.Parameter(torch.randn(n, D) * 0.01)
        self.convs = nn.ModuleList([RGATLayer(D, D, R) for _ in range(2)])
        self.roots = nn.ModuleList([nn.Linear(D, D, bias=False) for _ in range(2)])

    def forward(self, ei, et, want_att=False):
        h, att = self.x, None
        for k, (c, w0) in enumerate(zip(self.convs, self.roots)):
            out, a = c(h, ei, et)
            if want_att and k == 1:
                att = a
            h = out + w0(h)
            if k == 0:
                h = F.relu(h)
        return h, att


class RGATLayer(nn.Module):
    """WIRGAT, logit cộng (Busbridge et al. 2019, Eq. 1, 3, 4, 6, 8), một đầu, D = 1, có bias như RGATConv.
    Khác RGATConv của PyG chỉ ở cách tính: G^(r) = H W^(r) tính cho mọi nút một lần ([R, N, F']) rồi mới lấy theo
    cạnh, thay vì nhân ma trận W^(r) riêng cho từng cạnh ([E, F, F'], ~3 GB với 186k cạnh)."""

    def __init__(self, fin, fout, R):
        super().__init__()
        self.R = R
        self.weight = nn.Parameter(torch.empty(R, fin, fout))
        self.q = nn.Parameter(torch.empty(fout, 1))
        self.k = nn.Parameter(torch.empty(fout, 1))
        self.bias = nn.Parameter(torch.zeros(fout))
        for p in (self.weight, self.q, self.k):
            nn.init.xavier_uniform_(p)

    def forward(self, h, ei, et):
        src, dst = ei[0], ei[1]
        G = torch.einsum("nf,rfo->rno", h, self.weight)          # g_i^(r) = W^(r) h_i, mọi nút, mọi quan hệ
        gj = G[et, src]                                           # giá trị (value) từ nút nguồn j
        gi = G[et, dst]                                           # nút đích i, cùng quan hệ
        logit = F.leaky_relu(gi @ self.q + gj @ self.k, 0.2).view(-1)
        alpha = pyg_softmax(logit, dst * self.R + et)            # WIRGAT: chuẩn hóa trong từng (i, r)
        out = torch.zeros(h.size(0), G.size(-1), device=h.device).index_add_(0, dst, alpha[:, None] * gj)
        return out + self.bias, alpha


def check_rgat_equal(ei, et, R, n_edges=20000):
    """So RGATLayer với RGATConv của PyG (cùng trọng số) trên n_edges cạnh đầu."""
    torch.manual_seed(0)
    e, t = ei[:, :n_edges], et[:n_edges]
    n = int(e.max()) + 1
    x = torch.randn(n, D, device=DEV)
    ref = RGATConv(D, D, R, attention_mechanism="within-relation", attention_mode="additive-self-attention",
                   heads=1).to(DEV)
    with torch.no_grad():
        ref.bias.normal_()
    mine = RGATLayer(D, D, R).to(DEV)
    with torch.no_grad():
        mine.weight.copy_(ref.weight)
        mine.q.copy_(ref.q)
        mine.k.copy_(ref.k)
        mine.bias.copy_(ref.bias)
        o1, (_, a1) = ref(x, e, t, return_attention_weights=True)
        o2, a2 = mine(x, e, t)
    return float((o1 - o2).abs().max()), float((a1.view(-1) - a2).abs().max())


class Fusion(nn.Module):
    """β_c = softmax_c(qᵀ tanh(W x_c + b)) trên các kênh có mặt (AM-GCN Eq. 8–9), z = [β_e e ; β_h h]."""

    def __init__(self, hid=D):
        super().__init__()
        self.W = nn.Linear(D, hid)
        self.q = nn.Linear(hid, 1, bias=False)

    def forward(self, e, h, has_h):
        we = self.q(torch.tanh(self.W(e)))
        wh = self.q(torch.tanh(self.W(h)))
        wh = torch.where(has_h[:, None], wh, torch.full_like(wh, -float("inf")))
        beta = torch.softmax(torch.cat([we, wh], 1), 1)
        hz = torch.where(has_h[:, None], h, torch.zeros_like(h))
        return torch.cat([beta[:, :1] * e, beta[:, 1:] * hz], 1), beta


def norm_adj(train):
    rows_, cols = [], []
    for u, its in train.items():
        for i in its:
            rows_ += [u, C.N_USERS + i]
            cols += [C.N_USERS + i, u]
    N = C.N_USERS + C.N_ITEMS
    idx = torch.tensor([rows_, cols])
    deg = torch.bincount(idx[0], minlength=N).float()
    dis = deg.pow(-0.5)
    dis[torch.isinf(dis)] = 0
    return torch.sparse_coo_tensor(idx, dis[idx[0]] * dis[idx[1]], (N, N)).coalesce()


def lcomp_setup(loc):
    b_idx = json.load(open(f"{KG}/body_index.json", encoding="utf-8"))
    l_idx = json.load(open(f"{KG}/lens_index.json", encoding="utf-8"))
    item_map = json.load(open(C.ITEM_MAP_JSON, encoding="utf-8"))
    bg = [item_map[s] for s, _ in sorted(b_idx.items(), key=lambda t: t[1])]
    lg = [item_map[s] for s, _ in sorted(l_idx.items(), key=lambda t: t[1])]
    Mm = torch.zeros(len(bg), len(lg), dtype=torch.bool)
    pos = {(int(r["body_iid"]), int(r["lens_iid"])) for f in ("kg_edges_compatible_with.csv",
                                                             "kg_edges_crops_sensor.csv") for r in rows(f)}
    br = {g: k for k, g in enumerate(bg)}
    lc = {g: k for k, g in enumerate(lg)}
    for b, l in pos:
        Mm[br[b], lc[l]] = True
    Uu = torch.as_tensor(load_npz(f"{KG}/unknown_mask.npz").toarray().astype(bool))
    bl = torch.tensor([loc.get(g, -1) for g in bg])
    ll = torch.tensor([loc.get(g, -1) for g in lg])
    return Mm, Uu, bl, ll


def l_comp(h, Mm, Uu, bl, ll, tau=0.2):
    """InfoNCE: mỗi cặp dương (b, l+) chọi với MỌI ống l- có M = 0 ∧ U = 0 của thân b; sim = cosine."""
    hb = F.normalize(h[bl.clamp(min=0)], dim=1)
    hl = F.normalize(h[ll.clamp(min=0)], dim=1)
    S = hb @ hl.T / tau                                          # [537, 1033]
    neg = ~Mm & ~Uu
    lse_neg = torch.logsumexp(S.masked_fill(~neg, -float("inf")), 1)        # log Σ_{l-} exp(s)
    s_pos = S[Mm]
    rows_ = Mm.nonzero()[:, 0]
    return (torch.logaddexp(s_pos, lse_neg[rows_]) - s_pos).mean()


def probe_cakg(train):
    A = norm_adj(train).to(DEV)
    E0 = nn.Parameter(torch.randn(C.N_USERS + C.N_ITEMS, D, device=DEV) * 0.01)
    itype = C.load_item_type()
    g = torch.Generator(device=DEV).manual_seed(0)
    for with_acc in (False, True):
        ei, et, names, loc, n, counts = build_h(with_acc)
        R = len(names)
        log(f"\nĐồ thị con H ({'H_pk' if with_acc else 'H_loi'}): {n:,} nút ({len(loc):,} item), "
            f"{ei.size(1):,} cạnh (cả chiều rev_), {R} quan hệ")
        for k, v in counts.items():
            log(f"    {k:32s} {v:7,} cạnh xuôi")
        ei, et = ei.to(DEV), et.to(DEV)
        perm = torch.randperm(ei.size(1), generator=torch.Generator().manual_seed(0)).to(DEV)
        if not with_acc:
            conv = RGATConv(D, D, R, attention_mechanism="within-relation",
                            attention_mode="additive-self-attention", heads=1).to(DEV)
            xx = nn.Parameter(torch.randn(n, D, device=DEV) * 0.01)

            def step_pyg():
                xx.grad = None
                conv.zero_grad()
                conv(xx, ei, et).pow(2).mean().backward()
            sec, peak = timed(step_pyg, n=2)
            log(f"  RGATConv của PyG, MỘT lớp, forward + backward trên toàn H: {sec * 1000:,.0f} ms | đỉnh GPU "
                f"{mib(peak)} (GPU 6 GB: phần vượt tràn sang bộ nhớ chung của Windows, rất chậm)")
            del conv, xx
            torch.cuda.empty_cache()
        d_out, d_att = check_rgat_equal(ei[:, perm], et[perm], R)
        log(f"  RGATLayer (tự cài) so với RGATConv của PyG trên 20.000 cạnh ngẫu nhiên, cùng trọng số: "
            f"lệch đầu ra tối đa {d_out:.2e}, lệch hệ số attention tối đa {d_att:.2e}")
        enc = HwEncoder(n, R).to(DEV)
        fu, fi = Fusion().to(DEV), Fusion().to(DEV)
        # chỉ số cục bộ của mọi item (−1 = không có nút trong H)
        item_loc = torch.full((C.N_ITEMS,), -1, dtype=torch.long)
        for gi, li in loc.items():
            item_loc[gi] = li
        item_loc = item_loc.to(DEV)
        has_hi = item_loc >= 0
        # h_u = trung bình h_b trên các thân trong train ("owns" = interacted_with tới thân)
        ur, uc, uv = [], [], []
        for u, its in train.items():
            bs = [loc[i] for i in its if itype[i] == 0 and i in loc]
            for b in bs:
                ur.append(u)
                uc.append(b)
                uv.append(1.0 / len(bs))
        Aub = torch.sparse_coo_tensor(torch.tensor([ur, uc]), torch.tensor(uv), (C.N_USERS, n)).coalesce().to(DEV)
        has_hu = torch.zeros(C.N_USERS, dtype=torch.bool)
        has_hu[torch.tensor(sorted(set(ur)))] = True
        has_hu = has_hu.to(DEV)
        Mm, Uu, bl, ll = [t.to(DEV) for t in lcomp_setup(loc)]
        log(f"  người có h_u (có thân trong H): {int(has_hu.sum()):,}; item có h_i: {int(has_hi.sum()):,}; "
            f"thân / ống của M có nút: {int((bl >= 0).sum())} / {int((ll >= 0).sum())}")
        params = [E0, *enc.parameters(), *fu.parameters(), *fi.parameters()]
        n_par = sum(p.numel() for p in [*enc.parameters(), *fu.parameters(), *fi.parameters()])
        log(f"  tham số thêm so với LightGCN (RGAT + gộp kênh): {n_par:,}")

        def forward_all():
            Ek, acc = E0, E0
            for _ in range(3):
                Ek = torch.sparse.mm(A, Ek)
                acc = acc + Ek
            Ef = acc / 4
            eU, eI = Ef[:C.N_USERS], Ef[C.N_USERS:]
            h, _ = enc(ei, et)
            hI = h[item_loc.clamp(min=0)]
            hU = torch.sparse.mm(Aub, h)
            zU, _ = fu(eU, hU, has_hu)
            zI, _ = fi(eI, hI, has_hi)
            return zU, zI, h

        for bs in (2048,):
            def step():
                zU, zI, h = forward_all()
                u = torch.randint(0, C.N_USERS, (bs,), device=DEV, generator=g)
                p = torch.randint(0, C.N_ITEMS, (bs,), device=DEV, generator=g)
                q = torch.randint(0, C.N_ITEMS, (bs,), device=DEV, generator=g)
                for prm in params:
                    prm.grad = None
                bpr = F.softplus(-((zU[u] * zI[p]).sum(1) - (zU[u] * zI[q]).sum(1))).mean()
                loss = bpr + 0.1 * l_comp(h, Mm, Uu, bl, ll)
                loss.backward()
            sec, peak = timed(step)
            nb = -(-460193 // bs)
            log(f"  CaKG-Rec batch {bs}: {sec * 1000:,.0f} ms/bước × {nb} = {sec * nb:,.1f} s/epoch "
                f"(chưa tính âm mẫu, chấm val) | đỉnh GPU {mib(peak)}")

        def step_lc():
            h, _ = enc(ei, et)
            for prm in enc.parameters():
                prm.grad = None
            l_comp(h, Mm, Uu, bl, ll).backward()
        sec, peak = timed(step_lc)
        log(f"  riêng RGAT + L_comp (không LightGCN): {sec * 1000:,.1f} ms/bước | đỉnh GPU {mib(peak)}")

        with torch.no_grad():
            h, att = enc(ei, et, want_att=True)
            log(f"  return_attention_weights ở lớp 2: hệ số {tuple(att.shape)}")
            # kiểm WIRGAT: với mỗi (đích, quan hệ), tổng hệ số = 1
            key = ei[1] * R + et
            ssum = torch.zeros(int(key.max()) + 1, device=DEV).index_add_(0, key, att.view(-1))
            used = torch.unique(key)
            log(f"    WIRGAT: tổng hệ số theo (nút đích, quan hệ): min {float(ssum[used].min()):.4f}, "
                f"max {float(ssum[used].max()):.4f}")
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
            t = time.perf_counter()
            zU, zI, _ = forward_all()
            torch.cuda.synchronize()
            log(f"  một lần tính biểu diễn mọi người / mọi item (eval, no_grad): "
                f"{(time.perf_counter() - t) * 1000:,.0f} ms | đỉnh GPU {mib(torch.cuda.max_memory_allocated())}")
        keep = (zU.detach(), zI.detach(), loc, has_hi)
        del enc, fu, fi
        torch.cuda.empty_cache()
    del A, E0
    torch.cuda.empty_cache()
    return keep


# ── KGAT ──────────────────────────────────────────────────────────────────────

def ckg():
    data = torch.load(str(C.KG_PT), weights_only=False)
    offs, n = {}, 0
    for nt in data.node_types:
        offs[nt] = n
        n += data[nt].num_nodes
    srcs, dsts, rels = [], [], []
    n_kg_fwd = 0
    for r, et in enumerate(data.edge_types):
        s, rel, d = et
        st = data[et]
        keep = torch.ones(st.edge_index.size(1), dtype=torch.bool)
        if "ngam_khong_chac" in st:
            keep = st.ngam_khong_chac.view(-1) == 0
        srcs.append(st.edge_index[0, keep] + offs[s])
        dsts.append(st.edge_index[1, keep] + offs[d])
        rels.append(torch.full((int(keep.sum()),), r))
        if not rel.startswith("rev_") and rel != "interacted_with":
            n_kg_fwd += int(keep.sum())
    return torch.stack([torch.cat(srcs), torch.cat(dsts)]), torch.cat(rels), len(data.edge_types), n, offs, n_kg_fwd


def probe_kgat():
    ei, et, R, n, offs, n_kg_fwd = ckg()
    log(f"\nKGAT, đồ thị cộng tác: {n:,} nút, {ei.size(1):,} cạnh (cả rev_), {R} quan hệ; "
        f"bộ ba tri thức xuôi (không tính interacted_with) {n_kg_fwd:,}; cả rev_ {2 * n_kg_fwd:,}; "
        f"cả interacted_with và rev_ {ei.size(1):,}")
    ei, et = ei.to(DEV), et.to(DEV)
    g = torch.Generator(device=DEV).manual_seed(0)
    E = nn.Parameter(torch.randn(n, D, device=DEV) * 0.01)
    Er = nn.Parameter(torch.randn(R, D, device=DEV) * 0.01)
    Wr = nn.Parameter(torch.randn(R, D, D, device=DEV) * 0.01)
    dims = [64, 64, 32, 16]
    W1 = nn.ModuleList([nn.Linear(dims[k], dims[k + 1]) for k in range(3)]).to(DEV)
    W2 = nn.ModuleList([nn.Linear(dims[k], dims[k + 1]) for k in range(3)]).to(DEV)
    params = [E, Er, Wr, *W1.parameters(), *W2.parameters()]
    head, tail = ei[0], ei[1]   # bộ ba (h, r, t): tin đi từ t về h (N_h = các bộ ba có đầu h)

    by_rel = [(r, (et == r).nonzero().view(-1)) for r in range(R)]

    def attention():
        parts, idxs = [], []
        for r, ix in by_rel:                                   # W_r e cho cạnh của quan hệ r, không tạo [E, d, d]
            wt = E[tail[ix]] @ Wr[r].T
            wh = E[head[ix]] @ Wr[r].T
            parts.append((wt * torch.tanh(wh + Er[r])).sum(1))
            idxs.append(ix)
        out = torch.empty(ei.size(1), device=DEV).index_put((torch.cat(idxs),), torch.cat(parts))
        return pyg_softmax(out, head, num_nodes=n)

    def propagate(pi):
        h, layers = E, [E]
        for k in range(3):
            eN = torch.zeros(n, h.size(1), device=DEV).index_add_(0, head, pi[:, None] * h[tail])
            h = F.leaky_relu(W1[k](h + eN)) + F.leaky_relu(W2[k](h * eN))
            layers.append(F.normalize(h, dim=1))
        return torch.cat(layers, 1)

    def cf_step(pi_fn):
        def step():
            pi = pi_fn()
            Z = propagate(pi)
            u = torch.randint(0, C.N_USERS, (1024,), device=DEV, generator=g) + offs["user"]
            p = torch.randint(0, C.N_ITEMS, (1024,), device=DEV, generator=g) + offs["item"]
            q = torch.randint(0, C.N_ITEMS, (1024,), device=DEV, generator=g) + offs["item"]
            for prm in params:
                prm.grad = None
            F.softplus(-((Z[u] * Z[p]).sum(1) - (Z[u] * Z[q]).sum(1))).mean().backward()
        return step

    nb_cf = -(-460193 // 1024)
    sec, peak = timed(cf_step(attention), n=3)
    log(f"  (a) attention có gradient mỗi bước, CF batch 1024: {sec * 1000:,.0f} ms/bước × {nb_cf} = "
        f"{sec * nb_cf / 60:,.1f} phút/epoch | đỉnh GPU {mib(peak)}")
    with torch.no_grad():
        torch.cuda.synchronize()
        t = time.perf_counter()
        pi_fixed = attention()
        torch.cuda.synchronize()
        t_att = time.perf_counter() - t
    sec, peak = timed(cf_step(lambda: pi_fixed), n=3)
    log(f"  (b) attention cố định (tính lại 1 lần / epoch, {t_att * 1000:,.0f} ms), CF batch 1024: "
        f"{sec * 1000:,.0f} ms/bước × {nb_cf} = {sec * nb_cf / 60:,.1f} phút/epoch | đỉnh GPU {mib(peak)}")

    def kg_step():
        idx = torch.randint(0, ei.size(1), (2048,), device=DEV, generator=g)
        h_, r_, t_ = head[idx], et[idx], tail[idx]
        t2 = torch.randint(0, n, (2048,), device=DEV, generator=g)
        w = Wr[r_]                                             # 2048 × 64 × 64, nhỏ

        def sc(t):
            return (torch.bmm(w, E[h_].unsqueeze(-1)).squeeze(-1) + Er[r_]
                    - torch.bmm(w, E[t].unsqueeze(-1)).squeeze(-1)).pow(2).sum(1)
        for prm in params:
            prm.grad = None
        F.softplus(-(sc(t2) - sc(t_))).mean().backward()
    sec, peak = timed(kg_step)
    log(f"  bước TransR (L_KG) batch 2048 (batch_size_kg mặc định của code tác giả): {sec * 1000:,.1f} ms/bước; "
        f"{-(-ei.size(1) // 2048)} bước / epoch nếu dùng mọi bộ ba kể cả interacted_with và rev_ (như code tác giả) "
        f"= {sec * -(-ei.size(1) // 2048):,.1f} s | đỉnh GPU {mib(peak)}")
    del E, Er, Wr, W1, W2, pi_fixed
    torch.cuda.empty_cache()


# ── độ trễ một yêu cầu ────────────────────────────────────────────────────────

def probe_latency(train, zU, zI, loc, has_hi):
    itype = C.load_item_type()
    ctx = C.load_cvr_context()
    bodies = C.build_train_bodies(train, None, itype)
    m1 = defaultdict(set)
    for f in ("kg_edges_compatible_with.csv", "kg_edges_crops_sensor.csv"):
        for r in rows(f):
            m1[int(r["lens_iid"])].add(int(r["body_iid"]))
    suit = defaultdict(list)
    for r in rows("kg_edges_suitable_for.csv"):
        suit[int(r["iid"])].append(r["usecase"])
    import importlib
    sys.path.insert(0, "ai/pipeline")
    E = importlib.import_module("eval_05")
    lens, cmask = E.certain_violation_mask(bodies, ctx)
    lens_t = torch.as_tensor(lens)
    rng = np.random.default_rng(0)
    users = rng.choice(C.N_USERS, 1000, replace=False)
    hbody = zI  # dùng biểu diễn item làm h_b giả để tính đóng góp từng thân (chỉ đo giờ)
    for dev in (DEV, torch.device("cpu")):
        ZU, ZI = zU.to(dev), zI.to(dev)
        lt = lens_t.to(dev)
        times = []
        n_path = 0
        for u in users.tolist():
            if dev.type == "cuda":
                torch.cuda.synchronize()
            t = time.perf_counter()
            s = ZU[u] @ ZI.T
            tr = torch.as_tensor(sorted(train[u]), device=dev)
            s[tr] = -float("inf")
            mrow = torch.as_tensor(cmask[u], device=dev)
            s[lt[mrow]] = -float("inf")
            top = torch.topk(s, 10).indices.tolist()
            bs = bodies.get(u, set())
            for l in top:
                if itype[l] != 1:
                    continue
                cand = m1[l] & bs
                if cand:
                    b = max(cand, key=lambda b_: float(hbody[b_, D:].to(dev) @ ZI[l, D:]))
                    c = suit[l][0] if suit[l] else None
                    n_path += 1
            times.append(time.perf_counter() - t)
        a = np.array(times) * 1000
        log(f"  {dev.type.upper():4s}: p50 {np.percentile(a, 50):.2f} ms, p95 {np.percentile(a, 95):.2f} ms, "
            f"max {a.max():.2f} ms (1.000 người; điểm + bỏ train + mặt nạ QĐ 4-9 + top-10 + đường giải thích; "
            f"{n_path} đường dựng được, biểu diễn ngẫu nhiên)")


def main(out_log: Path) -> None:
    assert not out_log.exists(), f"log đã có, không ghi đè: {out_log}"
    head, dirty = git_state()
    log(f"script {__file__} (sha256 {sha256_file(__file__)[:16]}…) | git HEAD {head}, có thay đổi chưa commit: {dirty}")
    log(f"GPU {torch.cuda.get_device_name(0)} | torch {torch.__version__} | RAM trống "
        f"{mib(psutil.virtual_memory().available)}")
    log("Trọng số ngẫu nhiên, không optimizer.step, không chấm val / test.")
    train = C.load_train()
    zU, zI, loc, has_hi = probe_cakg(train)
    probe_kgat()
    log("\nĐộ trễ một yêu cầu (biểu diễn tính sẵn 67.661 × 128 và 27.940 × 128):")
    probe_latency(train, zU.cpu(), zI.cpu(), loc, has_hi)
    log(f"\nRSS tiến trình (cuối chương trình) ≈ {mib(psutil.Process().memory_info().rss)}")
    out_log.parent.mkdir(parents=True, exist_ok=True)
    out_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"-> {out_log}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
