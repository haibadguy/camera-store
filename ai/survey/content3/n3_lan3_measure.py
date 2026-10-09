"""
Lần đo thứ 3 của nội dung 3: các phép đo (1)-(6) và tập N (kế hoạch docs/reviews/n3_eval_lan3_plan.md, mục 5, 8, 9).
Không chạy bộ đánh giá: chỉ đọc các file kết quả của eval_external.py (mỗi chế độ một file) và chấm lại / tổng hợp.

Phép đo:
  (1)(2) bảng số theo nguồn cho từng bộ đánh giá (lan2 = SỐ CHÍNH, lan3, truoc_0710, lần đo 2), trên tập đủ và tập bỏ dev
  (3)    độ chính xác ngàm theo mount_source (lan2, lan3)
  (4)    độ chính xác của việc vào M: phần tử của M có đáp án loại đúng là thân (hàng) / ống (cột)
  (5)    baseline B1 (bản của Hải) và B2 (Compatible Mountings) so với quy tắc, cùng cách so ngàm (H3 cho mọi phương pháp)
  (6)    khoảng bootstrap theo cụm (bootstrap_ci.py) cho mọi tỉ lệ
  N      sản phẩm ngoài 1.493 khớp được ở lan3 (H1): KHÔNG ĐỘC LẬP, CHỈ THAM KHẢO; tách phần máy phim

Chạy (đặt PYTHONHASHSEED=0):
  ai\\.venv\\Scripts\\python.exe ai/survey/content3/n3_lan3_measure.py --half holdout \\
      --lan2 <csv> --lan3 <csv> --truoc <csv> --lan-do-2 ai/data/survey/eval_external_matches.csv \\
      --ngoai-lan3 <csv> --ngoai-lan2 <csv> --out-csv <bảng số, tên mới>.csv
  Chạy thử trên nửa fix: --half fix ... --thu-ngoai-tu-fix (cho phép phần N đọc file của nửa fix, chỉ để thử code).
"""
import argparse, csv, collections, hashlib, json, re, sys
sys.path.insert(0, "ai/survey/content3")
sys.stdout.reconfigure(encoding="utf-8")
import eval_external as ev
import mountlex
from bootstrap_ci import cluster_ci, B, SEED

SPLIT = "ai/survey/content3/eval_split.csv"
DEV = "ai/survey/content3/label_dev_50.csv"
ATTR = "ai/data/kg/item_attributes.csv"
BIDX = "ai/data/kg/body_index.json"
LIDX = "ai/data/kg/lens_index.json"
HAI = "ai/data/kg_v62abf54/linked_products.csv"
HAI_MAP = "ai/data/processed_v62abf54/item_map.json"
SRCS = ("lensfun", "openmvg", "wikidata")

HAI_MOUNT = {"Canon EF": "canon_ef", "Canon RF": "canon_rf", "Nikon F": "nikon_f", "Nikon Z": "nikon_z",
             "Sony E": "sony_e", "Fujifilm X": "fuji_x", "Micro Four Thirds": "mft", "L-Mount": "l_mount"}
HAI_TYPE = {"Body": "than", "Lens": "ong"}
CM_MOUNT = {"Canon RF": "canon_rf", "Canon EF-M": "canon_efm", "Canon EF": "HO_EF", "Canon FD": "canon_fd",
            "Nikon Z": "nikon_z", "Nikon F": "nikon_f", "Nikon 1": "nikon_1", "Sony E": "sony_e", "Sony A": "sony_a",
            "Fujifilm X": "fuji_x", "Fujifilm G": "fuji_g", "Micro Four Thirds": "mft", "Four Thirds": "four_thirds",
            "L-Mount": "l_mount", "Leica M": "leica_m", "Pentax K": "pentax_k", "Pentax Q": "pentax_q",
            "Samsung NX": "samsung_nx", "Sigma SA": "sigma_sa", "M42": "m42", "T-Mount": "t_mount", "C-Mount": None}

