"""
08_explain.py -- Giải thích cho CaKG-Rec: đường u –owns→ b* –ρ→ l –suitable_for→ c*, câu tiếng Việt, kiểm mọi cạnh được
nhắc, Path Coverage, Faithfulness (docs/cakg_design.md khối 8; kế hoạch docs/reviews/cakg_eval_plan.md mục 5, 7, 11).
Viết 14/10/2026. Hàm: eval_cakg.py. Kiểm thử dựng tay: ai/survey/cakg/test_eval_cakg.py.

Ví dụ (thiết kế khối 8): người có D750 và D500 (cả hai M = 1 với ống l), β_h(u) = 0,4, β_h(l) = 0,5,
h_D750 = (0,9; 0,1), h_D500 = (0,3; 0,5), h_l = (0,8; 0,2): c(D750) = 0,4·0,5·0,74/2 = 0,0740, c(D500) = 0,0340 -> b* = D750.

Các bước (một checkpoint CaKG-Rec, một tập):
  1. top-K' = top-K SAU mặt nạ (15) QĐ 4-9, full ranking như eval_05;
  2. với mọi người có thân và mọi ống trong top-10': dựng đường (nếu có), câu, kiểm sự kiện (lỗi phải = 0);
  3. PC@5, PC@10, PC_ngắn, PC_mọi_sp (25);
  4. Faithfulness (26) trên tối đa --max-faith cặp có đường đủ 3 bước (seed 20261014), đối chứng ngẫu nhiên, bootstrap.
Chạy test chỉ khi có --allow-test (bước 6 của kế hoạch, sau khi chốt cakg_final.toml) và cây git sạch.

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/08_explain.py --run-dir results/cakg/<...>/<lần chạy> --split val --label <nhãn>
"""

import argparse
import importlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

T06 = importlib.import_module("06_cakg_train")


def load_cakg(run_dir, train, log=print, device=E.DEVICE):
    run_dir = Path(run_dir)
    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))["cfg"]
    cfg = {k: v for k, v in cfg.items() if not k.startswith("_")}
    m = T06.build_cakg(cfg, train, log=log, device=device)
    pt = run_dir / "best.pt"
    m.load_state_dict(torch.load(pt, map_location=device, weights_only=False)["model"])
    m.eval()
    return m, cfg, E.sha256(pt)


