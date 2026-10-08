"""Nội dung 4, việc 1: kiểm nguồn và đếm số ống mỗi nhãn mục đích sử dụng theo ai/config/usecase_rules.toml.

Làm 4 việc:
  1. Kiểm bản sao của từng nguồn (ai/data/external/usecase_sources/): sha256 khớp TOML, có phần nội dung bài
     (câu dau_hieu_bai, không phải trang lỗi / chỉ có hộp cookie).
  2. Kiểm từng câu trích của mỗi luật có trong bản sao văn bản. Luật đang dùng mà không còn căn cứ
     "da_doc_trang" nào OK thì DỪNG (mã thoát 2), không đếm.
  3. Gắn nhãn cho từng ống (chỉ ống đọc được tiêu cự + khẩu độ từ tiêu đề), đếm số ống mỗi nhãn, kèm các số đối chiếu.
  4. In 5 ống ví dụ mỗi nhãn (seed cố định), ghi bảng nhãn ra ai/data/survey/usecase_labels_draft.csv.

Tiêu cự quy đổi 35mm chỉ dùng ở đây (QĐ 4-1). Khổ không rõ: tính với mọi hệ số trong crop.khong_ro, giữ nhãn chung.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/count_usecase.py
"""
import collections, csv, hashlib, html, random, re, sys, tomllib

sys.path.insert(0, "ai/survey/content3")
sys.stdout.reconfigure(encoding="utf-8")
import eval_external as ev  # noqa: E402

CFG = tomllib.load(open("ai/config/usecase_rules.toml", "rb"))
SRC_DIR = "ai/data/external/usecase_sources/"
OUT_CSV = "ai/data/survey/usecase_labels_draft.csv"
SEED = 20261008
RULES = CFG["rules"]
LABELS = [k for k, r in RULES.items() if r.get("trang_thai") != "da_bo"]   # nhãn sinh cạnh
MIN_TXT = 2000                                                              # văn bản ngắn hơn -> coi là trang rỗng / lỗi


