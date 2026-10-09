"""Chương 2: đếm lại từ file gốc (chỉ đọc, đọc từng dòng, không nạp cả file).

(1) Số dòng và số người dùng khác nhau của Electronics.jsonl.gz (Bảng 2.1, dòng "Electronics thô").
    Người dùng được đếm qua mã băm blake2b 8 byte của user_id (để tiết kiệm RAM); xác suất trùng băm với
    ~1,8e7 người là cỡ n^2 / 2^65 ≈ 1e-5, log ghi rõ.
(2) Phạm vi của câu CHANGELOG 07/10 "9.461 nhóm bị lặp, 9.460 nhóm trùng y hệt cả asin lẫn nội dung":
    thử giả thuyết nhóm = (user, parent_asin, timestamp) có >= 2 dòng trong camera_interactions_k5.csv của
    bản cũ (ai/data/processed_v62abf54/), rồi đọc lại các dòng đó trong file gốc, so asin / title / text.

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/report/c2_raw_scan.py --label 20261009_lan1
"""
import argparse
import array
import collections
import gzip
import hashlib
import json
import os
import time

import numpy as np
import pandas as pd

from report_common import REPORT_LOG_DIR, Log, header

RAW_REVIEWS = "ai/data/raw/Electronics.jsonl.gz"
OLD_K5 = "ai/data/processed_v62abf54/camera_interactions_k5.csv"


def field(line, key):
    """Lấy giá trị chuỗi "key": "..." trong một dòng JSON mà không parse cả dòng."""
    k = f'"{key}": "'
    i = line.find(k)
    if i < 0:
        return None
    j = line.find('"', i + len(k))
    return line[i + len(k):j]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_c2_raw_scan_{a.label}.log"))
    header(log, __file__)

    # ── (2a) nhóm lặp trong k-core bản cũ ──
    old = pd.read_csv(OLD_K5, dtype={"user_id": str, "parent_asin": str})
    log(f"\n(2a) {OLD_K5}: {len(old):,} dòng, cột {list(old.columns)}")
    g_ui = old.groupby(["user_id", "parent_asin"]).size()
    log(f"  nhóm (user, item) có >= 2 dòng: {(g_ui >= 2).sum():,}; số dòng thừa: {(g_ui[g_ui >= 2] - 1).sum():,}")
    g = old.groupby(["user_id", "parent_asin", "timestamp"]).size()
    dup = g[g >= 2]
    log(f"  nhóm (user, item, timestamp) có >= 2 dòng: {len(dup):,}; số dòng thừa: {(dup - 1).sum():,}; "
        f"phân bố cỡ nhóm: {dict(sorted(collections.Counter(dup.values).items()))}")
    g4 = old.groupby(["user_id", "parent_asin", "timestamp", "rating"]).size()
    log(f"  nhóm (user, item, timestamp, rating) có >= 2 dòng: {(g4 >= 2).sum():,}; dòng thừa: {(g4[g4 >= 2] - 1).sum():,}")
    keys = {(u, p, int(t)) for (u, p, t) in dup.index}
    users_dup = {k[0] for k in keys}

    # ── (1) + (2b) một lượt đọc file gốc ──
    t0 = time.time()
    hashes = array.array("Q")
    n_lines = n_no_user = 0
    rows = collections.defaultdict(list)
    with gzip.open(RAW_REVIEWS, "rt", encoding="utf-8") as f:
        for line in f:
            n_lines += 1
            u = field(line, "user_id")
            if u is None:
                n_no_user += 1
                continue
            hashes.append(int.from_bytes(hashlib.blake2b(u.encode(), digest_size=8).digest(), "little"))
            if u in users_dup:
                d = json.loads(line)
                k = (d["user_id"], d["parent_asin"], int(d["timestamp"]))
                if k in keys:
                    rows[k].append((d.get("asin"), d.get("title"), d.get("text"), d.get("rating")))
            if n_lines % 5_000_000 == 0:
                print(f"  ... {n_lines:,} dòng, {time.time() - t0:.0f}s", flush=True)
    uniq = np.unique(np.frombuffer(hashes, dtype=np.uint64)).size
    log(f"\n(1) {RAW_REVIEWS}: {n_lines:,} dòng; dòng không có user_id: {n_no_user:,}")
    log(f"  người dùng khác nhau (đếm qua băm blake2b 8 byte): {uniq:,}")
    log(f"  (xác suất có ít nhất một cặp trùng băm ≈ n^2/2^65 = {uniq ** 2 / 2 ** 65:.1e}; nếu trùng thì số thật lớn hơn)")
    log(f"  thời gian đọc: {time.time() - t0:.0f}s")

    found = {k: v for k, v in rows.items() if len(v) >= 2}
    same_asin_text = sum(1 for v in found.values() if len({(r[0], r[2]) for r in v}) == 1)
    same_all = sum(1 for v in found.values() if len(set(v)) == 1)
    log(f"\n(2b) đọc lại {len(keys):,} nhóm (user, item, timestamp) trong file gốc:")
    log(f"  nhóm tìm thấy >= 2 dòng trong file gốc: {len(found):,}; không thấy đủ: {len(keys) - len(found):,}")
    log(f"  nhóm mà mọi dòng trùng cả asin lẫn text: {same_asin_text:,}")
    log(f"  nhóm mà mọi dòng trùng cả asin, title, text, rating: {same_all:,}")
    for k, v in found.items():
        if len({(r[0], r[2]) for r in v}) != 1:
            log(f"  nhóm KHÁC: user …{k[0][-6:]}, item {k[1]}, ts {k[2]}: "
                + "; ".join(f"asin {r[0]}, text '{(r[2] or '')[:40]}'" for r in v))
    log.save()


if __name__ == "__main__":
    main()
