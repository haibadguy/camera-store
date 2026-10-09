"""So sha256 từng file giữa bản đang dùng và bản chạy lại vào thư mục nháp (chỉ đọc).

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/report/compare_sha256.py --label 20261009_lan1
Log: ai/data/survey/report/run_compare_sha256_<label>.log (đã có thì DỪNG).
"""
import argparse
import os

from report_common import REPORT_LOG_DIR, Log, header, sha256_file

PROC_FILES = ["camera_interactions_k5.csv", "camera_items_meta.jsonl", "filtering_stats.json", "user_map.json",
              "item_map.json", "train.txt", "val.txt", "test.txt", "val_negatives.json", "test_negatives.json"]
KG03_FILES = ["item_attributes.csv", "compat_pairs.csv", "compatibility_matrix.npz", "unknown_mask.npz",
              "body_index.json", "lens_index.json", "mount_compat_stats.json", "mount_compat_log.txt"]
INTERIM_FILES = ["meta_k5_min.jsonl", "child_asins_k5.json"]
KG04_FILES = ["kg_hetero.pt", "kg_node_index.json", "kg_stats.json"] + [
    f"kg_edges_{r}.csv" for r in ["interacted_with", "compatible_with", "crops_sensor", "requires_adapter",
                                  "has_spec_mount", "has_spec_sensor_format", "has_spec_focal_range",
                                  "has_spec_aperture_class", "suitable_for"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--proc-old", default="ai/data/processed")
    ap.add_argument("--proc-new", default="ai/data/processed_rerun_20261009/ai/data/processed")
    ap.add_argument("--kg-old", default="ai/data/kg")
    ap.add_argument("--kg-new", default="ai/data/kg_rerun_20261009")
    ap.add_argument("--interim-old", default="ai/data/interim")
    ap.add_argument("--kg04-log-old", default="ai/data/kg/kg_validation_log_20261008_khongchac_lan1.txt")
    ap.add_argument("--kg04-log-new", default="ai/data/kg_rerun_20261009/kg04/kg_validation_log_20261009_rerun_lan1.txt")
    a = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_compare_sha256_{a.label}.log"))
    header(log, __file__)

    groups = [
        ("01–02 (processed)", [(os.path.join(a.proc_old, f), os.path.join(a.proc_new, f)) for f in PROC_FILES]),
        ("03 (kg)", [(os.path.join(a.kg_old, f), os.path.join(a.kg_new, f)) for f in KG03_FILES]),
        ("03 (cache interim)", [(os.path.join(a.interim_old, f), os.path.join(a.kg_new, "interim", f))
                                for f in INTERIM_FILES]),
        ("04 (kg)", [(os.path.join(a.kg_old, f), os.path.join(a.kg_new, "kg04", f)) for f in KG04_FILES]
         + [(a.kg04_log_old, a.kg04_log_new)]),
    ]
    for name, pairs in groups:
        log(f"\n=== {name} ===")
        same = 0
        for old, new in pairs:
            if not (os.path.exists(old) and os.path.exists(new)):
                log(f"  THIẾU FILE: {old} có={os.path.exists(old)} | {new} có={os.path.exists(new)}")
                continue
            h1, h2 = sha256_file(old), sha256_file(new)
            ok = h1 == h2
            same += ok
            log(f"  {'TRÙNG' if ok else 'KHÁC '}  {os.path.basename(old):42s} {h1}" + ("" if ok else f" | mới {h2}"))
            if not ok and old.endswith((".txt", ".json", ".csv")) and os.path.getsize(old) < 5_000_000:
                lo = open(old, encoding="utf-8").read().splitlines()
                ln = open(new, encoding="utf-8").read().splitlines()
                diff = [(i, x, y) for i, (x, y) in enumerate(zip(lo, ln)) if x != y]
                log(f"         số dòng {len(lo)} / {len(ln)}; dòng khác: {len(diff)} (in tối đa 5)")
                for i, x, y in diff[:5]:
                    log(f"         dòng {i + 1}: cũ  {x[:150]}")
                    log(f"                  mới {y[:150]}")
        log(f"  -> {same}/{len(pairs)} file trùng sha256")
    log.save()


if __name__ == "__main__":
    main()
