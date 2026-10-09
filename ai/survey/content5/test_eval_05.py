"""Kiểm thử dựng tay cho đánh giá nội dung 5 (ai/pipeline/eval_05.py), theo docs/reviews/n5_eval_plan.md mục 10.

A. Ví dụ mục 1 của kế hoạch: hạng 3 -> Hit@2 = Recall@2 = 0, Hit@3 = Recall@3 = 1, NDCG@3 = 0,5; khi chấm test bỏ
   cả train (D) và val (E); khi chấm val chỉ bỏ train.
B. Quy tắc hòa: 3 sản phẩm cùng điểm, hạng và top-K theo π.
C. Item train / val không bao giờ vào top-K, kể cả khi điểm cao nhất; ứng viên −∞ (MountAware) vẫn xếp trước
   sản phẩm không phải ứng viên (kịch bản chỉ ống).
D. Bộ lọc MountAware: mặt nạ certain_violation_mask = (judge_lens is True), người không có thân / thân ngoài M không
   bị lọc. Dựng tay + toàn bộ dữ liệu thật (mọi người có thân × mọi ống trong M).
E. Recall@K = Hit@K từng người (per_user_metrics tự kiểm; thử cố ý làm sai thì phải báo lỗi).
F. CVR từ top-K (eval_05.cvr_from_top) = common_05.full_catalog_cvr (đã kiểm ở test_cvr.py) trên ví dụ dựng tay.
G. Nhóm kịch bản "ống cho người đã có thân".
H. Sampled 1+99: âm mẫu bằng điểm xếp trên item cần đoán (quy tắc của Hải).
I. Bootstrap: hai "mô hình" giống hệt nhau -> hiệu luôn bằng 0; khoảng chứa giá trị điểm.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content5/test_eval_05.py
"""
import math
import sys
import time

import numpy as np
import torch

sys.path.insert(0, "ai/pipeline")
sys.stdout.reconfigure(encoding="utf-8")
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402

fails = 0


def check(name, got, want):
    global fails
    ok = (isinstance(want, float) and isinstance(got, float) and math.isclose(got, want, abs_tol=1e-12)) or got == want
    fails += not ok
    print(f"{'OK ' if ok else 'SAI'} {name}: {got}" + ("" if ok else f"  (kỳ vọng {want})"))


def scorer(table):
    """table: {uid: [điểm từng sản phẩm]} -> score_batch."""
    def f(uids):
        return torch.tensor([table[int(u)] for u in uids.tolist()], dtype=torch.float32, device=E.DEVICE)
    return f


def fr(table, sp, pi, k_max, k_list, cand=None):
    return E.full_rank(scorer(table), sp, np.array(pi), cand_items=cand, k_max=k_max, k_list=k_list)


print("=== A. Ví dụ mục 1 ===")
A, B, Cc, D, Ee = range(5)
S1 = {1: [0.7, 0.9, 0.8, 1.0, 0.1]}                      # D (train) điểm cao nhất -> phải bị loại
sp_test = E.make_split("test", {1: {D}}, {1: A}, val={1: Ee})
r = fr(S1, sp_test, range(5), 3, [1, 2, 3])
check("chấm test: hạng của A (bỏ D, E)", int(r["rank"][0]), 3)
check("chấm test: top-3", r["top"][0].tolist(), [B, Cc, A])
pu = E.per_user_metrics(r["rank"], r["top"], sp_test.pos, k_list=[2, 3])
check("Hit@2", float(pu["hit@2"][0]), 0.0)
check("Recall@2", float(pu["recall@2"][0]), 0.0)
check("Hit@3", float(pu["hit@3"][0]), 1.0)
check("Recall@3", float(pu["recall@3"][0]), 1.0)
check("NDCG@3 = 1/log2(4)", float(pu["ndcg@3"][0]), 0.5)
sp_val = E.make_split("val", {1: {D}}, {1: Ee})
r = fr(S1, sp_val, range(5), 3, [1, 2, 3])
check("chấm val (target E, chỉ bỏ D): hạng của E", int(r["rank"][0]), 4)
check("chấm val: top-3 không có D", r["top"][0].tolist(), [B, Cc, A])
sp_test_nov = E.make_split("test", {1: {D}}, {1: A})
r = fr(S1, sp_test_nov, range(5), 3, [1, 2, 3])
check("(đối chiếu) nếu KHÔNG bỏ item val: hạng của A vẫn 3 vì E điểm thấp", int(r["rank"][0]), 3)
S1b = {1: [0.7, 0.9, 0.8, 1.0, 0.95]}                    # E (val) điểm cao: bỏ hay không làm đổi hạng
r1 = fr(S1b, sp_test, range(5), 3, [1, 2, 3])
r2 = fr(S1b, sp_test_nov, range(5), 3, [1, 2, 3])
check("E điểm 0,95: bỏ item val -> hạng A = 3, top không có E", (int(r1["rank"][0]), Ee in r1["top"][0]), (3, False))
check("E điểm 0,95: không bỏ item val -> hạng A = 4", int(r2["rank"][0]), 4)
try:
    E.make_split("test", {1: {D}}, {1: D})
    check("item cần đoán nằm trong train phải báo lỗi", "không báo", "báo lỗi")
