"""Kiểm CVR mới (ai/pipeline/common_05.py, QĐ 4-9) bằng ví dụ dựng tay, rồi tra vài cặp trên dữ liệu thật.

Phần A — dữ liệu dựng tay (không đọc file):
  sản phẩm: 0 D3500 (thân Nikon F) | 1 FM (thân máy phim Nikon F) | 2 ống Canon EF | 3 ống Nikon DX
            4 phụ kiện | 5 ống "không chắc" (ngoài M) | 6 ống Sony E | 7 ống không ngàm (ngoài M)
            8 thân không xác định ngàm (ngoài M)
  M = 1: (D3500, DX). "Không biết": (FM, DX) [máy phim + ống cùng ngàm, QĐ 3-16] và (FM, EF) [giả định của ví dụ QĐ 4-9].
Phần B — đếm tay lại full_catalog_cvr (gộp micro, bỏ người dùng không có ống chấm được).
Phần C — dữ liệu thật ai/data/kg (đầu ra nội dung 3 + 4): tra lại ví dụ QĐ 4-9 với thân và ống có thật.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/test_cvr.py
"""
import math
import sys

import numpy as np

sys.path.insert(0, "ai/pipeline")
sys.stdout.reconfigure(encoding="utf-8")
import common_05 as C  # noqa: E402

fails = 0


def check(name, got, want):
    global fails
    ok = (isinstance(want, float) and isinstance(got, float) and math.isclose(got, want)) or got == want
    fails += not ok
    print(f"{'OK ' if ok else 'SAI'} {name}: {got}" + ("" if ok else f"  (kỳ vọng {want})"))


D3500, FM, EF, DX, ACC, UNC, SE, NOMOUNT, BODY_X = range(9)
NAME = {None: "không chấm được", True: "vi phạm", False: "không vi phạm"}
item_type = np.array([0, 0, 1, 1, 2, 1, 1, 1, 0])
ctx = C.CvrContext(lenses_in_m={EF, DX, SE}, bodies_in_m={D3500, FM},
                   m1={(D3500, DX)}, unknown={(FM, DX), (FM, EF)})


def J(name, lens, bodies, want):
    check(name, NAME[C.judge_lens(lens, bodies, ctx)], NAME[want])


print("=== A. judge_lens trên dữ liệu dựng tay ===")
J("ví dụ QĐ 4-9: D3500 + FM, ống Canon EF", EF, {D3500, FM}, None)
J("D3500 một mình, ống Canon EF (M = 0, không cặp 'không biết')", EF, {D3500}, True)
J("D3500 + FM, ống Nikon DX (D3500 có M = 1)", DX, {D3500, FM}, False)
J("FM một mình, ống Nikon DX (chỉ có cặp 'không biết')", DX, {FM}, None)
J("D3500 + FM, ống Sony E (cả hai cặp M = 0, không 'không biết')", SE, {D3500, FM}, True)
J("ống 'không chắc' (ngoài M)", UNC, {D3500}, None)
J("ống không ngàm (ngoài M)", NOMOUNT, {D3500}, None)
J("thân ngoài M một mình, ống Canon EF", EF, {BODY_X}, None)
J("D3500 + thân ngoài M, ống Canon EF (thân ngoài M không có M = 0)", EF, {D3500, BODY_X}, None)
J("D3500 + thân ngoài M, ống Nikon DX (vẫn có M = 1)", DX, {D3500, BODY_X}, False)
J("không có thân nào", EF, set(), None)

print("\n=== B. full_catalog_cvr: gộp micro, bỏ người dùng không có ống chấm được ===")
# điểm của từng sản phẩm theo người dùng; sản phẩm trong train bị ẩn (-inf)
S = {
    # u1: top-3 = EF (không chấm được), DX (không vi phạm), ACC (không tính)
    1: [0, 0, 9, 8, 7, 0, 0, 0, 0],
    # u2: DX trong train bị ẩn; top-3 = EF (vi phạm), SE (vi phạm), UNC (ngoài M); top-2 = EF, SE
    2: [0, 0, 9, 99, 0, 7, 8, 0, 0],
    # u3: chỉ có FM; top-3 = DX, EF (đều không chấm được), NOMOUNT -> bỏ khỏi phép tính
    3: [0, 0, 8, 9, 0, 0, 0, 7, 0],
    # u4: chỉ có thân ngoài M; top-3 = EF, SE, DX -> bỏ
    4: [0, 0, 9, 7, 0, 0, 8, 0, 0],
}
train = {1: {D3500, FM}, 2: {D3500, DX}, 3: {FM}, 4: {BODY_X}, 5: {ACC}}
cvr_users = C.build_train_bodies(train, None, item_type)
check("build_train_bodies: mọi thân trong train, bỏ người không có thân", cvr_users,
      {1: {D3500, FM}, 2: {D3500}, 3: {FM}, 4: {BODY_X}})
