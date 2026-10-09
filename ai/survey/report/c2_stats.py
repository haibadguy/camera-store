"""Chương 2: số liệu mô tả và kiểm rò rỉ trên dữ liệu sau gộp lặp (chỉ đọc ai/data/processed/).

In: phân vị tương tác / người và / sản phẩm, phân bố số sao, 4 phép kiểm rò rỉ (Bảng 2.6 / mục 2.5.3),
số sản phẩm có trong val / test mà không có trong train, sha256 các file đầu ra.
Phân vị tính bằng numpy.percentile mặc định (nội suy tuyến tính).

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/report/c2_stats.py --label 20261009_lan1
"""
import argparse
import collections
import os

import numpy as np
import pandas as pd

from report_common import REPORT_LOG_DIR, Log, header, sha256_file

P = "ai/data/processed"


def read_pairs(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        u, i = line.split()
        out[int(u)] = int(i)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_c2_stats_{a.label}.log"))
    header(log, __file__)

    df = pd.read_csv(f"{P}/camera_interactions_k5.csv", dtype={"user_id": str, "parent_asin": str})
    log(f"\ncamera_interactions_k5.csv: {len(df):,} dòng; {df.user_id.nunique():,} người; {df.parent_asin.nunique():,} sản phẩm")
    q = [25, 50, 75, 90, 95, 99]
    pu = df.groupby("user_id").size().to_numpy()
    pi = df.groupby("parent_asin").size().to_numpy()
    for name, x in [("người dùng", pu), ("sản phẩm", pi)]:
        log(f"Tương tác / {name}: min {x.min()}, TB {x.mean():.2f}, "
            + ", ".join(f"P{k} {np.percentile(x, k):g}" for k in q) + f", max {x.max()}")
    vc = df.rating.value_counts().sort_index()
    log("Phân bố số sao (trên toàn bộ dòng sau k-core):")
    for r, c in vc.items():
        log(f"  {r:g} sao: {c:,} ({c / len(df) * 100:.2f}%)")
    log(f"  TB số sao: {df.rating.mean():.3f}")

    # ── train / val / test ──
    train = {}
    for line in open(f"{P}/train.txt", encoding="utf-8"):
        p = list(map(int, line.split()))
        train[p[0]] = p[1:]
    val, test = read_pairs(f"{P}/val.txt"), read_pairs(f"{P}/test.txt")
    n_train_lines = sum(len(v) for v in train.values())
    n_train_set = sum(len(set(v)) for v in train.values())
    log(f"\ntrain: {len(train):,} người, {n_train_lines:,} tương tác (đếm theo tập từng người: {n_train_set:,}); "
        f"val {len(val):,}; test {len(test):,}")
    log("Kiểm rò rỉ:")
    log(f"  val = test: {sum(val[u] == test[u] for u in val):,}")
    log(f"  test ∈ train: {sum(test[u] in set(train[u]) for u in test):,}")
    log(f"  val ∈ train: {sum(val[u] in set(train[u]) for u in val):,}")
    log(f"  dòng lặp (user, item) trong CSV: {len(df) - len(df.drop_duplicates(['user_id', 'parent_asin'])):,}")
    ntr = collections.Counter(len(v) for v in train.values())
    log(f"  người có đúng 3 sản phẩm train: {ntr[3]:,}")

    item_train = collections.Counter(i for v in train.values() for i in v)
    vt_items = set(val.values()) | set(test.values())
    no_train = {i for i in vt_items if item_train[i] == 0}
    lt5 = {i for i in vt_items if item_train[i] < 5}
    log(f"\nSản phẩm có trong val hoặc test: {len(vt_items):,}")
    log(f"  … không có tương tác train nào: {len(no_train):,} "
        f"(chỉ ở val: {len(no_train & set(val.values()) - set(test.values())):,}, "
        f"chỉ ở test: {len(no_train & set(test.values()) - set(val.values())):,})")
    log(f"  … có < 5 tương tác train: {len(lt5):,}")
    log(f"  người có item test không có tương tác train: {sum(item_train[i] == 0 for i in test.values()):,}; "
        f"item val: {sum(item_train[i] == 0 for i in val.values()):,}")
    log(f"  sản phẩm trong item_map mà không có tương tác train: "
        f"{sum(1 for i in range(df.parent_asin.nunique()) if item_train[i] == 0):,}")

    log("\nsha256 đầu ra (ai/data/processed):")
    for f in ["camera_interactions_k5.csv", "camera_items_meta.jsonl", "filtering_stats.json", "user_map.json",
              "item_map.json", "train.txt", "val.txt", "test.txt", "val_negatives.json", "test_negatives.json"]:
        log(f"  {f:28s} {sha256_file(os.path.join(P, f))}")
    log.save()


if __name__ == "__main__":
    main()
