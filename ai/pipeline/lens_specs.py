"""
Đọc tiêu cự và khẩu độ từ tiêu đề ống kính (nội dung 4, nút focal_range / aperture_class của đồ thị).

Ví dụ: "Canon EF 70-200mm f/2.8L IS III USM Lens" -> f1 = 70, f2 = 200, a1 = 2.8, a2 = None
  -> nút tiêu cự: 36–70, 71–135, 136–300 (zoom nối mọi khoảng nó đi qua, QĐ 4-1)
  -> nút khẩu độ: ≤2.8 (theo a1 = số f nhỏ nhất, tức ở đầu rộng)

Bản đầu (v0) chép nguyên từ ai/survey/content3/eval_external.py (head_for, head_main, FOCAL, APER, _num, lens_sig),
để nội dung 3 không bị ảnh hưởng khi sửa bộ đọc ở đây. Mọi lần sửa sau v0 chỉ dựa trên ca lệch của nửa fix
(kế hoạch docs/reviews/n4_focal_aperture_plan.md) và ghi lý do ngay tại chỗ sửa.
"""
import re

READER_VERSION = "v0"


def head_for(t):
    """Phần đầu tiêu đề: trước 'for / compatible / replacement / fits ...'."""
    return re.split(r"\s(?:for|compatible|replacement|fits|designed|works)\b", t.lower(), maxsplit=1)[0]


def head_main(t):
    """Phần chủ thể tiêu đề: trước 'with / + / & / plus / bundle / kit' (ống bán kèm phụ kiện)."""
    return re.split(r"\s(?:with|w/|\+|&|plus|bundle|kit)\s|\s\+", head_for(t), maxsplit=1)[0]


FOCAL = re.compile(r"(\d{1,4}(?:\.\d)?)\s?(?:-\s?(\d{1,4}(?:\.\d)?))?\s?mm")
APER = re.compile(r"(?:f\s?/?\s?|1\s?:\s?)(\d{1,2}(?:\.\d{1,2})?)(?:\s?-\s?(\d{1,2}(?:\.\d{1,2})?))?", re.I)


def _f(x):
    return None if x is None else float(x)


def read_text(text):
    """Đọc trong một đoạn văn bản đã cắt. Trả về (f1, f2, a1, a2) dạng số thực (f2 / a2 = None nếu không có),
    hoặc None nếu không đọc được cả tiêu cự lẫn khẩu độ."""
    t = text.lower().replace("–", "-")
    fm = FOCAL.search(t)
    if not fm:
        return None
    am = APER.search(t[fm.end():]) or APER.search(t)
    if not am:
        return None
    return _f(fm.group(1)), _f(fm.group(2)), _f(am.group(1)), _f(am.group(2))


def read_title(title):
    """Đọc từ tiêu đề Amazon (phần chủ thể)."""
    return read_text(head_main(title))


# ---------------------------------------------------------------- khoảng của nút (QĐ 4-1, content4_design mục 3.2)
# Tiêu cự THẬT (không quy đổi). Biên: <24 | [24, 35] | (35, 70] | (70, 135] | (135, 300] | >300.
FOCAL_BINS = [("<24", 0, 24), ("24-35", 24, 35), ("36-70", 35, 70), ("71-135", 70, 135),
              ("136-300", 135, 300), (">300", 300, float("inf"))]
# Khẩu độ theo a1 (số f nhỏ nhất). Biên: (0, 1.4] | (1.4, 2.0] | (2.0, 2.8] | (2.8, 4] | >4.
APER_BINS = [("<=1.4", 1.4), ("<=2.0", 2.0), ("<=2.8", 2.8), ("<=4", 4.0), (">4", float("inf"))]


def focal_nodes(f1, f2=None):
    """Các khoảng tiêu cự mà ống phủ: ống một tiêu cự -> 1 khoảng; zoom -> mọi khoảng giao với [f1, f2]."""
    lo, hi = (f1, f2) if f2 is not None else (f1, f1)
    out = []
    for name, blo, bhi in FOCAL_BINS:
        if name == "<24":
            hit = lo < 24
        elif name == "24-35":
            hit = lo <= 35 and hi >= 24
        else:
            hit = lo <= bhi and hi > blo
        if hit:
            out.append(name)
    return tuple(out)


def aperture_node(a1):
    for name, hi in APER_BINS:
        if a1 <= hi:
            return name
    return None
