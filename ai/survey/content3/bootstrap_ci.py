"""
Khoảng tin cậy bootstrap theo cụm (kế hoạch đo lần 3 của nội dung 3, mục 5.6 và 9.6; thay cho Wilson, Red Team T6).

Ví dụ: 7 listing của Canon EF 75-300 III khớp cùng một mục Lensfun -> cùng một cụm. Khi lấy lại mẫu, cả 7 listing
được lấy (hoặc bỏ) cùng nhau, nên khoảng tin cậy không hẹp giả tạo như khi coi 7 listing là 7 mẫu độc lập.

Cách tính: mỗi đơn vị (ô chấm hoặc sản phẩm) có (cụm, tử, mẫu). Cộng tử và mẫu theo cụm. Lấy lại C cụm có hoàn lại
(C = số cụm), B = 10.000 lần, tỉ lệ của mỗi lần = tổng tử / tổng mẫu. Khoảng = phân vị 2,5 % và 97,5 % (numpy, nội suy
tuyến tính). Lần nào có tổng mẫu = 0 thì bỏ và báo số lần bị bỏ. Mỗi chỉ số dùng bộ sinh số mới cùng seed 20261009, cụm
sắp theo tên, nên kết quả không phụ thuộc thứ tự tính.

Chạy thử: ai\\.venv\\Scripts\\python.exe ai/survey/content3/bootstrap_ci.py
"""
import collections
import numpy as np

B = 10_000
SEED = 20261009


def cluster_ci(units, b=B, seed=SEED):
    """units: các bộ (cụm, tử, mẫu). Trả về dict(tu, mau, ty_le, lo, hi, so_cum, bo_lan)."""
    agg = collections.defaultdict(lambda: [0, 0])
    for c, t, m in units:
        agg[c][0] += t
        agg[c][1] += m
    tu = sum(a[0] for a in agg.values())
    mau = sum(a[1] for a in agg.values())
    out = dict(tu=tu, mau=mau, ty_le=(tu / mau if mau else None), lo=None, hi=None, so_cum=len(agg), bo_lan=0)
    if mau == 0:
        return out
    keys = sorted(agg)
    num = np.array([agg[k][0] for k in keys], dtype=float)
    den = np.array([agg[k][1] for k in keys], dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(keys), size=(b, len(keys)))
    n, d = num[idx].sum(axis=1), den[idx].sum(axis=1)
    ok = d > 0
    lo, hi = np.percentile(n[ok] / d[ok], [2.5, 97.5])
    out.update(lo=float(lo), hi=float(hi), bo_lan=int(b - ok.sum()))
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    fails = 0

    def check(name, cond):
        global fails
        fails += not cond
        print(f"{'OK ' if cond else 'SAI'} {name}")

    r = cluster_ci([(f"c{i}", 1, 1) for i in range(50)])
    check(f"đúng hết -> khoảng [1, 1]: {r}", r["lo"] == 1.0 and r["hi"] == 1.0)
    # 90 cụm đúng + 10 cụm sai, mỗi cụm 1 ô  vs  cùng 100 ô nhưng gộp thành 10 cụm 10 ô (1 cụm sai hết)
    a = cluster_ci([(f"c{i}", int(i >= 10), 1) for i in range(100)])
    g = cluster_ci([(f"c{i // 10}", int(i >= 10), 1) for i in range(100)])
    check(f"cùng tỉ lệ 0,9: {a['ty_le']} = {g['ty_le']}", a["ty_le"] == g["ty_le"] == 0.9)
    check(f"gộp cụm -> khoảng rộng hơn: {a['hi'] - a['lo']:.3f} < {g['hi'] - g['lo']:.3f}",
          (a["hi"] - a["lo"]) < (g["hi"] - g["lo"]))
    r1 = cluster_ci([("b", 1, 1), ("a", 0, 1), ("c", 1, 1)])
    r2 = cluster_ci([("c", 1, 1), ("a", 0, 1), ("b", 1, 1)])
    check(f"không phụ thuộc thứ tự: {r1} = {r2}", r1 == r2)
    r = cluster_ci([("a", 1, 1), ("b", 0, 0)])
    check(f"có cụm mẫu 0 -> có lần bị bỏ: bo_lan={r['bo_lan']}", r["bo_lan"] > 0)
    check("mẫu 0 -> không có khoảng", cluster_ci([])["lo"] is None)
    print("TẤT CẢ ĐÚNG" if not fails else f"{fails} CA SAI")
    sys.exit(1 if fails else 0)