def norm(s):
    s = html.unescape(s).lower()
    for a, b in (("—", "-"), ("–", "-"), ("’", "'"), ("“", '"'), ("”", '"'), ("\xa0", " ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s)


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------- 1. bản sao nguồn
def check_sources():
    print("=== 1. Bản sao nguồn ===")
    texts = {}
    for name, s in CFG["sources"].items():
        h_ok = sha256(SRC_DIR + s["ban_sao"]) == s["sha256_html"]
        t_ok = sha256(SRC_DIR + s["ban_sao_txt"]) == s["sha256_txt"]
        raw = open(SRC_DIR + s["ban_sao_txt"], encoding="utf-8").read()
        t = norm(raw)
        content_ok = len(raw) >= MIN_TXT and norm(s["dau_hieu_bai"]) in t and "access denied" not in t
        status = "OK" if (h_ok and t_ok and content_ok) else "LỖI"
        print(f"  {name:22s} {status:3s} sha256 html={'khớp' if h_ok else 'LỆCH'} txt={'khớp' if t_ok else 'LỆCH'} "
              f"nội dung bài={'có' if content_ok else 'THIẾU'} ({len(raw)} ký tự){'  [không dùng]' if s.get('khong_dung') else ''}")
        if status == "OK":
            texts[name] = t
    return texts


# ---------------------------------------------------------------- 2. câu trích của từng luật
def check_quotes(texts):
    print("\n=== 2. Câu trích của từng luật (kiểm theo bản sao văn bản) ===")
    failed = []
    for rid, r in RULES.items():
        n_ok = 0
        print(f"-- {rid}{' (đã bỏ, chỉ để tham khảo)' if r.get('trang_thai') == 'da_bo' else ''}")
        for c in r.get("can_cu", []):
            if c["source"] not in texts:
                st = "THIẾU (bản sao lỗi)"
            else:
                frags = [f.strip(" .,") for f in norm(c["trich"]).split("...") if f.strip(" .,")]
                st = "OK" if all(f in texts[c["source"]] for f in frags) else "THIẾU"
            if st == "OK" and c["kiem_chung"] == "da_doc_trang":
                n_ok += 1
            print(f"    {st:5s} [{c['kiem_chung']}] {c['source']}: {c['trich'][:80]}")
        print(f"    => căn cứ da_doc_trang OK: {n_ok}")
        if n_ok == 0 and r.get("trang_thai") != "da_bo":
            failed.append(rid)
    return failed


# ---------------------------------------------------------------- 3. gắn nhãn
def crops(a):
    c = CFG["crop"]
    if a["mount"] in c["theo_ngam"]:
        return [c["theo_ngam"][a["mount"]]]
    if a["khung"] == "ff":
        return [c["ff"]]
    if a["khung"] == "apsc":
        return [c["apsc_canon"] if a["mount"].startswith("canon") else c["apsc_khac"]]
    if a["khung"] == "khac" and a["mount"] == "canon_ef":
        return [c["aps_h"]]
    return list(c["khong_ro"])


def labels_at(f1, f2, ap1, ap2, crop, is_macro_word, portrait_hi=None):
    lo, hi = f1 * crop, (f2 or f1) * crop
    ap_tele = ap2 or ap1
    out = set()
    if lo <= RULES["phong_canh"]["lo_eq_max"]:
        out.add("phong_canh")
    if hi >= RULES["the_thao_chim"]["hi_eq_min"]:
        out.add("the_thao_chim")
    a, b = RULES["chan_dung"]["eq_overlap"]
    b = b if portrait_hi is None else portrait_hi
    if lo <= b and hi >= a and ap_tele <= RULES["chan_dung"]["ap_tele_max"]:
        out.add("chan_dung")
    if is_macro_word and (f2 is None or not RULES["macro"]["chi_ong_mot_tieu_cu"]):
        out.add("macro")
    if lo <= RULES["vlog"]["lo_eq_max_tham_khao"]:
        out.add("vlog_thamkhao")
    return frozenset(out)


def label(f1, f2, ap1, ap2, cs, mw, portrait_hi=None):
    res = [labels_at(f1, f2, ap1, ap2, c, mw, portrait_hi) for c in cs]
    return frozenset.intersection(*res), res


def main():
    texts = check_sources()
    failed = check_quotes(texts)
    if failed:
        print(f"\nDỪNG: luật không còn căn cứ da_doc_trang nào OK: {failed}. Không đếm.")
        sys.exit(2)

    macro_re = re.compile(RULES["macro"]["tu_khoa"], re.I)
    attrs = [a for a in csv.DictReader(open("ai/data/kg/item_attributes.csv", encoding="utf-8")) if a["item_type"] == "ong"]
    rows, no_sig_macro = [], []
    for a in attrs:
        h = ev.head_main(a["title"])
        mw = bool(macro_re.search(h))
        s = ev.lens_sig(h)
        if not s:
            if mw:
                no_sig_macro.append(a)
            continue
        f1, f2, ap1, ap2 = [float(x) if x else None for x in s]
        cs = crops(a)
        lab, res = label(f1, f2, ap1, ap2, cs, mw)
        lab_no135, _ = label(f1, f2, ap1, ap2, cs, mw, portrait_hi=float("inf"))
        rows.append(dict(iid=a["iid"], parent_asin=a["parent_asin"], mount=a["mount"], khung=a["khung"],
                         f1=f1, f2=f2, ap1=ap1, ap2=ap2, crops="/".join(str(c) for c in cs), khong_ro=len(cs) > 1,
                         lo_eq="/".join(f"{f1 * c:g}" for c in cs), hi_eq="/".join(f"{(f2 or f1) * c:g}" for c in cs),
                         macro_word=mw, union=frozenset.union(*res), labels=lab, labels_no135=lab_no135, title=a["title"]))

    print(f"\n=== 3. Đếm ===\nống: {len(attrs)}; đọc được tiêu cự + khẩu độ: {len(rows)}")
    cnt = collections.Counter(l for r in rows for l in r["labels"])
    for l in LABELS:
        print(f"  {l:15s} {cnt[l]:5d}")
    print(f"  (không nhãn nào) {sum(1 for r in rows if not (r['labels'] & set(LABELS))):5d}")

    # ống không rõ khổ (QĐ thiết kế: tính với 1,0 và 1,6, chỉ gắn nhãn khi cả hai cùng ra)
    kr = [r for r in rows if r["khong_ro"]]
    print(f"\nống không rõ khổ (tính với {CFG['crop']['khong_ro']}): {len(kr)}; "
          f"có ít nhất một nhãn bị bỏ vì hai cách tính khác nhau: {sum(1 for r in kr if (r['union'] - r['labels']) & set(LABELS))}")
    for l in LABELS:
        print(f"  {l:15s} được gắn: {sum(l in r['labels'] for r in kr):4d}   bị bỏ vì lệch: "
              f"{sum(l in r['union'] and l not in r['labels'] for r in kr):4d}")

    # đối chiếu (không đổi luật)
    v = [r for r in rows if "vlog_thamkhao" in r["labels"]]
    print(f"\n[đối chiếu] vlog đã bỏ, luật tham khảo lo_eq <= {RULES['vlog']['lo_eq_max_tham_khao']}: {len(v)} ống, "
          f"trong đó cũng là phong_canh: {sum('phong_canh' in r['labels'] for r in v)}")
    gain = [r for r in rows if "chan_dung" in r["labels_no135"] and "chan_dung" not in r["labels"]]
    lose = [r for r in rows if "chan_dung" in r["labels"] and "chan_dung" not in r["labels_no135"]]
    print(f"[đối chiếu] nếu bỏ mốc trên 135 của chân dung: thêm nhãn {len(gain)} ống, mất nhãn {len(lose)} ống")
    for r in sorted(gain, key=lambda r: int(r["iid"]))[:15]:
        print(f"    + iid={r['iid']} {r['lo_eq']}..{r['hi_eq']}mm f/{r['ap2'] or r['ap1']:g} {r['title'][:80]}")
    a85 = RULES["chan_dung"]["eq_overlap"][0]
    near = [r for r in rows if "chan_dung" not in r["labels"] and not r["khong_ro"]
            and 75 <= (r["f2"] or r["f1"]) * float(r["crops"]) < a85 and (r["ap2"] or r["ap1"]) <= RULES["chan_dung"]["ap_tele_max"]]
    print(f"[đối chiếu] chân dung: ống khẩu độ <= f/2.8 có hi_eq trong [75, {a85}) không được nhãn: {len(near)}")
    mz = [r for r in rows if r["macro_word"] and r["f2"] is not None]
    print(f"[đối chiếu] macro: có từ khóa {sum(r['macro_word'] for r in rows)} ống; zoom có từ khóa (không gắn nhãn): {len(mz)}; "
          f"có từ khóa nhưng không đọc được tiêu cự+khẩu độ: {len(no_sig_macro)}")

    # ---------------------------------------------------------------- 4. ví dụ
    print(f"\n=== 4. Ví dụ 5 ống mỗi nhãn (random.Random({SEED}), lấy mẫu trên danh sách sắp theo iid) ===")
    for l in LABELS:
        pool = sorted((r for r in rows if l in r["labels"]), key=lambda r: int(r["iid"]))
        print(f"-- {l} ({len(pool)})")
        for r in random.Random(SEED).sample(pool, min(5, len(pool))):
            print(f"    iid={r['iid']:>5} {r['parent_asin']} | {r['f1']:g}{'-' + format(r['f2'], 'g') if r['f2'] else ''}mm "
                  f"f/{r['ap1']:g}{'-' + format(r['ap2'], 'g') if r['ap2'] else ''} | crop {r['crops']} -> {r['lo_eq']}..{r['hi_eq']}mm "
                  f"| nhãn {sorted(r['labels'] & set(LABELS))} | {r['title'][:110]}")

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iid", "parent_asin", "mount", "khung", "f1", "f2", "ap1", "ap2", "crops", "lo_eq", "hi_eq",
                    "khong_ro", "labels", "title"])
        for r in sorted(rows, key=lambda r: int(r["iid"])):
            w.writerow([r["iid"], r["parent_asin"], r["mount"], r["khung"], r["f1"], r["f2"] or "", r["ap1"], r["ap2"] or "",
                        r["crops"], r["lo_eq"], r["hi_eq"], r["khong_ro"],
                        ";".join(sorted(r["labels"] & set(LABELS))), r["title"]])
    print(f"\nĐã ghi {OUT_CSV} ({len(rows)} dòng)")


if __name__ == "__main__":
    main()
