"""Kiểm thử dựng tay CaKG-Rec v2 (docs/reviews/cakg_v2_plan.md mục 7). Viết 16/10/2026.
KHÔNG huấn luyện (không optimizer.step), không chấm val / test. Log ghi ra file TÊN MỚI trong ai/data/survey/cakg_v2/.

 V0. Ví dụ tính tay của kế hoạch, chạy qua CODE THẬT (cakg_model.gated_score, CaKGRec.pos_user_side,
     CaKGRec.sample_hardneg):
     A: u có thân 80D; 90D (thân cùng ngàm) = hành vi 1,1 + phần cứng 2,4; ống EF-S 10-18 = 2,8 + 0,5; thẻ nhớ = 3,0
        -> v1: 3,5 / 3,3 / 3,0 (90D đứng đầu); A: 1,1 / 3,3 / 3,0 (90D xuống cuối).
     B: h_80D = (1; 0), h_90D = (0,8; 0,6): u có cả hai -> h_u = (0,9; 0,3); cặp dương (u, 90D): v1 h_uᵀh_90D = 0,90,
        B: h_u bỏ 90D = (1; 0), 0,80. u' chỉ có 80D, cặp dương (u', 80D): v1 ‖h_80D‖² = 1, B: cổng đóng.
     C: ŷ(thẻ) = 3,0, ŷ(đèn) = 1,0, ŷ(90D) = 3,5 -> v1 −ln σ(2) = 0,12693; C thêm −ln σ(−0,5) = 0,97408 -> 1,1010.
        sample_hardneg trên CSR nhỏ: chỉ lấy trong tập ứng viên, người không có ứng viên bị bỏ.
 V1. variant = "v1" KHÔNG đổi mô hình test lần 1: make_cfg(0,1; 1) = cfg đã lưu của lần chạy v1 seed 1; nạp best.pt v1
     vào code cũ (git HEAD lúc tách nhánh, 98e5100) và code mới -> cùng điểm, cùng loss trên một batch.
 V2. A "lens_gate" (trọng số Xavier, dữ liệu thật): cổng phía sản phẩm = 1.251 ống có h, 0 thân; người có h_u: thân và
     sản phẩm không có h = e_uᵀe_i đúng từng bit, ống có h = z_uᵀz_i; loss() = BPR từ điểm score_fn + λ1 L_comp + λ2 reg.
 V3. B "loo_hu": người |B| = 2, cặp dương là thân -> z_u dựng từ h của thân CÒN LẠI (tính độc lập từ bodies_h);
     |B| = 1 -> cổng phía người đóng; cặp dương không phải thân -> như lúc chấm; loss() khớp tính độc lập.
 V4. C "body_hardneg": tập ứng viên của 500 người có h_u trùng tập tính bằng tay (thân có h, cùng ngàm, không có trong
     train); người không có h_u: rỗng; loss() = mean(−ln σ(ŷ_ui − ŷ_uj) + 𝟙[có ứng viên] −ln σ(ŷ_ui − ŷ_uj2)) + ...

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/cakg_v2/test_cakg_v2.py --label 20261016_lan1
"""
import argparse
import importlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header  # noqa: E402
import common_05 as C    # noqa: E402
import cakg_model as CK  # noqa: E402
import eval_05 as E      # noqa: E402

T06 = importlib.import_module("06_cakg_train")
DEV = E.DEVICE
V1_S1 = "results/cakg/val_sweep_20261014/val_cakg_lam1-1e-01_s1"
BASE_COMMIT = "98e5100"           # main lúc tách nhánh nam/cakg-v2 (code đã chấm test lần 1)
fails = 0
log = None


def check(name, got, want, tol=5e-6):
    global fails
    if isinstance(want, (float, int)) and not isinstance(want, bool) and isinstance(got, (float, int)):
        ok = math.isclose(float(got), float(want), abs_tol=tol)
    else:
        ok = got == want
    fails += not ok
    log(f"{'OK ' if ok else 'SAI'} {name}: {got}" + ("" if ok else f"  (kỳ vọng {want})"))


def check_le(name, got, bound):
    global fails
    ok = got <= bound
    fails += not ok
    log(f"{'OK ' if ok else 'SAI'} {name}: {got:.3e} (≤ {bound:g})")


class _IdFusion:
    """Fusion giả cho ví dụ tay: z_u = h_u nếu có (để đọc trực tiếp h_u mà pos_user_side dựng)."""
    def __call__(self, e, h, has):
        return torch.where(has[:, None], h, torch.zeros_like(h)), None


