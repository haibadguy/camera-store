"""
Nội dung 4, việc 2: đo độ chính xác của bước đọc tiêu cự / khẩu độ từ tiêu đề ống (kế hoạch
docs/reviews/n4_focal_aperture_plan.md, mục 3–5). Đáp án và tập chia do fa_match.py sinh (cố định).

Hai bộ đọc được chấm trên cùng tập:
  cu  : eval_external.lens_sig(eval_external.head_main(tiêu đề))  — bộ đọc trước khi sửa (count_usecase bản đầu dùng)
  moi : ai/pipeline/lens_specs.read_title(tiêu đề)                — bộ đọc sau khi sửa theo nửa fix

Chỉ số (mỗi ô = (phép đo, nguồn, ống); đọc không ra = sai):
  Tiêu cự  T1 mm đúng       : (f1, f2) đọc được = đáp án
           T2 khoảng nút đúng: tập khoảng tiêu cự (6 khoảng, lens_specs.focal_nodes) = tập của đáp án
  Khẩu độ  K1 số f đúng     : (a1, a2) đọc được = đáp án
           K2 khoảng nút đúng: khoảng khẩu độ (5 khoảng, lens_specs.aperture_node, theo a1) = của đáp án
           phụ: K3 a1 đúng; K4 khẩu độ đầu tele (a2, không có thì a1) đúng — luật chân dung dùng số này
  Theo ống (tiêu cự): đúng khi đúng ở MỌI nguồn có đáp án.
Khoảng tin cậy: bootstrap theo cụm (ai/survey/content3/bootstrap_ci.py: B = 10.000, seed 20261009, phân vị 2,5–97,5 %).
  Cụm của ô = (nguồn, cum_nguon); cụm của ống = cụm Lensfun nếu có, không thì Wikidata.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/fa_eval.py --half fix --out-csv <file mới>.csv [--liet-ke]
  --liet-ke chỉ dùng được với --half fix (in từng ca lệch). Với holdout, script chỉ in số; file CSV có từng ô.
"""
import argparse, collections, csv, os, sys

sys.path.insert(0, "ai/survey/content3")
sys.path.insert(0, "ai/pipeline")
sys.stdout.reconfigure(encoding="utf-8")
import eval_external as ev  # noqa: E402
import lens_specs as ls  # noqa: E402
from bootstrap_ci import cluster_ci  # noqa: E402

KEY = "ai/survey/content4/fa_answer_key.csv"
SPLIT = "ai/survey/content4/fa_split.csv"
ATTRS = "ai/data/kg/item_attributes.csv"


def fl(x):
    return float(x) if x not in (None, "") else None


def read_cu(title):
    s = ev.lens_sig(ev.head_main(title))
    return tuple(fl(x) for x in s) if s else None


def read_moi(title):
    return ls.read_title(title)


READERS = {"cu": read_cu, "moi": read_moi}


def fmt(v):
    return "-" if v is None else "/".join("" if x is None else f"{x:g}" for x in v)


def score(r, rd):
    """Chấm một ô với kết quả đọc rd = (f1, f2, a1, a2) hoặc None."""
    t = (fl(r["dap_an_1"]), fl(r["dap_an_2"]))
    if r["phep_do"] == "tieu_cu":
        if rd is None:
            return dict(T1=0, T2=0), None
        got = (rd[0], rd[1])
        return dict(T1=int(got == t), T2=int(ls.focal_nodes(*got) == ls.focal_nodes(*t))), got
    if rd is None:
        return dict(K1=0, K2=0, K3=0, K4=0), None
    got = (rd[2], rd[3])
    return dict(K1=int(got == t), K2=int(ls.aperture_node(got[0]) == ls.aperture_node(t[0])),
                K3=int(got[0] == t[0]), K4=int((got[1] or got[0]) == (t[1] or t[0]))), got