OUT = []          # mọi chỉ số -> --out-csv
N_FALLBACK = collections.Counter()


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def single(m):
    return bool(m) and m not in ("khong_ro", "khong_co", "nhieu") and ">" not in m


def fam(m):
    return "ho_canon_ef" if m in ("canon_ef", "canon_efs", "HO_EF") else m


def cl(r):
    """Cụm của một ô = mã mục nguồn (cum_nguon); thiếu thì dùng (nguồn, sản phẩm) và đếm."""
    if r.get("cum_nguon"):
        return r["cum_nguon"]
    N_FALLBACK[r["nguon"]] += 1
    return f"{r['nguon']}:asin:{r['parent_asin']}"


def pct(x):
    return "-" if x is None else f"{x * 100:.1f}%"


def rec(phep_do, che_do, tap, nguon, chi_so, units, ci=True, chi_dem=False):
    units = list(units)
    res = cluster_ci(units) if ci else None
    if res is None:   # không có cụm (file lần đo 2): chỉ điểm
        t, m = sum(u[1] for u in units), sum(u[2] for u in units)
        res = dict(tu=t, mau=m, ty_le=(t / m if m else None), lo=None, hi=None, so_cum=None, bo_lan=None)
    row = dict(phep_do=phep_do, che_do=che_do, tap=tap, nguon=nguon, chi_so=chi_so, tu=res["tu"], mau=res["mau"],
               ty_le="" if res["ty_le"] is None else round(res["ty_le"], 6),
               ci_lo="" if (res["lo"] is None or chi_dem) else round(res["lo"], 6),
               ci_hi="" if (res["hi"] is None or chi_dem) else round(res["hi"], 6),
               so_cum="" if res["so_cum"] is None else res["so_cum"], bo_lan="" if res["bo_lan"] is None else res["bo_lan"])
    OUT.append(row)
    if chi_dem:
        s = f"{res['tu']}/{res['mau']} (dưới 10 ô: chỉ báo số đếm)"
    else:
        s = f"{res['tu']}/{res['mau']} = {pct(res['ty_le'])}"
        if res["lo"] is not None:
            s += f"  [{pct(res['lo'])} – {pct(res['hi'])}] ({res['so_cum']} cụm"
            s += f", bỏ {res['bo_lan']} lần)" if res["bo_lan"] else ")"
            if res["mau"] < 10:
                s += " (ít mẫu)"
    print(f"    {chi_so:44} {s}")
    return res


def cnt(phep_do, che_do, tap, nguon, chi_so, n):
    OUT.append(dict(phep_do=phep_do, che_do=che_do, tap=tap, nguon=nguon, chi_so=chi_so, tu=n, mau="", ty_le="",
                    ci_lo="", ci_hi="", so_cum="", bo_lan=""))
    print(f"    {chi_so:44} {n}")


def load_rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def product_cluster(rows, ck=None):
    """Cụm của sản phẩm (chỉ số gộp nguồn): theo Lensfun, không có thì Wikidata, rồi openMVG."""
    ck = ck or cl
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["parent_asin"]].setdefault(r["nguon"], r)
    out = {}
    for p, d in by.items():
        for s in ("lensfun", "wikidata", "openmvg"):
            if s in d:
                out[p] = ck(d[s])
                break
    return out


