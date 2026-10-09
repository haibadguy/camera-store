"""Đếm cạnh has_spec -> focal_range / aperture_class dự kiến theo bộ đọc ai/pipeline/lens_specs.py (chưa dựng đồ thị).
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/count_spec_nodes.py
"""
import collections, csv, sys

sys.path.insert(0, "ai/pipeline")
sys.stdout.reconfigure(encoding="utf-8")
import lens_specs as ls  # noqa: E402

lenses = [a for a in csv.DictReader(open("ai/data/kg/item_attributes.csv", encoding="utf-8")) if a["item_type"] == "ong"]
reads = [ls.read_title(a["title"]) for a in lenses]
ok = [r for r in reads if r]
print(f"bộ đọc lens_specs {ls.READER_VERSION}; ống {len(lenses)}; đọc được tiêu cự + khẩu độ {len(ok)} "
      f"(zoom {sum(1 for r in ok if r[1] is not None)}, một tiêu cự {sum(1 for r in ok if r[1] is None)})")
fb = collections.Counter(b for r in ok for b in ls.focal_nodes(r[0], r[1]))
ab = collections.Counter(ls.aperture_node(r[2]) for r in ok)
print(f"cạnh -> focal_range: {sum(fb.values())}; theo khoảng: " + ", ".join(f"{b} {fb[b]}" for b, _, _ in ls.FOCAL_BINS))
print(f"cạnh -> aperture_class: {sum(ab.values())}; theo khoảng: " + ", ".join(f"{b} {ab[b]}" for b, _ in ls.APER_BINS))
