"""
Báo kết quả eval_external.py tách theo 2 nửa của eval_split.csv (QĐ 13).

  fix     : được xem ca sai để sửa quy tắc.
  holdout : chỉ in SỐ TỔNG, và chỉ khi có cờ --holdout (chấm một lần, sau khi đã chốt quy tắc).
            Script KHÔNG có chế độ in ca sai của holdout.

Chạy:
  ai\\.venv\\Scripts\\python.exe ai/survey/content3/eval_split_report.py                 # bảng nửa fix
  ai\\.venv\\Scripts\\python.exe ai/survey/content3/eval_split_report.py --errors        # + ca sai loại của nửa fix
  ai\\.venv\\Scripts\\python.exe ai/survey/content3/eval_split_report.py --holdout       # + bảng nửa holdout
  --matches <csv> để chấm một file kết quả khác (vd bản trước khi sửa).
"""
import argparse, csv, collections, sys
sys.stdout.reconfigure(encoding="utf-8")

SPLIT = "ai/survey/content3/eval_split.csv"


def pct(a, b):
    return f"{a}/{b} = {a / b * 100:.1f}%" if b else "-"


def table(rows, title):
    print(f"\n=== {title} ===")
    print(f"{'nguồn':9} | {'khớp':>5} | {'loại đúng':>18} | {'ngàm: đúng/gán':>18} (trống) | {'khung thân: đúng/gán':>20} (trống)")
    by_src = collections.defaultdict(list)
    for r in rows:
        by_src[r["nguon"]].append(r)
    for s in ["lensfun", "openmvg", "wikidata"]:
        rs = by_src.get(s, [])
        lt = [r for r in rs if r["loai_dung"] != ""]
        ld = sum(int(r["loai_dung"]) for r in lt)
        ng = [r for r in rs if r["ngam_dung"] in ("0", "1")]
        nb = sum(r["ngam_dung"] == "bo_trong" for r in rs)
        kg = [r for r in rs if r["khung_dung"] in ("0", "1")]
        kb = sum(r["khung_dung"] == "bo_trong" for r in rs)
        print(f"{s:9} | {len(rs):5} | {pct(ld, len(lt)):>18} | {pct(sum(r['ngam_dung'] == '1' for r in ng), len(ng)):>18} ({nb:3}) "
              f"| {pct(sum(r['khung_dung'] == '1' for r in kg), len(kg)):>20} ({kb:3})")
    # theo sản phẩm: loại đúng nếu đúng ở MỌI nguồn có đáp án loại
    per = collections.defaultdict(list)
    for r in rows:
        if r["loai_dung"] != "":
            per[r["parent_asin"]].append(int(r["loai_dung"]))
    ok = sum(all(v) for v in per.values())
    print(f"theo sản phẩm (đúng ở mọi nguồn có đáp án loại): {pct(ok, len(per))}")
    conf = collections.Counter()
    seen = set()
    for r in rows:
        if r["loai_dap_an"] and r["parent_asin"] not in seen:
            seen.add(r["parent_asin"])
            conf[(r["loai_dap_an"], r["loai_quy_tac"])] += 1
    print("bảng nhầm loại (đáp án -> quy tắc), mỗi sản phẩm 1 lần, nguồn đầu tiên:")
    for (a, q), n in sorted(conf.items()):
        print(f"   {a:5} -> {q:9}: {n}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", default="ai/data/survey/eval_external_matches.csv")
    ap.add_argument("--errors", action="store_true", help="in ca sai loại / ngàm / khung của nửa FIX")
    ap.add_argument("--holdout", action="store_true", help="in bảng số tổng của nửa HOLDOUT (chấm một lần)")
    args = ap.parse_args()
    half = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open(SPLIT, encoding="utf-8"))}
    rows = list(csv.DictReader(open(args.matches, encoding="utf-8-sig")))
    missing = {r["parent_asin"] for r in rows} - set(half)
    assert not missing, f"{len(missing)} sản phẩm khớp được nhưng không có trong {SPLIT}"
    print(f"file: {args.matches} | {len({r['parent_asin'] for r in rows})} sản phẩm khớp được")
    fix = [r for r in rows if half[r["parent_asin"]] == "fix"]
    table(fix, f"NỬA FIX ({len({r['parent_asin'] for r in fix})} sản phẩm)")
    if args.errors:
        print("\n--- ca sai của nửa FIX ---")
        for r in sorted(fix, key=lambda r: (r["loai_dap_an"], r["loai_quy_tac"], r["parent_asin"], r["nguon"])):
            bad = [k for k in ("loai_dung", "ngam_dung", "khung_dung") if r[k] == "0"]
            if bad:
                print(f"{r['nguon'][:4]} {r['parent_asin']} sai={','.join(b[:-5] for b in bad)} | đáp án {r['loai_dap_an']}/"
                      f"{r['ngam_dap_an']}/{r['khung_dap_an']} | quy tắc {r['loai_quy_tac']}/{r['ngam_quy_tac']}/"
                      f"{r['khung_quy_tac']} | {r['title'][:110]} || {r['ten_nguon']}")
    if args.holdout:
        ho = [r for r in rows if half[r["parent_asin"]] == "holdout"]
        table(ho, f"NỬA HOLDOUT ({len({r['parent_asin'] for r in ho})} sản phẩm)")


if __name__ == "__main__":
    main()
