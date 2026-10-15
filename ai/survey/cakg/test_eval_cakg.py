"""Kiểm thử dựng tay phần C (ai/pipeline/eval_cakg.py, 08_explain.py) theo docs/reviews/cakg_eval_plan.md mục 11.
Viết 14/10/2026. CHỈ dùng tập VAL (không đọc nhãn test). Không huấn luyện.

 C1. Ví dụ khối 7 (người hai hệ máy, dựng tay): CVR trước mặt nạ @4 = 1/3; QĐ 4-9 chặn đúng Canon EF; ∃b chặn cả 3 ống.
 C2. Dữ liệu thật, uid 378 (Sony a7 + Nikon D750): ống Nikon AF-S 200-500mm f/5.6E không bị QĐ 4-9 chặn, bị ∃b chặn;
     mọi ống bị QĐ 4-9 chặn cũng bị ∃b chặn (mọi người).
 C3. Đếm mặt nạ trên dữ liệu thật khớp log run_dem_cakg_20261014_lan1.log: cặp bị chặn 8.557.447 / 8.904.038;
     kịch bản val bị chặn: lắp được 0 / 109, không lắp được 236 / 236, không phán được 0 / 0.
 C4. LightGCN s1 nội dung 5 dựng lại từ best.pt (sha256 như n5_final.toml): top-20 val trùng mảng đã lưu.
 C5. CVR_relaxed trên top-10 val LightGCN s1: 23.441 ống, 3.005 vi phạm, R1 nới 61, R2 nới 109, 50 người (log dem);
     uid 2465, ống iid 19161: strict vi phạm, R1 vi phạm, R2 không vi phạm.
 C6. Path Coverage trên top-10 val LightGCN s1 (trước mặt nạ): 20.436 đường ngắn, 9.095 đường đủ trên 23.441 ống chấm
     được (log dem).
 C7. LightGCN + mặt nạ trên val: CVR strict (và R1, R2) sau mặt nạ (15) và (16) = 0; trước mặt nạ = 0,1282.
 C8. Phân rã (24), ví dụ khối 8: c(D750) = 0,0740, c(D500) = 0,0340, b* = D750; trên mô hình thật: Σ_b c_u(b, l) = phần
     phần cứng của điểm; mọi câu giải thích trên top-10 val (sau mặt nạ): 0 lỗi sự kiện.
 C9. Faithfulness: phản thực tế không bỏ gì -> đúng điểm score_fn; có đối chứng thân / nhãn đúng khi có thân / nhãn
     khác (nhãn đối chứng khác c*, làm rõ 15/10); C9 chỉ mô tả khi < 30 cặp; "mô hình" β_h = 0 -> FS_PN = 0, ΔS = 0;
     bootstrap hai chuỗi giống hệt -> hiệu = 0. Thêm 15/10: dùng checkpoint chốt seed 1 (val) thay checkpoint chạy thử.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/cakg/test_eval_cakg.py --label 20261014_lan1 [--cakg-run <thư mục>]
"""
import argparse
import importlib
import math
import os
import sys
import tomllib
from types import SimpleNamespace

import numpy as np
import torch

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header  # noqa: E402
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

X08 = importlib.import_module("08_explain")
DEV = E.DEVICE
LGCN_S1 = "results/n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1"
CAKG_RUN = "results/cakg/val_sweep_20261014/val_cakg_lam1-1e-01_s1"   # checkpoint chốt seed 1 (val)
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