def v0():
    log("\nV0. Ví dụ tính tay")
    # A: 1 chiều cho mỗi kênh; z = [e; h] (β = 1 cho dễ đọc) -> z_uᵀz_i = e_uᵀe_i + h_uᵀh_i
    e_u, h_u = torch.tensor([[1.0]]), torch.tensor([[1.0]])
    e_i = torch.tensor([[1.1], [2.8], [3.0]])            # 90D, ống EF-S 10-18, thẻ nhớ
    h_i = torch.tensor([[2.4], [0.5], [0.0]])
    zu = torch.cat([e_u, h_u], 1).expand(3, 2)
    zi = torch.cat([e_i, h_i], 1)
    v1 = CK.gated_score(e_u.expand(3, 1), e_i, zu, zi, torch.tensor([True, True, False]))
    va = CK.gated_score(e_u.expand(3, 1), e_i, zu, zi, torch.tensor([False, True, False]))
    check("A: điểm v1 (90D, ống, thẻ)", [round(x, 4) for x in v1.tolist()], [3.5, 3.3, 3.0])
    check("A: điểm biến thể A (cổng chỉ mở cho ống)", [round(x, 4) for x in va.tolist()], [1.1, 3.3, 3.0])
    check("A: thứ hạng v1 / A", [v1.argsort(descending=True).tolist(), va.argsort(descending=True).tolist()],
          [[0, 1, 2], [1, 2, 0]])

    # B: stub CaKGRec với 2 người (u: 80D + 90D; u': 80D), item 0 = 80D, 1 = 90D, 2 = thẻ nhớ (không h)
    m = object.__new__(CK.CaKGRec)
    m.variant = "loo_hu"
    h = torch.tensor([[1.0, 0.0], [0.8, 0.6]])            # h_80D, h_90D (chỉ số nút cục bộ 0, 1)
    m.item_loc = torch.tensor([0, 1, -1])
    m.is_body_h = torch.tensor([True, True, False])
    m.has_hu = torch.tensor([True, True])
    m.n_bu = torch.tensor([2.0, 1.0])
    m.n_nodes_h = 2
    m.ub_keys = torch.tensor([0 * 2 + 0, 0 * 2 + 1, 1 * 2 + 0])   # (u, 80D), (u, 90D), (u', 80D)
    m.fu = _IdFusion()
    hU = torch.stack([h.mean(0), h[0]])
    check("B: h_u của u (80D + 90D)", [round(x, 4) for x in hU[0].tolist()], [0.9, 0.3])
    u, i = torch.tensor([0, 1, 0]), torch.tensor([1, 0, 2])  # (u, 90D), (u', 80D), (u, thẻ)
    zu_pos, has_pos = m.pos_user_side(u, i, torch.zeros(2, 1), h, hU)
    check("B: (u, 90D) h_u bỏ 90D", [round(x, 4) for x in zu_pos[0].tolist()], [1.0, 0.0])
    check("B: h_uᵀh_90D v1 / B", [round(float(hU[0] @ h[1]), 4), round(float(zu_pos[0] @ h[1]), 4)], [0.9, 0.8])
    check("B: (u', 80D) |B| = 1 -> cổng đóng; (u, thẻ) giữ nguyên h_u", has_pos.tolist(), [True, False, True])
    check("B: (u, thẻ) z_u = h_u", [round(x, 4) for x in zu_pos[2].tolist()], [0.9, 0.3])

    # C: số học BPR và lấy mẫu
    t1 = float(F.softplus(torch.tensor(-(3.0 - 1.0))))
    t2 = float(F.softplus(torch.tensor(-(3.0 - 3.5))))
    check("C: −ln σ(3,0 − 1,0)", round(t1, 5), 0.12693)
    check("C: −ln σ(3,0 − 3,5)", round(t2, 5), 0.97408)
    check("C: tổng", round(t1 + t2, 4), 1.1010)
    s = object.__new__(CK.CaKGRec)
    s.hn_ptr = torch.tensor([0, 3, 3, 4])                  # người 0: {10, 11, 12}; người 1: rỗng; người 2: {5}
    s.hn_idx = torch.tensor([10, 11, 12, 5])
    torch.manual_seed(3)
    uu = torch.tensor([0, 1, 2] * 3000)
    j2, ok = s.sample_hardneg(uu)
    check("C: ok = có ứng viên", ok[:3].tolist(), [True, False, True])
    got0 = j2[0::2].tolist()                               # các hàng của người 0 (ok bỏ người 1 -> xen kẽ 0, 2)
    got2 = j2[1::2].tolist()
    check("C: người 0 chỉ lấy trong {10, 11, 12}; người 2 luôn 5", [set(got0), set(got2)], [{10, 11, 12}, {5}])
    fr = np.bincount(np.array(got0) - 10, minlength=3) / len(got0)
    check_le("C: lấy đều (lệch tần suất lớn nhất so với 1/3, 3.000 lần)", float(np.abs(fr - 1 / 3).max()), 0.03)