except AssertionError:
    check("item cần đoán nằm trong train phải báo lỗi", "báo lỗi", "báo lỗi")

print("\n=== B. Quy tắc hòa theo π ===")
pi = [2, 0, 1, 3]                                         # π(0) = 2, π(1) = 0, π(2) = 1
S2 = {u: [1.0, 1.0, 1.0, 0.5] for u in (10, 11, 12)}
sp = E.make_split("val", {}, {10: 0, 11: 1, 12: 2})
r = fr(S2, sp, pi, 3, [1, 2, 3])
check("hạng của 0, 1, 2 (cùng điểm 1,0; π = 2, 0, 1)", r["rank"].tolist(), [3, 1, 2])
check("top-3 = thứ tự π tăng: 1, 2, 0", r["top"][0].tolist(), [1, 2, 0])
check("số ứng viên hòa điểm với item cần đoán", r["n_tie"].tolist(), [2, 2, 2])
r = fr(S2, sp, [0, 1, 2, 3], 3, [1, 2, 3])
check("đổi π = thứ tự tự nhiên -> hạng 1, 2, 3", r["rank"].tolist(), [1, 2, 3])
pi_real = E.tie_keys()
check("π thật là hoán vị của 0..N_ITEMS-1", sorted(pi_real.tolist()) == list(range(C.N_ITEMS)), True)
check("π thật cố định (seed 20261009, gọi 2 lần như nhau)", bool(np.array_equal(pi_real, E.tie_keys())), True)

print("\n=== C. Train / val không vào top-K; ứng viên −∞ trước sản phẩm không phải ứng viên ===")
S3 = {20: [9, 8, 7, 1, 2, 3, 4, 5]}                       # train {0, 1}, val 2 có điểm cao nhất
r = fr(S3, E.make_split("test", {20: {0, 1}}, {20: 5}, val={20: 2}), range(8), 3, [1, 2, 3])
check("chấm test: top-3 không chứa 0, 1 (train), 2 (val)", r["top"][0].tolist(), [7, 6, 5])
r = fr(S3, E.make_split("val", {20: {0, 1}}, {20: 2}), range(8), 3, [1, 2, 3])
check("chấm val: top-3 = 2, 7, 6 (không chứa train)", r["top"][0].tolist(), [2, 7, 6])
inf = float("inf")
S4 = {21: [5, -inf, -inf, 9, 9, 9]}                       # chỉ 0..2 là ứng viên (ống), 1 và 2 bị lọc −∞
cand = np.array([1, 1, 1, 0, 0, 0], bool)
r = fr(S4, E.make_split("val", {}, {21: 2}), [5, 4, 3, 2, 1, 0], 3, [1, 2, 3], cand=cand)
check("chỉ ống: top-3 = 0, rồi 2, 1 theo π (không lẫn 3, 4, 5 dù điểm 9)", r["top"][0].tolist(), [0, 2, 1])
check("chỉ ống: hạng của ống 2 bị lọc −∞ = 2", int(r["rank"][0]), 2)

print("\n=== D. Bộ lọc MountAware ===")
D3200, FM10, EF, DX, ACC, UNC, SE, NOMOUNT, BODY_X, T6S = range(10)
ctx = C.CvrContext(lenses_in_m={EF, DX, SE}, bodies_in_m={D3200, FM10, T6S},
                   m1={(D3200, DX), (T6S, EF)}, unknown={(FM10, DX)})
bodies = {0: {D3200}, 1: {D3200, FM10}, 2: {FM10}, 3: {T6S, FM10}, 4: {BODY_X}, 5: {D3200, BODY_X}}
lens_cols, mask = E.certain_violation_mask(bodies, ctx, n_users=7)
check("cột của mặt nạ = ống trong M", lens_cols.tolist(), [EF, DX, SE])
want = {0: [True, False, True], 1: [True, False, True], 2: [True, False, True], 3: [False, False, True],
        4: [False, False, False], 5: [False, False, False], 6: [False, False, False]}
for u in range(7):
    check(f"u{u} {sorted(bodies.get(u, []))}: ống bị lọc (EF, DX, SE)", mask[u].tolist(), want[u])
    check(f"u{u}: mặt nạ = judge_lens is True", mask[u].tolist(),
          [C.judge_lens(int(l), bodies.get(u, set()), ctx) is True for l in lens_cols])

t = time.time()
item_type = C.load_item_type()
train = C.load_train()
rctx = C.load_cvr_context()
rb = C.build_train_bodies(train, None, item_type)
lens_cols, mask = E.certain_violation_mask(rb, rctx)
n_diff = 0
n_true = 0
for u, bs in rb.items():
    j = np.array([C.judge_lens(int(l), bs, rctx) is True for l in lens_cols])
    n_diff += int((j != mask[u]).sum())
    n_true += int(j.sum())
