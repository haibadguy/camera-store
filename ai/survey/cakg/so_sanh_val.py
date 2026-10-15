"""Bảng so sánh trên VAL (seed 1) để hiểu mô hình, KHÔNG thay cho kết luận trên test. Viết 15/10/2026.
CHỈ ĐỌC checkpoint đã có (không huấn luyện, không đọc test). Log và json ghi ra file TÊN MỚI trong ai/data/survey/cakg/.

Mô hình (seed 1):
  - CaKG-Rec chốt (λ1 = 0,1): results/cakg/val_sweep_20261014/val_cakg_lam1-1e-01_s1/best.pt;
  - LightGCN nội dung 5: results/n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1/best.pt (sha256 như n5_final.toml);
  - LightGCN + mặt nạ QĐ 4-9: cùng checkpoint, số trước và sau mặt nạ lấy trong CÙNG một lần chấm (cùng điểm);
  - KGAT chốt (lr = 0,001): results/cakg/val_sweep_20261014/val_kgat_lr-1e-03_s1/best.pt.
Mỗi mô hình chấm 2 nhánh từ CÙNG một hàm điểm: trước mặt nạ, sau mặt nạ (15) QĐ 4-9 (eval_05.evaluate).
Cột: NDCG@20, Recall@10, CVR@10, kịch bản chỉ ống R@10 nhóm lắp được / không lắp được.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/cakg/so_sanh_val.py --label 20261015_lan1
"""
import argparse
import importlib
import json
import os
import sys
import tomllib

import torch

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

X08 = importlib.import_module("08_explain")
T07 = importlib.import_module("07_kgat_train")
SW = "results/cakg/val_sweep_20261014"
LGCN = "results/n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1"


def load_kgat(run_dir, train):
    cfg = json.load(open(f"{run_dir}/config.json", encoding="utf-8"))["cfg"]
    m = T07.build_kgat(cfg, train, log=lambda s: None)
    m.load_state_dict(torch.load(f"{run_dir}/best.pt", map_location=E.DEVICE, weights_only=False)["model"])
    m.eval()
    return m, E.sha256(f"{run_dir}/best.pt")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    out_dir = "ai/data/survey/cakg"
    log = Log(os.path.join(out_dir, f"run_so_sanh_val_{a.label}.log"))
    header(log, __file__)
    train = C.load_train()
    ev = E.EvalContext("val", train)
    lt, mt = EC.masks_on_device(ev)["qd49"]
    with open("ai/config/n5_final.toml", "rb") as f:
        lg_sha = next(r["best_pt_sha256"] for r in tomllib.load(f)["lightgcn"]["runs"] if r["seed"] == 1)
    rows = {}

    def run(name, model, sha):
        log(f"\n=== {name} (best.pt sha256 {sha[:16]}…) ===")
        sf = model.score_fn()                         # một lần tính biểu diễn, dùng cho cả hai nhánh
        out = {}
        for br, f in (("truoc_mat_na", sf), ("sau_mat_na_qd49", EC.mask_scorer(sf, lt, mt))):
            log(f"  --- {br} ---")
            r = E.evaluate(f, ev, log=lambda s: log("  " + s))
            out[br] = {"ndcg@20": r["full"]["ndcg@20"], "recall@10": r["full"]["recall@10"],
                       "cvr@10": r["cvr"]["cvr@10"], "cvr_n_viol@10": r["cvr"]["cvr_n_violations@10"],
                       "cvr_n_lenses@10": r["cvr"]["cvr_n_lenses@10"],
                       "scn_lap_duoc_R@10": r["scenario"]["lap_duoc"]["lens_only"]["recall@10"],
                       "scn_khong_lap_duoc_R@10": r["scenario"]["khong_lap_duoc"]["lens_only"]["recall@10"],
                       "n_lap_duoc": r["scenario"]["lap_duoc"]["n_users"],
                       "n_khong_lap_duoc": r["scenario"]["khong_lap_duoc"]["n_users"]}
        rows[name] = {"sha256": sha, **out}

    m, cfg, sha = X08.load_cakg(f"{SW}/val_cakg_lam1-1e-01_s1", train, log=lambda s: None)
    run("CaKG-Rec λ1 = 0,1", m, sha)
    del m
    m, _, sha = EC.load_lightgcn(LGCN, train, expect_sha=lg_sha)
    run("LightGCN (nội dung 5)", m, sha)
    del m
    m, sha = load_kgat(f"{SW}/val_kgat_lr-1e-03_s1", train)
    run("KGAT lr = 0,001", m, sha)
    del m

    log("\nBẢNG (VAL, seed 1; chỉ để hiểu mô hình, không thay kết luận trên test)")
    hdr = f"{'mô hình':<34} {'NDCG@20':>8} {'R@10':>7} {'CVR@10':>7} {'lắp được R@10':>14} {'không lắp được R@10':>20}"
    log(hdr)
    for name, r in rows.items():
        for br, lab in (("truoc_mat_na", "trước mặt nạ"), ("sau_mat_na_qd49", "sau mặt nạ QĐ 4-9")):
            x = r[br]
            log(f"{name + ', ' + lab:<34} {x['ndcg@20']:>8.5f} {x['recall@10']:>7.4f} {x['cvr@10']:>7.4f} "
                f"{x['scn_lap_duoc_R@10']:>14.4f} {x['scn_khong_lap_duoc_R@10']:>20.4f}")
    fn = os.path.join(out_dir, f"so_sanh_val_{a.label}.json")
    assert not os.path.exists(fn)
    json.dump({"git": E.git_state(), "rows": rows}, open(fn, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    log(f"-> {fn}")
    log.save()


if __name__ == "__main__":
    main()