def batch_for(m, g, n=2048):
    yes = torch.nonzero(m.has_hu).view(-1)
    u = torch.randint(0, C.N_USERS, (n,), generator=g)
    u[:800] = yes[torch.randint(0, len(yes), (800,), generator=g)].cpu()
    i = torch.randint(0, C.N_ITEMS, (n,), generator=g)
    j = torch.randint(0, C.N_ITEMS, (n,), generator=g)
    return u, i, j


def v1(train):
    log("\nV1. variant = v1 không đổi so với code test lần 1")
    cfg_saved = json.loads(open(os.path.join(V1_S1, "config.json"), encoding="utf-8").read())["cfg"]
    check("make_cfg(0,1; 1) = cfg đã lưu của v1 seed 1 (không có khóa variant)", T06.make_cfg(0.1, 1), cfg_saved)
    src = subprocess.run(["git", "show", f"{BASE_COMMIT}:ai/pipeline/cakg_model.py"], capture_output=True,
                         check=True).stdout
    with tempfile.TemporaryDirectory() as td:
        fn = os.path.join(td, "cakg_model_base.py")
        open(fn, "wb").write(src)
        spec = importlib.util.spec_from_file_location("cakg_model_base", fn)
        OLD = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(OLD)
    sd = torch.load(os.path.join(V1_S1, "best.pt"), map_location=DEV, weights_only=False)["model"]
    new = T06.build_cakg(cfg_saved, train, log=lambda s: None)
    new.load_state_dict(sd, strict=True)
    item_type = C.load_item_type()
    H = OLD.build_h()
    A_ub, has_hu, _ = OLD.user_body_matrix(train, item_type, H.item_loc, H.n_nodes)
    L05B = importlib.import_module("05b_lightgcn_train")
    adj = L05B.build_norm_adj(train, C.N_USERS, C.N_ITEMS).to(DEV)
    old = OLD.CaKGRec(adj, H, A_ub, has_hu, OLD.lcomp_tensors(H.item_loc), lam1=0.1).to(DEV)
    old.load_state_dict(sd, strict=True)
    new.eval()
    old.eval()
    users = torch.arange(0, C.N_USERS, 67, device=DEV)
    with torch.no_grad():
        c_old, c_old2, c_new = old.components(), old.components(), new.components()
        S_old = OLD.CaKGRec.make_scorer(c_old, old.hidx)(users)
        S_mix = CK.CaKGRec.make_scorer(c_old, new.hidx)(users)
        S_old2 = OLD.CaKGRec.make_scorer(c_old2, old.hidx)(users)
        S_new = CK.CaKGRec.make_scorer(c_new, new.hidx)(users)
    check("cùng biểu diễn -> bộ chấm cũ và mới cho điểm đúng từng bit", bool(torch.equal(S_old, S_mix)), True)
    base = float((S_old - S_old2).abs().max())
    d = float((S_old - S_new).abs().max())
    log(f"  lệch do GPU không tất định (code cũ tính 2 lần): {base:.3e}; |điểm| lớn nhất {float(S_old.abs().max()):.2f}")
    check_le(f"điểm code cũ vs mới ({len(users):,} người × 27.940 sp), lệch tương đối so với |điểm| lớn nhất",
             d / float(S_old.abs().max()), 1e-6)
    check("top-20 trùng ở mọi người", bool(torch.equal(S_old.topk(20).indices, S_new.topk(20).indices)), True)
    g = torch.Generator().manual_seed(11)
    u, i, j = (t.to(DEV) for t in batch_for(new, g))
    with torch.no_grad():
        lo, ln = float(old.loss(u, i, j)), float(new.loss(u, i, j))
    check_le(f"loss() code cũ {lo:.6f} vs mới {ln:.6f}", abs(lo - ln), 1e-5)
    del old, new