r = C.full_catalog_cvr(lambda u: np.array(S[u], dtype=float), cvr_users, train, None, item_type, k_list=[2, 3], ctx=ctx)
# K = 3: u1 chấm 1 ống (DX, 0 vi phạm); u2 chấm 2 ống (EF, SE, 2 vi phạm); u3, u4 bị bỏ
#        micro = 2 / 3 (macro sẽ là (0/1 + 2/2) / 2 = 0,5)
check("K=3 số người dùng được tính", r["cvr_n_users@3"], 2)
check("K=3 số ống chấm được", r["cvr_n_lenses@3"], 3)
check("K=3 số vi phạm", r["cvr_n_violations@3"], 2)
check("K=3 CVR micro", r["cvr@3"], 2 / 3)
# K = 2: u1 top-2 = EF, DX -> chấm DX; u2 top-2 = EF, SE -> 2 vi phạm
check("K=2 CVR micro", r["cvr@2"], 2 / 3)
check("K=2 số người dùng được tính", r["cvr_n_users@2"], 2)
check("số người dùng có thân", r["cvr_n_users_with_body"], 4)
r0 = C.full_catalog_cvr(lambda u: np.array(S[u], dtype=float), {3: {FM}}, train, None, item_type, k_list=[3], ctx=ctx)
check("không ai chấm được -> CVR = nan, 0 người dùng", (math.isnan(r0["cvr@3"]), r0["cvr_n_users@3"]), (True, 0))

print("\n=== C. Dữ liệu thật (ai/data/kg) ===")
it = C.load_item_type()
b2l = C.load_body_to_lenses()
rc = C.load_cvr_context(b2l)
print(f"loại: {dict(zip(*np.unique(it, return_counts=True)))} | ống trong M {len(rc.lenses_in_m)} | thân trong M "
      f"{len(rc.bodies_in_m)} | cặp M = 1 {len(rc.m1)} | cặp 'không biết' {len(rc.unknown)}")
check("số cặp M = 1 đọc từ cạnh đồ thị", len(rc.m1), 72720)
# Không có D3500 trong dữ liệu: dùng D3200 (Nikon F, APS-C) và FM-10 (máy phim Nikon F) có thật
D3200, FM10, EF50, DX35 = 11711, 189, 7056, 13212
real = {
    "ví dụ QĐ 4-9 trên dữ liệu thật: D3200 + FM-10, ống Canon EF 50mm f/1.8 STM": (EF50, {D3200, FM10}),
    "D3200 + FM-10, ống Nikon AF-S DX 35mm f/1.8G": (DX35, {D3200, FM10}),
    "FM-10 một mình, ống Nikon AF-S DX 35mm f/1.8G": (DX35, {FM10}),
}
print(f"  (FM-10, EF 50 STM): M = 1? {(FM10, EF50) in rc.m1} | 'không biết'? {(FM10, EF50) in rc.unknown}")
print(f"  (D3200, EF 50 STM): M = 1? {(D3200, EF50) in rc.m1} | 'không biết'? {(D3200, EF50) in rc.unknown}")
print(f"  (FM-10, DX 35): M = 1? {(FM10, DX35) in rc.m1} | 'không biết'? {(FM10, DX35) in rc.unknown}")
print(f"  (D3200, DX 35): M = 1? {(D3200, DX35) in rc.m1}")
for name, (lens, bodies) in real.items():
    print(f"  {name}: {NAME[C.judge_lens(lens, bodies, rc)]}")

train_real = C.load_train()
cu = C.build_train_bodies(train_real, b2l, it)
old_rule = {u: {b for b in bs if b in b2l} for u, bs in cu.items()}
import csv  # noqa: E402
film = {int(a["iid"]) for a in csv.DictReader(open(C.ITEM_ATTR_CSV, encoding="utf-8")) if a["may_phim"] == "True"}
no_m1 = {b for b in rc.bodies_in_m if b not in b2l}
print(f"\nngười dùng có thân trong train: {len(cu):,}; trong đó có thân ngoài M: "
      f"{sum(1 for bs in cu.values() if bs - rc.bodies_in_m):,}; có thân máy phim: "
      f"{sum(1 for bs in cu.values() if bs & film):,}; có thân trong M mà không có ống M = 1 nào: "
      f"{sum(1 for bs in cu.values() if bs & no_m1):,} ({len(no_m1)} thân như vậy, {len(no_m1 & film)} là máy phim)")
print(f"(đối chiếu) quy tắc cũ của build_train_bodies (chỉ thân có ít nhất một ống M = 1) trên dữ liệu mới: "
      f"{sum(1 for bs in old_rule.values() if bs):,} người dùng")

print(f"\n{'ĐẠT CẢ' if fails == 0 else f'SAI {fails}'}")
sys.exit(1 if fails else 0)
