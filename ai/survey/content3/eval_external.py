"""
Đo độ chính xác của quy tắc nội dung 3 (loại / ngàm / khung) bằng nguồn thông số BÊN NGOÀI (QĐ 10).
Nguồn chỉ dùng làm đáp án, KHÔNG dùng trong quy tắc.

Đầu vào:
  ai/data/kg/item_attributes.csv                      (kết quả quy tắc, do 03_mount_compat.py sinh)
  ai/data/external/lensfun/*.xml                      (Lensfun, CC BY-SA 3.0)
  ai/data/external/openmvg/sensor_database.csv        (openMVG, MIT)
  ai/data/external/wikidata/mount_models.json         (Wikidata, CC0)
Đầu ra:
  ai/data/survey/eval_external_matches.csv  (mọi sản phẩm khớp được + đáp án + đúng/sai)
  ai/data/survey/eval_external_summary.json
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content3/eval_external.py

KHỚP TÊN "CHẮC CHẮN"
  Thân máy: chuỗi model của nguồn (bỏ tên hãng, phải có chữ số) xuất hiện NGUYÊN VẸN (theo token) trong phần đầu tiêu đề
            (trước "for / compatible / replacement / fits"), tiêu đề có tên hãng; lấy khớp dài nhất; nếu các ứng viên dài nhất
            cho đáp án khác nhau -> bỏ (không chắc).
  Ống kính: cùng hãng + cùng tiêu cự + cùng khẩu độ (đọc ở phần đầu tiêu đề). Đáp án ngàm chỉ lấy khi MỌI ống cùng chữ ký
            trong nguồn có cùng 1 ngàm (vd Canon 50mm f/1.8 có cả EF và RF -> bỏ). Không dùng chữ chỉ ngàm trong tiêu đề để
            lọc ứng viên, để bước khớp không tự 'đồng ý' với quy tắc.
"""
import csv, glob, json, re, sys, collections
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding="utf-8")

OURS = "ai/data/kg/item_attributes.csv"
OUT_CSV = "ai/data/survey/eval_external_matches.csv"
OUT_JSON = "ai/data/survey/eval_external_summary.json"

MAKERS = {  # từ trong tiêu đề -> hãng chuẩn
    "canon": "canon", "nikon": "nikon", "sony": "sony", "minolta": "sony", "konica": "sony", "fujifilm": "fujifilm",
    "fuji": "fujifilm", "fujinon": "fujifilm", "olympus": "olympus", "om": "olympus", "panasonic": "panasonic",
    "lumix": "panasonic", "pentax": "pentax", "ricoh": "pentax", "samsung": "samsung", "leica": "leica", "sigma": "sigma",
    "tamron": "tamron", "tokina": "tokina", "samyang": "samyang", "rokinon": "samyang", "bower": "samyang",
    "zeiss": "zeiss", "voigtlander": "voigtlander", "hasselblad": "hasselblad", "kodak": "kodak", "yongnuo": "yongnuo",
    "laowa": "laowa", "venus": "laowa", "viltrox": "viltrox", "meike": "meike", "7artisans": "7artisans",
    "ttartisan": "ttartisan", "irix": "irix", "lensbaby": "lensbaby", "mitakon": "mitakon", "zhongyi": "mitakon",
}


def maker_of(s):
    s = (s or "").lower()
    for w in re.findall(r"[a-z0-9]+", s):
        if w in MAKERS:
            return MAKERS[w]
    return None


def toks(s):
    s = s.lower().replace("‐", "-").replace("–", "-")
    s = re.sub(r"[/,()\[\]|+&:;\"]", " ", s)
    return [t for t in s.split() if t]


def head_for(t):
    """Phần đầu tiêu đề: trước 'for / compatible / replacement / fits ...' (để không khớp nhầm phụ kiện)."""
    return re.split(r"\s(?:for|compatible|replacement|fits|designed|works)\b", t.lower(), maxsplit=1)[0]


def head_main(t):
    """Phần đầu tiêu đề trước 'with / + / & / bundle' (dùng cho ống kính)."""
    return re.split(r"\s(?:with|w/|\+|&|plus|bundle|kit)\s|\s\+", head_for(t), maxsplit=1)[0]