# ---------------------------------------------------------------- (1)(2)
def table1(rows, che_do, tap, tap_size, ci=True, phep_do="(1)"):
    prods = {r["parent_asin"] for r in rows}
    cl = globals()["cl"] if ci else (lambda r: "-")     # file không có cụm (lần đo 2): chỉ báo điểm
    print(f"\n  == {phep_do} bộ đánh giá {che_do} | tập {tap} ({tap_size} sản phẩm) ==")
    cnt(phep_do, che_do, tap, "", "so_san_pham_cua_tap", tap_size)
    cnt(phep_do, che_do, tap, "", "so_san_pham_khop_duoc", len(prods))
    cnt(phep_do, che_do, tap, "", "so_san_pham_khong_khop_duoc", tap_size - len(prods))
    for s in SRCS:
        rs = [r for r in rows if r["nguon"] == s]
        print(f"   [{s}]")
        cnt(phep_do, che_do, tap, s, "khop", len(rs))
        if s != "openmvg":
            rec(phep_do, che_do, tap, s, "loai_dung/cham", [(cl(r), int(r["loai_dung"]), 1) for r in rs
                                                             if r["loai_dung"] in ("0", "1")], ci)
            rec(phep_do, che_do, tap, s, "ngam_dung/gan", [(cl(r), int(r["ngam_dung"]), 1) for r in rs
                                                            if r["ngam_dung"] in ("0", "1")], ci)
            cnt(phep_do, che_do, tap, s, "ngam_bo_trong", sum(r["ngam_dung"] == "bo_trong" for r in rs))
            cnt(phep_do, che_do, tap, s, "ngam_khac_ngam_khong_cham(quy_tac_khong_gan)",
                sum(r["ngam_dung"] == "dap_an_khac_ngam" for r in rs))
            cnt(phep_do, che_do, tap, s, "ngam_khac_ngam_khong_cham(dap_an_khong_ro)",
                sum(r["ngam_dung"] == "dap_an_khac_ngam_khong_ro" for r in rs))
            cnt(phep_do, che_do, tap, s, "ngam_khac_ngam_tinh_sai",
                sum(r["ngam_dap_an"] == "khac_ngam" and r["ngam_dung"] == "0" for r in rs))
            ho = [(cl(r), int(r["ngam_dung"][3:]), 1) for r in rs if r["ngam_dung"].startswith("ho:")]
            if ho:
                rec(phep_do, che_do, tap, s, "ngam_muc_ho_dung/n", ho, ci)
        if s != "wikidata":
            rec(phep_do, che_do, tap, s, "khung_than_dung/gan", [(cl(r), int(r["khung_dung"]), 1) for r in rs
                                                                  if r["khung_dung"] in ("0", "1")], ci)
            cnt(phep_do, che_do, tap, s, "khung_bo_trong", sum(r["khung_dung"] == "bo_trong" for r in rs))
    per = collections.defaultdict(list)
    for r in rows:
        if r["loai_dung"] in ("0", "1"):
            per[r["parent_asin"]].append(int(r["loai_dung"]))
    pc = product_cluster([r for r in rows if r["loai_dung"] in ("0", "1")], cl)
    print("   [theo sản phẩm]")
    rec(phep_do, che_do, tap, "theo_san_pham", "loai_dung_moi_nguon/co_dap_an",
        [(pc[p], int(all(v)), 1) for p, v in per.items()], ci)
    conf, seen = collections.Counter(), set()
    for r in rows:
        if r["loai_dap_an"] and r["parent_asin"] not in seen:
            seen.add(r["parent_asin"])
            conf[(r["loai_dap_an"], r["loai_quy_tac"])] += 1
    print("   bảng nhầm loại (đáp án -> quy tắc), mỗi sản phẩm 1 lần, nguồn đầu tiên:")
    for (a, q), n in sorted(conf.items()):
        cnt(phep_do, che_do, tap, "nham_loai", f"{a}->{q}", n)


# ---------------------------------------------------------------- (3)
def by_mount_source(rows, che_do, tap, attr):
    print(f"\n  == (3) ngàm theo mount_source | {che_do} | {tap} ==")
    for s in ("lensfun", "wikidata"):
        rs = [r for r in rows if r["nguon"] == s]
        groups = collections.defaultdict(list)
        for r in rs:
            groups[attr[r["parent_asin"]]["mount_source"] or "(trong)"].append(r)
        print(f"   [{s}]")
        for g in sorted(groups):
            gr = groups[g]
            u = [(cl(r), int(r["ngam_dung"]), 1) for r in gr if r["ngam_dung"] in ("0", "1")]
            rec("(3)", che_do, tap, s, f"{g}: ngam_dung/gan", u, chi_dem=len(u) < 10)
            cnt("(3)", che_do, tap, s, f"{g}: ngam_bo_trong", sum(r["ngam_dung"] == "bo_trong" for r in gr))
        cnt("(3)", che_do, tap, s, "o_muc_ho_khong_tach(ho:)", sum(r["ngam_dung"].startswith("ho:") for r in rs))