def consistency(m, u, i, j, extra_pos=None, j2=None, ok=None):
    """loss() tính lại độc lập: BPR từ điểm score_fn (cặp dương có thể thay bằng extra_pos) + λ1 L_comp + λ2 reg."""
    with torch.no_grad():
        c = m.components()
        S = m.make_scorer(c, m.hidx)(u)
        si = S.gather(1, i[:, None]).view(-1) if extra_pos is None else extra_pos
        sj = S.gather(1, j[:, None]).view(-1)
        t = F.softplus(-(si - sj))
        reg = m.user_emb(u).pow(2).sum() + m.item_emb(i).pow(2).sum() + m.item_emb(j).pow(2).sum()
        if j2 is not None:
            sj2 = S[ok].gather(1, j2[:, None]).view(-1)
            t = t + torch.zeros_like(t).masked_scatter(ok, F.softplus(-(si[ok] - sj2)))
            reg = reg + m.item_emb(j2).pow(2).sum()
        lc = CK.l_comp(c["h"], m.M, m.U, m.bl, m.ll, 0.2)
        return float(t.mean() + 0.1 * lc + 1e-3 * 0.5 * reg / len(u))


def v2(train):
    log("\nV2. Biến thể A (lens_gate)")
    torch.manual_seed(0)
    m = T06.build_cakg(T06.make_cfg(0.1, 0, variant="lens_gate"), train, log=lambda s: log("  " + s))
    m.eval()
    item_type = torch.as_tensor(C.load_item_type(), device=DEV)
    check("cổng phía sản phẩm: số ống có h / số thân", [int((m.gate_i & (item_type == 1)).sum()),
                                                        int((m.gate_i & (item_type == 0)).sum())], [1251, 0])
    check("cổng phía sản phẩm ⊆ có h", bool((m.gate_i & ~m.has_hi).any()), False)
    c = m.components()
    sf = m.make_scorer(c, m.hidx)
    yes = torch.nonzero(c["has_hu"]).view(-1)[:500]
    with torch.no_grad():
        S = sf(yes)
        E_ = c["eU"][yes] @ c["eI"].T
        closed = ~m.gate_i
        check("người có h_u: thân và sản phẩm không có h = e_uᵀe_i đúng từng bit",
              bool(torch.equal(S[:, closed], E_[:, closed])), True)
        gi = torch.nonzero(m.gate_i).view(-1)
        dz = (S[:, gi] - c["zU"][yes] @ c["zI"][gi].T).abs().max()
    check_le("người có h_u: ống có h = z_uᵀz_i, lệch", float(dz), 1e-6)
    g = torch.Generator().manual_seed(7)
    u, i, j = batch_for(m, g)
    i[:400] = m.hidx[torch.randint(0, len(m.hidx), (400,), generator=g)].cpu()
    u, i, j = u.to(DEV), i.to(DEV), j.to(DEV)
    with torch.no_grad():
        got = float(m.loss(u, i, j))
    want = consistency(m, u, i, j)
    check_le(f"loss() {got:.6f} = tính độc lập {want:.6f}", abs(got - want), 1e-5)
    del m


