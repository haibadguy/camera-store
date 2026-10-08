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
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content3/eval_external.py --bo-danh-gia lan3 --half fix
      --out-csv <file mới>.csv --out-json <file mới>.json   (bắt buộc; đặt PYTHONHASHSEED=0)

BỘ ĐÁNH GIÁ (--bo-danh-gia, bắt buộc; kế hoạch đo lần 3: docs/reviews/n3_eval_lan3_plan.md)
  truoc_0710 : bản trước 3 lần sửa khớp tên ngày 07/10, DỰNG LẠI theo mô tả (mã gốc không còn trong git):
               không lọc tiêu đề phụ kiện; khớp ống chỉ cần hãng + tiêu cự + khẩu độ; lớp "product model" của
               Wikidata luôn coi là máy ảnh. Chỉ dùng cho phép đo độ nhạy.
  lan2       : bản dùng ở lần đo holdout thứ 1 và 2 (giống hệt mã commit ea6abb0).
  lan3       : bản sửa theo Red Team n3 lần 1 (S2, N4), dùng cho lần đo thứ 3.
TẬP (--half, bắt buộc): lọc sản phẩm theo ai/survey/content3/eval_split.csv TRƯỚC khi khớp
  fix / holdout / ngoai (không thuộc 1.493 sản phẩm đã chia) / all.

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
SPLIT = "ai/survey/content3/eval_split.csv"
EVAL_MODES = ("truoc_0710", "lan2", "lan3")
MODE = "lan3"   # gán trong main() theo --bo-danh-gia

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


def head_main(t, plus=True):
    """Phần đầu tiêu đề trước 'with / + / & / bundle' (dùng cho ống kính).
    plus=False (lan3, chỉ cho bộ lọc phụ kiện, Red Team N4): không cắt ở 'plus', vì 'Plus' hay là một phần tên
    model ('Galaxy S8 Plus … Screen Protector'), cắt ở đó làm từ phụ kiện phía sau lọt qua bộ lọc."""
    sep = r"with|w/|\+|&|plus|bundle|kit" if plus else r"with|w/|\+|&|bundle|kit"
    return re.split(rf"\s(?:{sep})\s|\s\+", head_for(t), maxsplit=1)[0]


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
        for ci, c in enumerate(root.findall("camera")):
            maker = maker_of(c.findtext("maker")) or maker_of(c.findtext("model"))
            fixed = fn.startswith(("compact", "actioncams")) or not re.match(r"[A-Z0-9]", c.findtext("mount") or "x")
            truth = dict(type="khac" if fixed else "than",
                         mount=None if fixed else lensfun_mount(c.findtext("mount")),
                         khung=None if fixed else crop_to_khung(c.findtext("cropfactor")),
                         name=c.findtext("model"), id=f"lensfun:{fn}:cam{ci}")
            for m in c.findall("model"):
                for k in body_keys(m.text or "", maker):
                    cams.append((maker, k, truth))
        for li, l in enumerate(root.findall("lens")):
            mounts = {lensfun_mount(x.text) for x in l.findall("mount")}
            if fn.startswith(("compact", "actioncams")) or not mounts:
                continue
            models = [x.text or "" for x in l.findall("model")]
            maker = maker_of(l.findtext("maker")) or maker_of(models[0])
            for m in models:
                sig = lens_sig(m)
                if sig and maker:
                    lenses.append(((maker,) + sig, dict(mounts=mounts, crop=l.findtext("cropfactor"), name=m,
                                                        id=f"lensfun:{fn}:lens{li}")))
    return cams, lenses