# ---------------------------------------------------------------- ánh xạ ngàm của nguồn -> mã của nhóm
def lensfun_mount(m):
    m = m or ""
    table = [("Canon EF-S", "canon_efs"), ("Canon EF-M", "canon_efm"), ("Canon EF", "canon_ef"), ("Canon RF", "canon_rf"),
             ("Canon FD", "canon_fd"), ("Nikon F", "nikon_f"), ("Nikon Z", "nikon_z"), ("Nikon CX", "nikon_1"),
             ("Sony E", "sony_e"), ("Sony Alpha", "sony_a"), ("Minolta AF", "sony_a"), ("Fujifilm X", "fuji_x"),
             ("Fujifilm G", "fuji_g"), ("Micro 4/3", "mft"), ("4/3 System", "four_thirds"), ("Pentax Q", "pentax_q"),
             ("Pentax K", "pentax_k"), ("Samsung NX mini", "khac_ngam"), ("Samsung NX", "samsung_nx"),
             ("Leica L", "l_mount"), ("Leica M", "leica_m"), ("Sigma SA", "sigma_sa"), ("M42", "m42"), ("T2", "t_mount")]
    for k, v in table:
        if m.startswith(k):
            return v
    return "khac_ngam"


def wikidata_mount(label):
    l = (label or "").lower()
    table = [("canon ef-s", "canon_efs"), ("canon ef-m", "canon_efm"), ("canon ef lens", "canon_ef"), ("canon rf", "canon_rf"),
             ("canon fd", "canon_fd"), ("nikon f-mount", "nikon_f"), ("nikon z", "nikon_z"), ("nikon 1", "nikon_1"),
             ("sony e", "sony_e"), ("minolta a", "sony_a"), ("fujifilm x", "fuji_x"), ("fujifilm g", "fuji_g"),
             ("micro four thirds", "mft"), ("four thirds", "four_thirds"), ("k-mount", "pentax_k"), ("l-mount", "l_mount"),
             ("leica m", "leica_m"), ("sigma sa", "sigma_sa"), ("samsung nx-mount", "samsung_nx"), ("m42", "m42")]
    for k, v in table:
        if l.startswith(k):
            return v
    return None


def crop_to_khung(c):
    if c is None:
        return None
    c = float(c)
    if c < 0.95:
        return "khac"       # medium format
    if c <= 1.1:
        return "ff"
    if c < 1.45:
        return "khac"       # APS-H
    if c <= 1.75:
        return "apsc"
    return "khac"


def width_to_khung(w):
    w = float(w)
    if w >= 34:
        return "ff"
    if 26 <= w < 34:
        return "khac"       # APS-H
    if 20 <= w < 26:
        return "apsc"
    return "khac"


def body_keys(model, maker):
    """Các khóa model (danh sách token) từ 1 tên model, đã bỏ tên hãng."""
    out = []
    for part in re.split(r"\s/\s", model):
        tk = toks(part)
        while tk and (tk[0] in MAKERS or tk[0] in ("corporation", "imaging", "company")):
            tk = tk[1:]
        if not tk or not any(re.search(r"\d", t) for t in tk):
            continue
        out.append(tuple(tk))
        s = " ".join(tk)                                   # Sony 'alpha 6000' -> 'a6000'
        m = re.match(r"alpha\s+(\d{1,4}[a-z]*)$", s)
        if m:
            out.append(("a" + m.group(1),))
    return out


# ---------------------------------------------------------------- nạp nguồn
def load_lensfun():
    cams, lenses = [], []
    for f in glob.glob("ai/data/external/lensfun/*.xml"):
        fn = f.replace("\\", "/").split("/")[-1]
        root = ET.parse(f).getroot()
        for c in root.findall("camera"):
            maker = maker_of(c.findtext("maker")) or maker_of(c.findtext("model"))
            fixed = fn.startswith(("compact", "actioncams")) or not re.match(r"[A-Z0-9]", c.findtext("mount") or "x")
            truth = dict(type="khac" if fixed else "than",
                         mount=None if fixed else lensfun_mount(c.findtext("mount")),
                         khung=None if fixed else crop_to_khung(c.findtext("cropfactor")),
                         name=c.findtext("model"))
            for m in c.findall("model"):
                for k in body_keys(m.text or "", maker):
                    cams.append((maker, k, truth))
        for l in root.findall("lens"):
            mounts = {lensfun_mount(x.text) for x in l.findall("mount")}
            if fn.startswith(("compact", "actioncams")) or not mounts:
                continue
            models = [x.text or "" for x in l.findall("model")]
            maker = maker_of(l.findtext("maker")) or maker_of(models[0])
            for m in models:
                sig = lens_sig(m)
                if sig and maker:
                    lenses.append(((maker,) + sig, dict(mounts=mounts, crop=l.findtext("cropfactor"), name=m)))
    return cams, lenses


