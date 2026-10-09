"""
So hai file kết quả của eval_external.py (vd bộ đánh giá lan2 và lan3) theo từng (nguồn, sản phẩm).
CHỈ dùng cho file của nửa FIX (kiểm tra: dừng nếu có sản phẩm thuộc holdout).

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content3/compare_eval_modes.py A.csv B.csv [--nhan-a lan2 --nhan-b lan3]
In: (1) có giống hệt không (bỏ qua cột cum_nguon và ten_nguon nếu chỉ một bên có / do thứ tự set);
    (2) sản phẩm chỉ có ở một bên; (3) sản phẩm đổi đáp án / đổi ô chấm; (4) bảng số của mỗi bên.
"""
import argparse, csv, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
SPLIT = "ai/survey/content3/eval_split.csv"
KEYS = ["loai_khop", "loai_dap_an", "ngam_dap_an", "khung_dap_an", "loai_dung", "ngam_dung", "khung_dung",
        "loai_quy_tac", "ngam_quy_tac", "khung_quy_tac"]


def load(p):
    return {(r["nguon"], r["parent_asin"]): r for r in csv.DictReader(open(p, encoding="utf-8-sig"))}


def counts(rows):
    out = {}
    for s in ("lensfun", "openmvg", "wikidata"):
        rs = [r for (src, _), r in rows.items() if src == s]
        f = lambda col, v: sum(r[col] == v for r in rs)
        out[s] = dict(khop=len(rs), loai=f"{f('loai_dung', '1')}/{f('loai_dung', '1') + f('loai_dung', '0')}",
                      ngam=f"{f('ngam_dung', '1')}/{f('ngam_dung', '1') + f('ngam_dung', '0')}",
                      khung=f"{f('khung_dung', '1')}/{f('khung_dung', '1') + f('khung_dung', '0')}",
                      ngam_khac_ngam=f("ngam_dung", "dap_an_khac_ngam"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--nhan-a", default="A"); ap.add_argument("--nhan-b", default="B")
    args = ap.parse_args()
    half = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open(SPLIT, encoding="utf-8"))}
    A, B = load(args.a), load(args.b)
    bad = {k[1] for k in list(A) + list(B) if half.get(k[1]) != "fix"}
    if bad:
        sys.exit(f"DỪNG: {len(bad)} sản phẩm không thuộc nửa fix trong file so sánh")
    na, nb = args.nhan_a, args.nhan_b
    print(f"{na}: {args.a} ({len(A)} dòng) | {nb}: {args.b} ({len(B)} dòng)")
    common_cols = [c for c in next(iter(A.values())).keys() if c in next(iter(B.values())) and c not in ("cum_nguon", "ten_nguon")]
    same = set(A) == set(B) and all(all(A[k][c] == B[k][c] for c in common_cols) for k in A)
    print(f"giống hệt trên các cột chung (trừ cum_nguon, ten_nguon): {same}")
    ten_khac = sum(A[k]["ten_nguon"] != B[k]["ten_nguon"] for k in set(A) & set(B))
    print(f"số dòng khác cột ten_nguon (tên hiển thị): {ten_khac}")
    for lab, only, src in ((f"chỉ có ở {na}", set(A) - set(B), A), (f"chỉ có ở {nb}", set(B) - set(A), B)):
        print(f"\n--- {lab}: {len(only)} dòng ---")
        for k in sorted(only):
            r = src[k]
            print(f"  {k[0][:4]} {k[1]} {r['loai_khop']:8} đáp án {r['loai_dap_an']}/{r['ngam_dap_an']} | quy tắc "
                  f"{r['loai_quy_tac']}/{r['ngam_quy_tac']} | loai_dung={r['loai_dung']} ngam_dung={r['ngam_dung']} | "
                  f"{r['title'][:90]} || {r['ten_nguon']}")
    ch = [k for k in sorted(set(A) & set(B)) if any(A[k][c] != B[k][c] for c in KEYS)]
    print(f"\n--- đổi đáp án hoặc ô chấm: {len(ch)} dòng ---")
    for k in ch:
        diff = ", ".join(f"{c}: {A[k][c]!r} -> {B[k][c]!r}" for c in KEYS if A[k][c] != B[k][c])
        print(f"  {k[0][:4]} {k[1]} | {diff} | {A[k]['title'][:80]} || {A[k]['ten_nguon']} -> {B[k]['ten_nguon']}")
    print("\n--- số đúng/chấm theo nguồn ---")
    ca, cb = counts(A), counts(B)
    for s in ca:
        print(f"  {s:9} {na}: {ca[s]} \n  {'':9} {nb}: {cb[s]}")


if __name__ == "__main__":
    main()
