"""Kiểm thử dựng tay cho ai/pipeline/09_explain_lightgcn.py (docs/reviews/final_system_explain_plan.md mục 5).
Viết 16/10/2026. Không huấn luyện, chỉ dùng VAL (không đọc test). Log ghi ra file TÊN MỚI trong ai/data/survey/final_system/.

 L1. Ví dụ kế hoạch mục 2: e_D750ᵀe_l = 1,2, e_D500ᵀe_l = 0,4 -> b* = D750; hòa điểm -> iid nhỏ hơn.
 L2. c*: ống 2 nhãn -> nhãn đứng trước theo thứ tự nút usecase; không nhãn -> None.
 L3. AdjBuilder.build() trùng 05b.build_norm_adj(train) từng phần tử (chỉ số và giá trị).
 L4. Bỏ cạnh (u, b): trùng build_norm_adj của train đã bỏ b khỏi u; số phần tử khác 0 giảm 2; điểm lan truyền lại
     trùng LightGCN dựng trên train đã bỏ cạnh (cùng trọng số).
 L5. propagate(m, m.adj) trùng m.score_fn().
 L6. "Không bỏ gì": chấm lại riêng từng người (one_user_topk) cho 200 cặp (u, l) lấy từ top-10 đã lưu (val) -> l vẫn
     trong top-10 (FS = 0).
 L7. Người không có thân: LGExplainer không dựng đường nào.
 L8. Kiểm sự kiện bắt được lỗi: đổi b* thành một thân người dùng không có -> verify_explanation báo lỗi.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/final_system/test_explain_lightgcn.py --label 20261016_lan1
"""
import argparse
import importlib
import math
import os
import sys
import tomllib

import numpy as np
import torch

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header  # noqa: E402
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

X09 = importlib.import_module("09_explain_lightgcn")
L05B = importlib.import_module("05b_lightgcn_train")
DEV = E.DEVICE
fails = 0
log = None


def check(name, got, want):
    global fails
    ok = got == want
    fails += not ok
    log(f"{'OK ' if ok else 'SAI'} {name}: {got}" + ("" if ok else f"  (kỳ vọng {want})"))


def check_le(name, got, bound):
    global fails
    ok = got <= bound
    fails += not ok
    log(f"{'OK ' if ok else 'SAI'} {name}: {got:.3e} (≤ {bound:g})")


def same_sparse(a, b):
    a, b = a.coalesce().cpu(), b.coalesce().cpu()
    return bool(torch.equal(a.indices(), b.indices()) and torch.equal(a.values(), b.values()))