def load_openmvg():
    cams = []
    for r in csv.DictReader(open("ai/data/external/openmvg/sensor_database.csv", encoding="utf-8")):
        maker = maker_of(r["CameraMaker"])
        if not maker:
            continue
        truth = dict(type=None, mount=None, khung=width_to_khung(r["SensorWidth(mm)"]), name=r["CameraModel"])
        for k in body_keys(r["CameraModel"], maker):
            cams.append((maker, k, truth))
    return cams


def load_wikidata():
    rows = json.load(open("ai/data/external/wikidata/mount_models.json", encoding="utf-8"))["results"]["bindings"]
    items = collections.defaultdict(lambda: dict(mounts=set(), names=set(), cls=None, maker=None))
    for b in rows:
        it = items[b["item"]["value"]]
        m = wikidata_mount(b["mountLabel"]["value"])
        if m:
            it["mounts"].add(m)
        it["names"].add(b["itemLabel"]["value"])
        for a in (b.get("aliases", {}).get("value") or "").split(" | "):
            if a:
                it["names"].add(a)
        it["cls"] = b["classLabel"]["value"]
        it["maker"] = it["maker"] or maker_of(b.get("makerLabel", {}).get("value")) or maker_of(b["itemLabel"]["value"])
    cams, lenses = [], []
    for it in items.values():
        if not it["mounts"]:
            continue
        ms = it["mounts"]
        if ms == {"canon_ef", "canon_efs"}:
            ms = {"canon_efs"}               # DSLR Canon APS-C: Wikidata ghi cả EF và EF-S
        # lớp "product model"/"product line" chứa cả máy lẫn ống: tên đọc được tiêu cự + khẩu độ thì coi là ống
        is_lens = it["cls"] in ("lens model", "camera lens") or (
            it["cls"] in ("product model", "digital camera product line") and any(lens_sig(x) for x in it["names"]))
        name = sorted(it["names"])[0]
        if is_lens:
            for n in it["names"]:
                sig = lens_sig(n)
                if sig and it["maker"]:
                    lenses.append(((it["maker"],) + sig, dict(mounts=ms, crop=None, name=n)))
        else:
            truth = dict(type="than", mount=next(iter(ms)) if len(ms) == 1 else None, khung=None, name=name,
                         family={("canon_ef" if m in ("canon_ef", "canon_efs") else m) for m in it["mounts"]})
            for n in it["names"]:
                for k in body_keys(n, it["maker"]):
                    cams.append((it["maker"], k, truth))
    return cams, lenses


FOCAL = re.compile(r"(\d{1,4}(?:\.\d)?)\s?(?:-\s?(\d{1,4}(?:\.\d)?))?\s?mm")
APER = re.compile(r"(?:f\s?/?\s?|1\s?:\s?)(\d{1,2}(?:\.\d{1,2})?)(?:\s?-\s?(\d{1,2}(?:\.\d{1,2})?))?", re.I)


def _num(x):
    return None if x is None else str(float(x)).rstrip("0").rstrip(".")


def lens_sig(text):
    t = text.lower().replace("–", "-")
    fm = FOCAL.search(t)
    if not fm:
        return None
    am = APER.search(t[fm.end():]) or APER.search(t)
    if not am:
        return None
    return (_num(fm.group(1)), _num(fm.group(2)), _num(am.group(1)), _num(am.group(2)))