def v3(train):
    log("\nV3. Biến thể B (loo_hu)")
    torch.manual_seed(0)
    m = T06.build_cakg(T06.make_cfg(0.1, 0, variant="loo_hu"), train, log=lambda s: None)
    m.eval()
    item_type = C.load_item_type()
    H = CK.build_h()
    _, _, bodies_h = CK.user_body_matrix(train, item_type, H.item_loc, H.n_nodes)
    two = [u for u, bs in bodies_h.items() if len(bs) == 2][:300]
    one = [u for u, bs in bodies_h.items() if len(bs) == 1][:300]
    with torch.no_grad():
        eU, eI = m.behaviour()
        h, hU, _ = m.hardware()
        u = torch.tensor(two + one, device=DEV)
        i = torch.tensor([bodies_h[x][0] for x in two + one], device=DEV)
        zu_pos, has_pos = m.pos_user_side(u, i, eU, h, hU)
        other = torch.tensor([H.item_loc[bodies_h[x][1]] for x in two], device=DEV)
        want, _ = m.fu(eU[u[:300]], h[other], torch.ones(300, dtype=torch.bool, device=DEV))
        check_le("|B| = 2, cặp dương là thân: z_u = Fusion(e_u, h của thân còn lại), lệch",
                 float((zu_pos[:300] - want).abs().max()), 1e-4)
        check("|B| = 2: cổng phía người mở / |B| = 1: đóng", [bool(has_pos[:300].all()), bool(has_pos[300:].any())],
              [True, False])
        # cặp dương không phải thân: như lúc chấm
        i2 = torch.tensor([next(iter(sorted(set(train[x]) - set(bodies_h[x])))) for x in two], device=DEV)
        zu2, hp2 = m.pos_user_side(u[:300], i2, eU, h, hU)
        zref, _ = m.fu(eU[u[:300]], hU[u[:300]], m.has_hu[u[:300]])
        check("cặp dương không phải thân: z_u như lúc chấm (đúng từng bit)", bool(torch.equal(zu2, zref)), True)
        # loss(): điểm dương tính độc lập
        g = torch.Generator().manual_seed(9)
        ub, ib, jb = batch_for(m, g)
        ub[:600] = u.cpu()
        ib[:600] = i.cpu()
        ub, ib, jb = ub.to(DEV), ib.to(DEV), jb.to(DEV)
        got = float(m.loss(ub, ib, jb))
        c = m.components()
        S = m.make_scorer(c, m.hidx)(ub)
        si = S.gather(1, ib[:, None]).view(-1).clone()
        hI = h[m.item_loc[ib[:600]].clamp(min=0)]
        zi, _ = m.fi(eI[ib[:600]], hI, m.has_hi[ib[:600]])
        hu_ind = torch.stack([h[torch.tensor([H.item_loc[b] for b in bodies_h[x] if b != bodies_h[x][0]],
                                             device=DEV)].mean(0) if len(bodies_h[x]) > 1
                              else torch.zeros(h.size(1), device=DEV) for x in two + one])
        zu_ind, _ = m.fu(eU[ub[:600]], hu_ind, torch.tensor([len(bodies_h[x]) > 1 for x in two + one], device=DEV))
        s_pos = torch.where(torch.tensor([len(bodies_h[x]) > 1 for x in two + one], device=DEV),
                            (zu_ind * zi).sum(1), (eU[ub[:600]] * eI[ib[:600]]).sum(1))
        si[:600] = s_pos
    want = consistency(m, ub, ib, jb, extra_pos=si)
    check_le(f"loss() {got:.6f} = tính độc lập (h_u bỏ thân dương tính từ bodies_h) {want:.6f}", abs(got - want), 1e-5)
    del m


def v4(train):
    log("\nV4. Biến thể C (body_hardneg)")
    torch.manual_seed(0)
    m = T06.build_cakg(T06.make_cfg(0.1, 0, variant="body_hardneg"), train, log=lambda s: log("  " + s))
    m.eval()
    item_type = C.load_item_type()
    H = CK.build_h()
    _, _, bodies_h = CK.user_body_matrix(train, item_type, H.item_loc, H.n_nodes)
    mt = CK.body_mounts()
    ptr, idx = m.hn_ptr.cpu().numpy(), m.hn_idx.cpu().numpy()
    rng = np.random.default_rng(20261016)
    us = rng.choice(sorted(bodies_h), 500, replace=False)
    bad = 0
    for u in us.tolist():
        own = set(train[u])
        um = {mt[b] for b in bodies_h[u] if b in mt}
        want = sorted(g for g in H.item_loc if item_type[g] == 0 and g in mt and mt[g] in um and g not in own)
        bad += idx[ptr[u]:ptr[u + 1]].tolist() != want
    check("tập ứng viên trùng tính tay (500 người có h_u)", bad, 0)
    noh = np.flatnonzero(~m.has_hu.cpu().numpy())
    check("người không có h_u: không có ứng viên", int((ptr[noh + 1] - ptr[noh]).sum()), 0)
    g = torch.Generator().manual_seed(5)
    u, i, j = (t.to(DEV) for t in batch_for(m, g))
    with torch.no_grad():
        torch.cuda.manual_seed_all(123)
        torch.manual_seed(123)
        got = float(m.loss(u, i, j))
        torch.cuda.manual_seed_all(123)
        torch.manual_seed(123)
        j2, ok = m.sample_hardneg(u)
    check("có hàng có âm mẫu thân trong batch thử (> 0)", int(ok.sum()) > 0, True)
    check("mọi j2 là thân", bool((torch.as_tensor(item_type, device=DEV)[j2] == 0).all()), True)
    want = consistency(m, u, i, j, j2=j2, ok=ok)
    check_le(f"loss() {got:.6f} = tính độc lập {want:.6f}", abs(got - want), 1e-5)
    del m


def main():
    global log
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join("ai/data/survey/cakg_v2", f"run_test_cakg_v2_{a.label}.log"))
    header(log, __file__)
    v0()
    train = C.load_train()
    v1(train)
    v2(train)
    v3(train)
    v4(train)
    log(f"\nKẾT QUẢ: {'ĐẠT CẢ' if fails == 0 else f'{fails} kiểm SAI'}")
    log.save()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
