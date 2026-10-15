"""
eval_cakg.py -- Phần đánh giá thêm cho nội dung 6–8 (docs/cakg_design.md khối 7–8; kế hoạch đăng ký trước
docs/reviews/cakg_eval_plan.md mục 5, 10, 11, 12). Viết 14/10/2026. Dùng lại eval_05 (full ranking, CVR QĐ 4-9,
kịch bản, sampled), KHÔNG sửa eval_05. Kiểm thử dựng tay: ai/survey/cakg/test_eval_cakg.py.

Ví dụ (thiết kế khối 7, người có Sony a7 + Nikon D750; top-4: Nikon 200-500, Canon EF 70-200, thẻ nhớ, Sony FE 50):
  CVR trước mặt nạ @4 = 1 / 3; mặt nạ (15) QĐ 4-9 chặn Canon EF (mọi thân M = 0) -> CVR sau = 0 (do cách dựng);
  mặt nạ (16) ∃b chặn thêm Nikon 200-500 (a7 M = 0) và Sony FE 50 (D750 M = 0).

Gồm:
  - mặt nạ (15) = eval_05.certain_violation_mask; mặt nạ (16) ∃b: exists_violation_mask; mask_scorer (công thức 17);
  - CVR_relaxed R1 / R2 (công thức 19–22) từ top-K đã xếp: relaxed_context, cvr_relaxed_from_top;
  - đường giải thích (23), b* theo đóng góp (24), c* theo α lớp 2 trên rev_suitable_for, câu tiếng Việt, kiểm mọi
    cạnh được nhắc có trong đồ thị: PathContext, Explainer, sentence, verify_explanation;
  - Path Coverage (25): pc_from_top;
  - Faithfulness (26): faithfulness (bỏ đúng các cạnh của đường, chạy lại RGAT, xếp lại, áp mặt nạ) + đối chứng ngẫu nhiên;
  - evaluate_with_masks: chấm một mô hình trước mặt nạ, sau mặt nạ (15) và sau mặt nạ ∃b (16), kèm CVR_relaxed, PC,
    số người mất item cần đoán vì mặt nạ; lưu mảng từng người (kế hoạch mục 12);
  - load_lightgcn: dựng lại LightGCN nội dung 5 từ best.pt (không huấn luyện lại) để chấm "LightGCN + mặt nạ".
"""

import csv
import importlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402

KG = C.DATA_DIR / "kg"
FAITH_SEED = 20261014          # chọn tối đa 2.000 cặp cho Faithfulness (kế hoạch mục 5)
USECASE_VI = {"phong_canh": "phong cảnh", "the_thao_chim": "thể thao / chim", "chan_dung": "chân dung",
              "macro": "macro"}


