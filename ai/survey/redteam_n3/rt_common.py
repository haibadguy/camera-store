"""
Hàm dùng chung cho các script chẩn đoán Red Team nội dung 3 (lần 1, phần B: T1, T2, T3).
Chỉ ĐỌC ai/data/kg/item_attributes.csv; mọi phép "chạy thử" đều vá tạm mount_detect TRONG BỘ NHỚ, không ghi file.
"""
import contextlib
import csv
import importlib.util
import os
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "ai/pipeline"))
import mount_detect as md  # noqa: E402

ATTR = os.path.join(ROOT, "ai/data/kg/item_attributes.csv")
RULES = os.path.join(ROOT, "ai/config/mount_rules.toml")
FIELDS = ["item_type", "mount", "khung", "may_phim", "mount_source", "evidence", "uncertain"]


def load_rows():
    return list(csv.DictReader(open(ATTR, encoding="utf-8")))


def load_rules():
    spec = importlib.util.spec_from_file_location("mc03", os.path.join(ROOT, "ai/pipeline/03_mount_compat.py"))
    mc03 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc03)
    return mc03.Rules(RULES)


def is_single(m):          # giống 03_mount_compat.py
    return m not in ("khong_co", "khong_ro", "nhieu", "") and ">" not in m


def classify(r):
    cats = r["categories"].split(" > ") if r["categories"] else []
    out = md.classify_item(r["title"], cats, int(r["n_child_asin"] or 0))
    return {k: str(out[k]) for k in FIELDS}


def classify_all(rows):
    return {r["parent_asin"]: classify(r) for r in rows}


def check_baseline(rows):
    """Chạy lại classify_item với code hiện tại; phải khớp item_attributes.csv từng trường."""
    res = classify_all(rows)
    bad = [r["parent_asin"] for r in rows if any(res[r["parent_asin"]][k] != r[k] for k in FIELDS)]
    print(f"kiểm lại: chạy lại classify_item trên {len(rows):,} sản phẩm, số sản phẩm lệch item_attributes.csv "
          f"(trường {FIELDS}): {len(bad)}")
    for a in bad[:5]:
        print("   lệch:", a)
    return res


def series_from(body_series_list):
    return [(re.compile(r"\b(?:" + b + r")"), re.compile(p), m, k, n) for b, p, m, k, n in body_series_list]


@contextlib.contextmanager
def patched(**attrs):
    """Vá tạm các thuộc tính của mount_detect, trả lại như cũ khi ra khỏi khối with."""
    old = {k: getattr(md, k) for k in attrs}
    try:
        for k, v in attrs.items():
            setattr(md, k, v)
        yield
    finally:
        for k, v in old.items():
            setattr(md, k, v)
