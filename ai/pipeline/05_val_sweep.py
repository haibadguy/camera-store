"""
05_val_sweep.py -- Dò siêu tham số trên val, seed 1 (docs/reviews/n5_eval_plan.md mục 7.2 bước 2; QĐ 5-5, 5-6).

5 lần chạy, lần lượt:
  LightGCN λ ∈ {1e-5, 1e-4, 1e-3}  (tối đa 300 epoch, chấm val mỗi 10 epoch)
  R-GCN   lr ∈ {0,01; 0,001}       (tối đa 100 epoch, chấm val mỗi 5 epoch)
Mỗi lần chạy là một tiến trình con (05b / 05c) ghi vào results/n5/val_sweep_<nhãn>/<tên lần chạy>/ với log riêng
train_<thời điểm>.log. Không chấm test.

Chạy tiếp: bị ngắt (Ctrl+C, mất điện, máy ngủ...) thì gõ lại ĐÚNG lệnh cũ (cùng --label):
  - lần chạy đã có result.json: bỏ qua;
  - lần chạy dở: tiếp từ lần chấm val gần nhất (last.pt);
  - lần chạy chưa bắt đầu: chạy mới.
Cuối cùng in bảng NDCG@20 val của 5 lần chạy và cấu hình tốt nhất mỗi mô hình (chưa ghi n5_final.toml — bước 3
của kế hoạch do Nam chốt và commit).

Lệnh (PowerShell, từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/05_val_sweep.py --label 20261010
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_05 as E  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PIPE = Path(__file__).resolve().parent
RUNS = [  # (tên, script, tham số riêng)
    ("val_lightgcn_l2-1e-05_s1", "05b_lightgcn_train.py", ["--l2", "1e-5", "--seed", "1"]),
    ("val_lightgcn_l2-1e-04_s1", "05b_lightgcn_train.py", ["--l2", "1e-4", "--seed", "1"]),
    ("val_lightgcn_l2-1e-03_s1", "05b_lightgcn_train.py", ["--l2", "1e-3", "--seed", "1"]),
    ("val_rgcn_lr-1e-02_s1",     "05c_rgcn_train.py",     ["--lr", "0.01", "--seed", "1"]),
    ("val_rgcn_lr-1e-03_s1",     "05c_rgcn_train.py",     ["--lr", "0.001", "--seed", "1"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="nhãn của đợt dò, vd 20261010 (giữ nguyên khi chạy tiếp)")
    ap.add_argument("--allow-dirty", action="store_true", help="cho chạy khi file đã theo dõi trong git bị sửa")
    ap.add_argument("--smoke", action="store_true", help="(kiểm thử) mỗi lần chạy chỉ 1 epoch")
    a = ap.parse_args()
    root = E.N5_DIR / f"{'smoke_' if a.smoke else ''}val_sweep_{a.label}"
    root.mkdir(parents=True, exist_ok=True)
    log = E.Log(root / f"sweep_{E.now_tag()}.log")
    git = E.git_state()
    log(f"Dò val | {root} | git {git} | {len(RUNS)} lần chạy" + (" | SMOKE: 1 epoch" if a.smoke else ""))
    if git["dirty"] and not a.allow_dirty:
        log("DỪNG: có file đã theo dõi trong git bị sửa mà chưa commit. Commit trước (hoặc --allow-dirty).")
        sys.exit(2)
    if E.DEVICE.type != "cuda":
        log("DỪNG: không thấy GPU (torch.cuda.is_available() = False).")
        sys.exit(2)

    t_all = time.time()
    for k, (name, script, args) in enumerate(RUNS, 1):
        rd = root / name
        if (rd / "result.json").exists():
            log(f"[{k}/{len(RUNS)}] {name}: đã xong, bỏ qua")
            continue
        cmd = [sys.executable, "-W", "ignore", str(PIPE / script), *args, "--run-dir", str(rd)]
        if a.smoke:
            cmd += ["--max-epoch", "1", "--eval-every", "1"]
        log(f"[{k}/{len(RUNS)}] {name}: {'chạy tiếp' if (rd / 'last.pt').exists() else 'bắt đầu'} lúc "
            f"{time.strftime('%H:%M:%S')} | {' '.join(cmd[3:])}")
        t = time.time()
        try:
            rc = subprocess.run(cmd).returncode
        except KeyboardInterrupt:
            log(f"Bị ngắt ở {name} sau {(time.time() - t) / 60:.1f} phút. Gõ lại đúng lệnh để chạy tiếp.")
            sys.exit(130)
        if rc != 0:
            log(f"DỪNG: {name} lỗi (mã {rc}) sau {(time.time() - t) / 60:.1f} phút; xem log trong {rd}")
            sys.exit(rc)
        log(f"[{k}/{len(RUNS)}] {name}: xong sau {(time.time() - t) / 60:.1f} phút")

    log(f"\nXong cả {len(RUNS)} lần chạy ({(time.time() - t_all) / 60:.1f} phút ở lần gọi này).")
    log(f"{'lần chạy':<26} {'NDCG@20 val':>11} {'R@20 val':>9} {'epoch tốt':>9} {'đã chạy':>7} "
        f"{'s/epoch':>7}  ghi chú")
    summary = {}
    for name, _, _ in RUNS:
        r = json.loads((root / name / "result.json").read_text(encoding="utf-8"))
        f = r["val"]["full"]
        summary[name] = {"model": r["model"], "cfg": r["cfg"], "val_ndcg@20": f["ndcg@20"],
                         "val_recall@20": f["recall@20"], "best_epoch": r["best_epoch"],
                         "epochs_run": r["epochs_run"], "chua_chac_hoi_tu": r["chua_chac_hoi_tu"],
                         "median_sec_per_epoch": r["median_sec_per_epoch"]}
        log(f"{name:<26} {f['ndcg@20']:>11.5f} {f['recall@20']:>9.5f} {r['best_epoch']:>9} {r['epochs_run']:>7} "
            f"{r['median_sec_per_epoch']:>7.1f}  {'chưa chắc hội tụ' if r['chua_chac_hoi_tu'] else 'dừng sớm'}")
    for m in ("LightGCN", "R-GCN"):
        cand = {n: s for n, s in summary.items() if s["model"].startswith(m)}
        best = max(cand, key=lambda n: cand[n]["val_ndcg@20"])
        log(f"Tốt nhất theo NDCG@20 val — {m}: {best}")
    out = root / f"summary_{E.now_tag()}.json"
    out.write_text(json.dumps({"git": git, "runs": summary}, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {out}")
    log.close()


if __name__ == "__main__":
    main()
