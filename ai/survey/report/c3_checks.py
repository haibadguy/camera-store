"""Chương 3: in các giá trị thật cho ví dụ xuyên suốt và các chỗ [CẦN KIỂM] (chỉ đọc ai/data/kg/, eval_split.csv,
đầu ra bộ đánh giá lan2 của lần đo 3).

(1) dòng item_attributes.csv + chỉ số hàng / cột của thân B00WUI65LI (Rebel 2000 phim), ống B00004THD0 (EF 75-300 III),
    Rebel T6s (iid 12902);
(2) cặp (B00WUI65LI, B00004THD0) trong compat_pairs.csv, giá trị M, U tại ô đó;
(3) cột của ống B00004THD0: mức / luật theo từng nhóm ngàm-khung của thân (đối chiếu bảng "Biến thể");
(4) ống RF-S: có trong dữ liệu không, vào M không, vì sao luật canon_rfs_on_rf_ff quyết định 0 cặp;
(5) hạn chế 17: số cụm nguồn (nguồn, cum_nguon) có sản phẩm ở cả nửa fix và holdout.

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/report/c3_checks.py --label 20261009_lan1
"""
import argparse
import collections
import csv
import json
import os
import re

from scipy.sparse import load_npz

from report_common import REPORT_LOG_DIR, Log, header

KG = "ai/data/kg"
COLS = ["iid", "parent_asin", "item_type", "mount", "khung", "may_phim", "mount_source", "evidence", "uncertain",
        "uncertain_reason", "n_child_asin", "categories", "title"]
FIX_CSV = "ai/data/survey/n3_lan3/fix_lan2_thu2.csv"
HOLD_CSV = "ai/data/survey/n3_lan3/holdout_lan2_20261008.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_c3_checks_{a.label}.log"))
    header(log, __file__)

    attrs = {r["parent_asin"]: r for r in csv.DictReader(open(f"{KG}/item_attributes.csv", encoding="utf-8"))}
    by_iid = {int(r["iid"]): r for r in attrs.values()}
    b_idx = json.load(open(f"{KG}/body_index.json", encoding="utf-8"))
    l_idx = json.load(open(f"{KG}/lens_index.json", encoding="utf-8"))
    M = load_npz(f"{KG}/compatibility_matrix.npz").tocsr()
    U = load_npz(f"{KG}/unknown_mask.npz").tocsr()
    pairs = list(csv.DictReader(open(f"{KG}/compat_pairs.csv", encoding="utf-8")))

    BODY, LENS = "B00WUI65LI", "B00004THD0"
    t6s = by_iid[12902]["parent_asin"]
    log("\n(1) item_attributes.csv")
    for asin in [BODY, LENS, t6s]:
        r = attrs[asin]
        log("  " + " | ".join(f"{c}={r[c]}" for c in COLS))
        log(f"    hàng trong body_index: {b_idx.get(asin)}; cột trong lens_index: {l_idx.get(asin)}")

    log("\n(2) cặp (thân B00WUI65LI, ống B00004THD0)")
    rows = [p for p in pairs if p["body_asin"] == BODY and p["lens_asin"] == LENS]
    for p in rows:
        log("  compat_pairs.csv: " + ", ".join(f"{k}={v}" for k, v in p.items()))
    i, j = b_idx[BODY], l_idx[LENS]
    log(f"  M[{i}, {j}] = {M[i, j]}, U[{i}, {j}] = {U[i, j]}")

    log("\n(3) cột của ống B00004THD0 theo (ngàm, khung, phim) của thân")
    col = {p["body_asin"]: p for p in pairs if p["lens_asin"] == LENS}
    grp = collections.defaultdict(collections.Counter)
    for basin, bi in b_idx.items():
        b = attrs[basin]
        p = col.get(basin)
        lv = (p["level"], p["rule_id"]) if p else ("incompatible", "(mặc định, không có dòng)")
        grp[(b["mount"], b["khung"], b["may_phim"])][lv] += 1
    for k in sorted(grp):
        log(f"  thân {k}: {dict(grp[k])}")
    r = attrs[t6s]
    p = col.get(t6s)
    log(f"  Rebel T6s {t6s}: mức {p['level'] if p else 'incompatible'}, luật {p['rule_id'] if p else '-'}; "
        f"M = {M[b_idx[t6s], j]}")

    log("\n(4) ống RF-S")
    rfs = [x for x in attrs.values() if re.search(r"\brf-?s\b", x["title"].lower())]
    log(f"  sản phẩm có 'RF-S' trong tiêu đề: {len(rfs)}")
    for x in rfs:
        log(f"    iid {x['iid']} {x['parent_asin']} {x['item_type']}/{x['mount']}/{x['khung']} "
            f"uncertain={x['uncertain']} vào M={x['parent_asin'] in l_idx} | {x['title'][:100]}")
    rf_bodies = [x for x in attrs.values() if x["parent_asin"] in b_idx and x["mount"] == "canon_rf"]
    log(f"  thân canon_rf trong M: {len(rf_bodies)}; khung: {dict(collections.Counter(x['khung'] for x in rf_bodies))}")
    rf_lens = [x for x in attrs.values() if x["parent_asin"] in l_idx and x["mount"] == "canon_rf"]
    log(f"  ống canon_rf trong M: {len(rf_lens)}; khung: {dict(collections.Counter(x['khung'] for x in rf_lens))}")

    log("\n(5) hạn chế 17: cụm nguồn ở cả hai nửa (bộ đánh giá lan2, lần đo 3)")
    half = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open("ai/survey/content3/eval_split.csv",
                                                                       encoding="utf-8-sig"))}
    cl = collections.defaultdict(lambda: collections.defaultdict(set))
    n_rows = 0
    for path in [FIX_CSV, HOLD_CSV]:
        for r in csv.DictReader(open(path, encoding="utf-8-sig")):
            if r["parent_asin"] in half and r.get("cum_nguon"):
                cl[(r["nguon"], r["cum_nguon"])][half[r["parent_asin"]]].add(r["parent_asin"])
                n_rows += 1
    both = {k: v for k, v in cl.items() if v.get("fix") and v.get("holdout")}
    log(f"  ô có cum_nguon: {n_rows:,}; cụm (nguồn, cum_nguon): {len(cl):,}; cụm có sản phẩm ở cả fix và holdout: "
        f"{len(both):,}")
    for src in sorted({k[0] for k in cl}):
        n_all = sum(1 for k in cl if k[0] == src)
        n_b = sum(1 for k in both if k[0] == src)
        hold_in = set().union(*[v["holdout"] for k, v in both.items() if k[0] == src]) if n_b else set()
        hold_all = set().union(*[v.get("holdout", set()) for k, v in cl.items() if k[0] == src])
        log(f"    {src}: {n_b}/{n_all} cụm; sản phẩm holdout thuộc các cụm đó: {len(hold_in)}/{len(hold_all)}")
    hold_any = set().union(*[v["holdout"] for v in both.values()]) if both else set()
    hold_total = {p for p, h in half.items() if h == "holdout"}
    log(f"  sản phẩm holdout có ít nhất một ô thuộc cụm hai nửa: {len(hold_any)}/{len(hold_total)}")
    big = sorted(both.items(), key=lambda kv: -(len(kv[1]['fix']) + len(kv[1]['holdout'])))[:5]
    for (src, c), v in big:
        t = attrs[next(iter(v["holdout"]))]["title"][:70]
        log(f"    vd {src} cụm {c}: fix {len(v['fix'])}, holdout {len(v['holdout'])} | {t}")
    log.save()


if __name__ == "__main__":
    main()
