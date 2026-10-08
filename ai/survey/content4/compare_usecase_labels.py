"""So hai bảng nhãn mục đích (đầu ra count_usecase.py): số ống mỗi nhãn và từng ống đổi nhãn / đổi kết quả đọc.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/compare_usecase_labels.py <cũ>.csv <mới>.csv
"""
import collections, csv, sys

sys.stdout.reconfigure(encoding="utf-8")
old, new = ({r["parent_asin"]: r for r in csv.DictReader(open(p, encoding="utf-8"))} for p in sys.argv[1:3])
print(f"cũ {sys.argv[1]}: {len(old)} ống | mới {sys.argv[2]}: {len(new)} ống")
for name, d in (("cũ", old), ("mới", new)):
    c = collections.Counter(l for r in d.values() for l in r["labels"].split(";") if l)
    print(f"  {name}: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) +
          f", không nhãn {sum(1 for r in d.values() if not r['labels'])}")
spec = lambda r: (r["f1"], r["f2"], r["ap1"], r["ap2"])
for a in sorted(set(old) | set(new)):
    o, n = old.get(a), new.get(a)
    if o and n and o["labels"] == n["labels"] and spec(o) == spec(n):
        continue
    so = f"{spec(o)} [{o['labels']}]" if o else "(không đọc được)"
    sn = f"{spec(n)} [{n['labels']}]" if n else "(không đọc được)"
    print(f"  {a}: {so} -> {sn} | {(n or o)['title'][:100]}")
