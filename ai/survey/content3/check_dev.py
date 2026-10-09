"""So quy tắc mới (ai/pipeline/mount_detect.py) với nhãn dev 50 do Claude tự chấm (label_dev_50_claude.csv).
CHỈ dùng để tìm lỗi và sửa quy tắc (tập dev). Không dùng làm số đánh giá chính thức.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content3/check_dev.py"""
import csv, json, sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "ai/pipeline")
from mount_detect import classify_item

meta = {}
for line in open("ai/data/survey/meta_full_k5.jsonl", encoding="utf-8"):
    d = json.loads(line); meta[d["parent_asin"]] = d
child = json.load(open("ai/data/survey/child_asins.json", encoding="utf-8"))
gold = list(csv.DictReader(open("ai/survey/content3/label_dev_50_claude.csv", encoding="utf-8")))
ok = {"loai": 0, "ngam": 0, "khung": 0}
for g in gold:
    m = meta[g["parent_asin"]]
    r = classify_item(m.get("title") or "", m.get("categories") or [], len(child.get(g["parent_asin"], {})))
    pred = {"loai": r["item_type"], "ngam": r["mount"], "khung": r["khung"]}
    flags = []
    for k in ok:
        if pred[k] == g[k]:
            ok[k] += 1
        else:
            flags.append(f"{k}: quy tắc={pred[k]!r} / nhãn={g[k]!r}")
    if flags:
        print(f"#{g['stt']:>2} {g['parent_asin']} {(m.get('title') or '')[:80]}")
        print(f"     {' ; '.join(flags)} | nguồn={r['mount_source']} bằng chứng={r['evidence']!r} uncertain={r['uncertain']}")
print({k: f"{v}/{len(gold)}" for k, v in ok.items()})