def explain_all(model, cfg, ev, train, top, log=print, k=10):
    """Đường + câu + kiểm cho mọi (người có thân, ống trong top-k). Trả về (danh sách đường, số lỗi, Explainer, H, B_u^H)."""
    H = CK.build_h(drop_suitable_for=cfg["drop_suitable_for"])
    _, _, bodies_h = CK.user_body_matrix(train, ev.item_type, H.item_loc, H.n_nodes)
    pctx = EC.PathContext(train, ev.item_type)
    xp = EC.Explainer(model.components(), H, bodies_h, pctx)
    has = EC.h_edge_checker(H)
    out, n_err, n_lens = [], 0, 0
    for r, u in enumerate(ev.split.users.tolist()):
        if u not in ev.bodies:
            continue
        for l in top[r, :k].tolist():
            if ev.item_type[l] != 1:
                continue
            n_lens += 1
            ex = xp.explain(u, l)
            if ex is None:
                continue
            s = EC.sentence(ex, pctx)
            err = EC.verify_explanation(ex, s, pctx, has)
            n_err += len(err)
            if err and n_err <= 20:
                log(f"  LỖI giải thích (u {u}, l {l}): {err}")
            ex["sentence"], ex["errors"] = s, err
            out.append(ex)
    log(f"  đường dựng được: {len(out):,} / {n_lens:,} ống (người có thân, top-{k}); đủ 3 bước: "
        f"{sum(e['c_star'] is not None for e in out):,}; lỗi sự kiện: {n_err}")
    return out, n_err, xp, H, bodies_h, pctx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="thư mục một lần chạy 06_cakg_train (config.json, best.pt)")
    ap.add_argument("--split", default="val", choices=["val", "test"])
    ap.add_argument("--allow-test", action="store_true", help="chỉ dùng ở bước chạy test một lần của kế hoạch")
    ap.add_argument("--label", required=True)
    ap.add_argument("--max-faith", type=int, default=2000)
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args()
    git = E.git_state()
    if a.split == "test" and (not a.allow_test or git["dirty"]):
        sys.exit("DỪNG: chấm test cần --allow-test và cây git sạch (kế hoạch mục 4.2 bước 6).")
    out_dir = Path(a.out_dir) if a.out_dir else Path(a.run_dir) / f"explain_{a.split}_{a.label}"
    out_dir.mkdir(parents=True, exist_ok=False)
    log = E.Log(out_dir / f"explain_{E.now_tag()}.log")
    log(f"08_explain | {a.run_dir} | tập {a.split} | git {git}")
    train = C.load_train()
    model, cfg, sha = load_cakg(a.run_dir, train, log=log)
    log(f"best.pt sha256 {sha}")
    ev = E.EvalContext(a.split, train)
    masks = EC.masks_on_device(ev)
    t = time.time()
    fr = E.full_rank(EC.mask_scorer(model.score_fn(), *masks["qd49"]), ev.split, ev.pi)
    log(f"top-20 sau mặt nạ QĐ 4-9: {time.time() - t:.1f}s")
    expls, n_err, xp, H, bodies_h, pctx = explain_all(model, cfg, ev, train, fr["top"], log=log)
    pc, _ = EC.pc_from_top(ev.split.users, fr["top"], ev.bodies, ev.item_type, ev.ctx, pctx)
    log("  Path Coverage (sau mặt nạ): " + " ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v:,}"
                                                    for k, v in pc.items()))
    pairs = EC.sample_faith_pairs(expls, a.max_faith)
    log(f"Faithfulness: {len(pairs):,} cặp (tối đa {a.max_faith:,}, seed {EC.FAITH_SEED}) trên "
        f"{sum(e['c_star'] is not None for e in expls):,} cặp có đường đủ 3 bước")
    Hd = CK.HwGraph(H.ei.to(E.DEVICE), H.et.to(E.DEVICE), H.rel_names, H.item_loc, H.n_nodes, H.off, H.node_names,
                    H.counts)
    t = time.time()
    fs = EC.faithfulness(model, Hd, bodies_h, ev, ev.split, masks["qd49"], pctx, pairs, K=10)
    summ = EC.faithfulness_summary(fs)
    log(f"  {time.time() - t:.1f}s | FS_PN@10 = {summ['fs_pn']:.4f}, ΔS = {summ['dS_mean']:.5f} trên {summ['n_pairs']:,} cặp")
    for x, lab in (("body", "đối chứng thân (C9)"), ("label", "đối chứng nhãn")):
        log(f"  {lab}: có {summ[f'n_pairs_with_ctrl_{x}']:,} cặp, không có {summ[f'n_pairs_no_ctrl_{x}']:,} cặp"
            + (" (ống chỉ có một nhãn)" if x == "label" else " (người chỉ có một thân M = 1 với ống)"))
        for k_, v in summ.get(f"bootstrap_ctrl_{x}", {}).items():
            log(f"    {k_}: {v[0]:.4f} [{v[1]:.4f}; {v[2]:.4f}]")
    if summ["c9_chi_mo_ta"]:
        log(f"  C9: dưới {EC.C9_MIN_PAIRS} cặp có đối chứng thân -> CHỈ BÁO MÔ TẢ")
    with open(out_dir / "explanations.jsonl", "x", encoding="utf-8") as f:
        for e in expls:
            f.write(json.dumps({k: (v if not isinstance(v, dict) else {str(b): c for b, c in v.items()})
                                for k, v in e.items()}, ensure_ascii=False) + "\n")
    np.savez(out_dir / "faithfulness_pairs.npz", **fs)
    res = {"run_dir": str(a.run_dir), "split": a.split, "git": git, "best_pt_sha256": sha, "cfg": cfg,
           "n_explanations": len(expls), "n_fact_errors": n_err, "path_coverage_after_mask_qd49": pc,
           "faithfulness": summ, "explanations_sha256": E.sha256(out_dir / "explanations.jsonl")}
    (out_dir / "summary.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {out_dir / 'summary.json'}")
    log.close()


if __name__ == "__main__":
    main()