def c1():
    log("\n=== C1. Ví dụ khối 7 (dựng tay) ===")
    a7, d750, nik, can, sony, card = 0, 1, 10, 11, 12, 20
    ctx = C.CvrContext(lenses_in_m={nik, can, sony}, bodies_in_m={a7, d750}, m1={(d750, nik), (a7, sony)}, unknown=set())
    bodies = {0: {a7, d750}}
    lens, q = E.certain_violation_mask(bodies, ctx, n_users=1)
    _, x = EC.exists_violation_mask(bodies, ctx, n_users=1)
    names = {nik: "Nikon 200-500", can: "Canon EF 70-200", sony: "Sony FE 50"}
    check("QĐ 4-9 chặn", [names[int(l)] for l in lens[q[0]]], ["Canon EF 70-200"])
    check("∃b chặn", sorted(names[int(l)] for l in lens[x[0]]), ["Canon EF 70-200", "Nikon 200-500", "Sony FE 50"])
    item_type = np.full(30, 2)
    item_type[[nik, can, sony]] = 1
    item_type[[a7, d750]] = 0
    rc = EC.RelaxedContext(mount={a7: "sony_e", d750: "nikon_f", nik: "nikon_f", can: "canon_ef", sony: "sony_e"},
                           ab={}, named={}, ra=set())
    top = np.array([[nik, can, card, sony]])
    out, _ = EC.cvr_relaxed_from_top(np.array([0]), top, bodies, item_type, ctx, rc, k_list=[4])
    check("CVR trước mặt nạ @4", round(out["cvr_strict@4"], 4), 0.3333)
    top_m = np.array([[nik, card, sony, 21]])                     # sau mặt nạ (15): Canon EF bị bỏ
    check("CVR sau mặt nạ @4", EC.cvr_relaxed_from_top(np.array([0]), top_m, bodies, item_type, ctx, rc,
                                                        k_list=[4])[0]["cvr_strict@4"], 0.0)


def c2_c3(ev, masks):
    log("\n=== C2–C3. Mặt nạ trên dữ liệu thật ===")
    (lt, q), (_, x) = masks["qd49"], masks["exists"]
    q, x = q.cpu().numpy(), x.cpu().numpy()
    lens = lt.cpu().numpy()
    check("cặp bị chặn QĐ 4-9 / ∃b (người có thân, ống trong M)", [int(q.sum()), int(x.sum())], [8557447, 8904038])
    check("mọi ô QĐ 4-9 chặn đều bị ∃b chặn", bool((q & ~x).sum() == 0), True)
    col = {int(l): j for j, l in enumerate(lens)}
    sp = ev.split
    for g, w in (("lap_duoc", (0, 109)), ("khong_lap_duoc", (236, 236)), ("khong_phan_duoc", (0, 0))):
        sel = np.flatnonzero(ev.scn_lab == g)
        bq = sum(bool(q[sp.users[r], col[sp.pos[r]]]) for r in sel)
        bx = sum(bool(x[sp.users[r], col[sp.pos[r]]]) for r in sel)
        check(f"kịch bản val {g} ({len(sel)} người): item val bị chặn QĐ 4-9 / ∃b", [bq, bx], list(w))
    # uid 378
    attrs = {int(r["iid"]): r for r in EC._rows("item_attributes.csv")}
    u = 378
    bs = sorted(ev.bodies[u])
    log(f"  uid 378: thân {[(b, attrs[b]['mount'], attrs[b]['title'][:30]) for b in bs]}")
    lens200 = [i for i, r in attrs.items() if r["item_type"] == "ong" and "200-500" in r["title"]
               and "Nikon" in r["title"] and "5.6E" in r["title"] and i in col]
    log(f"  ống Nikon 200-500mm f/5.6E trong M: {[(i, attrs[i]['title'][:50]) for i in lens200]}")
    check("uid 378 có thân sony_e và nikon_f", sorted({attrs[b]["mount"] for b in bs}), ["nikon_f", "sony_e"])
    check("có ống Nikon 200-500 f/5.6E trong M", len(lens200) >= 1, True)
    for l in lens200:
        check(f"  ống {l}: QĐ 4-9 không chặn, ∃b chặn", [bool(q[u, col[l]]), bool(x[u, col[l]])], [False, True])
    sony = [l for l in lens if attrs[int(l)]["mount"] == "sony_e" and any((b, int(l)) in ev.ctx.m1 for b in bs)]
    check("uid 378: mọi ống sony_e lắp được trên a7 đều bị ∃b chặn (D750 M = 0), QĐ 4-9 không chặn",
          [all(x[u, col[int(l)]] for l in sony), any(q[u, col[int(l)]] for l in sony), len(sony) > 0], [True, False, True])