def main():
    global log
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join("ai/data/survey/final_system", f"run_test_explain_lg_{a.label}.log"))
    header(log, __file__)

    log("\nL1. b*")
    eI = torch.zeros(30, 2)
    eI[5] = torch.tensor([1.0, 0.0])                     # ống l
    eI[10] = torch.tensor([1.2, 3.0])                    # D750: e·e_l = 1,2
    eI[20] = torch.tensor([0.4, -1.0])                   # D500: 0,4
    b, sc = X09.pick_body([10, 20], eI, 5)
    check("điểm e_bᵀe_l (D750, D500)", [round(sc[10], 4), round(sc[20], 4)], [1.2, 0.4])
    check("b* = D750 (iid 10)", b, 10)
    eI[20] = torch.tensor([1.2, 7.0])
    check("hòa 1,2 = 1,2 -> iid nhỏ hơn", X09.pick_body([20, 10], eI, 5)[0], 10)

    log("\nL2. c*")
    H = CK.build_h()
    order = list(H.node_names["usecase"])
    log(f"  thứ tự nút usecase: {order}")
    check("2 nhãn (đảo thứ tự đầu vào) -> nhãn đứng trước theo thứ tự nút",
          X09.pick_label([order[2], order[1]], order), order[1])
    check("không nhãn -> None", X09.pick_label([], order), None)

    log("\nL3–L5. Đồ thị bỏ cạnh, lan truyền")
    train = C.load_train()
    adjb = X09.AdjBuilder(train)
    ref = L05B.build_norm_adj(train, C.N_USERS, C.N_ITEMS)
    full = adjb.build()
    check("build() = build_norm_adj(train) từng phần tử", same_sparse(full, ref), True)
    item_type = C.load_item_type()
    bodies = C.build_train_bodies(train, None, item_type)
    u = next(x for x in sorted(bodies) if len(train[x]) >= 5)
    b = sorted(bodies[u])[0]
    drop = adjb.build((u, b))
    tr2 = {k: (set(v) - {b} if k == u else v) for k, v in train.items()}
    ref2 = L05B.build_norm_adj(tr2, C.N_USERS, C.N_ITEMS)
    check(f"bỏ (u {u}, b {b}) = build_norm_adj(train bỏ cạnh)", same_sparse(drop, ref2), True)
    check("số phần tử khác 0 giảm 2", int(full._nnz()) - int(drop._nnz()), 2)
    n5 = tomllib.loads(open("ai/config/n5_final.toml", encoding="utf-8").read())
    rr = n5["lightgcn"]["runs"][0]
    m, _, _ = EC.load_lightgcn(rr["dir"], train, expect_sha=rr["best_pt_sha256"])
    with torch.no_grad():
        eU, eIm = X09.propagate(m, m.adj)
        users = torch.arange(0, C.N_USERS, 97, device=DEV)
        check_le("propagate(m, m.adj) vs m.score_fn(), lệch", float((eU[users] @ eIm.T - m.score_fn()(users)).abs().max()),
                 1e-4)
        m2 = L05B.LightGCN(C.N_USERS, C.N_ITEMS, 64, 3, ref2.to(DEV), 1e-3).to(DEV)
        m2.load_state_dict(m.state_dict())
        eUd, eId = X09.propagate(m, drop)
        S_a = eUd[u] @ eId.T
        S_b = m2.score_fn()(torch.tensor([u], device=DEV))[0]
        check_le("điểm của u sau khi bỏ cạnh = LightGCN dựng trên train đã bỏ cạnh, lệch", float((S_a - S_b).abs().max()),
                 1e-4)
        check("bỏ cạnh có làm đổi điểm của u (> 1e-3)", bool((S_a - eU[u] @ eIm.T).abs().max() > 1e-3), True)

    log("\nL6. Không bỏ gì -> l vẫn trong top-10 (val, top-10 đã lưu)")
    ev = E.EvalContext("val", train)
    _, sv = X09.load_saved("val", 1)
    masks = EC.masks_on_device(ev)
    rng = np.random.default_rng(1)
    rows = [r for r, x in enumerate(ev.split.users.tolist()) if x in ev.bodies]
    pairs = []
    for r in rng.choice(rows, 400, replace=False).tolist():
        ls = [l for l in sv["top20_full"][r, :10].tolist() if ev.item_type[l] == 1]
        if ls:
            pairs.append((r, int(ev.split.users[r]), ls[0]))
    pairs = pairs[:200]
    miss = 0
    for r, uu, l in pairs:
        top, _ = X09.one_user_topk(eU, eIm, uu, ev.split, r, ev.pi, *masks["qd49"])
        miss += l not in top
    check(f"số cặp l rơi khỏi top-10 khi chấm lại không bỏ gì ({len(pairs)} cặp)", miss, 0)

    log("\nL7–L8. Người không có thân; kiểm sự kiện")
    pctx = EC.PathContext(train, ev.item_type)
    xp = X09.LGExplainer(eIm.cpu(), ev.bodies, pctx, order)
    nob = next(x for x in ev.split.users.tolist() if x not in ev.bodies)
    lenses = [i for i in range(C.N_ITEMS) if ev.item_type[i] == 1][:300]
    check("người không có thân: số đường dựng được trên 300 ống", sum(xp.explain(nob, l) is not None for l in lenses), 0)
    has = EC.h_edge_checker(H)
    ex = None
    for r, uu, l in pairs:
        ex = xp.explain(uu, l)
        if ex is not None:
            break
    s = EC.sentence(ex, pctx)
    check("câu đúng: số lỗi", len(EC.verify_explanation(ex, s, pctx, has)), 0)
    other = next(x for x in sorted(pctx.m1_by_lens[ex["l"]]) if x not in train[ex["u"]])
    bad = dict(ex, b_star=other, rho=pctx.rho[(other, ex["l"])])
    errs = EC.verify_explanation(bad, EC.sentence(bad, pctx), pctx, has)
    check("đổi b* thành thân người dùng không có -> có lỗi 'owns'", any("owns" in e for e in errs), True)

    log(f"\nKẾT QUẢ: {'ĐẠT CẢ' if fails == 0 else f'{fails} kiểm SAI'}")
    log.save()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