# ---------------------------------------------------------------- khớp
# Tiêu đề mà PHẦN ĐẦU (trước with/+/&/for) có từ phụ kiện -> không coi là khớp chắc chắn (vd "Nikon D5 AN-DC15 Camera Strap",
# "X-T2 Leather Case"). Danh sách này thuộc bước đánh giá, viết riêng, không lấy từ quy tắc.
ACC_EVAL = re.compile(r"\b(?:case|cover|bag|pouch|protector|strap|grip|cage|battery|batteries|charger|memory|card|tripod|"
                      r"monopod|adapter|teleconverter|converter|cloth|decal|skin|sticker|hood|cap|filter|remote|cable|"
                      r"eyecup|bracket|plate|shield|guard|film|holster|harness|rig|mount|lcd|screen|flash|light|"
                      r"microphone|mic|replacement|parts?|manual|book|guide|dvd)\b")


def index_bodies(cams):
    idx = collections.defaultdict(list)
    for maker, k, truth in cams:
        idx[k].append((maker, truth))
    return idx


def match_body(title, idx, maxlen=6):
    t_maker = {MAKERS[w] for w in re.findall(r"[a-z0-9]+", title.lower()) if w in MAKERS}
    tk = toks(head_for(title))
    best, cands = 0, []
    for i in range(len(tk)):
        for n in range(1, maxlen + 1):
            k = tuple(tk[i:i + n])
            if len(k) < n:
                break
            for maker, truth in idx.get(k, []):
                if maker not in t_maker:
                    continue
                if n > best:
                    best, cands = n, [truth]
                elif n == best:
                    cands.append(truth)
    if not cands:
        return None, 0
    keyf = lambda tr: (tr["type"], tr["mount"], tr["khung"], tuple(sorted(tr.get("family", []))))
    if len({keyf(c) for c in cands}) > 1:
        return "ambiguous", len(cands)
    return cands[0], len(cands)


def match_lens(title, lidx):
    h = head_main(title)
    mk = maker_of(h)
    sig = lens_sig(h)
    if not mk or not sig:
        return None
    entries = lidx.get((mk,) + sig)
    if not entries:
        return None
    # Chắc chắn: MỌI token trong tên ống của nguồn (bỏ tên hãng) phải có trong phần đầu tiêu đề.
    tt = set(ctoks(h))
    entries = [e for e in entries if set(t for t in ctoks(e["name"]) if t not in MAKERS) <= tt]
    if not entries:
        return None
    mounts = set().union(*[e["mounts"] for e in entries])
    # Khung của ống KHÔNG chấm: hệ số crop của Lensfun là của máy dùng để hiệu chỉnh, không phải vòng ảnh.
    return dict(type="ong", mount=next(iter(mounts)) if len(mounts) == 1 else None, mounts=mounts, khung=None,
                name=entries[0]["name"], n=len(entries))


def ctoks(s):
    """Token chuẩn hoá cho tên ống: 'EF-S 18-55mm f/3.5-5.6 IS II' -> ef s 18-55 mm f 3.5-5.6 is ii."""
    s = s.lower().replace("–", "-").replace("f/", "f ")
    return re.findall(r"[a-z]+|\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?", s)


