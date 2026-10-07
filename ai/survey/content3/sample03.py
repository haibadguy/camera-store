"""Lấy 30 mẫu (15 Body + 15 Lens, seed 42) từ ứng viên của quy tắc script 03, trên 27.940 item mới."""
import json, random, sys
sys.stdout.reconfigure(encoding="utf-8")
META = "ai/data/processed/camera_items_meta.jsonl"
cand = {"Body": [], "Lens": []}
for line in open(META, encoding="utf-8"):
    item = json.loads(line)
    c = " ".join(item.get("categories", [])).lower()
    is_b = any(k in c for k in ["dslr cameras", "mirrorless cameras", "digital cameras", "point & shoot"])
    is_l = any(k in c for k in ["camera lenses", "slr camera lenses", "lenses"])
    if is_b or is_l:
        cand["Body" if is_b else "Lens"].append(item)
rng = random.Random(42)
for h in ["Body", "Lens"]:
    print(f"\n===== {h} ({len(cand[h])}) =====")
    for i, it in enumerate(rng.sample(cand[h], 15), 1):
        print(f"{h[0]}{i:02d} {it['parent_asin']} | {' > '.join(it['categories'][2:])} | {it['title'][:150]}")
