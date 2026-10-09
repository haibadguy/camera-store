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

READER_VERSION = "v1"
# v1 (08/10/2026, sửa theo nửa fix và 2 lỗi đã biết; kế hoạch mục 7 bước A, mục 9):
#   S1 lỗi đã biết "F/1.8-22": dải "a1-a2" có a2 >= 11 là dải từ mở lớn nhất tới khép nhỏ nhất, không phải zoom
#      khẩu độ thay đổi -> bỏ a2. Cả dải >= 11 ("f/22-32") -> bỏ cả lần khớp đó, tìm khẩu độ kế tiếp.
#   S2 lỗi đã biết "Tokina 12mm - 24mm": tiêu cự zoom ghi "mm" ở cả hai đầu.
#   S3 ca fix B07PZB3YKH: khẩu độ nằm ngay sau "with" ("14-140mm ... Lens with F3.5-5.6 II").


def head_for(t):
    """Phần đầu tiêu đề: trước 'for / compatible / replacement / fits ...'."""
    return re.split(r"\s(?:for|compatible|replacement|fits|designed|works)\b", t.lower(), maxsplit=1)[0]


def head_main(t):
    """Phần chủ thể tiêu đề: trước 'with / + / & / plus / bundle / kit' (ống bán kèm phụ kiện)."""
    return re.split(r"\s(?:with|w/|\+|&|plus|bundle|kit)\s|\s\+", head_for(t), maxsplit=1)[0]


# S2: "(?:mm\s?)?" cho phép "12mm - 24mm" (v0 chỉ đọc được 12). "50mm f/1.8" vẫn chỉ đọc 50 (không có "mm" thứ hai).
FOCAL = re.compile(r"(\d{1,4}(?:\.\d)?)\s?(?:mm\s?)?(?:-\s?(\d{1,4}(?:\.\d)?))?\s?mm")
APER = re.compile(r"(?:f\s?/?\s?|1\s?:\s?)(\d{1,2}(?:\.\d{1,2})?)(?:\s?-\s?(\d{1,2}(?:\.\d{1,2})?))?", re.I)
# S1: ngưỡng 11. Trong 1.581 tên ống của Lensfun, khẩu độ đầu tele lớn nhất của zoom là f/9 (Canon RF 200-800mm F6.3-9);
# khẩu độ khép nhỏ nhất của ống thường là f/16, f/22, f/32. Ống một tiêu cự f/11 (vd RF 800mm F11) không có dải nên giữ.
MIN_APERTURE_FROM = 11.0
# S3: khẩu độ đứng ngay sau "with" / "w/" (head_main cắt ở đó).
WITH_APER = re.compile(r"\s(?:with|w/)\s+(?=(?:f\s?/?\s?|1\s?:\s?)\d)")


def _f(x):
    return None if x is None else float(x)


def _aperture(t, start):
    """Lần khớp khẩu độ đầu tiên hợp lệ: ưu tiên sau tiêu cự (từ vị trí start), không có thì ở bất kỳ đâu."""
    for s in (t[start:], t):
        for am in APER.finditer(s):
            a1, a2 = _f(am.group(1)), _f(am.group(2))
            if a2 is not None and a2 >= MIN_APERTURE_FROM:
                if a1 >= MIN_APERTURE_FROM:          # "f/22-32": cả dải là khẩu độ khép -> tìm tiếp
                    continue
                a2 = None                            # "F/1.8-22" -> f/1.8
            return a1, a2
    return None


def read_text(text):
    """Đọc trong một đoạn văn bản đã cắt. Trả về (f1, f2, a1, a2) dạng số thực (f2 / a2 = None nếu không có),
    hoặc None nếu không đọc được cả tiêu cự lẫn khẩu độ."""
    t = text.lower().replace("–", "-")
    fm = FOCAL.search(t)
    if not fm:
        return None
    ap = _aperture(t, fm.end())
    if not ap:
        return None
    return _f(fm.group(1)), _f(fm.group(2)), ap[0], ap[1]


def read_title(title):
    """Đọc từ tiêu đề Amazon (phần chủ thể). S3: phần chủ thể có tiêu cự mà không có khẩu độ, và ngay sau chỗ cắt
    là "with <khẩu độ>" -> đọc thêm khẩu độ đó."""
    h = head_main(title)
    r = read_text(h)
    if r is None and FOCAL.search(h):
        rest = head_for(title)[len(h):]
        m = WITH_APER.match(rest)
        if m:
            r = read_text(h + " " + rest[m.end():])
    return r


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