# ---------------------------------------------------------------- (4)
def m_membership(rows, che_do, tap, tap_asins, mb, ml):
    print(f"\n  == (4) độ chính xác của việc vào M | {che_do} | {tap} ==")
    n_m = len(mb) + len(ml)
    mb_t, ml_t = mb & tap_asins, ml & tap_asins
    cnt("(4)", che_do, tap, "", "phan_tu_M (537 than + 1033 ong)", n_m)
    cnt("(4)", che_do, tap, "", "phan_tu_M_thuoc_tap", len(mb_t) + len(ml_t))
    cnt("(4)", che_do, tap, "", "than_M_thuoc_tap", len(mb_t))
    cnt("(4)", che_do, tap, "", "ong_M_thuoc_tap", len(ml_t))
    have = {r["parent_asin"] for r in rows if r["loai_dap_an"] and r["parent_asin"] in (mb_t | ml_t)}
    cnt("(4)", che_do, tap, "", "phan_tu_M_thuoc_tap_co_dap_an_loai", len(have))
    print(f"    độ phủ: {len(have)}/{n_m} = {pct(len(have) / n_m)} của M; "
          f"{len(have)}/{len(mb_t) + len(ml_t)} = {pct(len(have) / max(1, len(mb_t) + len(ml_t)))} của phần M thuộc tập")
    role = {p: "than" for p in mb_t}
    role.update({p: "ong" for p in ml_t})
    for s in ("lensfun", "wikidata"):
        rs = [r for r in rows if r["nguon"] == s and r["loai_dap_an"] and r["parent_asin"] in role]
        print(f"   [{s}]")
        rec("(4)", che_do, tap, s, "hang_M: dap_an_la_than/co_dap_an",
            [(cl(r), int(r["loai_dap_an"] == "than"), 1) for r in rs if role[r["parent_asin"]] == "than"])
        rec("(4)", che_do, tap, s, "cot_M: dap_an_la_ong/co_dap_an",
            [(cl(r), int(r["loai_dap_an"] == "ong"), 1) for r in rs if role[r["parent_asin"]] == "ong"])
        rec("(4)", che_do, tap, s, "ca_M: dap_an_dung_vai_tro/co_dap_an",
            [(cl(r), int(r["loai_dap_an"] == role[r["parent_asin"]]), 1) for r in rs])
    per = collections.defaultdict(list)
    tr = [r for r in rows if r["loai_dap_an"] and r["parent_asin"] in role]
    for r in tr:
        per[r["parent_asin"]].append(r["loai_dap_an"] == role[r["parent_asin"]])
    pc = product_cluster(tr)
    print("   [theo sản phẩm: đúng vai trò ở mọi nguồn có đáp án loại]")
    for lab, rl in (("hang_M", "than"), ("cot_M", "ong"), ("ca_M", None)):
        rec("(4)", che_do, tap, "theo_san_pham", f"{lab}: dung_vai_tro/co_dap_an",
            [(pc[p], int(all(v)), 1) for p, v in per.items() if rl is None or role[p] == rl])
    wrong = collections.Counter((role[p], r["loai_dap_an"]) for r in tr for p in [r["parent_asin"]]
                                if r["loai_dap_an"] != role[p])
    for (a, b), n in sorted(wrong.items()):
        cnt("(4)", che_do, tap, "o_sai", f"vai_tro_M={a} -> dap_an={b}", n)