def load_openmvg():
    cams = []
    for ri, r in enumerate(csv.DictReader(open("ai/data/external/openmvg/sensor_database.csv", encoding="utf-8"))):
        maker = maker_of(r["CameraMaker"])
        if not maker:
            continue
        truth = dict(type=None, mount=None, khung=width_to_khung(r["SensorWidth(mm)"]), name=r["CameraModel"],
                     id=f"openmvg:{ri}")
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
    for uri, it in items.items():
        if not it["mounts"]:
            continue
        ms = it["mounts"]
        if ms == {"canon_ef", "canon_efs"}:
            ms = {"canon_efs"}               # DSLR Canon APS-C: Wikidata ghi cả EF và EF-S
        # lớp "product model"/"product line" chứa cả máy lẫn ống: tên đọc được tiêu cự + khẩu độ thì coi là ống
        # (lần sửa (c) ngày 07/10; bản truoc_0710 không có)
        is_lens = it["cls"] in ("lens model", "camera lens") or (MODE != "truoc_0710" and
            it["cls"] in ("product model", "digital camera product line") and any(lens_sig(x) for x in it["names"]))
        name = sorted(it["names"])[0]
        if is_lens:
            for n in it["names"]:
                sig = lens_sig(n)
                if sig and it["maker"]:
                    lenses.append(((it["maker"],) + sig, dict(mounts=ms, crop=None, name=n, id=f"wikidata:{uri}")))
        else:
            truth = dict(type="than", mount=next(iter(ms)) if len(ms) == 1 else None, khung=None, name=name,
                         family={("canon_ef" if m in ("canon_ef", "canon_efs") else m) for m in it["mounts"]},
                         id=f"wikidata:{uri}")
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
                      r"microphone|mic|replacement|parts?|manual|book|guide|dvd)\b")   # bản lan2 (và lần đo 1, 2)

# Bản lan3 (Red Team n3 lần 1):
#  S2: bỏ 7 từ quá rộng film, mount, lcd, screen, flash, light, card; thay bằng CỤM phụ kiện cụ thể. Mỗi cụm đều chứa
#      đúng từ cũ (số ít, có \b), nên tập tiêu đề bị loại chỉ có thể THU HẸP: sản phẩm từng qua bộ lọc vẫn qua.
#      Vd "Nikon F100 35mm Film Camera", "Sony FE 50mm F1.8 E-Mount", "Nikon D3500 3.0\" LCD" không còn bị loại.
#  N4: "guide" -> "guides?"; thêm "eye cup(s)", "jacket(s)".
ACC_EVAL_LAN3_WORDS = (r"case|cover|bag|pouch|protector|strap|grip|cage|battery|batteries|charger|memory|tripod|"
                       r"monopod|adapter|teleconverter|converter|cloth|decal|skin|sticker|hood|cap|filter|remote|cable|"
                       r"eyecup|eye[\s-]cups?|jackets?|bracket|plate|shield|guard|holster|harness|rig|"
                       r"microphone|mic|replacement|parts?|manual|book|guides?|dvd")
