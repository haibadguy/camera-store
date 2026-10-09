"""So bộ đọc cũ (eval_external.lens_sig) với bộ đọc mới (ai/pipeline/lens_specs.py) trên mọi ống của item_attributes.csv.
In chi tiết các ống KHÔNG thuộc holdout (fa_split.csv); với ống holdout chỉ in số đếm (kế hoạch
docs/reviews/n4_focal_aperture_plan.md: không xem holdout trước khi chạy đo).
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/fa_reader_diff.py
"""
import collections, csv, sys

sys.path.insert(0, "ai/survey/content3")
sys.path.insert(0, "ai/pipeline")
sys.stdout.reconfigure(encoding="utf-8")
import eval_external as ev  # noqa: E402
import lens_specs as ls  # noqa: E402


def cu(t):
    s = ev.lens_sig(ev.head_main(t))
    return tuple(float(x) if x else None for x in s) if s else None


half = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open("ai/survey/content4/fa_split.csv", encoding="utf-8"))}
lenses = [a for a in csv.DictReader(open("ai/data/kg/item_attributes.csv", encoding="utf-8")) if a["item_type"] == "ong"]
print(f"Bộ đọc mới: {ls.READER_VERSION}. Ống: {len(lenses)}; đọc được cũ {sum(cu(a['title']) is not None for a in lenses)}, "
      f"mới {sum(ls.read_title(a['title']) is not None for a in lenses)}")
c = collections.Counter()
for a in sorted(lenses, key=lambda a: a["parent_asin"]):
    o, n = cu(a["title"]), ls.read_title(a["title"])
    if o == n:
        continue
    h = half.get(a["parent_asin"], "ngoai")
    c[h] += 1
    if h != "holdout":
        print(f"  [{h:5s}] {a['parent_asin']} cũ {o} -> mới {n} | {a['title'][:110]}")
print("Số ống đổi kết quả đọc theo nửa:", dict(c))