def lgcn_checks(ev, train, masks, rc, pctx):
    log("\n=== C4–C7. LightGCN s1 nội dung 5 (+ mặt nạ), VAL ===")
    with open("ai/config/n5_final.toml", "rb") as f:
        fin = tomllib.load(f)
    sha = next(r["best_pt_sha256"] for r in fin["lightgcn"]["runs"] if r["seed"] == 1)
    m, cfg, got_sha = EC.load_lightgcn(LGCN_S1, train, expect_sha=sha)
    check("sha256 best.pt = n5_final.toml", got_sha, sha)
    sf = m.score_fn()
    fr = E.full_rank(sf, ev.split, ev.pi)
    saved_top = np.load(f"{LGCN_S1}/val_top20_full.npy")
    saved_users = np.load(f"{LGCN_S1}/val_users.npy")
    check("người dùng val trùng mảng đã lưu", bool(np.array_equal(saved_users, ev.split.users)), True)
    diff = np.flatnonzero((fr["top"] != saved_top).any(1))
    worst = 0.0
    if len(diff):
        S = sf(torch.as_tensor(ev.split.users[diff], device=DEV)).cpu()
        for k, r in enumerate(diff):
            j = np.flatnonzero(fr["top"][r] != saved_top[r])
            ok_set = sorted(fr["top"][r][j].tolist()) == sorted(saved_top[r][j].tolist())
            sc = S[k, fr["top"][r][j]]
            worst = max(worst, float(sc.max() - sc.min()) if ok_set else float("inf"))
    log(f"  top-20 val dựng lại: {len(diff)} / {len(saved_top):,} hàng khác mảng đã lưu (GPU không tất định)")
    check("hàng lệch ≤ 0,05% số người", len(diff) <= 0.0005 * len(saved_top), True)
    check_le("hàng lệch chỉ là hoán vị các sản phẩm có điểm chênh nhau (max chênh)", worst, 1e-5)
    rx, _ = EC.cvr_relaxed_from_top(ev.split.users, fr["top"], ev.bodies, ev.item_type, ev.ctx, rc, k_list=[10])
    check("@10: ống chấm được / vi phạm / nới R1 / nới R2 / người được nới",
          [rx["n_lenses@10"], rx["n_violations@10"], rx["n_relaxed_r1@10"], rx["n_relaxed_r2@10"],
           rx["n_users_relaxed_r2@10"]], [23441, 3005, 61, 109, 50])
    check("CVR strict / R1 / R2 @10", [round(rx[k], 4) for k in ("cvr_strict@10", "cvr_relaxed_r1@10",
                                                                 "cvr_relaxed_r2@10")], [0.1282, 0.1256, 0.1235])
    u, l = 2465, 19161
    r = int(np.flatnonzero(ev.split.users == u)[0])
    check("uid 2465: ống 19161 trong top-10 val", l in fr["top"][r, :10].tolist(), True)
    v = C.judge_lens(l, ev.bodies[u], ev.ctx)
    r1, r2 = EC.relax_flags(u, l, ev.bodies[u], rc)
    check("uid 2465, ống 19161: strict vi phạm, R1 vẫn vi phạm, R2 được nới", [v, r1, r2], [True, False, True])
    pc, _ = EC.pc_from_top(ev.split.users, fr["top"], ev.bodies, ev.item_type, ev.ctx, pctx, k_list=[10])
    check("PC trên top-10 val (trước mặt nạ): ống chấm được / đường ngắn / đường đủ",
          [pc["n_judgable@10"], pc["n_short@10"], pc["n_full@10"]], [23441, 20436, 9095])
    log("  -- evaluate_with_masks (LightGCN + mặt nạ, val) --")
    res = EC.evaluate_with_masks(sf, ev, rc, pctx, log=lambda s: log("  " + s), tag="LightGCN s1 ")
    check("trước mặt nạ: CVR strict @10 (= eval_05)", round(res["truoc_mat_na"]["cvr"]["cvr@10"], 4), 0.1282)
    check("trước mặt nạ: cvr_relaxed strict = eval_05.cvr", res["truoc_mat_na"]["cvr_relaxed"]["cvr_strict@10"],
          res["truoc_mat_na"]["cvr"]["cvr@10"])
    for br in ("mat_na_qd49", "mat_na_exists"):
        rr = res[br]
        check(f"{br}: CVR strict @5/@10/@20 = 0 (eval_05) và strict / R1 / R2 = 0",
              [rr["cvr"][f"cvr@{k}"] for k in (5, 10, 20)] + [rr["cvr_relaxed"][f"{k}@10"] for k in
                                                              ("cvr_strict", "cvr_relaxed_r1", "cvr_relaxed_r2")],
              [0.0] * 6)
    check("mat_na_qd49: người có item val bị chặn theo nhóm", res["mat_na_qd49"]["n_target_blocked_by_scenario"],
          {"lap_duoc": 0, "khong_lap_duoc": 236, "khong_phan_duoc": 0})
    check("mat_na_exists: người có item val bị chặn theo nhóm", res["mat_na_exists"]["n_target_blocked_by_scenario"],
          {"lap_duoc": 109, "khong_lap_duoc": 236, "khong_phan_duoc": 0})
    check("sau mặt nạ QĐ 4-9: kịch bản 'không lắp được' Recall@10 chỉ ống = 0",
          res["mat_na_qd49"]["scenario"]["khong_lap_duoc"]["lens_only"]["recall@10"], 0.0)
    del m
    torch.cuda.empty_cache()


