"""
Kiểm thử bằng VÍ DỤ DỰNG TAY cho các bản bộ đánh giá của eval_external.py (truoc_0710 / lan2 / lan3).
Không đọc dữ liệu sản phẩm, không đọc nguồn ngoài: chỉ gọi các hàm khớp với chỉ mục giả.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content3/test_eval_external.py
"""
import sys
sys.path.insert(0, "ai/survey/content3")
sys.stdout.reconfigure(encoding="utf-8")
import eval_external as ev

fails = 0


def check(name, got, want):
    global fails
    ok = got == want
    fails += not ok
    print(f"{'OK ' if ok else 'SAI'} {name}: được {got!r}, cần {want!r}")


# ---------------------------------------------------------------- 1. bộ lọc tiêu đề phụ kiện
# (tiêu đề, lan2 loại?, lan3 loại?)
ACC_CASES = [
    # S2: không còn bị loại ở lan3
    ("Nikon F100 35mm SLR Film Camera Body", True, False),
    ("Canon EOS Rebel 2000 35mm Film SLR Camera", True, False),
    ("Sony FE 50mm F1.8 Standard Lens E-Mount", True, False),
    ("Sigma 30mm F1.4 DC DN Contemporary Lens for Sony E", False, False),
    ("Nikon D3500 24.2MP DSLR Camera 3.0\" LCD", True, False),
    ("Canon PowerShot SX740 HS Built-in Flash", True, False),
    ("Fujifilm X-T4 Mirrorless Camera Dual Card Slot", True, False),
    ("Sony Alpha 7S III Low Light Full Frame Camera", True, False),
    ("Sony A7 III Touch Screen Mirrorless Camera", True, False),
    # hạn chế đã biết, KHÔNG sửa (ngoài danh sách Red Team): "manual" vẫn loại "Manual Focus" -> K1000 vẫn bị loại
    ("Pentax K1000 Manual Focus SLR Film Camera", True, True),
    # S2: vẫn bị loại ở cả hai bản (cụm phụ kiện cụ thể)
    ("Nikon D3500 Screen Protector Film", True, True),
    ("Neewer Ring Light for Nikon", True, True),
    ("Godox V1 Speedlite Flash for Canon", True, True),
    ("SanDisk 64GB SD Card for Canon EOS R6", True, True),
    ("GoPro Hero 9 Suction Cup Mount", True, True),
    ("Nikon D850 LCD Screen Panel Repair Part", True, True),
    ("Canon Ec-S Focusing Screen for 5D", True, True),
    ("Fujifilm Instax Mini Instant Film", True, True),
    ("Sigma MC-11 Mount Converter Canon EF to Sony E", True, True),
    ("Fotodiox Lens Mount Adapter Canon EF to Sony E", True, True),
    # N4: lan2 để lọt, lan3 loại
    ("Samsung Galaxy S8 Plus Tempered Glass Screen Protector", False, True),
    ("Canon EOS Rebel T6s Expanded Guides", False, True),
    ("Nikon D7000 Eye Cup DK-21 Replacement", False, True),  # head_for cắt ở "replacement" nên lan2 để lọt
    ("Nikon D7000 Rubber Eye Cup DK-21", False, True),
    ("Panasonic Lumix G9 Eye Cup", False, True),
    ("Nikon D750 Silicone Jacket", False, True),
    # không đổi: bộ máy cắt ở with/+, không có từ phụ kiện ở phần đầu
    ("Canon EOS Rebel T7 DSLR Camera with 18-55mm Lens, Bag, Memory Card", False, False),
    ("Nikon D3500 DSLR + 18-55mm VR Lens", False, False),
]
for t, want2, want3 in ACC_CASES:
    for mode, want in (("lan2", want2), ("lan3", want3)):
        ev.MODE = mode
        check(f"[{mode}] loại tiêu đề phụ kiện? | {t}", ev.acc_title(t), want)
ev.MODE = "truoc_0710"
check("[truoc_0710] không lọc phụ kiện | Nikon D3500 Screen Protector Film",
      ev.acc_title("Nikon D3500 Screen Protector Film"), False)

