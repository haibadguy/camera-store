"""Tạo file chấm tay mẫu DEV (50 sản phẩm) cho nội dung 3. Chấm mù: file chấm KHÔNG chứa kết quả quy tắc.

Đầu vào : ai/data/survey/survey2_items.jsonl (survey2.py), ai/data/survey/child_asins.json (child_asins.py)
Đầu ra  : ai/survey/content3/label_dev_50.csv   (file để Nam chấm, thứ tự đã xáo trộn)
          ai/data/survey/label_dev_50_rule.csv   (kết quả quy tắc + tầng lấy mẫu, để so sau; KHÔNG mở trước khi chấm xong)
Chạy    : ai\\.venv\\Scripts\\python.exe ai/survey/content3/make_label_dev.py

Phân tầng theo loại (thân / ống / phụ kiện-khác) và theo nguồn xác định ngàm của quy tắc khảo sát.
Seed cố định để tái lập. Mẫu TEST 200 sau này phải loại các ASIN đã nằm trong mẫu dev."""
import csv, json, random, re, sys
sys.stdout.reconfigure(encoding="utf-8")

ITEMS = "ai/data/survey/survey2_items.jsonl"
CHILD = "ai/data/survey/child_asins.json"
OUT_LABEL = "ai/survey/content3/label_dev_50.csv"
OUT_RULE = "ai/data/survey/label_dev_50_rule.csv"
SEED = 20261007

rows = [json.loads(l) for l in open(ITEMS, encoding="utf-8")]
child = json.load(open(CHILD, encoding="utf-8"))
THIRD = re.compile(r"\b(sigma|tamron|tokina|rokinon|samyang|bower|opteka|yongnuo|meike|7artisans|ttartisan|viltrox|neewer|"
                   r"zeiss|voigtlander|lensbaby|vivitar|venus|laowa|irix|kenko|altura|jintu|lightdow)\b", re.I)


def n_child(r):
    return len(child.get(r["asin"], {}))


def is_multi_variant(r):
    return r["type"] == "lens" and len(r["rec"]) == 1 and THIRD.search(r["title"]) and n_child(r) > 1


BODY = ("body", "body_cat_but_accessory")
LENS_EDGE = ("lens_cat_but_accessory", "lens_cat_no_focal")
# (tên tầng, điều kiện, số mẫu). Các tầng xét theo thứ tự; 1 item chỉ thuộc tầng đầu tiên nó khớp.
STRATA = [
    # Thân máy: 14
    ("than_series_only", lambda r: r["type"] in BODY and r["SER"] and not r["T"] and len(r["rec"]) == 1, 6),
    ("than_title",       lambda r: r["type"] in BODY and r["T"] and len(r["rec"]) == 1, 4),
    ("than_no_mount",    lambda r: r["type"] in BODY and not r["rec"], 4),
    # Ống kính: 22
    ("ong_multi_variant", is_multi_variant, 3),
    ("ong_title",         lambda r: r["type"] == "lens" and r["T"] and len(r["rec"]) == 1, 6),
    ("ong_slr_only",      lambda r: r["type"] == "lens" and r["SLR"] and not r["T"] and len(r["rec"]) == 1, 5),
    ("ong_no_mount",      lambda r: r["type"] == "lens" and not r["rec"], 4),
    ("ong_edge",          lambda r: r["type"] in LENS_EDGE, 4),
    # Phụ kiện / khác: 14
    ("pk_title_mount",    lambda r: r["type"] == "accessory_or_other" and len(r["cats"]) > 0 and len(r["T"]) >= 1, 5),
    ("khac_compact_cm",   lambda r: r["type"] == "camera_fixed_or_video" and r["CM"], 3),
    ("pk_no_mount",       lambda r: r["type"] == "accessory_or_other" and len(r["cats"]) > 0 and not r["T"], 3),
    ("khac_no_category",  lambda r: r["type"] == "accessory_or_other" and r["cats"] == "", 3),
]

rng = random.Random(SEED)
assigned = {}
for r in rows:
    for name, cond, _ in STRATA:
        if cond(r):
            assigned[r["asin"]] = name
            break
picked = []
for name, _, k in STRATA:
    pool = sorted((r for r in rows if assigned.get(r["asin"]) == name), key=lambda r: r["asin"])
    sample = rng.sample(pool, k)
    print(f"{name:20s} quần thể {len(pool):6d}  lấy {k}")
    picked += [(name, r) for r in sample]
rng.shuffle(picked)   # xáo trộn để thứ tự không lộ tầng

meta = {}
for line in open("ai/data/survey/meta_full_k5.jsonl", encoding="utf-8"):
    d = json.loads(line)
    meta[d["parent_asin"]] = d

with open(OUT_LABEL, "w", encoding="utf-8-sig", newline="") as f:   # utf-8-sig để Excel đọc đúng ký tự
    w = csv.writer(f)
    w.writerow(["stt", "parent_asin", "link", "title", "categories", "loai", "ngam", "khung", "ghi_chu"])
    for i, (_, r) in enumerate(picked, 1):
        cats = " > ".join(meta[r["asin"]].get("categories") or [])
        w.writerow([i, r["asin"], f"https://www.amazon.com/dp/{r['asin']}", r["title"], cats, "", "", "", ""])

with open(OUT_RULE, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["stt", "parent_asin", "tang", "type_rule", "mount_rule", "T", "SER", "SLR", "CM_raw", "n_child_asin"])
    for i, (name, r) in enumerate(picked, 1):
        w.writerow([i, r["asin"], name, r["type"], "|".join(r["rec"]), "|".join(r["T"]), "|".join(r["SER"]),
                    "|".join(r["SLR"]), r["cm_raw"] or "", n_child(r)])
print(f"đã ghi {len(picked)} dòng -> {OUT_LABEL} và {OUT_RULE}")