def c8_hand():
    log("\n=== C8. Phân rã (24), ví dụ khối 8 (dựng tay) ===")
    D750, D500, L, U0 = 0, 1, 2, 0
    comps = {"betaU": torch.tensor([[0.6, 0.4]]), "betaI": torch.tensor([[1, 0], [1, 0], [0.5, 0.5]]),
             "h": torch.tensor([[0.9, 0.1], [0.3, 0.5], [0.8, 0.2]]), "alpha2": torch.zeros(0)}
    H = SimpleNamespace(rel_names=[], item_loc={D750: 0, D500: 1, L: 2}, ei=torch.zeros(2, 0, dtype=torch.long),
                        et=torch.zeros(0, dtype=torch.long), off={}, node_names={})
    pctx = SimpleNamespace(rho={(D750, L): "compatible_with", (D500, L): "compatible_with"},
                           bodies_for=lambda u, l, bh: [b for b in bh.get(u, ()) if (b, l) in
                                                        {(D750, L), (D500, L)}])
    xp = EC.Explainer(comps, H, {U0: [D750, D500]}, pctx)
    ex = xp.explain(U0, L)
    check("c(D750), c(D500)", [round(ex["contrib"][D750], 4), round(ex["contrib"][D500], 4)], [0.0740, 0.0340])
    check("b*", ex["b_star"], D750)
    hu = (comps["h"][0] + comps["h"][1]) / 2
    check("Σ c = β_h(u) β_h(l) ⟨h_u, h_l⟩", round(sum(ex["contrib"].values()), 4),
          round(float(0.4 * 0.5 * hu @ comps["h"][2]), 4))