ACC_EVAL_LAN3_PHRASES = [
    # film
    r"(?:protector|protective|protection|screen|lcd|display|guard|tempered|glass|hydrogel|anti-?glare|matte|clear)\s+film",
    r"film\s+(?:protectors?|guards?|covers?|packs?|rolls?|sheets?|cartridges?)", r"instant\s+film",
    # mount
    r"(?:shoe|hot[\s-]?shoe|cold[\s-]?shoe|flash|suction(?:\s+cup)?|cup|car|wall|ceiling|desk|phone|smartphone|clamp|"
    r"helmet|chest|head|bike|bicycle|handlebar|dashboard|windshield|magnetic|quick[\s-]?release|arca(?:[\s-]swiss)?|camera)\s+mount",
    r"mount\s+(?:kits?|clamps?|holders?|rings?)",
    # lcd
    r"lcd\s+(?:viewfinders?|loupes?|magnifiers?|shades?|panels?|modules?|assembly|repair)",
    r"lcd\s+(?:display\s+)?screen\s+(?:panels?|modules?|assembly|repair)",
    # screen
    r"focusing\s+screen", r"screen\s+(?:loupes?|magnifiers?|shades?|panels?|modules?|assembly|repair)", r"green\s+screen",
    # flash
    r"(?:speedlit\w*|speedlight\w*|ring|macro|external|hot[\s-]?shoe|camera|slave|studio|on-camera|ttl|wireless|xenon|"
    r"bounce|compact|clip-?on)\s+flash",
    r"flash\s+(?:units?|guns?|diffusers?|triggers?|heads?|kits?|modifiers?|reflectors?|benders?|speedlit\w*|speedlight\w*|"
    r"stands?|transmitters?|receivers?|meters?|tubes?|bulbs?|lamps?)",
    # light
    r"(?:led|video|ring|fill|studio|continuous|panel|key|flash|photo|photography|softbox|on-camera|camera|selfie|"
    r"bi-?colou?r|rgb|strobe|night)\s+light",
    r"light\s+(?:stands?|kits?|panels?|box(?:es)?|meters?|modifiers?|bulbs?|tents?|reflectors?|tubes?|wands?|bars?)",
    # card
    r"(?:sd|sdhc|sdxc|cf|cfast|cfexpress|xqd|micro\s?sd(?:hc|xc)?|compact\s?flash|eye-?fi|wi-?fi|gr[ae]y|"
    r"white\s+balance|colou?r|\d+\s?gb)\s+card",
    r"card\s+(?:readers?|cases?|holders?|wallets?)",
]
ACC_EVAL_LAN3 = re.compile(r"\b(?:" + ACC_EVAL_LAN3_WORDS + r")\b|\b(?:" + "|".join(ACC_EVAL_LAN3_PHRASES) + r")\b")


def acc_title(title):
    """Tiêu đề bị loại khỏi đánh giá vì phần đầu có từ phụ kiện (lần sửa (a) ngày 07/10)."""
    if MODE == "truoc_0710":
        return False
    if MODE == "lan2":
        return bool(ACC_EVAL.search(head_main(title)))
    return bool(ACC_EVAL_LAN3.search(head_main(title, plus=False)))


# Red Team N4: token kiểu khẩu độ ("f4", "f2", "f2.8") đứng ngay sau tiêu cự ("70-210mm F4", "12-28 F4", "58mm F2")
# là khẩu độ của ống, không phải tên thân Nikon F4 / F2. Chỉ áp ở lan3.
APER_TOKEN = re.compile(r"f\d{1,2}(?:\.\d+)?$")


def aperture_not_body(tk, i, n):
    return MODE == "lan3" and n == 1 and bool(APER_TOKEN.match(tk[i])) and i > 0 and (
        bool(re.search(r"\d", tk[i - 1])) or tk[i - 1] == "mm")


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
            if aperture_not_body(tk, i, n):
                continue
            for maker, truth in idx.get(k, []):
                if maker not in t_maker:
                    continue
                if n > best:
                    best, cands = n, [truth]
                elif n == best:
                    cands.append(truth)
    if not cands:
        return None, 0, ""
    keyf = lambda tr: (tr["type"], tr["mount"], tr["khung"], tuple(sorted(tr.get("family", []))))
    if len({keyf(c) for c in cands}) > 1:
        return "ambiguous", len(cands), ""
    # cum_nguon: mã mục nguồn nhỏ nhất trong các ứng viên (không phụ thuộc thứ tự set) -> cụm cho bootstrap
    return cands[0], len(cands), min(c["id"] for c in cands)


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
    # (lần sửa (b) ngày 07/10; bản truoc_0710 không có)
    if MODE != "truoc_0710":
        tt = set(ctoks(h))
        entries = [e for e in entries if set(t for t in ctoks(e["name"]) if t not in MAKERS) <= tt]
    if not entries:
        return None
    mounts = set().union(*[e["mounts"] for e in entries])
    # Khung của ống KHÔNG chấm: hệ số crop của Lensfun là của máy dùng để hiệu chỉnh, không phải vòng ảnh.
    return dict(type="ong", mount=next(iter(mounts)) if len(mounts) == 1 else None, mounts=mounts, khung=None,
                name=entries[0]["name"], n=len(entries), id=min(e["id"] for e in entries))


