"""
v3_sweep.py — hàng đợi huấn luyện v3 trên máy nhóm (docs/reviews/v3_eval_plan.md mục 3, 4, 6, 8.3; quyết định của Nam
06/11/2026). Viết 06/11/2026 theo khuôn 06_val_sweep.py. KHÔNG chấm test.

Nhóm lần chạy (--group):
  s1: DÒ trên val, seed 1, trần 1.000 epoch, theo đúng thứ tự (kế hoạch mục 6.1):
      1. LightGCN λ2 = 1e-3 (CHẠY TIẾP từ last.pt epoch 300), λ2 = 3e-3, 1e-2 (mới);
      2. CaKG-Rec v2 A lens_gate, λ1 = 0,1 (CHẠY TIẾP);
      3. KGAT lr = 1e-4 (CHẠY TIẾP), lr = 3e-3 (mới);
      4. R-GCN lr = 3e-4, 1e-4 (mới; chấm val mỗi 5 epoch như cũ).
  Các lần cũ đã DỪNG SỚM dưới trần cũ (LightGCN λ2 1e-5 / 1e-4; R-GCN lr 1e-2 / 1e-3; KGAT lr 1e-3) giữ nguyên, không
  chạy lại (quy tắc dừng không đổi nên trần 1.000 cho cùng kết quả). Seed 2–5 và ablation: nhóm sau, khi đã chốt
  ai/config/v3_final.toml (kế hoạch mục 6.1–6.2).

Chạy tiếp (PA2, điều kiện của Nam 06/11): chỉ khi last.pt của lần cũ ĐẠT ở kiểm results/v3/kiem_last_pt_<nhãn>.json
(--kiem; đủ Adam + RNG, code / dữ liệu không đổi). Khi đó thư mục cũ được CHÉP sang results/v3/<nhóm>_<nhãn>/<tên>/
(trừ result.json và mảng val_*.npy của lần chấm cuối cũ; kết quả cũ ở results/n5, results/cakg giữ nguyên), ghi
resume_source.json (nguồn, sha256 last.pt / best.pt / config.json), rồi gọi script huấn luyện với --max-epoch 1000:
train_05.run thấy chỉ max_epoch tăng -> chạy tiếp, ghi config.json -> max_epoch_changes. Không ĐẠT -> chạy lại từ đầu.

Mỗi lần chạy: log train_<thời điểm>.log của train_05, history trong result.json, ảnh đường cong val
curve_val_e<epoch>.png (ai/survey/v3/ve_duong_cong.py, sau khi lần chạy xong). Log của script này:
sweep_<nhóm>_<thời điểm>.log (tên mới mỗi lần gọi; dòng "[k/n] tên: xong sau X phút" như các đợt cũ).
Bị ngắt: gõ lại đúng lệnh (cùng --group, --label) -> lần đã có result.json bỏ qua, lần dở chạy tiếp từ last.pt.

Lệnh (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/v3_sweep.py --group s1 --label 20261106 --kiem results/v3/kiem_last_pt_lan2.json
"""

