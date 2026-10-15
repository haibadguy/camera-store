"""Kiểm thử dựng tay phần A (CaKG-Rec) theo docs/reviews/cakg_eval_plan.md mục 11. Viết 14/10/2026.

Mọi ví dụ của thiết kế (số ở ai/data/survey/cakg/run_vidu_tinh_tay_20261014_lan2.log) chạy qua CODE THẬT
(ai/pipeline/cakg_model.py, rgat_layer.py, 05b_lightgcn_train.py) phải ra đúng số; thêm các kiểm trên dữ liệu thật.
KHÔNG huấn luyện (trọng số Xavier ngẫu nhiên, không optimizer.step), không chấm val / test.

 A1. Khối 1: LightGCN 1 lớp trên 4 cạnh (build_norm_adj + lightgcn_propagate) -> e_u1 = 0,55178 ...; BPR = 0,84058.
 A2. Khối 2: một lớp RGAT tại thân b -> α = (0,2689; 0,7311), h_b' = ReLU(1,7689; 2,2311); HwEncoder: ReLU chỉ sau lớp 1.
 A3. RGATLayer so với RGATConv của PyG (cùng trọng số): (a) đồ thị nhỏ ngẫu nhiên, q / k chung; (b) q^(r), k^(r) riêng
     từng quan hệ = tổng các RGATConv chạy riêng từng quan hệ; (c) 20.000 cạnh ngẫu nhiên của H thật, d = 64;
     (d) gradient theo đầu vào. Ngưỡng 1e-5 (kế hoạch mục 11).
 A4. Khối 3–4: gộp kênh có cổng (Fusion, gated_score): β, z, ŷ(u1, l2) = 0,09468 = 0,03543 + 0,05925; ŷ(u1, C) = 0,17;
     ŷ(u2, l2) = 0,14; ŷ(u2, C) = 0,09.
 A5. Khối 5: L_comp một cặp dương = 0,08510; nếu đưa cặp U vào mẫu số = 0,37618 (để thấy code KHÔNG làm vậy).
 A6. Khối 6: L_total = 0,61101 (số học); trên mô hình thật: loss() = BPR + λ1 L_comp + λ2 reg tính độc lập, và điểm
     dùng trong loss() trùng điểm score_fn() dùng khi chấm.
 A7. Đồ thị con H thật: số nút / cạnh từng quan hệ khớp thiết kế khối 2; không có nút người dùng; không có cạnh
     ngam_khong_chac; bản bỏ suitable_for: 12 quan hệ, cùng tập nút.
 A8. Người có h_u = 10.359; cặp L_comp 72.720 / 476.155 / 5.846; mọi thân / ống của M có nút.
 A9. Cổng trên mô hình thật: người không có h_u -> mọi điểm = e_uᵀe_i (đúng từng bit); người có h_u -> sản phẩm không
     có h = e_uᵀe_i, có h = z_uᵀz_i.
 A10. Mặt nạ (15) trong 06_cakg_train.mask_scorer: −∞ đúng các ô eval_05.certain_violation_mask = True.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/cakg/test_cakg.py --label 20261014_lan1
"""
import argparse
import importlib
import math
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.nn import RGATConv

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header  # noqa: E402
import common_05 as C    # noqa: E402
import cakg_model as CK  # noqa: E402
import eval_05 as E      # noqa: E402
from rgat_layer import RGATLayer, HwEncoder  # noqa: E402

L05B = importlib.import_module("05b_lightgcn_train")
T06 = importlib.import_module("06_cakg_train")
DEV = E.DEVICE
fails = 0
log = None


def check(name, got, want, tol=5e-6):
    """So số (làm tròn như log tính tay: sai số ≤ tol) hoặc so bằng."""
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


