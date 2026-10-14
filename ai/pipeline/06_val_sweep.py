"""
06_val_sweep.py -- Dò siêu tham số trên val, seed 1, cho mô hình mới của nội dung 6–8 (docs/reviews/cakg_eval_plan.md
mục 4.1, 4.2 bước 3). Viết 14/10/2026 theo khuôn 05_val_sweep.py. KHÔNG chấm test.

Nhóm lần chạy (--group):
  cakg: CaKG-Rec λ1 ∈ {0,01; 0,1; 1,0}  (06_cakg_train.py; tối đa 300 epoch, chấm val mỗi 10 epoch, dừng sau 5 lần
        chấm không tăng). Chỉ số chọn: NDCG@20 full ranking val TRƯỚC mặt nạ (QĐ 5-6).
Mỗi lần chạy là một tiến trình con ghi vào results/cakg/val_sweep_<nhãn>/<tên lần chạy>/ với log riêng
train_<thời điểm>.log. Log của chính script này: sweep_<nhóm>_<thời điểm>.log (tên mới mỗi lần gọi).

Chạy tiếp: bị ngắt (Ctrl+C, mất điện, máy ngủ...) thì gõ lại ĐÚNG lệnh cũ (cùng --group, --label):
  - lần chạy đã có result.json: bỏ qua;
  - lần chạy dở: tiếp từ lần chấm val gần nhất (last.pt);
  - lần chạy chưa bắt đầu: chạy mới.
Cuối cùng in bảng NDCG@20 val (trước / sau mặt nạ), cấu hình tốt nhất, cờ "ở biên lưới", và kiểm mọi lần chạy cùng
sha256 code + đầu vào (config.json). KHÔNG ghi cakg_final.toml (bước 4 của kế hoạch do Nam chốt và commit).

Lệnh (PowerShell, từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/06_val_sweep.py --group cakg --label 20261014
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PIPE = Path(__file__).resolve().parent
OUT_DIR = C.RESULTS_DIR / "cakg"
GROUPS = {  # nhóm -> (tên tham số dò, [(tên lần chạy, script, tham số riêng, giá trị dò)])
    "cakg": ("lam1", [
        ("val_cakg_lam1-1e-02_s1", "06_cakg_train.py", ["--lam1", "0.01", "--seed", "1"], 0.01),
        ("val_cakg_lam1-1e-01_s1", "06_cakg_train.py", ["--lam1", "0.1", "--seed", "1"], 0.1),
        ("val_cakg_lam1-1e+00_s1", "06_cakg_train.py", ["--lam1", "1.0", "--seed", "1"], 1.0),
    ]),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", required=True, choices=sorted(GROUPS))
    ap.add_argument("--label", required=True, help="nhãn của đợt dò, vd 20261014 (giữ nguyên khi chạy tiếp)")
    ap.add_argument("--allow-dirty", action="store_true", help="cho chạy khi file đã theo dõi trong git bị sửa")
    ap.add_argument("--smoke", action="store_true", help="(kiểm thử) mỗi lần chạy chỉ 1 epoch")
    a = ap.parse_args()
    pname, runs = GROUPS[a.group]
    root = OUT_DIR / f"{'smoke_' if a.smoke else ''}val_sweep_{a.label}"
    root.mkdir(parents=True, exist_ok=True)
    log = E.Log(root / f"sweep_{a.group}_{E.now_tag()}.log")
    git = E.git_state()
    log(f"Dò val | nhóm {a.group} | {root} | git {git} | {len(runs)} lần chạy" + (" | SMOKE: 1 epoch" if a.smoke else ""))
    if git["dirty"] and not a.allow_dirty:
        log("DỪNG: có file đã theo dõi trong git bị sửa mà chưa commit. Commit trước (hoặc --allow-dirty).")
        sys.exit(2)
    if E.DEVICE.type != "cuda":
        log("DỪNG: không thấy GPU (torch.cuda.is_available() = False).")
        sys.exit(2)

    t_all = time.time()
    for k, (name, script, args, _) in enumerate(runs, 1):
        rd = root / name
        if (rd / "result.json").exists():
            log(f"[{k}/{len(runs)}] {name}: đã xong, bỏ qua")
            continue
        cmd = [sys.executable, "-W", "ignore", str(PIPE / script), *args, "--run-dir", str(rd)]
        if a.smoke:
            cmd += ["--max-epoch", "1", "--eval-every", "1"]
        log(f"[{k}/{len(runs)}] {name}: {'chạy tiếp' if (rd / 'last.pt').exists() else 'bắt đầu'} lúc "
            f"{time.strftime('%H:%M:%S')} | git {E.git_state()} | {' '.join(cmd[3:])}")
        t = time.time()
        try:
            rc = subprocess.run(cmd).returncode
        except KeyboardInterrupt:
            log(f"Bị ngắt ở {name} sau {(time.time() - t) / 60:.1f} phút. Gõ lại đúng lệnh để chạy tiếp.")
            sys.exit(130)
        if rc != 0:
            log(f"DỪNG: {name} lỗi (mã {rc}) sau {(time.time() - t) / 60:.1f} phút; xem log trong {rd}")
            sys.exit(rc)
        log(f"[{k}/{len(runs)}] {name}: xong sau {(time.time() - t) / 60:.1f} phút")

    log(f"\nXong cả {len(runs)} lần chạy ({(time.time() - t_all) / 60:.1f} phút ở lần gọi này).")
    log(f"{'lần chạy':<26} {'NDCG@20 val':>11} {'sau mặt nạ':>10} {'R@20 val':>9} {'epoch tốt':>9} {'đã chạy':>7} "
        f"{'s/epoch':>7} {'VRAM MiB':>8}  ghi chú")
    summary, shas = {}, {}
    for name, _, _, val in runs:
        r = json.loads((root / name / "result.json").read_text(encoding="utf-8"))
        c = json.loads((root / name / "config.json").read_text(encoding="utf-8"))
        shas[name] = (c.get("code_sha256"), c["inputs_sha256"])
        f = r["val"]["full"]
        fm = r.get("val_mask", {}).get("full", {})
        summary[name] = {"model": r["model"], "cfg": r["cfg"], pname: val, "val_ndcg@20": f["ndcg@20"],
                         "val_ndcg@20_mask": fm.get("ndcg@20"), "val_recall@20": f["recall@20"],
                         "best_epoch": r["best_epoch"], "epochs_run": r["epochs_run"],
                         "chua_chac_hoi_tu": r["chua_chac_hoi_tu"], "median_sec_per_epoch": r["median_sec_per_epoch"],
                         "peak_vram_allocated_mib": r.get("peak_vram_allocated_mib"),
                         "peak_vram_eval_allocated_mib": r.get("peak_vram_eval_allocated_mib"),
                         "git_start": c["git"], "git_at_finish": r["git_at_finish"]}
        s = summary[name]
        log(f"{name:<26} {f['ndcg@20']:>11.5f} {(fm.get('ndcg@20') or float('nan')):>10.5f} {f['recall@20']:>9.5f} "
            f"{r['best_epoch']:>9} {r['epochs_run']:>7} {r['median_sec_per_epoch']:>7.1f} "
            f"{(s['peak_vram_allocated_mib'] or 0):>8.0f}  "
            f"{'chưa chắc hội tụ' if r['chua_chac_hoi_tu'] else 'dừng sớm'}; git đầu {c['git']['commit'][:7]}"
            f"{' (dirty)' if c['git']['dirty'] else ''}")
    same = len({json.dumps(v, sort_keys=True) for v in shas.values()}) == 1
    log(f"Mọi lần chạy cùng sha256 code + đầu vào (config.json): {'CÓ' if same else 'KHÔNG — xem config.json'}")
    best = max(summary, key=lambda n: summary[n]["val_ndcg@20"])
    vals = sorted(v for *_, v in runs)
    edge = summary[best][pname] in (vals[0], vals[-1])
    log(f"Tốt nhất theo NDCG@20 val (trước mặt nạ): {best} ({pname} = {summary[best][pname]})"
        + (" — Ở BIÊN LƯỚI (ghi lại, không mở rộng lưới: kế hoạch mục 4.1)" if edge else ""))
    out = root / f"summary_{a.group}_{E.now_tag()}.json"
    out.write_text(json.dumps({"git": git, "group": a.group, "best": best, "best_at_grid_edge": edge,
                               "same_code_and_inputs": same, "runs": summary}, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    log(f"-> {out}")
    log.close()


if __name__ == "__main__":
    main()