# Mỗi cụm S2 phải chứa đúng 1 trong 7 từ cũ (số ít) -> tập bị loại chỉ thu hẹp
import re
OLD7 = re.compile(r"\b(?:film|mount|lcd|screen|flash|light|card)\b")
for t, want2, want3 in ACC_CASES:
    ev.MODE = "lan3"
    h = ev.head_main(t, plus=False)
    for m in re.finditer(r"\b(?:" + "|".join(ev.ACC_EVAL_LAN3_PHRASES) + r")\b", h):
        check(f"cụm S2 chứa từ cũ | {m.group(0)!r}", bool(OLD7.search(m.group(0))), True)

check("head_main cắt ở plus (lan2)", ev.head_main("Samsung Galaxy S8 Plus Screen Protector"), "samsung galaxy s8")
check("head_main không cắt ở plus (lan3)", ev.head_main("Samsung Galaxy S8 Plus Screen Protector", plus=False),
      "samsung galaxy s8 plus screen protector")

# ---------------------------------------------------------------- 2. token khẩu độ không khớp thành thân Nikon F4 / F2
F4 = dict(type="than", mount="nikon_f", khung="ff", name="Nikon F4", id="gia:f4")
F2 = dict(type="than", mount="nikon_f", khung="ff", name="Nikon F2", id="gia:f2")
D750 = dict(type="than", mount="nikon_f", khung="ff", name="Nikon D750", id="gia:d750")
idx = ev.index_bodies([("nikon", ("f4",), F4), ("nikon", ("f2",), F2), ("nikon", ("d750",), D750)])
BODY_CASES = [  # (tiêu đề, lan2, lan3) -> tên thân khớp được hoặc None
    ("Nikon 70-210mm F4 AF Zoom Lens", "Nikon F4", None),
    ("Nikon 70-210 mm F4 AF Zoom Lens", "Nikon F4", None),
    ("Helios 44-2 58mm F2 Lens for Nikon", "Nikon F2", None),
    ("Tokina at-X PRO 12-28 F4 DX Lens for Nikon", "Nikon F4", None),
    ("Nikon F4 35mm SLR Film Camera Body", "Nikon F4", "Nikon F4"),
    ("Nikon F2 Photomic Camera", "Nikon F2", "Nikon F2"),
    ("Nikon D750 FX-format Digital SLR Camera Body", "Nikon D750", "Nikon D750"),
]
for t, want2, want3 in BODY_CASES:
    for mode, want in (("lan2", want2), ("lan3", want3)):
        ev.MODE = mode
        tr, _, cum = ev.match_body(t, idx)
        check(f"[{mode}] khớp thân | {t}", tr["name"] if isinstance(tr, dict) else tr, want)

# ---------------------------------------------------------------- 3. bản truoc_0710: khớp ống không cần trùng mọi token
RF = dict(mounts={"canon_rf"}, crop=None, name="Canon RF 75-300mm f/4-5.6", id="gia:rf75300")
lidx = {("canon",) + ev.lens_sig(RF["name"]): [RF]}
t = "Canon EF 75-300mm f/4-5.6 III Telephoto Zoom Lens"
for mode, want in (("truoc_0710", "canon_rf"), ("lan2", None), ("lan3", None)):
    ev.MODE = mode
    m = ev.match_lens(t, lidx)
    check(f"[{mode}] khớp ống | {t}", m["mount"] if m else None, want)

# cụm cho bootstrap: không phụ thuộc thứ tự
A = dict(mounts={"canon_ef"}, crop=None, name="Canon EF 50mm f/1.8 II", id="gia:b")
B = dict(mounts={"canon_ef"}, crop=None, name="Canon EF 50mm f/1.8 II", id="gia:a")
ev.MODE = "lan3"
for order in ([A, B], [B, A]):
    m = ev.match_lens("Canon EF 50mm f/1.8 II Lens", {("canon",) + ev.lens_sig(A["name"]): order})
    check("cum_nguon = id nhỏ nhất", m["id"], "gia:a")

print(f"\n{'TẤT CẢ ĐÚNG' if not fails else f'{fails} CA SAI'}")
sys.exit(1 if fails else 0)