def main():
    ours = list(csv.DictReader(open(OURS, encoding="utf-8")))
    lf_c, lf_l = load_lensfun()
    om_c = load_openmvg()
    wd_c, wd_l = load_wikidata()
    srcs = {"lensfun": (index_bodies(lf_c), lf_l), "openmvg": (index_bodies(om_c), []), "wikidata": (index_bodies(wd_c), wd_l)}
    print(f"Lensfun: {len(lf_c):,} khóa thân, {len(lf_l):,} chữ ký ống | openMVG: {len(om_c):,} khóa | "
          f"Wikidata: {len(wd_c):,} khóa thân, {len(wd_l):,} chữ ký ống")
    rows, summary = [], {}
    for sname, (bidx, lens_list) in srcs.items():
        lidx = collections.defaultdict(list)
        for sig, e in lens_list:
            lidx[sig].append(e)
        st = collections.Counter()
        for o in ours:
            title = o["title"]
            if ACC_EVAL.search(head_main(title)):
                truth, _ = match_body(title, bidx)
                if truth is not None or (lidx and match_lens(title, lidx)):
                    st["bo_qua_tieu_de_phu_kien"] += 1
                continue
            truth, _ = match_body(title, bidx)
            kind = "than_may"
            if truth == "ambiguous":
                st["bo_qua_mo_ho"] += 1
                continue
            if truth is None and lidx:
                truth = match_lens(title, lidx)
                kind = "ong"
            if truth is None:
                continue
            st["khop"] += 1
            r = dict(nguon=sname, loai_khop=kind, parent_asin=o["parent_asin"], title=title[:150], ten_nguon=truth["name"],
                     loai_quy_tac=o["item_type"], ngam_quy_tac=o["mount"], khung_quy_tac=o["khung"],
                     loai_dap_an=truth["type"] or "", ngam_dap_an=truth["mount"] or "", khung_dap_an=truth["khung"] or "",
                     loai_dung="", ngam_dung="", khung_dung="")
            if truth["type"]:
                ok = o["item_type"] == truth["type"]
                r["loai_dung"] = int(ok); st["loai_n"] += 1; st["loai_dung"] += ok
            # ngàm/khung: chỉ so khi loại của quy tắc trùng loại đáp án (lỗi loại đã tính ở trên)
            if truth["type"] and o["item_type"] != truth["type"]:
                rows.append(r); continue
            if not truth["type"] and o["item_type"] not in ("than", "ong"):
                rows.append(r); continue
            single = o["mount"] not in ("khong_ro", "khong_co", "nhieu", "") and ">" not in o["mount"]
            if truth["mount"]:
                st["ngam_n"] += 1
                if single:
                    ok = o["mount"] == truth["mount"]
                    r["ngam_dung"] = int(ok); st["ngam_gan"] += 1; st["ngam_dung"] += ok
                else:
                    r["ngam_dung"] = "bo_trong"; st["ngam_bo_trong"] += 1
            elif truth.get("family") and single:      # Wikidata: thân Canon chỉ ghi 'EF' -> so ở mức họ ngàm EF/EF-S
                fam = "canon_ef" if o["mount"] in ("canon_ef", "canon_efs") else o["mount"]
                ok = fam in truth["family"] and len(truth["family"]) == 1
                st["ngam_ho_n"] += 1; st["ngam_ho_dung"] += ok
                r["ngam_dung"] = f"ho:{int(ok)}"
            if truth["khung"]:
                st["khung_n"] += 1
                if o["khung"] and o["khung"] != "khong_ro":
                    ok = o["khung"] == truth["khung"]
                    r["khung_dung"] = int(ok); st["khung_gan"] += 1; st["khung_dung"] += ok
                else:
                    r["khung_dung"] = "bo_trong"; st["khung_bo_trong"] += 1
            rows.append(r)
        summary[sname] = dict(st)
        pct = lambda a, b: f"{a}/{b} ({a / b * 100:.1f}%)" if b else "-"
        print(f"\n=== {sname}: khớp chắc chắn {st['khop']:,} sản phẩm (bỏ {st['bo_qua_mo_ho']} ca mơ hồ, "
              f"{st['bo_qua_tieu_de_phu_kien']} tiêu đề phụ kiện có nhắc tên máy/ống)")
        print(f"  loại : đúng {pct(st['loai_dung'], st['loai_n'])}")
        print(f"  ngàm : đáp án có {st['ngam_n']}; quy tắc gán {st['ngam_gan']}, đúng {pct(st['ngam_dung'], st['ngam_gan'])}; "
              f"quy tắc để trống {st['ngam_bo_trong']}" + (f"; so ở mức họ ngàm (EF/EF-S): đúng {pct(st['ngam_ho_dung'], st['ngam_ho_n'])}" if st['ngam_ho_n'] else ""))
        print(f"  khung: đáp án có {st['khung_n']}; quy tắc gán {st['khung_gan']}, đúng {pct(st['khung_dung'], st['khung_gan'])}; "
              f"quy tắc để trống {st['khung_bo_trong']}")
    cols = list(rows[0].keys())
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    json.dump(summary, open(OUT_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\n-> {OUT_CSV} ({len(rows)} dòng), {OUT_JSON}")


if __name__ == "__main__":
    main()