def _rows(name):
    with open(KG / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# -- Mặt nạ ------------------------------------------------------------------

def exists_violation_mask(bodies, ctx, n_users=None):
    """(16) biến thể ∃b của khung: True ở (u, l) nếu l ∈ ℐ_M và ∃b ∈ B_u ∩ ℬ_M có M_bl = 0 ∧ U_bl = 0.
    Cột theo cùng thứ tự với eval_05.certain_violation_mask (ống trong M tăng dần theo iid)."""
    lens = np.array(sorted(ctx.lenses_in_m), dtype=np.int64)
    col = {int(l): j for j, l in enumerate(lens)}
    ok = defaultdict(lambda: np.zeros(len(lens), bool))          # thân -> ô M = 1 hoặc U = 1
    for (b, l) in ctx.m1:
        ok[b][col[l]] = True
    for (b, l) in ctx.unknown:
        if l in col:
            ok[b][col[l]] = True
    mask = np.zeros((C.N_USERS if n_users is None else n_users, len(lens)), bool)
    for u, bs in bodies.items():
        for b in bs:
            if b in ctx.bodies_in_m:
                mask[u] |= ~ok[b]
    return lens, mask


def mask_scorer(score_batch, lens_t, cmask_t):
    """(17) ŷ' = ŷ + 𝓜: −∞ ở các ống bị chặn (cùng định nghĩa với 06_cakg_train.mask_scorer)."""
    def f(uids):
        S = score_batch(uids)
        S[:, lens_t] = S[:, lens_t].masked_fill(cmask_t[uids], -float("inf"))
        return S
    return f


def masks_on_device(ev, device=E.DEVICE):
    """{"qd49": (lens_t, mask_t), "exists": (lens_t, mask_t)} cho người dùng của ev."""
    l1, m1 = E.certain_violation_mask(ev.bodies, ev.ctx)
    l2, m2 = exists_violation_mask(ev.bodies, ev.ctx)
    assert np.array_equal(l1, l2)
    lt = torch.as_tensor(l1, device=device)
    return {"qd49": (lt, torch.as_tensor(m1, device=device)), "exists": (lt, torch.as_tensor(m2, device=device))}


# -- CVR_relaxed (19)–(22) ---------------------------------------------------

@dataclass
class RelaxedContext:
    mount: dict          # iid -> ngàm (item_attributes.csv)
    ab: dict             # uid -> {"m_ống>m_thân"} ngàm chuyển trong train (19)
    named: dict          # uid -> {ngàm} phụ kiện MỘT ngàm có chữ "adapter" trong tiêu đề (21)
    ra: set              # cặp (thân, ống) requires_adapter


def relaxed_context(train, bodies):
    attrs = {int(r["iid"]): r for r in _rows("item_attributes.csv")}
    ab = {i: r["mount"] for i, r in attrs.items() if r["item_type"] == "phu_kien" and ">" in r["mount"]}
    named = {i: r["mount"] for i, r in attrs.items() if r["item_type"] == "phu_kien" and ">" not in r["mount"]
             and r["mount"] not in ("khong_co", "khong_ro", "nhieu", "") and "adapter" in r["title"].lower()}
    return RelaxedContext(mount={i: r["mount"] for i, r in attrs.items()},
                          ab={u: {ab[i] for i in train[u] if i in ab} for u in bodies},
                          named={u: {named[i] for i in train[u] if i in named} for u in bodies},
                          ra={(int(r["body_iid"]), int(r["lens_iid"])) for r in _rows("kg_edges_requires_adapter.csv")})


def relax_flags(u, l, bs, rc):
    """(r1, r2) cho ống l đã bị tính vi phạm strict với người u (thân bs).
    R1 (20): ∃b ∈ B_u: (mount(l), mount(b)) ∈ 𝒜_u.  R2 (21) = R1 hoặc ∃b ∈ B_u: (b, l) requires_adapter và u có phụ
    kiện một ngàm chữ "adapter" cùng ngàm với b."""
    lm = rc.mount[l]
    bms = {rc.mount[b] for b in bs}
    r1 = any(x.split(">")[0] == lm and x.split(">")[1] in bms for x in rc.ab.get(u, ()))
    r2 = r1 or any((b, l) in rc.ra and rc.mount[b] in rc.named.get(u, ()) for b in bs)
    return r1, r2


def cvr_relaxed_from_top(users, top, bodies, item_type, ctx, rc, k_list=E.K_LIST):
    """(18), (22): CVR_strict và CVR_relaxed R1 / R2 (mẫu số giữ như strict). Trả về (tổng hợp, từng người):
    từng người = {k: (n_lenses, n_viol, n_r1, n_r2)} mảng theo users."""
    n = len(users)
    kmax = max(k_list)
    per = {k: tuple(np.zeros(n, np.int64) for _ in range(4)) for k in k_list}
    for r, u in enumerate(users.tolist()):
        bs = bodies.get(u)
        if not bs:
            continue
        flags = []
        for i in top[r, :kmax].tolist():
            v = C.judge_lens(int(i), bs, ctx) if item_type[i] == 1 else None
            flags.append((v, *(relax_flags(u, int(i), bs, rc) if v else (False, False))))
        for k in k_list:
            fk = [f for f in flags[:k] if f[0] is not None]
            per[k][0][r] = len(fk)
            per[k][1][r] = sum(f[0] for f in fk)
            per[k][2][r] = sum(f[1] for f in fk)
            per[k][3][r] = sum(f[2] for f in fk)
    out = {}
    for k in k_list:
        nl, nv, n1, n2 = (a.sum() for a in per[k])
        out[f"cvr_strict@{k}"] = float(nv / nl) if nl else float("nan")
        out[f"cvr_relaxed_r1@{k}"] = float((nv - n1) / nl) if nl else float("nan")
        out[f"cvr_relaxed_r2@{k}"] = float((nv - n2) / nl) if nl else float("nan")
        out[f"n_lenses@{k}"], out[f"n_violations@{k}"] = int(nl), int(nv)
        out[f"n_relaxed_r1@{k}"], out[f"n_relaxed_r2@{k}"] = int(n1), int(n2)
        out[f"n_users_relaxed_r2@{k}"] = int((per[k][3] > 0).sum())
    return out, per


# -- Đường giải thích (23), (24), câu tiếng Việt, Path Coverage (25) -------------

class PathContext:
    """Các cạnh của đồ thị dùng cho đường u –owns→ b –ρ→ l –suitable_for→ c (ρ ∈ {compatible_with, crops_sensor})."""

    def __init__(self, train, item_type):
        self.train, self.item_type = train, item_type
        self.attrs = {int(r["iid"]): r for r in _rows("item_attributes.csv")}
        self.rho = {}                                  # (thân, ống) -> "compatible_with" | "..._crop_unknown" | "crops_sensor"
        for r in _rows("kg_edges_compatible_with.csv"):
            self.rho[(int(r["body_iid"]), int(r["lens_iid"]))] = \
                "compatible_with" + ("_crop_unknown" if r["crop_unknown"] == "1" else "")
        for r in _rows("kg_edges_crops_sensor.csv"):
            key = (int(r["body_iid"]), int(r["lens_iid"]))
            assert key not in self.rho
            self.rho[key] = "crops_sensor"
        self.m1_by_lens = defaultdict(set)
        for (b, l) in self.rho:
            self.m1_by_lens[l].add(b)
        self.suit = defaultdict(list)                  # ống -> [nhãn mục đích] theo thứ tự file
        for r in _rows("kg_edges_suitable_for.csv"):
            self.suit[int(r["iid"])].append(r["usecase"])
        self.mount_edge = {}                           # thân / ống chắc chắn -> ngàm (has_spec_mount, không cờ)
        for r in _rows("kg_edges_has_spec_mount.csv"):
            if r["src_phu_kien"] == "0" and r["ngam_khong_chac"] == "0":
                self.mount_edge[int(r["iid"])] = r["mount"]
        self.focal = {}
        for r in _rows("kg_edges_has_spec_focal_range.csv"):
            self.focal.setdefault(int(r["iid"]), (r["f1"], r["f2"]))
        self.aperture = {int(r["iid"]): (r["a1"], r["a2"]) for r in _rows("kg_edges_has_spec_aperture_class.csv")}

    def bodies_for(self, u, l, bodies_h):
        """Các thân b ∈ B_u^H có M_bl = 1 (đường ngắn u → b → l tồn tại)."""
        return [b for b in bodies_h.get(u, ()) if (b, l) in self.rho]


def pc_from_top(users, top, bodies, item_type, ctx, pctx, k_list=(5, 10)):
    """(25) Path Coverage trên top-K (đã áp mặt nạ hay chưa là do top truyền vào), người có thân.
    Đếm: n_items (mọi sản phẩm), n_lenses (mọi ống), n_judgable (ống chấm được QĐ 4-9), n_short (có đường u → b → l),
    n_full (có đủ u → b → l → c). PC = n_full / n_lenses; PC_ngắn = n_short / n_lenses; PC_mọi_sp = n_full / n_items."""
    out, per = {}, {}
    for k in k_list:
        cnt = np.zeros((len(users), 5), np.int64)
        for r, u in enumerate(users.tolist()):
            bs = bodies.get(u)
            if not bs:
                continue
            for i in top[r, :k].tolist():
                cnt[r, 0] += 1
                if item_type[i] != 1:
                    continue
                cnt[r, 1] += 1
                cnt[r, 2] += C.judge_lens(int(i), bs, ctx) is not None
                if any((b, i) in pctx.rho for b in bs):
                    cnt[r, 3] += 1
                    cnt[r, 4] += i in pctx.suit
        s = cnt.sum(0)
        out[f"pc@{k}"] = float(s[4] / s[1]) if s[1] else float("nan")
        out[f"pc_ngan@{k}"] = float(s[3] / s[1]) if s[1] else float("nan")
        out[f"pc_moi_sp@{k}"] = float(s[4] / s[0]) if s[0] else float("nan")
        for j, nm in enumerate(["n_items", "n_lenses", "n_judgable", "n_short", "n_full"]):
            out[f"{nm}@{k}"] = int(s[j])
        per[k] = cnt
    return out, per


def _short(t, n=70):
    return t if len(t) <= n else t[:n - 1].rstrip() + "…"


def _focal_txt(f):
    f1, f2 = f
    return f1 if (not f2 or f2 == f1) else f"{f1}-{f2}"


def _aperture_txt(a):
    a1, a2 = a
    return a1 if (not a2 or a2 == a1) else f"{a1}-{a2}"


class Explainer:
    """Dựng đường giải thích (23) cho (u, l) từ biểu diễn của CaKG-Rec (comps = model.components(), chuyển về CPU).
      b* = argmax_{b ∈ B_u^H, M_bl = 1} c_u(b, l),  c_u(b, l) = β_{u,h} β_{l,h} h_bᵀh_l / |B_u^H|   (24); hòa: iid nhỏ hơn.
      c* = nhãn mục đích có α lớn nhất ở lớp RGAT 2 trên quan hệ rev_suitable_for vào l (5); hòa: thứ tự nút trong đồ thị.
    Σ_{b ∈ B_u^H} c_u(b, l) = β_{u,h}β_{l,h} h_uᵀh_l = phần phần cứng của ŷ_ul (công thức 7, 9): phân rã chính xác."""

    def __init__(self, comps, H, bodies_h, pctx):
        self.c = {k: (v.detach().cpu() if torch.is_tensor(v) else v) for k, v in comps.items()}
        self.H, self.bodies_h, self.pctx = H, bodies_h, pctx
        self.suit_edges = defaultdict(list)          # chỉ số nút cục bộ của ống -> [(chỉ số cạnh, thứ tự nhãn, tên nhãn)]
        if "rev_suitable_for" in H.rel_names:
            r = H.rel_names.index("rev_suitable_for")
            sel = torch.nonzero(H.et.cpu() == r).view(-1).tolist()
            src, dst = H.ei[0].cpu().tolist(), H.ei[1].cpu().tolist()
            for e in sel:
                k = src[e] - H.off["usecase"]
                self.suit_edges[dst[e]].append((e, k, H.node_names["usecase"][k]))

    def contributions(self, u, l, bodies):
        h, loc = self.c["h"], self.H.item_loc
        bu, bl = float(self.c["betaU"][u, 1]), float(self.c["betaI"][l, 1])
        nb = len(self.bodies_h[u])
        hl = h[loc[l]]
        return {b: bu * bl * float(h[loc[b]] @ hl) / nb for b in bodies}

    def explain(self, u, l):
        """dict đường giải thích, hoặc None nếu không có thân nào của u có M = 1 với l (không có đường ngắn)."""
        cand = self.pctx.bodies_for(u, l, self.bodies_h)
        if not cand:
            return None
        contrib = self.contributions(u, l, cand)
        b_star = min(cand, key=lambda b: (-contrib[b], b))
        c_star = alpha_c = None
        es = self.suit_edges.get(self.H.item_loc[l], [])
        if es:
            a = self.c["alpha2"]
            e, _, name = min(es, key=lambda t: (-float(a[t[0]]), t[1]))
            c_star, alpha_c = name, float(a[e])
        return {"u": u, "l": l, "b_star": b_star, "rho": self.pctx.rho[(b_star, l)], "c_star": c_star,
                "alpha_c": alpha_c, "contrib": contrib, "n_bodies_h": len(self.bodies_h[u]), "cand_bodies": cand}


def sentence(ex, pctx):
    """Câu tiếng Việt theo mẫu ở thiết kế khối 8; mọi chỗ điền đều lấy từ đồ thị (verify_explanation kiểm)."""
    at = pctx.attrs
    ln, bn = _short(at[ex["l"]]["title"]), _short(at[ex["b_star"]]["title"])
    mount = pctx.mount_edge[ex["b_star"]]
    if ex["rho"] == "compatible_with":
        s = f"Gợi ý {ln} vì ống này lắp trực tiếp được trên {bn} bạn đã mua (ngàm {mount})"
    elif ex["rho"] == "crops_sensor":
        s = (f"Gợi ý {ln} vì ống này lắp trực tiếp được trên {bn} bạn đã mua (ngàm {mount}), nhưng ống thiết kế cho "
             f"cảm biến nhỏ hơn nên ảnh sẽ bị cắt khung")
    else:
        s = (f"Gợi ý {ln} vì ống này lắp được trên {bn} bạn đã mua (ngàm {mount}); chưa rõ máy có tự cắt khung với "
             f"ống này không")
    if ex["c_star"] is not None:
        s += f", và phù hợp chụp {USECASE_VI[ex['c_star']]}"
        spec = []
        if ex["l"] in pctx.focal:
            spec.append(f"tiêu cự {_focal_txt(pctx.focal[ex['l']])} mm")
        if ex["l"] in pctx.aperture:
            spec.append(f"khẩu độ tối đa f/{_aperture_txt(pctx.aperture[ex['l']])}")
        if spec:
            s += " (" + ", ".join(spec) + ")"
    return s + "."


def verify_explanation(ex, s, pctx, H_has_edge):
    """Mọi sự kiện trong câu có trong đồ thị. H_has_edge(src_iid | ('usecase', tên), dst, rel) -> bool (cạnh của H).
    Trả về danh sách lỗi (rỗng = đúng)."""
    err = []
    u, l, b, at = ex["u"], ex["l"], ex["b_star"], pctx.attrs
    if b not in pctx.train[u] or pctx.item_type[b] != 0:
        err.append("owns: b* không phải thân trong train của u")
    if at[b]["may_phim"] == "True":
        err.append("b* là máy phim (không được có cạnh M = 1)")
    if pctx.rho.get((b, l)) != ex["rho"] or not H_has_edge(b, l, ex["rho"]) or not H_has_edge(l, b, "rev_" + ex["rho"]):
        err.append(f"cạnh {ex['rho']} (b*, l) không có trong đồ thị / H")
    mb = pctx.mount_edge.get(b)               # ngàm nêu trong câu là ngàm của THÂN (vd ống EF trên thân EF-S: canon_efs)
    if mb is None or not H_has_edge(b, ("mount", mb), "has_spec_mount"):
        err.append("thân b* không có cạnh has_spec_mount tới ngàm nêu trong câu")
    if f"(ngàm {mb})" not in s:
        err.append("câu không nhắc đúng ngàm của b*")
    if _short(at[l]["title"]) not in s or _short(at[b]["title"]) not in s:
        err.append("câu không nhắc đúng tên l / b*")
    if ex["c_star"] is not None:
        if ex["c_star"] not in pctx.suit.get(l, []) or not H_has_edge(l, ("usecase", ex["c_star"]), "suitable_for"):
            err.append("cạnh suitable_for (l, c*) không có")
        if l in pctx.focal and f"tiêu cự {_focal_txt(pctx.focal[l])} mm" not in s:
            err.append("tiêu cự không khớp cạnh has_spec")
        if l in pctx.aperture and f"f/{_aperture_txt(pctx.aperture[l])}" not in s:
            err.append("khẩu độ không khớp cạnh has_spec")
    return err


def h_edge_checker(H):
    """Hàm kiểm cạnh có trong H theo iid / tên nút."""
    keys = set()
    for s, d, r in zip(H.ei[0].tolist(), H.ei[1].tolist(), H.et.tolist()):
        keys.add((s, d, H.rel_names[r]))

    def loc(x):
        if isinstance(x, tuple):
            return H.off[x[0]] + H.node_names[x[0]].index(x[1])
        return H.item_loc[x]

    def has(src, dst, rel):
        try:
            return (loc(src), loc(dst), rel) in keys
        except (KeyError, ValueError):
            return False
    return has


# -- Faithfulness (26) -------------------------------------------------------

def _drop_edges(H, pairs_rel):
    """Bỏ các cạnh (nguồn cục bộ, đích cục bộ, chỉ số quan hệ) khỏi H (cả hai chiều phải được truyền vào)."""
    keep = torch.ones(H.ei.size(1), dtype=torch.bool, device=H.ei.device)
    for s, d, r in pairs_rel:
        hit = (H.ei[0] == s) & (H.ei[1] == d) & (H.et == r)
        assert int(hit.sum()) == 1, (s, d, r, int(hit.sum()))
        keep &= ~hit
    return H.ei[:, keep], H.et[keep]


def path_edges(H, b, l, rho, c):
    """Các cạnh có hướng của đường (b –ρ→ l, l –suitable_for→ c) và chiều rev_ (một cạnh của đồ thị = 2 cạnh có hướng)."""
    R = H.rel_names
    lb, ll = H.item_loc[b], H.item_loc[l]
    out = [(lb, ll, R.index(rho)), (ll, lb, R.index("rev_" + rho))]
    if c is not None:
        lc = H.off["usecase"] + H.node_names["usecase"].index(c)
        out += [(ll, lc, R.index("suitable_for")), (lc, ll, R.index("rev_suitable_for"))]
    return out


@torch.no_grad()
def counterfactual_score_row(model, Hd, bodies_h, u, drop_body, cut_edges, eU, eI):
    """Điểm mọi sản phẩm của u trên đồ thị phản thực tế: bỏ drop_body khỏi B_u^H (tính lại h_u theo (7)), bỏ các cạnh
    cut_edges khỏi H (chạy lại RGAT). Kênh hành vi GIỮ NGUYÊN: dùng lại eU, eI đã tính (model.components()), không lan
    truyền lại LightGCN (phép nhân thưa trên GPU không tất định, lệch ~1e-7 giữa hai lần tính). Hd: HwGraph trên cùng
    thiết bị với model; bodies_h: B_u^H của cakg_model.user_body_matrix. drop_body = None, cut_edges = [] -> điểm của
    score_fn (chỉ lệch sai số của RGAT)."""
    ei, et = _drop_edges(Hd, cut_edges)
    h, alpha = model.enc(ei, et)
    bodies = [b for b in bodies_h.get(u, []) if b != drop_body]
    hu = torch.zeros(1, h.size(1), device=h.device)
    has_u = torch.tensor([len(bodies) > 0], device=h.device)
    if bodies:
        hu = h[torch.tensor([Hd.item_loc[b] for b in bodies], device=h.device)].mean(0, keepdim=True)
    hI = h[model.item_loc.clamp(min=0)]
    has_hi = model.has_hi
    if model.beta_h_zero:
        has_u, has_hi = torch.zeros_like(has_u), torch.zeros_like(has_hi)
    zu, _ = model.fu(eU[u:u + 1], hu, has_u)
    zI, _ = model.fi(eI, hI, has_hi)
    S = eU[u:u + 1] @ eI.T
    if bool(has_u[0]):
        S = torch.where(has_hi[None, :], zu @ zI.T, S)
    return S


C9_MIN_PAIRS = 30              # dưới số này cặp có đối chứng thân: C9 chỉ báo mô tả (Nam chốt 15/10/2026)


def faithfulness(model, Hd, bodies_h, ev, sp, masks_t, pctx, pairs, K=10, rng=None, log=print):
    """(26) FS_PN@K và ΔS cho các cặp (u, l) có đường ĐỦ 3 bước (u, b*, l, c*) trong top-K' (pairs: Explainer.explain).
    Phản thực tế của lời giải thích: bỏ b* khỏi B_u^H, bỏ cạnh (b*, l) loại ρ và (l, c*) suitable_for, cả hai chiều.
    Hai đối chứng ngẫu nhiên cùng dạng, mỗi đối chứng thay MỘT thành phần của đường (làm rõ 15/10/2026, kế hoạch mục 14):
      - đối chứng thân (dùng cho C9): (b', l, c*), b' lấy đều trong các thân khác b* của u có M_b'l = 1; không có b'
        thì cặp không có đối chứng thân;
      - đối chứng nhãn: (b*, l, c'), c' lấy đều trong các nhãn mục đích KHÁC c* của l; ống chỉ có một nhãn thì cặp
        không có đối chứng nhãn (đếm và báo).
    Xếp lại bằng eval_05.full_rank (cùng quy tắc hòa π) trên MỘT người, ứng viên như sp, áp mặt nạ masks_t.
    Trả về dict mảng theo cặp: drop (l rơi khỏi top-K' khi bỏ đường giải thích), dS, và với x ∈ {body, label}:
    has_ctrl_x, drop_ctrl_x, dS_ctrl_x."""
    rng = np.random.default_rng(FAITH_SEED) if rng is None else rng
    row_of = {int(u): r for r, u in enumerate(sp.users.tolist())}
    lens_t, cmask_t = masks_t
    comps = model.components()
    sf_full = mask_scorer(model.make_scorer(comps, model.hidx), lens_t, cmask_t)
    eU, eI = comps["eU"], comps["eI"]
    keys = ["u", "l", "drop", "dS"] + [f"{a}_{x}" for x in ("body", "label")
                                       for a in ("has_ctrl", "drop_ctrl", "dS_ctrl")]
    out = {k: [] for k in keys}

    def score_and_drop(u, l, b, rho, c, drop_body):
        S = counterfactual_score_row(model, Hd, bodies_h, u, drop_body, path_edges(Hd, b, l, rho, c), eU, eI)
        r = row_of[u]
        sub = E.Split(sp.name, sp.users[r:r + 1], sp.pos[r:r + 1], np.array([0, sp.excl_ptr[r + 1] - sp.excl_ptr[r]]),
                      sp.excl_col[sp.excl_ptr[r]:sp.excl_ptr[r + 1]])
        f = mask_scorer(lambda uids: S.clone(), lens_t, cmask_t)              # uids = [u] (một người)
        top = E.full_rank(f, sub, ev.pi, k_max=K, k_list=[K])["top"][0]
        return int(l not in top.tolist()), float(f(torch.as_tensor([u], device=E.DEVICE))[0, l])

    def put(x, has, d=0, ds=0.0):
        out[f"has_ctrl_{x}"].append(int(has))
        out[f"drop_ctrl_{x}"].append(d)
        out[f"dS_ctrl_{x}"].append(ds)

    for ex in pairs:
        u, l, b, c = ex["u"], ex["l"], ex["b_star"], ex["c_star"]
        assert c is not None, "Faithfulness chỉ đo đường đủ 3 bước (công thức 26)"
        s0 = float(sf_full(torch.as_tensor([u], device=E.DEVICE))[0, l])
        d, s = score_and_drop(u, l, b, ex["rho"], c, b)
        out["u"].append(u)
        out["l"].append(l)
        out["drop"].append(d)
        out["dS"].append(s0 - s)
        others = [x for x in ex["cand_bodies"] if x != b]
        if others:
            b2 = int(rng.choice(others))
            d2, s2 = score_and_drop(u, l, b2, pctx.rho[(b2, l)], c, b2)
            put("body", True, d2, s0 - s2)
        else:
            put("body", False)
        labels = [x for x in pctx.suit[l] if x != c]
        if labels:
            c2 = str(rng.choice(labels))
            d3, s3 = score_and_drop(u, l, b, ex["rho"], c2, b)
            put("label", True, d3, s0 - s3)
        else:
            put("label", False)
    return {k: np.asarray(v) for k, v in out.items()}


def faithfulness_summary(fs, B=2000, seed=E.BOOT_SEED, min_pairs=C9_MIN_PAIRS):
    """FS_PN@K, ΔS trên mọi cặp; so với từng đối chứng trên các cặp có đối chứng đó (bootstrap ghép cặp theo (u, l)).
    C9 (đăng ký) = đối chứng thân; dưới min_pairs cặp có đối chứng thân thì C9 chỉ là số mô tả (c9_chi_mo_ta)."""
    n = len(fs["drop"])
    res = {"n_pairs": int(n), "fs_pn": float(fs["drop"].mean()) if n else float("nan"),
           "dS_mean": float(fs["dS"].mean()) if n else float("nan")}
    for x in ("body", "label"):
        m = fs[f"has_ctrl_{x}"] == 1
        res[f"n_pairs_with_ctrl_{x}"] = int(m.sum())
        res[f"n_pairs_no_ctrl_{x}"] = int((~m).sum())
        if m.any():
            res[f"bootstrap_ctrl_{x}"] = E.bootstrap_paired(
                {"expl": (fs["drop"][m].astype(float), None), "ctrl": (fs[f"drop_ctrl_{x}"][m].astype(float), None),
                 "dS_expl": (fs["dS"][m], None), "dS_ctrl": (fs[f"dS_ctrl_{x}"][m], None)},
                pairs=[("expl", "ctrl"), ("dS_expl", "dS_ctrl")], B=B, seed=seed)
    res["c9_chi_mo_ta"] = res["n_pairs_with_ctrl_body"] < min_pairs
    return res


def sample_faith_pairs(expls, max_pairs=2000, seed=FAITH_SEED):
    """Chọn tối đa max_pairs cặp có đường ĐỦ 3 bước (c* không rỗng), seed cố định; thứ tự ổn định theo (u, l)."""
    full = sorted((e for e in expls if e["c_star"] is not None), key=lambda e: (e["u"], e["l"]))
    if len(full) <= max_pairs:
        return full
    idx = np.sort(np.random.default_rng(seed).choice(len(full), max_pairs, replace=False))
    return [full[i] for i in idx]


# -- Chấm một mô hình trước / sau mặt nạ ---------------------------------------

ALL_BRANCHES = ("truoc_mat_na", "mat_na_qd49", "mat_na_exists")


def evaluate_with_masks(score_batch, ev, rc, pctx, log=print, save_dir=None, tag="", branches=ALL_BRANCHES, masks=None):
    """Chấm trước mặt nạ, sau mặt nạ (15) QĐ 4-9 (chính) và sau mặt nạ (16) ∃b (song song, mô tả) — mọi nhánh từ CÙNG
    hàm điểm score_batch. Mỗi nhánh: mọi chỉ số của eval_05.evaluate (full ranking, CVR strict, kịch bản, sampled, loại
    sản phẩm), cộng CVR_relaxed R1 / R2, Path Coverage @5 / @10, số người có item cần đoán bị mặt nạ chặn (tổng và theo
    nhóm kịch bản). branches: tập con của ALL_BRANCHES; masks: kết quả masks_on_device(ev) (dựng một lần cho nhiều mô hình)."""
    masks = masks_on_device(ev) if masks is None else masks
    allb = {"truoc_mat_na": score_batch,
            "mat_na_qd49": mask_scorer(score_batch, *masks["qd49"]),
            "mat_na_exists": mask_scorer(score_batch, *masks["exists"])}
    branches = {b: allb[b] for b in branches}
    sp = ev.split
    out = {}
    for name, sf in branches.items():
        log(f"  --- {tag}{name} ---")
        sd = None
        if save_dir is not None:
            sd = Path(save_dir)
            sd.mkdir(parents=True, exist_ok=True)
        res = E.evaluate(sf, ev, log=log, save_dir=sd, prefix=f"{sp.name}_{name}_")
        fr = E.full_rank(sf, sp, ev.pi)
        rx, rx_pu = cvr_relaxed_from_top(sp.users, fr["top"], ev.bodies, ev.item_type, ev.ctx, rc)
        pc, pc_pu = pc_from_top(sp.users, fr["top"], ev.bodies, ev.item_type, ev.ctx, pctx)
        res["cvr_relaxed"], res["path_coverage"] = rx, pc
        log(f"  [{sp.name}] CVR strict / R1 / R2 @10: {rx['cvr_strict@10']:.4f} / {rx['cvr_relaxed_r1@10']:.4f} / "
            f"{rx['cvr_relaxed_r2@10']:.4f} ({rx['n_violations@10']:,} vi phạm, nới R1 {rx['n_relaxed_r1@10']:,}, "
            f"R2 {rx['n_relaxed_r2@10']:,}, trên {rx['n_lenses@10']:,} ống)")
        log(f"  [{sp.name}] Path Coverage @10: PC {pc['pc@10']:.4f} ({pc['n_full@10']:,}/{pc['n_lenses@10']:,} ống), "
            f"PC_ngắn {pc['pc_ngan@10']:.4f}, PC_mọi_sp {pc['pc_moi_sp@10']:.4f}")
        if name != "truoc_mat_na":
            lt, mt = masks["qd49" if name == "mat_na_qd49" else "exists"]
            col = {int(x): j for j, x in enumerate(lt.tolist())}
            mt_c = mt.cpu().numpy()
            blocked = np.array([p in col and bool(mt_c[u, col[p]]) for u, p in zip(sp.users.tolist(), sp.pos.tolist())])
            res["n_target_blocked"] = int(blocked.sum())
            res["n_target_blocked_by_scenario"] = {g: int((blocked & (ev.scn_lab == g)).sum())
                                                   for g in ("lap_duoc", "khong_lap_duoc", "khong_phan_duoc")}
            log(f"  [{sp.name}] người có item cần đoán bị chặn: {res['n_target_blocked']:,} "
                f"{res['n_target_blocked_by_scenario']}")
        if sd is not None:
            res["arrays_sha256_extra"] = {}
            for k in rx_pu:
                for j, nm in enumerate(["n_lenses", "n_viol", "n_r1", "n_r2"]):
                    fn = sd / f"{sp.name}_{name}_relaxed_{nm}_at{k}.npy"
                    assert not fn.exists()
                    np.save(fn, rx_pu[k][j])
                    res["arrays_sha256_extra"][fn.name] = E.sha256(fn)
            for k in pc_pu:
                fn = sd / f"{sp.name}_{name}_pc_counts_at{k}.npy"
                assert not fn.exists()
                np.save(fn, pc_pu[k])
                res["arrays_sha256_extra"][fn.name] = E.sha256(fn)
        out[name] = res
    return out


# -- LightGCN nội dung 5 + mặt nạ (không huấn luyện lại) --------------------------

def load_lightgcn(run_dir, train, expect_sha=None, device=E.DEVICE):
    """Dựng LightGCN (05b) từ results/n5/.../best.pt với đúng cfg của config.json; kiểm sha256 best.pt nếu có."""
    L05B = importlib.import_module("05b_lightgcn_train")
    run_dir = Path(run_dir)
    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))["cfg"]
    pt = run_dir / "best.pt"
    sha = E.sha256(pt)
    if expect_sha is not None:
        assert sha == expect_sha, f"sha256 best.pt khác n5_final.toml: {pt}"
    adj = L05B.build_norm_adj(train, C.N_USERS, C.N_ITEMS).to(device)
    m = L05B.LightGCN(C.N_USERS, C.N_ITEMS, cfg["dim"], cfg["n_layers"], adj, cfg["l2"]).to(device)
    m.load_state_dict(torch.load(pt, map_location=device, weights_only=False)["model"])
    m.eval()
    return m, cfg, sha
