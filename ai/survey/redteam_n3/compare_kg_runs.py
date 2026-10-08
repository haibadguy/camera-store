"""
So sánh hai lần chạy 03_mount_compat.py (trước / sau khi sửa theo Red Team nội dung 3, lần 1).

Đọc (không ghi gì vào hai thư mục):
  --old  thư mục kết quả cũ (mặc định ai/data/kg_d339dda, bản sao lưu trước khi sửa)
  --new  thư mục kết quả mới (mặc định ai/data/kg)

In ra:
  1. Ma trận M: kích thước, số cặp M = 1, số cặp "không biết", số cặp theo mức, số cặp theo luật.
  2. Sản phẩm đổi loại / đổi ngàm / đổi khung / đổi cờ máy phim / đổi "không chắc"; sản phẩm chỉ đổi evidence.
  3. Cặp (thân, ống) đổi mức (theo compat_pairs.csv; cặp không có trong file = incompatible).
  4. Kiểm "ngoài dự kiến": mọi thay đổi ở mục 2 phải thuộc các nhóm --expect-type (đổi loại) hoặc
     "ống mới thành không chắc"; nếu không, in DỪNG.

Chạy từ thư mục gốc repo:
  ai\\.venv\\Scripts\\python.exe ai/survey/redteam_n3/compare_kg_runs.py > ai/data/survey/run_compare_kg_<nhãn>.log
"""
import argparse
import collections
import csv
import json
import os
import sys

from scipy.sparse import load_npz

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

FIELDS = ["item_type", "mount", "khung", "may_phim", "uncertain"]
LABEL = {"item_type": "đổi LOẠI", "mount": "đổi NGÀM", "khung": "đổi KHUNG", "may_phim": "đổi CỜ MÁY PHIM",
         "uncertain": "đổi 'KHÔNG CHẮC'"}


def load(d):
    attrs = {r["parent_asin"]: r for r in csv.DictReader(open(os.path.join(d, "item_attributes.csv"), encoding="utf-8"))}
    M = load_npz(os.path.join(d, "compatibility_matrix.npz"))
    U = load_npz(os.path.join(d, "unknown_mask.npz"))
    stats = json.load(open(os.path.join(d, "mount_compat_stats.json"), encoding="utf-8"))
    pairs = {}
    for r in csv.DictReader(open(os.path.join(d, "compat_pairs.csv"), encoding="utf-8")):
        pairs[(r["body_asin"], r["lens_asin"])] = (r["level"], r["rule_id"], r["lens_uncertain"], r["crop_unknown"])
    bodies = set(json.load(open(os.path.join(d, "body_index.json"), encoding="utf-8")))
    lenses = set(json.load(open(os.path.join(d, "lens_index.json"), encoding="utf-8")))
    return attrs, M, U, stats, pairs, bodies, lenses


