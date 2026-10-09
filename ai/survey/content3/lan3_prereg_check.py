"""
Ghi mốc đầu vào cho lần đo thứ 3 của nội dung 3 (docs/reviews/n3_eval_lan3_plan.md). Không chạy đánh giá.
In: sha256 của kết quả quy tắc, tập chia, các file nguồn ngoài; mẫu dev 50 nằm ở nửa nào (để lập tập holdout bỏ dev).
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content3/lan3_prereg_check.py
"""
import csv, glob, hashlib, collections, sys
sys.stdout.reconfigure(encoding="utf-8")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


files = ["ai/data/kg/item_attributes.csv", "ai/data/kg/body_index.json", "ai/data/kg/lens_index.json",
         "ai/survey/content3/eval_split.csv", "ai/survey/content3/label_dev_50.csv",
         "ai/data/external/openmvg/sensor_database.csv", "ai/data/external/wikidata/mount_models.json",
         "ai/data/kg_v62abf54/linked_products.csv"]
lensfun = sorted(glob.glob("ai/data/external/lensfun/*.xml"))
for p in files:
    print(f"{sha(p)}  {p}")
h = hashlib.sha256()
for p in lensfun:
    h.update(p.replace("\\", "/").split("/")[-1].encode() + b"\0" + sha(p).encode() + b"\n")
print(f"{h.hexdigest()}  ai/data/external/lensfun/*.xml ({len(lensfun)} file; băm của danh sách 'tên\\0sha256')")

half = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open("ai/survey/content3/eval_split.csv", encoding="utf-8"))}
dev = [r["parent_asin"] for r in csv.DictReader(open("ai/survey/content3/label_dev_50.csv", encoding="utf-8-sig"))]
c = collections.Counter(half.get(a, "ngoai_1493") for a in dev)
print(f"\nmẫu dev: {len(dev)} sản phẩm ({len(set(dev))} khác nhau) -> {dict(c)}")
print(f"nửa chia: {dict(collections.Counter(half.values()))}")
print("14 mẫu dev thuộc holdout (bỏ khỏi tập H733):", " ".join(sorted(a for a in dev if half.get(a) == "holdout")))