# ---------------------------------------------------------------- (5)
def method_mounts(r, p, hai, cm):
    """(chặt, họ) của từng phương pháp; None = không gán."""
    q = r["ngam_quy_tac"] if single(r["ngam_quy_tac"]) else None
    h = HAI_MOUNT.get(hai[p]["mount"]) if p in hai else None
    clear = cm.get(p, set())
    c = CM_MOUNT.get(next(iter(clear))) if len(clear) == 1 else None
    return {"quy_tac": (q, fam(q) if q else None),
            "B1_hai": (h, fam(h) if h else None),
            "B2_compatible_mountings": (None if c == "HO_EF" else c, fam(c) if c else None)}


def baselines(rows, che_do, tap, tap_asins, hai, cm, hai_items):
    print(f"\n  == (5) baseline | {che_do} | {tap} ==")
    cnt("(5)", che_do, tap, "", "san_pham_tap_khong_co_trong_item_map_cu", len(tap_asins - hai_items))
    cnt("(5)", che_do, tap, "", "san_pham_tap_co_trong_linked_products(B1)", len(tap_asins & set(hai)))
    cnt("(5)", che_do, tap, "", "san_pham_tap_co_cm_raw_1_ngam_ro(B2)", sum(len(cm.get(p, ())) == 1 for p in tap_asins))
    for s in ("lensfun", "wikidata"):
        rs = [r for r in rows if r["nguon"] == s and r["ngam_dap_an"]]
        skip = [r for r in rs if r["ngam_dap_an"] == "khac_ngam" and r.get("ngam_khac_that") != "1"]
        rs = [r for r in rs if not (r["ngam_dap_an"] == "khac_ngam" and r.get("ngam_khac_that") != "1")]
        print(f"   [{s}] ô có đáp án ngàm cụ thể: {len(rs)} (bỏ {len(skip)} ô khac_ngam không rõ)")
        cnt("(5)", che_do, tap, s, "o_co_dap_an_ngam", len(rs))
        cnt("(5)", che_do, tap, s, "o_khac_ngam_khong_ro_bo", len(skip))
        cnt("(5)", che_do, tap, s, "o_khac_ngam_that", sum(r["ngam_dap_an"] == "khac_ngam" for r in rs))
        for meth in ("quy_tac", "B1_hai", "B2_compatible_mountings"):
            for li, lev in enumerate(("chat", "ho")):
                cov, acc = [], []
                for r in rs:
                    m = method_mounts(r, r["parent_asin"], hai, cm)[meth][li]
                    t = r["ngam_dap_an"]
                    t = None if t == "khac_ngam" else (t if lev == "chat" else fam(t))
                    cov.append((cl(r), int(m is not None), 1))
                    if m is not None:
                        acc.append((cl(r), int(t is not None and m == t), 1))
                rec("(5)", che_do, tap, s, f"{meth} [{lev}] do_phu: gan/co_dap_an", cov)
                rec("(5)", che_do, tap, s, f"{meth} [{lev}] chinh_xac: dung/gan", acc)
        # loại: quy tắc và B1, hai lớp thân / ống
        rl = [r for r in rows if r["nguon"] == s and r["loai_dap_an"]]
        for meth in ("quy_tac", "B1_hai"):
            for X in ("than", "ong"):
                ass = (lambda r: r["loai_quy_tac"]) if meth == "quy_tac" else \
                      (lambda r: HAI_TYPE.get(hai[r["parent_asin"]]["category"]) if r["parent_asin"] in hai else None)
                rec("(5)", che_do, tap, s, f"loai {meth} [{X}] chinh_xac: dap_an_{X}/gan_{X}",
                    [(cl(r), int(r["loai_dap_an"] == X), 1) for r in rl if ass(r) == X])
                rec("(5)", che_do, tap, s, f"loai {meth} [{X}] do_phu: gan_{X}/dap_an_{X}",
                    [(cl(r), int(ass(r) == X), 1) for r in rl if r["loai_dap_an"] == X])


