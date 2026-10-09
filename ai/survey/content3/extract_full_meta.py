"""Trích metadata ĐẦY ĐỦ (mọi trường) của 27.940 sản phẩm sau k-core từ file gốc.
Đọc streaming, chỉ giữ dòng có parent_asin trong item_map. Không sửa ai/data/raw."""
import gzip, json, sys, time
ROOT = "ai/data"
OUT = sys.argv[1]
items = set(json.load(open(f"{ROOT}/processed/item_map.json", encoding="utf-8")))
t = time.time(); n = 0; kept = 0
with gzip.open(f"{ROOT}/raw/meta_Electronics.jsonl.gz", "rt", encoding="utf-8") as f, \
        open(OUT, "w", encoding="utf-8") as out:
    for line in f:
        n += 1
        # lọc nhanh bằng chuỗi trước khi parse
        i = line.find('"parent_asin": "')
        if i < 0:
            continue
        pa = line[i + 16:i + 26]
        if pa in items:
            d = json.loads(line)
            if d["parent_asin"] in items:
                d.pop("images", None); d.pop("videos", None)
                out.write(json.dumps(d, ensure_ascii=False) + "\n"); kept += 1
print(f"read {n:,} lines, kept {kept:,}, need {len(items):,}, {time.time()-t:.0f}s")