def fmt(n):
    return f"{n:,}".replace(",", ".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default="ai/data/kg_d339dda")
    ap.add_argument("--new", default="ai/data/kg")
    ap.add_argument("--expect-type", default="B00L2PN5L8,B00GX6K1X6,B001AO4JRK",
                    help="các ASIN được dự kiến đổi loại (kéo theo đổi ngàm / khung / cờ phim)")
    args = ap.parse_args()
    expect_type = set(args.expect_type.split(","))

    a0, M0, U0, s0, p0, b0, l0 = load(args.old)
    a1, M1, U1, s1, p1, b1, l1 = load(args.new)
    print(f"cũ: {args.old}\nmới: {args.new}")
    assert set(a0) == set(a1), "hai lần chạy có tập sản phẩm khác nhau"

    # ---------------- 1. Ma trận M ----------------
    print("\n" + "=" * 70 + "\n1. MA TRẬN M (thân x ống, không gồm ống 'không chắc')\n" + "=" * 70)
    rows = [
        ("kích thước M", f"{fmt(M0.shape[0])} x {fmt(M0.shape[1])}", f"{fmt(M1.shape[0])} x {fmt(M1.shape[1])}"),
        ("tổng số cặp", fmt(s0["pairs_total"]), fmt(s1["pairs_total"])),
        ("cặp M = 1", fmt(M0.nnz), fmt(M1.nnz)),
        ("… cờ 'chưa rõ có cắt khung'", fmt(s0["M_crop_unknown"]), fmt(s1["M_crop_unknown"])),
        ("cặp 'không biết'", fmt(U0.nnz), fmt(U1.nnz)),
        ("ống 'không chắc' (QĐ 4)", fmt(s0["n_lenses_uncertain"]), fmt(s1["n_lenses_uncertain"])),
    ]
    print(f"{'chỉ số':<32} | {'cũ':>14} | {'mới':>14}")
    for name, x, y in rows:
        print(f"{name:<32} | {x:>14} | {y:>14}")
    print(f"• thân vào M: thêm {sorted(b1 - b0)}, bớt {sorted(b0 - b1)}")
    print(f"• ống vào M : thêm {sorted(l1 - l0)}, bớt {sorted(l0 - l1)}")

    print("\nsố cặp theo mức (gồm cả dòng 'ống không chắc')")
    levels = sorted(set(s0["pairs_by_level"]) | set(s1["pairs_by_level"]))
    for lv in levels:
        x, y = s0["pairs_by_level"].get(lv, 0), s1["pairs_by_level"].get(lv, 0)
        print(f"  {lv:<42} | {fmt(x):>9} | {fmt(y):>9} | {y - x:+,}".replace(",", "."))
    print("\nsố cặp theo luật (ống vào M)")
    rules = sorted(set(s0["pairs_by_rule"]) | set(s1["pairs_by_rule"]))
    for rid in rules:
        x, y = s0["pairs_by_rule"].get(rid, 0), s1["pairs_by_rule"].get(rid, 0)
        print(f"  {rid:<48} | {fmt(x):>9} | {fmt(y):>9} | {y - x:+,}".replace(",", "."))

    # ---------------- 2. Sản phẩm đổi ----------------
    print("\n" + "=" * 70 + "\n2. SẢN PHẨM ĐỔI THUỘC TÍNH\n" + "=" * 70)
    changed = {a for a in a0 if any(a0[a][f] != a1[a][f] for f in FIELDS)}
    for f in FIELDS:
        ch = sorted(a for a in changed if a0[a][f] != a1[a][f])
        print(f"\n{LABEL[f]}: {len(ch)}")
        for a in ch:
            o, n = a0[a], a1[a]
            print(f"  {a} | {o['item_type']}/{o['mount']}/{o['khung'] or '-'}/phim={o['may_phim']}/kc={o['uncertain']} -> "
                  f"{n['item_type']}/{n['mount']}/{n['khung'] or '-'}/phim={n['may_phim']}/kc={n['uncertain']} "
                  f"| n_child={n['n_child_asin']}")
            print(f"     {n['title'][:140]}")
    ev_only = sorted(a for a in a0 if a not in changed and any(a0[a][f] != a1[a][f]
                                                               for f in ("evidence", "mount_source", "uncertain_reason")))
    print(f"\nchỉ đổi evidence / mount_source / uncertain_reason (loại, ngàm, khung, cờ phim, không chắc giữ nguyên): "
          f"{len(ev_only)}")
    for a in ev_only:
        print(f"  {a} | {a1[a]['item_type']}/{a1[a]['mount']} | '{a0[a]['evidence']}' -> '{a1[a]['evidence']}' "
              f"| {a1[a]['title'][:80]}")

    # ---------------- 3. Cặp đổi mức ----------------
    print("\n" + "=" * 70 + "\n3. CẶP (THÂN, ỐNG) ĐỔI MỨC (compat_pairs.csv; không có trong file = incompatible)\n" + "=" * 70)
    keys = set(p0) | set(p1)
    INC = ("incompatible", "", "", "")
    trans = collections.Counter()
    film0 = {a for a in a0 if a0[a]["item_type"] == "than" and a0[a]["may_phim"] == "True"}
    film1 = {a for a in a1 if a1[a]["item_type"] == "than" and a1[a]["may_phim"] == "True"}
    for k in keys:
        x, y = p0.get(k, INC), p1.get(k, INC)
        if x[0] != y[0] or x[1] != y[1]:
            b, l = k
            grp = ("thân/ống đổi thuộc tính" if (b in changed or l in changed)
                   else "thân phim" if (b in film0 or b in film1) else "khác")
            unc = "ống không chắc" if (y[2] == "1" if k in p1 else x[2] == "1") else "ống vào M"
            trans[(grp, unc, f"{x[0]} [{x[1] or '-'}]", f"{y[0]} [{y[1] or '-'}]")] += 1
    for (grp, unc, x, y), n in sorted(trans.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1])):
        print(f"  [{grp} | {unc}] {x} -> {y}: {fmt(n)}")

    # ---------------- 4. Kiểm ngoài dự kiến ----------------
    print("\n" + "=" * 70 + "\n4. KIỂM THAY ĐỔI NGOÀI DỰ KIẾN\n" + "=" * 70)
    unexpected = []
    for a in sorted(changed):
        if a in expect_type:
            continue
        o, n = a0[a], a1[a]
        only_unc = all(o[f] == n[f] for f in FIELDS if f != "uncertain")
        if only_unc and n["item_type"] == "ong" and o["uncertain"] == "False" and n["uncertain"] == "True":
            continue
        unexpected.append(a)
    missing = sorted(a for a in expect_type if a0[a]["item_type"] == a1[a]["item_type"])
    other_pairs = sum(n for (grp, *_), n in trans.items() if grp == "khác")
    print(f"• sản phẩm đổi ngoài dự kiến: {len(unexpected)} {unexpected}")
    print(f"• ASIN dự kiến đổi loại nhưng không đổi: {missing}")
    print(f"• cặp đổi mức không do thân phim hay sản phẩm đổi thuộc tính: {other_pairs}")
    if unexpected or missing or other_pairs:
        print("=> DỪNG: có thay đổi ngoài dự kiến, cần xem trước khi commit")
    else:
        print("=> OK: mọi thay đổi thuộc các nhóm dự kiến")


if __name__ == "__main__":
    main()