def a1():
    log("\n=== A1. Khối 1: LightGCN 1 lớp ===")
    train = {0: {0, 1}, 1: {1, 2}}                      # u1–A, u1–B, u2–B, u2–C
    adj = L05B.build_norm_adj(train, 2, 3)
    E0 = torch.tensor([[1.0], [0.0], [0.5], [-0.5], [1.0]])   # u1, u2, A, B, C
    e = CK.lightgcn_propagate(adj, E0, 1).view(-1).tolist()
    for nm, v, w in zip(["u1", "u2", "A", "B", "C"], e, [0.55178, 0.22855, 0.60355, 0.0, 0.5]):
        check(f"e_{nm}", round(v, 5), w)
    yB, yC = e[0] * e[3], e[0] * e[4]
    check("ŷ(u1, C)", round(yC, 5), 0.27589)
    check("BPR(u1, B, C) = softplus(−(ŷB − ŷC))", round(float(F.softplus(torch.tensor(-(yB - yC)))), 5), 0.84058)


def a2():
    log("\n=== A2. Khối 2: một lớp RGAT ===")
    # nút: 0 = b, 1 = l1, 2 = l2, 3 = ngàm; quan hệ 0 = rev_compatible_with (ống -> thân), 1 = rev_has_spec_mount
    h = torch.tensor([[0.5, 0.5], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    ei = torch.tensor([[1, 2, 3], [0, 0, 0]])
    et = torch.tensor([0, 0, 1])
    lay = RGATLayer(2, 2, 2)
    with torch.no_grad():
        lay.weight.copy_(torch.eye(2).expand(2, 2, 2))
        lay.q.copy_(torch.tensor([[1.0, 0.0], [1.0, 0.0]]))
        lay.k.copy_(torch.tensor([[0.0, 1.0], [0.0, 1.0]]))
        lay.bias.zero_()
        out, alpha = lay(h, ei, et)
    check("α(b←l1), α(b←l2), α(b←ngàm)", [round(x, 4) for x in alpha.tolist()], [0.2689, 0.7311, 1.0])
    hb = F.relu(out[0] + h[0])                          # + W_0 h_b với W_0 = I
    check("h_b' = ReLU(Σ α g + W_0 h_b)", [round(x, 4) for x in hb.tolist()], [1.7689, 2.2311])
    # HwEncoder: lớp 1 có ReLU, lớp 2 không
    torch.manual_seed(0)
    enc = HwEncoder(4, 2, dim=2)
    with torch.no_grad():
        o1, _ = enc.convs[0](enc.x, ei, et)
        x1 = F.relu(o1 + enc.roots[0](enc.x))
        o2, a2_ = enc.convs[1](x1, ei, et)
        want = o2 + enc.roots[1](x1)
        got, a_got = enc(ei, et)
    check("HwEncoder = lớp1 → ReLU → lớp2 (không ReLU), lệch tối đa", float((got - want).abs().max()), 0.0, tol=0)
    check("HwEncoder trả α của lớp 2", bool(torch.equal(a_got, a2_)), True)


def copy_from_pyg(mine, ref, r_only=None):
    with torch.no_grad():
        mine.weight.copy_(ref.weight)
        mine.q.copy_(ref.q[:, 0].expand_as(mine.q))
        mine.k.copy_(ref.k[:, 0].expand_as(mine.k))
        mine.bias.copy_(ref.bias)


def pyg(R, d, seed):
    torch.manual_seed(seed)
    ref = RGATConv(d, d, R, attention_mechanism="within-relation", attention_mode="additive-self-attention",
                   heads=1).to(DEV)
    with torch.no_grad():
        ref.bias.normal_()
    return ref


def a3(H):
    log("\n=== A3. RGATLayer so với RGATConv của PyG (cùng trọng số) ===")
    # (a) đồ thị nhỏ ngẫu nhiên, q / k chung
    g = torch.Generator().manual_seed(1)
    n, R, d, nE = 40, 5, 8, 300
    ei = torch.randint(0, n, (2, nE), generator=g).to(DEV)
    et = torch.randint(0, R, (nE,), generator=g).to(DEV)
    x = torch.randn(n, d, generator=g).to(DEV)
    ref = pyg(R, d, 2)
    mine = RGATLayer(d, d, R).to(DEV)
    copy_from_pyg(mine, ref)
    with torch.no_grad():
        o1, (_, a1_) = ref(x, ei, et, return_attention_weights=True)
        o2, a2_ = mine(x, ei, et)
    check_le("(a) đồ thị nhỏ (40 nút, 5 quan hệ, 300 cạnh): lệch đầu ra", float((o1 - o2).abs().max()), 1e-5)
    check_le("(a) lệch α", float((a1_.view(-1) - a2_).abs().max()), 1e-5)
    # (d) gradient theo đầu vào x
    xa = x.clone().requires_grad_(True)
    xb = x.clone().requires_grad_(True)
    ref(xa, ei, et).pow(2).sum().backward()
    mine(xb, ei, et)[0].pow(2).sum().backward()
    check_le("(d) lệch gradient theo x", float((xa.grad - xb.grad).abs().max()), 1e-5)

    # (b) q^(r), k^(r) riêng từng quan hệ: so với tổng các RGATConv chạy riêng trên cạnh của từng quan hệ
    torch.manual_seed(3)
    mine = RGATLayer(d, d, R).to(DEV)
    with torch.no_grad():
        mine.bias.normal_()
        o_mine, a_mine = mine(x, ei, et)
        acc = torch.zeros(n, d, device=DEV)
        a_ref = torch.zeros(nE, device=DEV)
        for r in range(R):
            sel = (et == r).nonzero().view(-1)
            ref_r = RGATConv(d, d, 1, attention_mechanism="within-relation",
                             attention_mode="additive-self-attention", heads=1).to(DEV)
            ref_r.weight.copy_(mine.weight[r:r + 1])
            ref_r.q.copy_(mine.q[r].view(d, 1))
            ref_r.k.copy_(mine.k[r].view(d, 1))
            ref_r.bias.zero_()
            o_r, (_, a_r) = ref_r(x, ei[:, sel], torch.zeros(len(sel), dtype=torch.long, device=DEV),
                                  return_attention_weights=True)
            acc += o_r
            a_ref[sel] = a_r.view(-1)
        acc += mine.bias
    check_le("(b) q^(r), k^(r) riêng: lệch đầu ra so với Σ_r RGATConv(quan hệ r)", float((o_mine - acc).abs().max()),
             1e-5)
    check_le("(b) lệch α", float((a_mine - a_ref).abs().max()), 1e-5)
    check("(b) các q^(r) thật sự khác nhau (không phải trường hợp chung)",
          bool((mine.q - mine.q[0]).abs().max() > 1e-3), True)

    # (c) 20.000 cạnh ngẫu nhiên của H thật, d = 64 (như probe)
    R = len(H.rel_names)
    perm = torch.randperm(H.ei.size(1), generator=torch.Generator().manual_seed(0))[:20000]
    e, t = H.ei[:, perm].to(DEV), H.et[perm].to(DEV)
    x = torch.randn(H.n_nodes, 64, generator=torch.Generator().manual_seed(4)).to(DEV)
    ref = pyg(R, 64, 5)
    mine = RGATLayer(64, 64, R).to(DEV)
    copy_from_pyg(mine, ref)
    with torch.no_grad():
        o1, (_, a1_) = ref(x, e, t, return_attention_weights=True)
        o2, a2_ = mine(x, e, t)
    check_le("(c) H thật, 20.000 cạnh, d 64: lệch đầu ra", float((o1 - o2).abs().max()), 1e-5)
    check_le("(c) lệch α", float((a1_.view(-1) - a2_).abs().max()), 1e-5)
    # WIRGAT trên toàn H: tổng α theo (đích, quan hệ) = 1
    with torch.no_grad():
        _, a = mine(x, H.ei.to(DEV), H.et.to(DEV))
        key = H.ei[1].to(DEV) * R + H.et.to(DEV)
        s = torch.zeros(H.n_nodes * R, device=DEV).index_add_(0, key, a)
        used = torch.unique(key)
    check_le("WIRGAT trên toàn H: max |Σ α theo (đích, quan hệ) − 1|", float((s[used] - 1).abs().max()), 1e-5)


def a4():
    log("\n=== A4. Khối 3–4: gộp kênh có cổng ===")
    fu = CK.Fusion(2, 2)
    with torch.no_grad():
        fu.W.weight.copy_(torch.eye(2))
        fu.W.bias.zero_()
        fu.q.weight.copy_(torch.tensor([[1.0, 1.0]]))
        # hàng: l2 (có h), u1 (có h), C (không), u2 (không)
        e = torch.tensor([[0.2, 0.4], [0.5, 0.1], [0.3, 0.2], [0.1, 0.3]])
        h = torch.tensor([[0.6, 0.0], [0.4, 0.2], [9.0, 9.0], [9.0, 9.0]])   # 9 = rác, phải bị bỏ qua
        has = torch.tensor([True, True, False, False])
        z, beta = fu(e, h, has)
    r5 = lambda t: [round(x, 5) for x in t.tolist()]  # noqa: E731
    check("β(l2)", r5(beta[0]), [0.51007, 0.48993])
    check("z_l2", r5(z[0]), [0.10201, 0.20403, 0.29396, 0.0])
    check("β(u1)", r5(beta[1]), [0.49612, 0.50388])
    check("z_u1", r5(z[1]), [0.24806, 0.04961, 0.20155, 0.10078])
    check("β(C), β(u2) (thiếu h)", [r5(beta[2]), r5(beta[3])], [[1.0, 0.0], [1.0, 0.0]])
    check("z_C (phần h = 0, không lấy vector rác)", r5(z[2]), [0.3, 0.2, 0.0, 0.0])
    l2, u1, Cc, u2 = 0, 1, 2, 3
    pairs = [(u1, l2), (u1, Cc), (u2, l2), (u2, Cc)]
    uu = torch.tensor([p[0] for p in pairs])
    ii = torch.tensor([p[1] for p in pairs])
    s = CK.gated_score(e[uu], e[ii], z[uu], z[ii], has[uu] & has[ii])
    check("ŷ(u1, l2), ŷ(u1, C), ŷ(u2, l2), ŷ(u2, C)", r5(s), [0.09468, 0.17, 0.14, 0.09])
    check("ŷ(u1, l2) phần hành vi", round(float((z[u1, :2] * z[l2, :2]).sum()), 5), 0.03543)
    check("ŷ(u1, l2) phần phần cứng", round(float((z[u1, 2:] * z[l2, 2:]).sum()), 5), 0.05925)


def a5():
    log("\n=== A5. Khối 5: L_comp ===")
    cos = [0.8, 0.3, -0.2, 0.6]                         # l1 (M=1), l2, l3 (M=0), l4 (U=1)
    hl = torch.tensor([[c, math.sqrt(1 - c * c)] for c in cos])
    h = torch.cat([torch.tensor([[1.0, 0.0]]), hl])     # nút 0 = thân b
    M = torch.tensor([[True, False, False, False]])
    U = torch.tensor([[False, False, False, True]])
    bl, ll = torch.tensor([0]), torch.tensor([1, 2, 3, 4])
    check("ℓ(b, l1), cặp U bỏ khỏi mẫu số", round(float(CK.l_comp(h, M, U, bl, ll, 0.2)), 5), 0.08510)
    check("(nếu lỡ đưa l4 vào mẫu số)", round(float(CK.l_comp(h, M, torch.zeros_like(U), bl, ll, 0.2)), 5), 0.37618)
    # trung bình trên cặp dương: hai thân, mỗi thân một dương -> trung bình hai giá trị
    h2 = torch.cat([h, torch.tensor([[0.0, 1.0]])])     # nút 5 = thân b2, cos(b2, l_k) = sin
    M2 = torch.tensor([[True, False, False, False], [False, True, False, False]])
    U2 = torch.tensor([[False, False, False, True], [False, False, False, False]])
    one = [float(CK.l_comp(h2, M2[r:r + 1], U2[r:r + 1], torch.tensor([b]), ll, 0.2)) for r, b in ((0, 0), (1, 5))]
    check("L_comp 2 thân = trung bình 2 cặp dương", round(float(CK.l_comp(h2, M2, U2, torch.tensor([0, 5]), ll, 0.2)),
                                                       7), round(sum(one) / 2, 7))


def real_model_checks(H):
    log("\n=== A7–A10. Dữ liệu thật ===")
    train = C.load_train()
    item_type = C.load_item_type()
    # A7: số nút / cạnh của H
    check("số nút H_lõi", H.n_nodes, 1822)
    check("số item có nút", len(H.item_loc), 1788)
    check("số quan hệ", len(H.rel_names), 14)
    check("số cạnh (cả rev_)", int(H.ei.size(1)), 186338)
    check("cạnh xuôi từng quan hệ = thiết kế khối 2", H.counts, CK.H_LOI_EXPECTED)
    per_rel = {nm: int((H.et == r).sum()) for r, nm in enumerate(H.rel_names)}
    check("mỗi quan hệ rev_ có cùng số cạnh với chiều xuôi",
          all(per_rel["rev_" + k] == v for k, v in per_rel.items() if not k.startswith("rev_")), True)
    types = {int(item_type[g]) for g in H.item_loc}
    check("loại item trong H chỉ là thân / ống (không có người dùng, phụ kiện)", sorted(types), [0, 1])
    check("số thân / ống", [sum(item_type[g] == 0 for g in H.item_loc), sum(item_type[g] == 1 for g in H.item_loc)],
          [537, 1251])
    hsm = CK._rows("kg_edges_has_spec_mount.csv")
    unsure = {int(r["iid"]) for r in hsm if r["ngam_khong_chac"] == "1"}
    r_mount = H.rel_names.index("has_spec_mount")
    src_mount = {int(s) for s in H.ei[0, H.et == r_mount].tolist()}
    unsure_loc = {H.item_loc[i] for i in unsure if i in H.item_loc}
    check("ống 'không chắc' (134) không có cạnh has_spec_mount trong H", len(unsure_loc & src_mount), 0)
    check("ống 'không chắc' còn nút (qua khổ / mục đích) / không có nút", [len(unsure_loc), len(unsure - set(H.item_loc))],
          [126, 8])
    Hd = CK.build_h(drop_suitable_for=True)
    check("bỏ suitable_for: 12 quan hệ, cùng số nút, cạnh = 186.338 − 2 × 1.080",
          [len(Hd.rel_names), Hd.n_nodes, int(Hd.ei.size(1)), Hd.item_loc == H.item_loc],
          [12, 1822, 186338 - 2160, True])
    # A8
    A_ub, has_hu, bodies_h = CK.user_body_matrix(train, item_type, H.item_loc, H.n_nodes)
    check("người có h_u", int(has_hu.sum()), 10359)
    rs = torch.sparse.sum(A_ub, 1).to_dense()
    check_le("mỗi hàng A_ub (người có h_u) tổng = 1: lệch tối đa", float((rs[has_hu] - 1).abs().max()), 1e-6)
    M, U, bl, ll, bg, lg = CK.lcomp_tensors(H.item_loc)
    check("L_comp dương / âm / U", [int(M.sum()), int((~M & ~U).sum()), int(U.sum())], [72720, 476155, 5846])
    check("thân / ống của M", [len(bg), len(lg)], [537, 1033])

    # mô hình thật, trọng số Xavier ngẫu nhiên (seed 0), λ1 = 0,1
    torch.manual_seed(0)
    cfg = T06.make_cfg(0.1, 0)
    m = T06.build_cakg(cfg, train, log=lambda s: log("  " + s))
    m.eval()
    # A9: cổng
    c = m.components()
    sf = m.make_scorer(c, m.hidx)
    nohu = torch.nonzero(~c["has_hu"]).view(-1)[:500]
    yeshu = torch.nonzero(c["has_hu"]).view(-1)[:500]
    with torch.no_grad():
        S0 = sf(nohu)
        check("người không có h_u: điểm = e_uᵀe_i đúng từng bit (500 người)", bool(torch.equal(S0, c["eU"][nohu] @ c["eI"].T)),
              True)
        S1 = sf(yeshu)
        noh = ~c["has_hi"]
        check("người có h_u, sản phẩm không có h: điểm = e_uᵀe_i (500 người)",
              bool(torch.equal(S1[:, noh], (c["eU"][yeshu] @ c["eI"].T)[:, noh])), True)
        dz = (S1[:, m.hidx] - c["zU"][yeshu] @ c["zI"][m.hidx].T).abs().max()
    check_le("người có h_u, sản phẩm có h: điểm = z_uᵀz_i, lệch", float(dz), 1e-6)
    check("số sản phẩm có h trong bộ chấm", int(m.hidx.numel()), 1788)
    # A6: loss() = BPR + λ1 L_comp + λ2 reg, và điểm trong loss trùng score_fn
    g = torch.Generator().manual_seed(7)
    u = torch.randint(0, C.N_USERS, (2048,), generator=g)
    u[:600] = yeshu[torch.randint(0, len(yeshu), (600,), generator=g)].cpu()   # có cả người có h_u
    i = torch.randint(0, C.N_ITEMS, (2048,), generator=g)
    i[:300] = m.hidx[torch.randint(0, len(m.hidx), (300,), generator=g)].cpu()
    j = torch.randint(0, C.N_ITEMS, (2048,), generator=g)
    u, i, j = u.to(DEV), i.to(DEV), j.to(DEV)
    with torch.no_grad():
        got = float(m.loss(u, i, j))
        S = sf(u)
        si, sj = S.gather(1, i[:, None]).view(-1), S.gather(1, j[:, None]).view(-1)
        bpr = float(F.softplus(-(si - sj)).mean())
        lc = float(CK.l_comp(c["h"], m.M, m.U, m.bl, m.ll, 0.2))
        reg = float(0.5 * (m.user_emb(u).pow(2).sum() + m.item_emb(i).pow(2).sum() + m.item_emb(j).pow(2).sum()) / 2048)
    log(f"  loss() = {got:.6f}; tính độc lập: BPR {bpr:.6f} + 0,1 × L_comp {lc:.6f} + 1e-3 × reg {reg:.6f}")
    check_le("loss() − (BPR + λ1 L_comp + λ2 reg), BPR từ điểm của score_fn", abs(got - (bpr + 0.1 * lc + 1e-3 * reg)),
             1e-5)
    check("số cặp có cổng mở trong batch thử (> 0)", int((m.has_hu[u] & m.has_hi[i]).sum()) > 0, True)
    check("L_total ví dụ khối 6 (0,6 + 0,1 × 0,08510 + 1e-3 × 2,5)", round(0.6 + 0.1 * 0.08510 + 1e-3 * 2.5, 5), 0.61101)
    # A10: mặt nạ
    bodies = C.build_train_bodies(train, None, item_type)
    ctx = C.load_cvr_context()
    lens, cmask = E.certain_violation_mask(bodies, ctx)
    lt, ct = torch.as_tensor(lens, device=DEV), torch.as_tensor(cmask, device=DEV)
    users = torch.as_tensor(sorted(bodies)[:2000], device=DEV)
    with torch.no_grad():
        Sm = T06.mask_scorer(sf, lt, ct)(users)
        isinf = torch.isinf(Sm[:, lt]) & (Sm[:, lt] < 0)
    check("mặt nạ: −∞ đúng các ô certain_violation_mask (2.000 người có thân)", bool(torch.equal(isinf, ct[users])), True)
    nolens = torch.ones(C.N_ITEMS, dtype=torch.bool, device=DEV)
    nolens[lt] = False
    check("mặt nạ không chạm sản phẩm ngoài 1.033 ống của M", bool(torch.isinf(Sm[:, nolens]).any()), False)
    check("số ô bị chặn trong 2.000 người > 0", int(isinf.sum()) > 0, True)


def main():
    global log
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join("ai/data/survey/cakg", f"run_test_cakg_{a.label}.log"))
    header(log, __file__)
    log(f"thiết bị {DEV}" + (f" ({torch.cuda.get_device_name(0)})" if DEV.type == "cuda" else "") +
        f" | torch {torch.__version__}")
    a1()
    a2()
    H = CK.build_h()
    a3(H)
    a4()
    a5()
    real_model_checks(H)
    log(f"\n{'ĐẠT CẢ' if fails == 0 else f'CÓ {fails} KIỂM TRA SAI'}")
    log.save()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