import argparse
import hashlib
import json
import shutil
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
OUT_DIR = C.RESULTS_DIR / "v3"
MAX_EPOCH = 1000
CURVE = C.ROOT / "ai" / "survey" / "v3" / "ve_duong_cong.py"
# (tên, script, tham số, thư mục lần cũ để chạy tiếp hoặc None)
GROUPS = {
    "s1": [
        ("lightgcn_l2-1e-03_s1", "05b_lightgcn_train.py", ["--l2", "1e-3", "--seed", "1"],
         "n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1"),
        ("lightgcn_l2-3e-03_s1", "05b_lightgcn_train.py", ["--l2", "3e-3", "--seed", "1"], None),
        ("lightgcn_l2-1e-02_s1", "05b_lightgcn_train.py", ["--l2", "1e-2", "--seed", "1"], None),
        ("cakg_v2A_lam1-1e-01_s1", "06_cakg_train.py", ["--lam1", "0.1", "--seed", "1", "--variant", "lens_gate"],
         "cakg/val_sweep_v2_20261016/val_v2_A_lens_gate_s1"),
        ("kgat_lr-1e-04_s1", "07_kgat_train.py", ["--lr", "1e-4", "--seed", "1"],
         "cakg/val_sweep_20261014/val_kgat_lr-1e-04_s1"),
        ("kgat_lr-3e-03_s1", "07_kgat_train.py", ["--lr", "3e-3", "--seed", "1"], None),
        ("rgcn_lr-3e-04_s1", "05c_rgcn_train.py", ["--lr", "3e-4", "--seed", "1"], None),
        ("rgcn_lr-1e-04_s1", "05c_rgcn_train.py", ["--lr", "1e-4", "--seed", "1"], None),
    ],
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def prepare_resume(src_rel, rd, kiem, log):
    """Chép lần cũ sang rd nếu last.pt ĐẠT kiểm; trả về True nếu sẽ chạy tiếp, False nếu chạy lại từ đầu."""
    if (rd / "resume_source.json").exists():
        return True                                    # đã chép ở lần gọi trước (đang chạy tiếp dở)
    row = next((r for r in kiem["runs"] if r["run"] == src_rel), None)
    src = C.RESULTS_DIR / src_rel
    if row is None or not row["dat"]:
        log(f"    last.pt của {src_rel} KHÔNG ĐẠT kiểm ({None if row is None else row['loi']}) -> chạy lại từ đầu")
        return False
    if sha256(src / "last.pt") != row["last_pt_sha256"]:
        log(f"    last.pt của {src_rel} đã đổi sau lần kiểm -> chạy lại từ đầu")
        return False
    assert not rd.exists() or not any(rd.iterdir()), f"thư mục đích không rỗng: {rd}"
    rd.mkdir(parents=True, exist_ok=True)
    copied = []
    for p in sorted(src.iterdir()):
        if p.name == "result.json" or (p.suffix == ".npy" and p.name.startswith("val_")):
            continue
        shutil.copy2(p, rd / p.name)
        copied.append(p.name)
    meta = {"source": src_rel, "copied": copied, "time": E.now_tag(), "git": E.git_state(),
            "sha256": {n: sha256(rd / n) for n in ("last.pt", "best.pt", "config.json")},
            "kiem": {"file": kiem["_file"], "dat": row["dat"], "state": row["state"]}}
    (rd / "resume_source.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"    chép {len(copied)} file từ results/{src_rel} (last.pt ĐẠT kiểm; epoch {row['state']['epoch']}, tốt nhất "
        f"{row['state']['best']:.5f} ở {row['state']['best_epoch']})")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", required=True, help=f"{sorted(GROUPS)} hoặc tên bất kỳ khi có --runs-json")
    ap.add_argument("--runs-json", default=None, help="danh sách lần chạy [[tên, script, tham số, nguồn chạy tiếp|null]] "
                    "do v3_chain.py sinh (đợt s1b / s25 / abl, theo ai/config/v3_final.toml)")
    ap.add_argument("--label", required=True, help="nhãn đợt, vd 20261106 (giữ nguyên khi chạy tiếp)")
    ap.add_argument("--kiem", required=True, help="results/v3/kiem_last_pt_<nhãn>.json (ai/survey/v3/kiem_last_pt.py)")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="(kiểm thử) thư mục smoke_; lần chạy tiếp: thêm 1 lần chấm "
                    "sau mốc 300; lần mới: 2 epoch, chấm mỗi epoch")
    ap.add_argument("--only", nargs="*", help="(kiểm thử) chỉ chạy các lần có tên này")
    a = ap.parse_args()
    kiem = json.loads((C.ROOT / a.kiem).read_text(encoding="utf-8"))
    kiem["_file"] = a.kiem
    if a.runs_json:
        all_runs = [tuple(r) for r in json.loads((C.ROOT / a.runs_json).read_text(encoding="utf-8"))]
    else:
        assert a.group in GROUPS, f"nhóm {a.group} không có sẵn, cần --runs-json"
        all_runs = GROUPS[a.group]
    runs = [r for r in all_runs if not a.only or r[0] in a.only]
    assert runs, "không có lần chạy nào"
    root = OUT_DIR / f"{'smoke_' if a.smoke else ''}{a.group}_{a.label}"
    root.mkdir(parents=True, exist_ok=True)
    log = E.Log(root / f"sweep_{a.group}_{E.now_tag()}.log")
    git = E.git_state()
    log(f"v3 | nhóm {a.group} | {root} | git {git} | {len(runs)} lần chạy | trần {MAX_EPOCH} epoch | kiểm {a.kiem}"
        + (f" | danh sách {a.runs_json}" if a.runs_json else "")
        + (" | SMOKE" if a.smoke else ""))
    if git["dirty"] and not a.allow_dirty:
        log("DỪNG: có file đã theo dõi trong git bị sửa mà chưa commit. Commit trước (hoặc --allow-dirty).")
        sys.exit(2)
    if E.DEVICE.type != "cuda":
        log("DỪNG: không thấy GPU.")
        sys.exit(2)

    t_all = time.time()
    for k, (name, script, args, src) in enumerate(runs, 1):
        rd = root / name
        if (rd / "result.json").exists():
            log(f"[{k}/{len(runs)}] {name}: đã xong, bỏ qua")
            continue
        resume = src is not None and prepare_resume(src, rd, kiem, log)
        max_ep = MAX_EPOCH
        extra = []
        if a.smoke:
            if resume:
                max_ep = 310                                          # 1 lần chấm sau mốc 300
            else:
                max_ep, extra = 2, ["--eval-every", "1"]
        cmd = [sys.executable, "-W", "ignore", str(PIPE / script), *args, "--run-dir", str(rd),
               "--max-epoch", str(max_ep), *extra]
        log(f"[{k}/{len(runs)}] {name}: {'chạy tiếp' if (rd / 'last.pt').exists() else 'bắt đầu'} lúc "
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} | git {E.git_state()} | {' '.join(cmd[3:])}")
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
        r = json.loads((rd / "result.json").read_text(encoding="utf-8"))
        log(f"    NDCG@20 val {r['val']['full']['ndcg@20']:.5f} | tốt nhất epoch {r['best_epoch']} / chạy "
            f"{r['epochs_run']} | {'dừng sớm' if r['stopped_early'] else 'CHẠM TRẦN -> chưa chắc hội tụ'}")
        subprocess.run([sys.executable, "-W", "ignore", str(CURVE), str(rd)])

    log(f"\nXong cả {len(runs)} lần chạy ({(time.time() - t_all) / 60:.1f} phút ở lần gọi này).")
    log(f"{'lần chạy':<26} {'NDCG@20 val':>11} {'R@20 val':>9} {'epoch tốt':>9} {'đã chạy':>7} {'s/epoch':>7}  ghi chú")
    summary = {}
    for name, *_ in runs:
        r = json.loads((root / name / "result.json").read_text(encoding="utf-8"))
        c = json.loads((root / name / "config.json").read_text(encoding="utf-8"))
        f = r["val"]["full"]
        summary[name] = {"model": r["model"], "cfg": r["cfg"], "val_ndcg@20": f["ndcg@20"], "val_recall@20": f["recall@20"],
                         "best_epoch": r["best_epoch"], "epochs_run": r["epochs_run"],
                         "chua_chac_hoi_tu": r["chua_chac_hoi_tu"], "median_sec_per_epoch": r["median_sec_per_epoch"],
                         "resumed_from": (json.loads((root / name / "resume_source.json").read_text(encoding="utf-8"))
                                          ["source"] if (root / name / "resume_source.json").exists() else None),
                         "max_epoch_changes": c.get("max_epoch_changes"), "git_start": c["git"],
                         "git_at_finish": r["git_at_finish"]}
        log(f"{name:<26} {f['ndcg@20']:>11.5f} {f['recall@20']:>9.5f} {r['best_epoch']:>9} {r['epochs_run']:>7} "
            f"{r['median_sec_per_epoch']:>7.1f}  {'chưa chắc hội tụ' if r['chua_chac_hoi_tu'] else 'dừng sớm'}"
            f"{'; chạy tiếp từ ' + summary[name]['resumed_from'] if summary[name]['resumed_from'] else ''}")
    out = root / f"summary_{a.group}_{E.now_tag()}.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {out}. KHÔNG tự chọn cấu hình: chọn theo NDCG@20 val và ghi ai/config/v3_final.toml (kế hoạch mục 6.1).")
    log.close()


if __name__ == "__main__":
    main()
