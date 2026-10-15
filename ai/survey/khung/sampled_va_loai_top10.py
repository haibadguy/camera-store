"""Số phụ cho mục 2.6 và 1.2.2 của khung: (1) thứ tự mô hình theo full ranking và theo sampled 1+99 ở K = 5/10/20;
(2) loại sản phẩm trung bình trong top-10 (thân / ống / phụ kiện / khác). Đọc result.json của lần chấm test 09/10.

CHỈ ĐỌC. Ví dụ trước: nếu Hit@20 full của LightGCN > R-GCN nhưng Hit@20 sampled của R-GCN > LightGCN thì
cách đo sampled đảo thứ tự hai mô hình ở K = 20 (điều khung muốn chứng minh ở mục "Full-ranking so với Sampled").

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/khung/sampled_va_loai_top10.py --label 20261014_lan1
"""
import argparse
import json
import os
import sys

sys.path.insert(0, "ai/survey/report")
from report_common import Log, header, sha256_file  # noqa: E402

TEST = "results/n5/test_final_20261009"
RUNS = {"Popularity": ["pop"], "MountAware": ["popma"], "LightGCN": ["lightgcn_s1", "lightgcn_s2", "lightgcn_s3"],
        "R-GCN": ["rgcn_s1", "rgcn_s2", "rgcn_s3"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join("ai/data/survey/khung", f"run_sampled_va_loai_top10_{a.label}.log"))
    header(log, __file__)
    res = {}
    for m, ds in RUNS.items():
        res[m] = []
        for d in ds:
            p = f"{TEST}/{d}/result.json"
            log(f"  sha256 {sha256_file(p)}  {p}")
            res[m].append(json.load(open(p, encoding="utf-8")))
    mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
    log("\n## (1) Hit@K full ranking và sampled 1+99 (trung bình qua seed)")
    tab = {}
    for m, rs in res.items():
        tab[m] = {k: (mean([r["full"][f"hit@{k}"] for r in rs]), mean([r["sampled_1_99"][f"hit@{k}"] for r in rs]))
                  for k in (5, 10, 20)}
        log(f"  {m:11s} " + " | ".join(f"@{k}: full {f:.4f} sampled {s:.4f}" for k, (f, s) in tab[m].items()))
    for k in (5, 10, 20):
        of = sorted(tab, key=lambda m: -tab[m][k][0])
        os_ = sorted(tab, key=lambda m: -tab[m][k][1])
        log(f"  thứ tự @{k}: full {of} | sampled {os_} | {'GIỐNG' if of == os_ else 'KHÁC'}")
    log("\n## (2) Loại sản phẩm trung bình trong top-10 (full ranking, mọi người dùng)")
    for m, rs in res.items():
        keys = rs[0]["top10_type_mix"].keys()
        log(f"  {m:11s} " + ", ".join(f"{k} {mean([r['top10_type_mix'][k] for r in rs]):.2f}" for k in keys))
    log.save()


if __name__ == "__main__":
    main()
