"""Khảo sát cho nội dung 4: thông số nào có trong metadata Amazon (details) của thân / ống,
và tiêu đề đọc được tiêu cự / khẩu độ ở bao nhiêu ống. Chỉ đếm, không sửa dữ liệu.
Đầu vào: ai/data/kg/item_attributes.csv, ai/data/survey/meta_full_k5.jsonl (extract_full_meta.py)
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/survey_specs.py
"""
import collections, csv, json, re, sys
sys.stdout.reconfigure(encoding="utf-8")

attrs = {r["parent_asin"]: r for r in csv.DictReader(open("ai/data/kg/item_attributes.csv", encoding="utf-8"))}
meta = {}
for line in open("ai/data/survey/meta_full_k5.jsonl", encoding="utf-8"):
    d = json.loads(line)
    meta[d["parent_asin"]] = d

for typ in ["than", "ong"]:
    asins = [a for a, r in attrs.items() if r["item_type"] == typ]
    keys = collections.Counter()
    for a in asins:
        keys.update((meta[a].get("details") or {}).keys())
    print(f"\n=== {typ}: {len(asins)} sản phẩm; khóa details phổ biến (>= 3%) ===")
    for k, c in keys.most_common():
        if c / len(asins) >= 0.03:
            print(f"  {c:5d} ({c / len(asins) * 100:5.1f}%)  {k}")
    iso_keys = [k for k in keys if "iso" in k.lower()]
    print(f"  khóa có 'iso': {[(k, keys[k]) for k in iso_keys]}")
    # ISO trong tiêu đề / features
    n_iso_feat = sum(1 for a in asins if re.search(r"\biso\b", " ".join(meta[a].get("features") or []).lower()))
    print(f"  features có nhắc 'ISO': {n_iso_feat}")

FOCAL = re.compile(r"(\d{1,4}(?:\.\d)?)\s?(?:-\s?(\d{1,4}(?:\.\d)?))?\s?mm")
APER = re.compile(r"(?:f\s?/?\s?|1\s?:\s?)(\d{1,2}(?:\.\d{1,2})?)(?:\s?-\s?(\d{1,2}(?:\.\d{1,2})?))?", re.I)
lens = [a for a, r in attrs.items() if r["item_type"] == "ong"]
nf = na = 0
for a in lens:
    t = attrs[a]["title"].lower()
    fm = FOCAL.search(t)
    nf += bool(fm)
    if fm and (APER.search(t[fm.end():]) or APER.search(t)):
        na += 1
print(f"\nỐng: {len(lens)}; tiêu đề có tiêu cự {nf} ({nf / len(lens) * 100:.1f}%), có cả tiêu cự + khẩu độ {na} "
      f"({na / len(lens) * 100:.1f}%)")
# ví dụ giá trị details của ống
for k in ["Maximum Focal Length", "Minimum Focal Length", "Maximum Aperture", "Focal Length Description", "Lens Type"]:
    vals = collections.Counter((meta[a].get("details") or {}).get(k) for a in lens if (meta[a].get("details") or {}).get(k))
    print(f"  {k}: {sum(vals.values())} ống; ví dụ {vals.most_common(6)}")
body = [a for a, r in attrs.items() if r["item_type"] == "than"]
for k in ["Photo Sensor Size", "Maximum ISO", "Minimum ISO", "ISO Range", "Effective Still Resolution", "Video Capture Resolution"]:
    vals = collections.Counter((meta[a].get("details") or {}).get(k) for a in body if (meta[a].get("details") or {}).get(k))
    print(f"  thân {k}: {sum(vals.values())}; ví dụ {vals.most_common(6)}")