# ---------------------------------------------------------------- N (H1)
def set_n(rows_n3, rows_n2, attr, split):
    print("\n##### TẬP N (H1): sản phẩm NGOÀI 1.493 khớp được ở lan3 — KHÔNG ĐỘC LẬP, CHỈ THAM KHẢO #####")
    cnt("N", "lan2", "N", "", "san_pham_ngoai_khop_duoc_o_lan2 (ky vong 0)", len({r["parent_asin"] for r in rows_n2}))
    prods = sorted({r["parent_asin"] for r in rows_n3})
    full = {p: attr[p]["title"] for p in prods}
    ev.MODE = "lan2"
    loc_lan2 = {p: ev.acc_title(full[p]) for p in prods}
    ev.MODE = "lan3"
    phim = {p for p in prods if re.search(r"\bfilm\b", ev.head_main(full[p], plus=False))}
    cnt("N", "lan3", "N", "", "san_pham_N", len(prods))
    cnt("N", "lan3", "N", "", "nguyen_nhan: bo_loc_phu_kien_lan2_loai (S2 / Manual Focus / N4)", sum(loc_lan2.values()))
    cnt("N", "lan3", "N", "", "nguyen_nhan: khac (vd chan F4/F2)", sum(not v for v in loc_lan2.values()))
    cnt("N", "lan3", "N_phim", "", "san_pham_co_chu_film_o_phan_dau", len(phim))
    cnt("N", "lan3", "N_phim", "", "trong_do_quy_tac_gan_may_phim=True", sum(attr[p]["may_phim"] == "True" for p in phim))
    for t, n in sorted(collections.Counter(attr[p]["item_type"] for p in phim).items()):
        cnt("N", "lan3", "N_phim", "", f"loai_quy_tac={t}", n)
    table1(rows_n3, "lan3", "N (không độc lập)", len(prods), phep_do="N")
    table1([r for r in rows_n3 if r["parent_asin"] in phim], "lan3", "N_phim (không độc lập)", len(phim), phep_do="N")
    table1([r for r in rows_n3 if r["parent_asin"] not in phim], "lan3", "N_khong_phim (không độc lập)",
           len(prods) - len(phim), phep_do="N")
    print("   sản phẩm N_phim (để đọc lại; không phải đáp án):")
    for p in sorted(phim):
        a = attr[p]
        print(f"     {p} quy tắc {a['item_type']}/{a['mount']}/may_phim={a['may_phim']} | {a['title'][:100]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--half", required=True, choices=["fix", "holdout"])
    for k in ("lan2", "lan3", "truoc", "lan-do-2", "ngoai-lan3", "ngoai-lan2", "out-csv"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--thu-ngoai-tu-fix", action="store_true", help="CHỈ để thử code: phần N đọc file của nửa fix")
    a = ap.parse_args()
    print(f"bootstrap: B = {B}, seed = {SEED}, cụm = cum_nguon (sản phẩm: Lensfun > Wikidata > openMVG)")
    for p in (a.lan2, a.lan3, a.truoc, a.lan_do_2, a.ngoai_lan3, a.ngoai_lan2, SPLIT, DEV, ATTR, BIDX, LIDX, HAI, HAI_MAP):
        print(f"  sha256 {sha(p)}  {p}")
    split = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open(SPLIT, encoding="utf-8"))}
    dev = {r["parent_asin"] for r in csv.DictReader(open(DEV, encoding="utf-8-sig"))}
    attr = {r["parent_asin"]: r for r in csv.DictReader(open(ATTR, encoding="utf-8"))}
    mb, ml = set(json.load(open(BIDX, encoding="utf-8"))), set(json.load(open(LIDX, encoding="utf-8")))
    hai = {r["parent_asin"]: r for r in csv.DictReader(open(HAI, encoding="utf-8"))}
    hai_items = set(json.load(open(HAI_MAP, encoding="utf-8")))
    cm = {p: mountlex.cm_mounts(r["cm_raw"])[0] for p, r in attr.items() if r["cm_raw"]}
    unk_hai = {r["mount"] for r in hai.values()} - set(HAI_MOUNT)
    assert not unk_hai, f"ngàm của bản Hải chưa có trong bảng ánh xạ: {unk_hai}"
    unk_cm = {m for v in cm.values() for m in v} - set(CM_MOUNT)
    assert not unk_cm, f"ngàm của Compatible Mountings chưa có trong bảng ánh xạ: {unk_cm}"
    print(f"M: {len(mb)} thân, {len(ml)} ống")

    half_asins = {p for p, h in split.items() if h == a.half}
    dev_in = dev & half_asins
    T_ALL, T_BD = ("H747", "H733") if a.half == "holdout" else ("F746", "F741")
    taps = [(T_BD, half_asins - dev_in), (T_ALL, half_asins)]   # tập bỏ dev in trước (số chính)
    print(f"tập {a.half}: {len(half_asins)} sản phẩm; mẫu dev trong tập: {len(dev_in)} -> {T_BD} = {len(half_asins - dev_in)}")

    modes = {}
    for name, p in (("lan2", a.lan2), ("lan3", a.lan3), ("truoc_0710", a.truoc)):
        rows = load_rows(p)
        bad = {r["parent_asin"] for r in rows} - half_asins
        assert not bad, f"{p}: {len(bad)} sản phẩm không thuộc nửa {a.half}"
        modes[name] = rows
    l2 = [r for r in load_rows(a.lan_do_2) if r["parent_asin"] in half_asins]

    print(f"\n##### (1)(2) SỐ CHÍNH = lan2 trên {T_BD}; bảng phụ: lan3 (sau khi sửa lỗi bộ đánh giá tìm từ ca holdout đã "
          f"xem), truoc_0710 (dựng lại theo mô tả, mã gốc không còn), lần đo 2 (quy tắc trước e8b39e6, không có cụm) #####")
    for tap, asins in taps:
        for name in ("lan2", "lan3", "truoc_0710"):
            table1([r for r in modes[name] if r["parent_asin"] in asins], name, tap, len(asins),
                   phep_do="(1)" if name == "lan2" else "(2)")
        table1([r for r in l2 if r["parent_asin"] in asins], "lan_do_2", tap, len(asins), ci=False, phep_do="(2)")

    print("\n##### (3) ĐỘ CHÍNH XÁC NGÀM THEO mount_source #####")
    for tap, asins in taps:
        for name in ("lan2", "lan3"):
            by_mount_source([r for r in modes[name] if r["parent_asin"] in asins], name, tap, attr)

    print("\n##### (4) ĐỘ CHÍNH XÁC CỦA VIỆC VÀO M #####")
    for tap, asins in taps:
        for name in ("lan2", "lan3"):
            m_membership([r for r in modes[name] if r["parent_asin"] in asins], name, tap, asins, mb, ml)

    print("\n##### (5) BASELINE: B1 bản của Hải, B2 Compatible Mountings (H3 áp cho mọi phương pháp) #####")
    for tap, asins in taps:
        for name in ("lan2", "lan3"):
            baselines([r for r in modes[name] if r["parent_asin"] in asins], name, tap, asins, hai, cm, hai_items)

    n3, n2 = load_rows(a.ngoai_lan3), load_rows(a.ngoai_lan2)
    if not a.thu_ngoai_tu_fix:
        bad = {r["parent_asin"] for r in n3 + n2} & set(split)
        assert not bad, f"file tập N có {len(bad)} sản phẩm thuộc 1.493"
    set_n(n3, n2, attr, split)

    if N_FALLBACK:
        print(f"\nCẢNH BÁO: ô thiếu cum_nguon (dùng cụm theo sản phẩm): {dict(N_FALLBACK)}")
    with open(a.out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(OUT[0].keys()))
        w.writeheader()
        w.writerows(OUT)
    print(f"\n-> {a.out_csv} ({len(OUT)} dòng chỉ số)")


if __name__ == "__main__":
    main()
