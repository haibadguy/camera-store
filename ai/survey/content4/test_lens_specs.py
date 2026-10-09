"""Kiểm bộ đọc tiêu cự / khẩu độ (ai/pipeline/lens_specs.py) bằng ví dụ dựng tay, và kiểm khoảng của nút.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/test_lens_specs.py
"""
import sys

sys.path.insert(0, "ai/pipeline")
sys.stdout.reconfigure(encoding="utf-8")
import lens_specs as ls  # noqa: E402

fails = 0


def check(name, got, want):
    global fails
    ok = got == want
    fails += not ok
    print(f"{'OK ' if ok else 'SAI'} {name}: {got}" + ("" if ok else f"  (kỳ vọng {want})"))


R = ls.read_title
# --- giữ nguyên hành vi v0
check("prime", R("Canon EF 50mm f/1.8 STM Lens"), (50.0, None, 1.8, None))
check("zoom khẩu độ thay đổi", R("Canon EF-S 18-55mm f/3.5-5.6 IS II"), (18.0, 55.0, 3.5, 5.6))
check("zoom khẩu độ cố định, chữ L", R("Canon EF 70-200mm f/2.8L IS III USM"), (70.0, 200.0, 2.8, None))
check("F1.8 không gạch", R("Sony FE 50mm F1.8 Standard Lens"), (50.0, None, 1.8, None))
check("1:2.8 kiểu Pentax", R("Pentax smc DA 35mm 1:2.4 AL"), (35.0, None, 2.4, None))
check("cắt ở 'for'", R("Rokinon 14mm F2.8 Ultra Wide Lens for Canon 5D 24mm"), (14.0, None, 2.8, None))
check("cắt ở '+': không đọc ống thứ hai", R("Canon EF 50mm f/1.8 + Canon 75-300mm f/4-5.6"), (50.0, None, 1.8, None))
check("không có khẩu độ -> None", R("Nikon NIKKOR Z 24-200mm VR | Compact all-in-one telephoto"), None)
check("không có tiêu cự -> None", R("Canon lens f/1.8"), None)
check("tiêu cự thập phân", R("Nikon 1 NIKKOR 6.7-13mm f/3.5-5.6 VR"), (6.7, 13.0, 3.5, 5.6))
# --- S1: dải khẩu độ max-min
check("S1 F/1.8-22 (SEL85F18)", R("Sony SEL85F18 85mm F/1.8-22 Medium-Telephoto Fixed Prime Camera Lens, Black"),
      (85.0, None, 1.8, None))
check("S1 f/2.8-22 kèm 'with'", R("Rokinon 14mm f/2.8-22 Ultra Wide Angle Lens with Built-In AE Chip"), (14.0, None, 2.8, None))
check("S1 a2 = 11 bị bỏ", R("Test 35mm f/2-11 Lens"), (35.0, None, 2.0, None))
check("S1 f/6.3-9 giữ (RF 200-800)", R("Canon RF 200-800mm F6.3-9 IS USM"), (200.0, 800.0, 6.3, 9.0))
check("S1 f/22-32 bỏ, lấy F4.5-6.3", R("Sigma 60-600mm f/22-32 Fixed Zoom F4.5-6.3 DG OS HSM Camera Lenses"),
      (60.0, 600.0, 4.5, 6.3))
check("S1 f/11 một tiêu cự giữ", R("Canon RF 800mm F11 IS STM"), (800.0, None, 11.0, None))
check("S1 zoom dải đầu là khẩu độ thật", R("Nikon AF-S FISHEYE NIKKOR 8-15mm f/3.5-4.5E ED F/4.5-29 Fixed Zoom"),
      (8.0, 15.0, 3.5, 4.5))
# --- S2: "12mm - 24mm"
check("S2 Tokina 12mm - 24mm", R("Tokina 12mm - 24mm f/4 PRO DX Autofocus Zoom Lens for Canon"), (12.0, 24.0, 4.0, None))
check("S2 650mm-1300mm", R("Bower SLY650C Long-Range 650mm-1300mm f/8 Telephoto Zoom Lens for Canon"),
      (650.0, 1300.0, 8.0, None))
# --- S3: khẩu độ sau "with"
check("S3 with F3.5-5.6", R("Panasonic Lumix G Vario 14-140mm Telephoto Zoom Lens with F3.5-5.6 II ASPH, Mirrorless"),
      (14.0, 140.0, 3.5, 5.6))
check("S3 không áp khi phần chủ thể đã có khẩu độ", R("Canon 50mm f/1.8 with f/1.4 hood"), (50.0, None, 1.8, None))
check("S3 không áp khi sau 'with' không phải khẩu độ", R("Tamron 18-200mm Di III VC with Hood"), None)
# --- khoảng của nút
F = ls.focal_nodes
check("nút 24", F(24.0), ("24-35",))
check("nút 35", F(35.0), ("24-35",))
check("nút 23.5", F(23.5), ("<24",))
check("nút 70", F(70.0), ("36-70",))
check("nút 70-200", F(70.0, 200.0), ("36-70", "71-135", "136-300"))
check("nút 18-55", F(18.0, 55.0), ("<24", "24-35", "36-70"))
check("nút 150-600", F(150.0, 600.0), ("136-300", ">300"))
check("nút 300", F(300.0), ("136-300",))
check("nút 35.5", F(35.5), ("36-70",))
A = ls.aperture_node
check("khẩu 1.4", A(1.4), "<=1.4")
check("khẩu 0.95", A(0.95), "<=1.4")
check("khẩu 1.8", A(1.8), "<=2.0")
check("khẩu 2.0", A(2.0), "<=2.0")
check("khẩu 2.8", A(2.8), "<=2.8")
check("khẩu 3.5", A(3.5), "<=4")
check("khẩu 4.0", A(4.0), "<=4")
check("khẩu 4.5", A(4.5), ">4")
print("TẤT CẢ ĐÚNG" if not fails else f"{fails} CA SAI")
sys.exit(1 if fails else 0)
