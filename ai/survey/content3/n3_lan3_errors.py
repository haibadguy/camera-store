"""
Ca sai của holdout ở lần đo 3 (nội dung 3), CHỈ để phân loại cho báo cáo (kế hoạch lần 3, mục 9.8).
Không sửa quy tắc, không sửa bộ đánh giá theo các ca này.

  --in : in mọi ô sai (loại / ngàm / khung) của bộ đánh giá chính (lan2) trên H747, kèm cờ thuộc H733;
         in thêm khác biệt từng dòng giữa lần đo 2 và lan2, giữa lan2 và lan3 (để kiểm lời giải thích trong CHANGELOG).
  --dem <csv> : đếm bảng phân loại (do Claude điền tay) theo ô / tập / nhóm; kiểm bảng phủ đúng mọi ô sai.

Chạy:
  ai\\.venv\\Scripts\\python.exe ai/survey/content3/n3_lan3_errors.py --in
  ai\\.venv\\Scripts\\python.exe ai/survey/content3/n3_lan3_errors.py --dem ai/survey/content3/n3_lan3_holdout_errors.csv
"""
import argparse, csv, collections, sys
sys.stdout.reconfigure(encoding="utf-8")

D = "ai/data/survey/n3_lan3/"
LAN2, LAN3 = D + "holdout_lan2_20261008.csv", D + "holdout_lan3_20261008.csv"
LAN_DO_2 = "ai/data/survey/eval_external_matches.csv"
SPLIT = "ai/survey/content3/eval_split.csv"
DEV = "ai/survey/content3/label_dev_50.csv"
KEYS = ["loai_khop", "loai_dap_an", "ngam_dap_an", "khung_dap_an", "loai_dung", "ngam_dung", "khung_dung",
        "loai_quy_tac", "ngam_quy_tac", "khung_quy_tac"]
CLASSES = ("dap_an_sai", "quy_tac_sai", "ca_hai_sai", "khong_ro")


def load(p, keep):
    return {(r["nguon"], r["parent_asin"]): r for r in csv.DictReader(open(p, encoding="utf-8-sig"))
            if r["parent_asin"] in keep}


def errors(rows):
    out = []
    for k, r in sorted(rows.items(), key=lambda kv: (kv[1]["parent_asin"], kv[0][0])):
        for o in ("loai", "ngam", "khung"):
            if r[f"{o}_dung"] == "0":
                out.append((k, o, r))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="show", action="store_true")
    ap.add_argument("--dem")
    a = ap.parse_args()
    half = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open(SPLIT, encoding="utf-8"))}
    ho = {p for p, h in half.items() if h == "holdout"}
    dev = {r["parent_asin"] for r in csv.DictReader(open(DEV, encoding="utf-8-sig"))} & ho
    l2 = load(LAN2, ho)
    errs = errors(l2)
    if a.show:
        print(f"ô sai của lan2 trên H747: {len(errs)} (thuộc H733: {sum(k[1] not in dev for k, _, _ in errs)})")
        for k, o, r in errs:
            print(f"{k[1]} {k[0][:4]} sai={o:5} H733={int(k[1] not in dev)} | đáp án {r['loai_dap_an']}/{r['ngam_dap_an']}/"
                  f"{r['khung_dap_an']} | quy tắc {r['loai_quy_tac']}/{r['ngam_quy_tac']}/{r['khung_quy_tac']} | "
                  f"{r['title'][:110]} || {r['ten_nguon']} | {r['cum_nguon']}")
        for na, A, nb, B in (("lan_do_2", load(LAN_DO_2, ho), "lan2", l2), ("lan2", l2, "lan3", load(LAN3, ho))):
            print(f"\n--- {na} -> {nb}: chỉ ở {na} {len(set(A) - set(B))}, chỉ ở {nb} {len(set(B) - set(A))} ---")
            for k in sorted(set(A) - set(B)):
                r = A[k]
                print(f"  bớt {k[0][:4]} {k[1]} loai_dung={r['loai_dung']} ngam_dung={r['ngam_dung']} "
                      f"khung_dung={r['khung_dung']} | {r['title'][:90]}")
            for k in sorted(set(B) - set(A)):
                print(f"  thêm {k[0][:4]} {k[1]} | {B[k]['title'][:90]}")
            ch = [k for k in sorted(set(A) & set(B)) if any(A[k][c] != B[k][c] for c in KEYS)]
            print(f"  đổi ô: {len(ch)} dòng")
            for k in ch:
                print(f"    {k[0][:4]} {k[1]} | " + ", ".join(f"{c}: {A[k][c]!r} -> {B[k][c]!r}" for c in KEYS
                                                       if A[k][c] != B[k][c]))
    if a.dem:
        rows = list(csv.DictReader(open(a.dem, encoding="utf-8-sig")))
        got = {(r["nguon"], r["parent_asin"], r["o_sai"]) for r in rows}
        want = {(k[0], k[1], o) for k, o, _ in errs}
        assert got == want, f"bảng phân loại không khớp ô sai: thiếu {want - got}, thừa {got - want}"
        bad = {r["phan_loai"] for r in rows} - set(CLASSES)
        assert not bad, f"nhóm lạ: {bad}"
        print(f"bảng {a.dem}: {len(rows)} ô sai, khớp đúng các ô sai của lan2 trên H747. "
              f"Người phân loại: {sorted({r['nguoi_phan_loai'] for r in rows})}")
        for tap, keep in (("H733", lambda r: r["thuoc_H733"] == "1"), ("H747", lambda r: True)):
            sub = [r for r in rows if keep(r)]
            print(f"\n=== {tap}: {len(sub)} ô sai, {len({r['parent_asin'] for r in sub})} sản phẩm ===")
            c = collections.Counter((r["o_sai"], r["nguon"], r["phan_loai"]) for r in sub)
            for o in ("loai", "ngam", "khung"):
                for s in ("lensfun", "openmvg", "wikidata"):
                    n = {k: c[(o, s, k)] for k in CLASSES}
                    if sum(n.values()):
                        print(f"  {o:5} {s:8}: " + ", ".join(f"{k} {v}" for k, v in n.items()))
            prod = collections.defaultdict(set)
            for r in sub:
                prod[r["parent_asin"]].add(r["phan_loai"])
            pc = collections.Counter("quy_tac_sai" if {"quy_tac_sai", "ca_hai_sai"} & v else
                                     "khong_ro" if "khong_ro" in v else "dap_an_sai" for v in prod.values())
            print(f"  theo sản phẩm (có ít nhất 1 ô quy tắc sai / ca hai sai -> tính 'quy tắc sai'): {dict(pc)}")
            lp = {r["parent_asin"] for r in sub if r["o_sai"] == "loai"}
            lq = {r["parent_asin"] for r in sub if r["o_sai"] == "loai" and r["phan_loai"] in ("quy_tac_sai", "ca_hai_sai")}
            print(f"  sản phẩm lệch về loại: {len(lp)}; trong đó do quy tắc (quy_tac_sai hoặc ca_hai_sai): {len(lq)}")


if __name__ == "__main__":
    main()