no_body = np.setdiff1d(np.arange(C.N_USERS), np.fromiter(rb, int))
check(f"dữ liệu thật: {len(rb):,} người có thân × {len(lens_cols):,} ống, số ô mặt nạ ≠ judge_lens", n_diff, 0)
print(f"    (số cặp (người, ống) chắc chắn vi phạm: {n_true:,}; {time.time() - t:.0f}s)")
check("dữ liệu thật: người không có thân không bị lọc ống nào", int(mask[no_body].sum()), 0)

print("\n=== E. Recall = Hit từng người ===")
try:
    E.per_user_metrics(np.array([3]), np.array([[1, 2, 9]]), np.array([0]), k_list=[3])
    check("hạng 3 nhưng item không nằm trong top-3 phải báo lỗi", "không báo", "báo lỗi")
except AssertionError:
    check("hạng 3 nhưng item không nằm trong top-3 phải báo lỗi", "báo lỗi", "báo lỗi")

print("\n=== F. CVR từ top-K = common_05.full_catalog_cvr (ví dụ test_cvr.py) ===")
itype = np.array([0, 0, 1, 1, 2, 1, 1, 1, 0, 0])
S = {1: [0, 0, 9, 8, 7, 0, 0, 0, 0, 0], 2: [0, 0, 9, 99, 7, 8, 0, 0, 0, 0], 3: [0, 0, 0, 9, 0, 8, 0, 7, 0, 0],
     4: [0, 0, 9, 7, 0, 0, 8, 0, 0, 0], 5: [0, 0, 0, 9, 8, 0, 0, 7, 0, 0], 6: [0, 0, 0, 0, 9, 0, 0, 0, 0, 0]}
tr = {1: {D3200, FM10}, 2: {D3200, DX}, 3: {FM10}, 4: {BODY_X}, 5: {T6S, FM10}, 6: {ACC}}
cu = C.build_train_bodies(tr, None, itype)
old = C.full_catalog_cvr(lambda u: np.array(S[u], dtype=float), cu, tr, None, itype, k_list=[2, 3], ctx=ctx)
sp = E.make_split("val", tr, {u: max(set(range(10)) - tr[u]) for u in tr})
r = fr(S, sp, range(10), 3, [])
new, per = E.cvr_from_top(sp.users, r["top"], cu, itype, ctx, k_list=[2, 3])
check("cvr_from_top = full_catalog_cvr (mọi khóa, K = 2, 3)", new, old)
check("CVR@3 = 2/3 (micro), 2 người được tính", (new["cvr@3"], new["cvr_n_users@3"]), (2 / 3, 2))

print("\n=== G. Nhóm kịch bản ===")
users = np.array([0, 1, 2, 3, 4, 6])
pos = np.array([EF, DX, DX, DX, EF, EF])
bd = {0: {D3200}, 1: {D3200, FM10}, 2: {FM10}, 3: {T6S, FM10}, 4: {D3200}}
lab, adp = E.scenario_groups(users, pos, bd, itype, ctx, adapter={(D3200, EF)})
check("nhãn kịch bản", lab.tolist(), ["khong_lap_duoc", "lap_duoc", "khong_phan_duoc", "khong_phan_duoc",
                                      "khong_lap_duoc", ""])
check("cặp requires_adapter trong nhóm không lắp được", adp.tolist(), [True, False, False, False, True, False])
lab2, _ = E.scenario_groups(np.array([0, 0]), np.array([UNC, ACC]), bd, itype, ctx)
check("item là ống ngoài M / phụ kiện -> ngoài kịch bản", lab2.tolist(), ["", ""])

print("\n=== H. Sampled 1+99: âm mẫu bằng điểm xếp trên ===")
S5 = {30: [1.0, 1.0, 0.5, 2.0]}
sp = E.make_split("val", {}, {30: 0})
check("điểm item 1,0; âm mẫu 1,0 / 0,5 / 2,0 -> hạng 3", int(E.sampled_rank(scorer(S5), sp, {30: [1, 2, 3]})[0]), 3)

print("\n=== I. Bootstrap ghép cặp ===")
rng = np.random.default_rng(0)
h = (rng.random(5000) < 0.3).astype(float)
num = rng.integers(0, 3, 5000)
den = num + rng.integers(0, 3, 5000)
bs = E.bootstrap_paired({"a": (h, None), "b": (h.copy(), None), "ca": (num, den), "cb": (num.copy(), den.copy())},
                        pairs=[("a", "b"), ("ca", "cb")], B=500, chunk=100)
check("hai mô hình giống hệt: hiệu (điểm, thấp, cao) = 0", bs["a - b"], (0.0, 0.0, 0.0))
check("tỷ số giống hệt: hiệu = 0", bs["ca - cb"], (0.0, 0.0, 0.0))
check("khoảng của a chứa giá trị điểm", bs["a"][1] <= bs["a"][0] <= bs["a"][2], True)
check("giá trị điểm của tỷ số = tổng tử / tổng mẫu", bs["ca"][0], float(num.sum() / den.sum()))

print(f"\n{'ĐẠT CẢ' if fails == 0 else f'SAI {fails}'}")
sys.exit(1 if fails else 0)