def cakg_checks(ev, train, masks, pctx, run_dir):
    log(f"\n=== C8–C9. Checkpoint CaKG-Rec ({run_dir}), VAL ===")
    model, cfg, sha = X08.load_cakg(run_dir, train, log=lambda s: log("  " + s))
    comps = model.components()
    sf = EC.mask_scorer(model.score_fn(), *masks["qd49"])
    fr = E.full_rank(sf, ev.split, ev.pi)
    expls, n_err, xp, H, bodies_h, pctx2 = X08.explain_all(model, cfg, ev, train, fr["top"],
                                                          log=lambda s: log("  " + s))
    check("số lỗi sự kiện trên mọi câu giải thích (top-10 val sau mặt nạ)", n_err, 0)
    check("có câu giải thích", len(expls) > 0, True)
    for e in expls[:3]:
        log(f"  ví dụ: u {e['u']}: {e['sentence']}")
    # Σ_b c_u(b, l) = phần phần cứng của điểm (trên 300 đường đầu)
    dmax = 0.0
    zU, zI = comps["zU"].cpu(), comps["zI"].cpu()
    for e in expls[:300]:
        allc = xp.contributions(e["u"], e["l"], bodies_h[e["u"]])
        hw = float(zU[e["u"], 64:] @ zI[e["l"], 64:])
        dmax = max(dmax, abs(sum(allc.values()) - hw))
    check_le("Σ_{b ∈ B_u^H} c_u(b, l) − β_uβ_l h_uᵀh_l (phần phần cứng của z_uᵀz_l), 300 đường", dmax, 1e-5)
    # c* có α lớn nhất
    ok = True
    a2 = comps["alpha2"].cpu()
    for e in expls:
        es = xp.suit_edges.get(H.item_loc[e["l"]], [])
        if e["c_star"] is not None:
            ok &= abs(e["alpha_c"] - max(float(a2[t[0]]) for t in es)) < 1e-9
    check("c* là nhãn có α lớp 2 lớn nhất trên rev_suitable_for", bool(ok), True)
    # C9: phản thực tế không bỏ gì -> đúng điểm
    Hd = CK.HwGraph(H.ei.to(DEV), H.et.to(DEV), H.rel_names, H.item_loc, H.n_nodes, H.off, H.node_names, H.counts)
    raw = model.make_scorer(comps, model.hidx)
    users = sorted(bodies_h)[:20]
    d = 0.0
    for u in users:
        S0 = raw(torch.as_tensor([u], device=DEV))[0]
        S1 = EC.counterfactual_score_row(model, Hd, bodies_h, u, None, [], comps["eU"], comps["eI"])[0]
        d = max(d, float((S0 - S1).abs().max() / S0.abs().max()))
    log(f"  phản thực tế không bỏ gì, float32: lệch tương đối max|ΔS| / max|S| = {d:.2e} (làm tròn; xem bản float64 dưới)")
    m64, _, _ = X08.load_cakg(run_dir, train, log=lambda s: None)
    m64 = m64.double()
    m64.adj, m64.A_ub = m64.adj.double(), m64.A_ub.double()
    c64 = m64.components()
    sf64 = m64.make_scorer(c64, m64.hidx)
    d64 = 0.0
    for u in users:
        S0 = sf64(torch.as_tensor([u], device=DEV))[0]
        S1 = EC.counterfactual_score_row(m64, Hd, bodies_h, u, None, [], c64["eU"], c64["eI"])[0]
        d64 = max(d64, float((S0 - S1).abs().max() / S0.abs().max()))
    check_le("phản thực tế không bỏ gì = score_fn (20 người có h_u), float64, lệch tương đối", d64, 1e-12)
    del m64, c64
    pairs = EC.sample_faith_pairs(expls, 40)
    check("chọn cặp Faithfulness: chỉ đường đủ 3 bước, ≤ 40", [all(p["c_star"] for p in pairs), len(pairs) <= 40],
          [True, True])
    fs = EC.faithfulness(model, Hd, bodies_h, ev, ev.split, masks["qd49"], pctx2, pairs)
    sm = EC.faithfulness_summary(fs, B=200)
    log(f"  checkpoint {run_dir}: FS_PN@10 {sm['fs_pn']:.4f}, ΔS {sm['dS_mean']:.5f}, {sm['n_pairs']} cặp; đối chứng "
        f"thân {sm['n_pairs_with_ctrl_body']}, đối chứng nhãn {sm['n_pairs_with_ctrl_label']} (số kiểm code, không phải kết quả)")
    check("FS_PN ∈ [0, 1]", 0.0 <= sm["fs_pn"] <= 1.0, True)
    check("có đối chứng nhãn ⇔ ống có ≥ 2 nhãn (nhãn đối chứng phải khác c*)",
          all((len(pctx2.suit[p["l"]]) > 1) == bool(h) for p, h in zip(pairs, fs["has_ctrl_label"])), True)
    check("có đối chứng thân ⇔ người có ≥ 2 thân M = 1 với ống",
          all((len(p["cand_bodies"]) > 1) == bool(h) for p, h in zip(pairs, fs["has_ctrl_body"])), True)
    check("C9 chỉ mô tả ⇔ < 30 cặp có đối chứng thân", sm["c9_chi_mo_ta"], sm["n_pairs_with_ctrl_body"] < 30)
    multi = [p for p in expls if p["c_star"] is not None and len(pctx2.suit[p["l"]]) > 1][:20]
    check("có cặp ống nhiều nhãn để kiểm đối chứng nhãn", len(multi) > 0, True)
    if multi:
        fsm = EC.faithfulness(model, Hd, bodies_h, ev, ev.split, masks["qd49"], pctx2, multi)
        check(f"{len(multi)} cặp ống nhiều nhãn: đều có đối chứng nhãn", int(fsm["has_ctrl_label"].sum()), len(multi))
    model.beta_h_zero = True                              # "mô hình" chỉ có kênh hành vi: cặp lấy từ top-10' của chính nó
    fr0 = E.full_rank(EC.mask_scorer(model.score_fn(), *masks["qd49"]), ev.split, ev.pi)
    ex0, n_err0, _, _, _, _ = X08.explain_all(model, cfg, ev, train, fr0["top"], log=lambda s: log("  β_h = 0: " + s))
    check("β_h = 0: số lỗi sự kiện (top-10 gồm ống EF trên thân EF-S, khác nhãn ngàm)", n_err0, 0)
    pairs0 = EC.sample_faith_pairs(ex0, 40)
    check("β_h = 0: có ≥ 20 cặp đường đủ 3 bước để kiểm", len(pairs0) >= 20, True)
    fs0 = EC.faithfulness(model, Hd, bodies_h, ev, ev.split, masks["qd49"], pctx2, pairs0)
    s0 = EC.faithfulness_summary(fs0, B=200)
    check("β_h = 0: FS_PN = 0, ΔS = 0 (đúng 0), hai đối chứng cũng 0",
          [s0["fs_pn"], float(np.abs(fs0["dS"]).max()),
           float(fs0["drop_ctrl_body"].sum() + fs0["drop_ctrl_label"].sum()),
           float(np.abs(fs0["dS_ctrl_body"]).max() + np.abs(fs0["dS_ctrl_label"]).max())], [0.0, 0.0, 0.0, 0.0])
    model.beta_h_zero = False
    same = EC.faithfulness_summary({**fs, "has_ctrl_body": np.ones_like(fs["drop"]), "drop_ctrl_body": fs["drop"],
                                    "dS_ctrl_body": fs["dS"]}, B=200)
    bs = same["bootstrap_ctrl_body"]
    check("bootstrap hai chuỗi giống hệt: hiệu và khoảng = 0", [bs["expl - ctrl"], bs["dS_expl - dS_ctrl"]],
          [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)])


def main():
    global log
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--cakg-run", default=CAKG_RUN)
    a = ap.parse_args()
    log = Log(os.path.join("ai/data/survey/cakg", f"run_test_eval_cakg_{a.label}.log"))
    header(log, __file__)
    c1()
    c8_hand()
    train = C.load_train()
    ev = E.EvalContext("val", train)
    masks = EC.masks_on_device(ev)
    rc = EC.relaxed_context(train, ev.bodies)
    pctx = EC.PathContext(train, ev.item_type)
    c2_c3(ev, masks)
    lgcn_checks(ev, train, masks, rc, pctx)
    cakg_checks(ev, train, masks, pctx, a.cakg_run)
    log(f"\n{'ĐẠT CẢ' if fails == 0 else f'CÓ {fails} KIỂM TRA SAI'}")
    log.save()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