def ctoks(s):
    """Token chuẩn hoá cho tên ống: 'EF-S 18-55mm f/3.5-5.6 IS II' -> ef s 18-55 mm f 3.5-5.6 is ii."""
    s = s.lower().replace("–", "-").replace("f/", "f ")
    return re.findall(r"[a-z]+|\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?", s)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", default=OURS)
    # bắt buộc ghi tên file mới (không ghi đè kết quả lần đo trước; mặc định cũ: OUT_CSV / OUT_JSON)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--bo-danh-gia", required=True, choices=EVAL_MODES)
    ap.add_argument("--half", required=True, choices=["fix", "holdout", "ngoai", "all"])
    args = ap.parse_args()
    global MODE
    MODE = args.bo_danh_gia
    out_csv, out_json = args.out_csv, args.out_json
    ours = list(csv.DictReader(open(args.ours, encoding="utf-8")))
    n_all = len(ours)
    if args.half != "all":
        half = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open(SPLIT, encoding="utf-8"))}
        ours = [o for o in ours if half.get(o["parent_asin"], "ngoai") == args.half]
    print(f"bộ đánh giá: {MODE} | tập: {args.half} ({len(ours):,}/{n_all:,} sản phẩm của {args.ours})")
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
            if acc_title(title):
                truth, _, _ = match_body(title, bidx)
                if truth is not None or (lidx and match_lens(title, lidx)):
                    st["bo_qua_tieu_de_phu_kien"] += 1
                continue
            truth, _, cum = match_body(title, bidx)
            kind = "than_may"
            if truth == "ambiguous":
                st["bo_qua_mo_ho"] += 1
                continue
            if truth is None and lidx:
                truth = match_lens(title, lidx)
                kind = "ong"
                cum = truth["id"] if truth else ""
            if truth is None:
                continue
            st["khop"] += 1
            r = dict(nguon=sname, loai_khop=kind, parent_asin=o["parent_asin"], title=title[:150], ten_nguon=truth["name"],
                     loai_quy_tac=o["item_type"], ngam_quy_tac=o["mount"], khung_quy_tac=o["khung"],
                     loai_dap_an=truth["type"] or "", ngam_dap_an=truth["mount"] or "", khung_dap_an=truth["khung"] or "",
                     loai_dung="", ngam_dung="", khung_dung="", cum_nguon=cum)
            if truth["type"]:
                ok = o["item_type"] == truth["type"]
                r["loai_dung"] = int(ok); st["loai_n"] += 1; st["loai_dung"] += ok
            # ngàm/khung: chỉ so khi loại của quy tắc trùng loại đáp án (lỗi loại đã tính ở trên)
            if truth["type"] and o["item_type"] != truth["type"]:
                rows.append(r); continue
            if not truth["type"] and o["item_type"] not in ("than", "ong"):
                rows.append(r); continue
            single = o["mount"] not in ("khong_ro", "khong_co", "nhieu", "") and ">" not in o["mount"]
            if MODE == "lan3" and truth["mount"] == "khac_ngam":
                # Red Team N4: ngàm của nguồn ngoài bảng mã của nhóm -> không chấm (bản cũ tính là sai)
                r["ngam_dung"] = "dap_an_khac_ngam"; st["ngam_dap_an_khac_ngam"] += 1
            elif truth["mount"]:
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
        if st["ngam_dap_an_khac_ngam"]:
            print(f"  ngàm: không chấm {st['ngam_dap_an_khac_ngam']} sản phẩm có đáp án ngoài bảng mã (khac_ngam)")
    summary["_chay"] = dict(bo_danh_gia=MODE, half=args.half, ours=args.ours, n_san_pham=len(ours))
    cols = list(rows[0].keys())
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    json.dump(summary, open(out_json, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\n-> {out_csv} ({len(rows)} dòng), {out_json}")


if __name__ == "__main__":
    main()
