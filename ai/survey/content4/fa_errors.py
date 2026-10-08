"""
Đếm bảng phân loại ca lệch của phép đo tiêu cự / khẩu độ (kế hoạch docs/reviews/n4_focal_aperture_plan.md, mục 7).
Bảng do Claude (người sửa bộ đọc) phân loại tay; script chỉ đếm và kiểm bảng có đủ mọi ô lệch của file đánh giá.

  phan_loai: dap_an_sai (khớp nhầm ống khác / nguồn thiếu, sai) | doc_sai (bộ đọc đọc sai tiêu đề) | ca_hai | khong_ro

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/fa_errors.py --bang <bảng phân loại>.csv --danh-gia <CSV của fa_eval>
"""
import argparse, collections, csv, sys

sys.stdout.reconfigure(encoding="utf-8")
MAIN = ("T1", "T2", "K1", "K2")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bang", required=True)
    ap.add_argument("--danh-gia", required=True)
    ap.add_argument("--bo-doc", default="moi", choices=["cu", "moi"])
    a = ap.parse_args()
    ev = list(csv.DictReader(open(a.danh_gia, encoding="utf-8")))
    bad = {(r["phep_do"], r["nguon"], r["parent_asin"]) for r in ev
           if any(r.get(f"{k}_{a.bo_doc}") == "0" for k in MAIN)}
    tab = list(csv.DictReader(open(a.bang, encoding="utf-8")))
    keys = {(r["phep_do"], r["nguon"], r["parent_asin"]) for r in tab}
    print(f"File đánh giá: {len(ev)} ô, lệch (bộ đọc '{a.bo_doc}', ít nhất một chỉ số chính sai): {len(bad)}")
    print(f"Bảng phân loại: {len(tab)} dòng; thiếu so với file đánh giá: {len(bad - keys)}; thừa: {len(keys - bad)}")
    if bad != keys:
        print("DỪNG: bảng phân loại không khớp tập ô lệch")
        sys.exit(2)
    total = collections.Counter((r["phep_do"], r["nguon"]) for r in ev)
    print("\nTheo phép đo, nguồn, phân loại:")
    for (p, n) in sorted(total):
        rs = [r for r in tab if (r["phep_do"], r["nguon"]) == (p, n)]
        c = collections.Counter(r["phan_loai"] for r in rs)
        print(f"  {p:8s} {n:9s} ô {total[(p, n)]:4d}, lệch {len(rs):3d}: " +
              ", ".join(f"{k} {v}" for k, v in sorted(c.items())))
        for k, v in sorted(collections.Counter((r["phan_loai"], r["chi_tiet"]) for r in rs).items()):
            print(f"      {k[0]:11s} {k[1]:26s} {v}")
    print("\nÔ do bộ đọc (doc_sai + ca_hai):")
    for r in tab:
        if r["phan_loai"] in ("doc_sai", "ca_hai"):
            print(f"  {r['phep_do']:8s} {r['nguon']:9s} {r['parent_asin']} {r['chi_tiet']}: {r['ly_do']}")
    # Số phụ (kế hoạch mục 9.2): tỉ lệ ô KHÔNG sai do bộ đọc = 1 - (doc_sai + ca_hai) / số ô; khong_ro tính là
    # không sai do bộ đọc ở số này, và đếm riêng. Bootstrap theo cụm như số chính.
    sys.path.insert(0, "ai/survey/content3")
    from bootstrap_ci import cluster_ci
    cls = {(r["phep_do"], r["nguon"], r["parent_asin"]): r["phan_loai"] for r in tab}
    print("\nSố phụ (không phải số chính; phân loại do người sửa bộ đọc làm): ô không sai do bộ đọc / số ô")
    for (p, n) in sorted(total):
        units = [((r["nguon"], r["cum_nguon"]),
                  int(cls.get((p, n, r["parent_asin"])) not in ("doc_sai", "ca_hai")), 1)
                 for r in ev if (r["phep_do"], r["nguon"]) == (p, n)]
        c = cluster_ci(units)
        k = sum(1 for r in tab if (r["phep_do"], r["nguon"]) == (p, n) and r["phan_loai"] == "khong_ro")
        print(f"  {p:8s} {n:9s} {c['tu']}/{c['mau']} = {100 * c['ty_le']:.1f}% [{100 * c['lo']:.1f}–{100 * c['hi']:.1f}] "
              f"(cụm {c['so_cum']}); trong đó khong_ro {k}")


if __name__ == "__main__":
    main()