def pct(c):
    if not c["mau"]:
        return "—"
    s = f"{c['tu']}/{c['mau']} = {100 * c['ty_le']:.1f}%"
    if c["lo"] is not None:
        s += f" [{100 * c['lo']:.1f}–{100 * c['hi']:.1f}]"
    return s + f" (cụm {c['so_cum']}{', ít mẫu' if c['mau'] < 10 else ''}{', bỏ ' + str(c['bo_lan']) + ' lần' if c['bo_lan'] else ''})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--half", required=True, choices=["fix", "holdout"])
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--liet-ke", action="store_true")
    a = ap.parse_args()
    if a.liet_ke and a.half != "fix":
        sys.exit("DỪNG: --liet-ke chỉ dùng cho nửa fix")
    if os.path.exists(a.out_csv):
        sys.exit(f"DỪNG: {a.out_csv} đã có, không ghi đè")

    print(f"Bộ đọc mới: lens_specs.READER_VERSION = {ls.READER_VERSION}")
    # Kiểm: số ống mà hai bộ đọc cho kết quả khác nhau (trên mọi ống, không cần đáp án)
    lenses = [x for x in csv.DictReader(open(ATTRS, encoding="utf-8")) if x["item_type"] == "ong"]
    diff = [x for x in lenses if read_cu(x["title"]) != read_moi(x["title"])]
    print(f"Ống (item_type = ong): {len(lenses)}; đọc được (cũ / mới): "
          f"{sum(read_cu(x['title']) is not None for x in lenses)} / {sum(read_moi(x['title']) is not None for x in lenses)}; "
          f"hai bộ đọc khác nhau ở {len(diff)} ống")

    half = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open(SPLIT, encoding="utf-8"))}
    rows = [r for r in csv.DictReader(open(KEY, encoding="utf-8")) if half[r["parent_asin"]] == a.half]
    print(f"Nửa {a.half}: {len(rows)} ô, {len({r['parent_asin'] for r in rows})} ống")

    # Kiểm đáp án (không phụ thuộc bộ đọc): ô có a2 >= 11 (dấu hiệu dải khẩu độ max-min), f2 <= f1
    odd = sum(1 for r in rows if r["phep_do"] == "khau_do" and fl(r["dap_an_2"]) and fl(r["dap_an_2"]) >= 11)
    odd += sum(1 for r in rows if r["phep_do"] == "tieu_cu" and fl(r["dap_an_2"]) and fl(r["dap_an_2"]) <= fl(r["dap_an_1"]))
    print(f"Đáp án bất thường (khẩu độ a2 >= 11 hoặc f2 <= f1): {odd}")
    both = collections.defaultdict(dict)
    for r in rows:
        if r["phep_do"] == "tieu_cu":
            both[r["parent_asin"]][r["nguon"]] = (r["dap_an_1"], r["dap_an_2"])
    bb = [v for v in both.values() if len(v) == 2]
    print(f"Ống có đáp án tiêu cự từ cả Lensfun và Wikidata: {len(bb)}; hai đáp án trùng: "
          f"{sum(v['lensfun'] == v['wikidata'] for v in bb)}")

    out = []
    for r in rows:
        rec = dict(r)
        for name, fn in READERS.items():
            sc, got = score(r, fn(r["tieu_de"]))
            rec[f"doc_{name}"] = fmt(got)
            for k, v in sc.items():
                rec[f"{k}_{name}"] = v
        out.append(rec)

    metrics = [("tieu_cu", "T1", "mm đúng"), ("tieu_cu", "T2", "khoảng nút đúng"),
               ("khau_do", "K1", "số f đúng (a1, a2)"), ("khau_do", "K2", "khoảng nút đúng"),
               ("khau_do", "K3", "[phụ] a1 đúng"), ("khau_do", "K4", "[phụ] khẩu độ đầu tele đúng")]
    for name in READERS:
        print(f"\n=== Bộ đọc '{name}' — nửa {a.half} ===")
        for phep, k, label in metrics:
            for nguon in ("lensfun", "wikidata"):
                units = [((r["nguon"], r["cum_nguon"]), r[f"{k}_{name}"], 1) for r in out
                         if r["phep_do"] == phep and r["nguon"] == nguon]
                if units:
                    print(f"  {k} {label:30s} {nguon:9s} {pct(cluster_ci(units))}")
            if phep == "tieu_cu":
                per = collections.defaultdict(list)
                for r in out:
                    if r["phep_do"] == "tieu_cu":
                        per[r["parent_asin"]].append(r)
                units = []
                for asin, rs in per.items():
                    src = {r["nguon"]: r for r in rs}
                    c = src.get("lensfun") or src["wikidata"]
                    units.append(((c["nguon"], c["cum_nguon"]), int(all(r[f"{k}_{name}"] for r in rs)), 1))
                print(f"  {k} {label:30s} {'theo ống':9s} {pct(cluster_ci(units))}")
        nn = sum(1 for r in out if r[f"doc_{name}"] == "-")
        print(f"  ô mà bộ đọc không đọc ra: {nn}")

    fields = list(dict.fromkeys(k for r in out for k in r))
    with open(a.out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    print(f"\nĐã ghi {a.out_csv} ({len(out)} ô)")

    if a.liet_ke:
        print("\n=== Ca lệch (bộ đọc 'moi', ít nhất một chỉ số chính sai) ===")
        bad = [r for r in out if any(r.get(f"{k}_moi") == 0 for k in ("T1", "T2", "K1", "K2"))]
        for r in sorted(bad, key=lambda r: (r["phep_do"], r["nguon"], r["parent_asin"])):
            t = (fl(r["dap_an_1"]), fl(r["dap_an_2"]))
            ks = [k for k in ("T1", "T2", "K1", "K2", "K3", "K4") if r.get(f"{k}_moi") == 0]
            print(f"{r['phep_do']:7s} {r['nguon']:8s} {r['parent_asin']} sai {','.join(ks):11s} đáp án {fmt(t):12s} "
                  f"đọc {r['doc_moi']:14s} | nguồn: {r['ten_nguon']} | tiêu đề: {r['tieu_de'][:150]}")
        print(f"Tổng: {len(bad)} ô")


if __name__ == "__main__":
    main()
