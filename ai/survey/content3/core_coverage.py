"""
Tính lại "vấn đề cốt lõi" của STATUS mục 4 (bản cũ: "chỉ 257/28.867 sản phẩm (0,9%) được xác định ngàm") trên dữ liệu
mới (27.940 sản phẩm sau gộp lặp) và đầu ra nội dung 3 mới (ai/data/kg/). Cũng tính lại số cũ từ file của Hải để so.

Đếm:
  - sản phẩm theo loại của quy tắc; thân / ống có đúng 1 ngàm; phần tử của M (body_index + lens_index);
  - tương tác (k-core, và tập train) chạm tới sản phẩm của M / sản phẩm có ngàm.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content3/core_coverage.py
"""
import csv, json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")


def single(m):
    return bool(m) and m not in ("khong_ro", "khong_co", "nhieu") and ">" not in m


def inter_share(path, items):
    n = hit = 0
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            n += 1
            hit += r["parent_asin"] in items
    return hit, n


def train_share(path, item_map, items):
    inv = {v: k for k, v in item_map.items()}
    n = hit = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            ids = line.split()[1:]
            n += len(ids)
            hit += sum(inv[int(i)] in items for i in ids)
    return hit, n


def pct(a, b):
    return f"{a:,}/{b:,} = {a / b * 100:.2f}%"


# ---------------------------------------------------------------- bản cũ (Hải, 62abf54)
old_items = json.load(open("ai/data/processed_v62abf54/item_map.json", encoding="utf-8"))
linked = {r["parent_asin"] for r in csv.DictReader(open("ai/data/kg_v62abf54/linked_products.csv", encoding="utf-8"))}
print("=== bản cũ (Hải, dữ liệu 62abf54) ===")
print(f"sản phẩm được xác định ngàm (linked_products.csv): {pct(len(linked), len(old_items))}")
h, n = inter_share("ai/data/processed_v62abf54/camera_interactions_k5.csv", linked)
print(f"tương tác k-core chạm sản phẩm có ngàm: {pct(h, n)}")
h, n = train_share("ai/data/processed_v62abf54/train.txt", old_items, linked)
print(f"tương tác train chạm sản phẩm có ngàm: {pct(h, n)}")

# ---------------------------------------------------------------- bản mới
attr = list(csv.DictReader(open("ai/data/kg/item_attributes.csv", encoding="utf-8")))
items = json.load(open("ai/data/processed/item_map.json", encoding="utf-8"))
assert len(attr) == len(items) and {r["parent_asin"] for r in attr} == set(items)
body = set(json.load(open("ai/data/kg/body_index.json", encoding="utf-8")))
lens = set(json.load(open("ai/data/kg/lens_index.json", encoding="utf-8")))
M = body | lens
N = len(attr)
print(f"\n=== bản mới (dữ liệu sau gộp lặp, ai/data/kg/) — {N:,} sản phẩm ===")
for t, c in collections.Counter(r["item_type"] for r in attr).most_common():
    print(f"  loại {t:9}: {pct(c, N)}")
bl = [r for r in attr if r["item_type"] in ("than", "ong")]
mounted = {r["parent_asin"] for r in bl if single(r["mount"])}
print(f"thân + ống: {pct(len(bl), N)}")
print(f"thân + ống có đúng 1 ngàm: {pct(len(mounted), N)} "
      f"(thân {sum(r['item_type'] == 'than' and single(r['mount']) for r in bl)}, "
      f"ống {sum(r['item_type'] == 'ong' and single(r['mount']) for r in bl)})")
print(f"phần tử của M (thân {len(body)} + ống {len(lens)}): {pct(len(M), N)}")
acc = {r["parent_asin"] for r in attr if r["item_type"] not in ("than", "ong") and r["mount"] not in ("khong_co", "")}
print(f"phụ kiện / khác có ghi ngàm (kể cả ngàm chuyển a>b): {pct(len(acc), N)}")
for lab, s in (("phần tử M", M), ("thân + ống có ngàm", mounted)):
    h, n = inter_share("ai/data/processed/camera_interactions_k5.csv", s)
    print(f"tương tác k-core chạm {lab}: {pct(h, n)}")
    h, n = train_share("ai/data/processed/train.txt", items, s)
    print(f"tương tác train chạm {lab}: {pct(h, n)}")
