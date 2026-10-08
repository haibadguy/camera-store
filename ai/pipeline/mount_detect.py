"""
mount_detect.py — Nhận diện LOẠI sản phẩm, NGÀM và KHUNG (ff/apsc/khac) từ tiêu đề + danh mục Amazon.
Dùng bởi 03_mount_compat.py. Phát triển từ bộ khảo sát ai/survey/content3/mountlex.py.

Quy ước mã ngàm và khung: giống docs/labeling_guide.md.
NGUYÊN TẮC: chỉ gán ngàm khi văn bản NÓI RÕ (tên ngàm, tiền tố dòng ống, dòng máy, hoặc hãng + DSLR).
details["Compatible Mountings"] KHÔNG dùng ở đây (QĐ 1) — chỉ lưu để phân tích.
"""
import os
import re
import tomllib

# -----------------------------------------------------------------------------
# 1. Loại sản phẩm
# -----------------------------------------------------------------------------
CUT = re.compile(r"\s(?:with|w/|\+|&|plus|and|bundle|includes?|kit)\s|\s\+|,|\(|\s-\s")


def head(t):
    """Phần đầu tiêu đề (trước with/+/&/bundle...): nơi nói sản phẩm chính là gì."""
    return CUT.split(t, maxsplit=1)[0]


ACC_WORDS = re.compile(r"\b(?:case|bag|pouch|battery|batteries|charger|diffuser|grip|strap|hood|caps?|filters?|adapter|"
                       r"protector|cover|skin|console|propellers?|remote|cable|tripod|bracket|cage|mount\s+plate|"
                       r"screen|eyecup|viewfinder|flash|speedlite|harness|sling|sticker|decal|cleaning|kit\s+only)\b")
LENS_POS = re.compile(r"\d\s?mm(?:\b|(?=f)).*?(?:(?:\b|(?<=mm))f\s?/?\s?\d|\bt\s?\d(?:\.\d)?\b|\b1:\d)"
                      r"|(?:\bf\s?/?\s?\d|\b1:\d).*?\d\s?mm\b")
LENS_NEG = re.compile(r"\b(?:hood|lens\s*caps?|caps?|filters?|adapter|tele-?\s?converter|teleplus|extender|converter|"
                      r"conversion|close-?\s?up|add-?on|attachment|snap-?on|clip|iphone|smartphone|phone|band|"
                      r"follow\s+focus|gear|tumbler|mug|cup|pouch|case|bag|cleaning|extension\s+tube|wrap|skin|sticker|"
                      r"protector|macro\s+lens\s+set|auxiliary|focusing\s+screen|optic)\b"
                      r"|(?<![\d.])0?\.\d{1,2}\s?x\b|\b\d(?:\.\d)?\s?x\s+(?:hd\s+)?(?:telephoto|wide|tele|fisheye)\b")
# Phụ kiện gắn bằng ren phía trước ống / nằm trong thân -> không phụ thuộc ngàm
NO_MOUNT_ACC = re.compile(r"\b(?:filters?|close-?\s?up|focusing\s+screen|conversion|converter\s+lens|snap-?on|clip)\b"
                          r"|(?<![\d.])0?\.\d{1,2}\s?x\b|\b\d(?:\.\d)?\s?x\s+(?:hd\s+)?(?:telephoto|wide|tele|fisheye)\b"
                          r"|\b\d{2}\s?mm\b.*\b(?:wide[\s-]angle|telephoto|fisheye|macro)\s+(?:hd\s+)?lens\b")
# Phụ kiện gắn qua ngàm
MOUNT_ACC = re.compile(r"\btele-?\s?converter|\bteleplus\b|\bextender\b|\bextension\s+tubes?\b")
LENS_STYLE_CAM = re.compile(r"\blens-style\s+camera\b")
ILC_WORDS = re.compile(r"\b(?:dslr|d-slr|digital\s+slr|slr|mirrorless|interchangeable|dslm|compact\s+system|body\s+only)\b")
FIXED_CAM_CATS = ["Point & Shoot Digital", "Instant Cameras", "Film Cameras", "Underwater Photography > Cameras",
                  "Video > Camcorders", "Sports & Action Video"]
NON_PHOTO_CATS = ["Service Plans", "Electronics Warranties"]


# --- Loại theo TIÊU ĐỀ (ưu tiên hơn danh mục; sửa lỗi phân loại 08/10/2026) ---
# "Chủ thể" = phần tiêu đề trước for / fits / compatible / with / + / & / bundle...: nơi nói sản phẩm chính là gì.
# Khác head(): GIỮ "(" và " - " để không cắt mất khẩu độ ("Sony E 55-210mm (SEL55210) F4.5-6.3") hay "(Body Only)".
SUBJ_CUT = re.compile(r"(?:^|[\s(\[,])(?:for|fits?|compatible|designed|works|with|w/|bundles?|bundled|includes?|including|"
                      r"plus|consists?)\b|\s\+|\+\s|\s&\s")


def subject(t):
    return SUBJ_CUT.split(t, maxsplit=1)[0]


# Từ cho biết chủ thể là MÁY ẢNH (thân)
# ("camera lens" không tính; "kit" chỉ tính khi có tiêu cự, vd "X-T30 XF18-55mm Kit" = máy + ống kit)
CAM_NOUN = re.compile(r"\bcameras?\b(?!\s+lens)|\bbody\b|\bdslr\b|\bd-slr\b|\bslr\b|\bmirrorless\b|\brangefinder\b|\bdslm\b|"
                      r"\binterchangeable\b|\bcompact\s+system\b|\d\s?mp\b|\bmegapixels?\b|\d\s?mm\b.*\bkit\b")
# Chủ thể có các từ này thì KHÔNG phải thân máy (phụ kiện nhắc tên máy: pin, ốp, sách hướng dẫn, cốc mắt ngắm...)
# "manual" đứng một mình KHÔNG tính (vd "Pentax K1000 Manual Focus SLR Film Camera" là thân máy); chỉ tính cụm
# chỉ sách hướng dẫn như "instruction manual", "user manual" (sửa 08/10/2026, Red Team nội dung 3 lần 1).
ACC_BODY = re.compile(r"\b(?:accessor(?:y|ies)|replacement|eyepiece|housing|armou?r|coupler|introduction|guide|book|dvd|"
                      r"(?:instruction|user|users|user's|owner|owners|owner's|operating|operation|service|repair|"
                      r"reference)\s+manuals?|training|monopod|shutter|release|dummy|plate|rig|light|microphone|mic|memory|card|lcd|"
                      r"glass|shield|guard|hot\s?shoe|leash|wrap|sleeve|holster|tether|stand|dock|controller|trigger|"
                      r"intervalometer|gps|receiver|transmitter|lens\s+mount|mount\s+adapter|starter\s+kit|software|"
                      r"upgrade|firmware)\b|monopod|tripod")
# Dòng máy ống liền (compact) của các hãng: có tên hãng nhưng không có ngàm.
# FinePix S1–S5 Pro là DSLR ngàm Nikon F, không phải compact -> không chặn (sửa N3, Red Team nội dung 3 lần 1)
COMPACT_LINE = re.compile(r"\b(?:cyber-?shot|dsc-|powershot|coolpix|finepix(?!\s+s[1-5]\s?pro\b)|ixus|elph|easyshare|stylus|tough|pixpro|"
                          r"lumix\s+(?:dmc-|dc-)?(?:fz|zs|tz|lx|fx|fh|fs|sz|ts|xs|lf|zr)\d*)")
# Chủ thể có tiêu cự + khẩu độ nhưng không phải ống máy ảnh
LENS_NEG_TITLE = re.compile(r"\b(?:telescopes?|microscopes?|binoculars?|monoculars?|spotting|scope|projector|cctv|"
                            r"cs[\s-]mount|security|surveillance|webcam|dash|camcorders?|drone|gopro|magnifier|loupe|"
                            r"eyepiece|barlow|glasses|sunglasses|replica|keychains?|key\s+chains?|shotglass|toy|"
                            r"covers?|neoprene|camo(?:uflage)?|foot|plate|collar|handle|quick[\s-]?release|replacement|"
                            r"(?:tripod|mount|adapter|step-?(?:up|down)|reverse|reversing)\s+rings?|"
                            r"(?:1\.4|1\.7|2\.0|2)\s?x)\b|\w+scope\b|\badapt\w*"
                            r"|\d\s?mp\b|\bmegapixels?\b|\b(?:digital|compact|bridge|video|action|instant|underwater|"
                            r"film)\s+cameras?\b")


def title_body(t):
    """Chủ thể của tiêu đề nói đây là THÂN MÁY: có dòng máy + từ chỉ máy ảnh, không có từ phụ kiện / dòng compact,
    và không có tiêu cự+khẩu độ đứng TRƯỚC dòng máy (tránh 'Canon EF 50mm f/1.8 ... Rebel')."""
    s = SUBJ_CUT.split(t, maxsplit=1)[0].split(",")[0]
    if not CAM_NOUN.search(s) or ACC_WORDS.search(s) or ACC_BODY.search(s) or LENS_NEG.search(s) or COMPACT_LINE.search(s):
        return False
    hit = body_series_match(s)
    if not hit:
        return False
    lp = LENS_POS.search(s)
    return not (lp and lp.start() < hit.start())


def title_lens(t):
    """Chủ thể của tiêu đề là ỐNG KÍNH: có tiêu cự + khẩu độ, không có từ phụ kiện / máy ảnh / kính thiên văn..."""
    s = subject(t)
    return bool(LENS_POS.search(s)) and not LENS_NEG.search(s) and not LENS_NEG_TITLE.search(s) \
        and not COMPACT_LINE.search(s)


def category_group(cats):
    p = " > ".join(cats)
    if "Lenses > Camera Lenses" in p:
        return "lens_cat"
    if ("Digital Cameras > DSLR Cameras" in p or "Digital Cameras > Mirrorless Cameras" in p
            or p.endswith("Camera & Photo > Digital Cameras")):
        return "body_cat"
    if any(k in p for k in FIXED_CAM_CATS):
        return "fixed_cam"
    if any(k in p for k in NON_PHOTO_CATS):
        return "non_photo"
    return "other"


# -----------------------------------------------------------------------------
# 2. Ngàm nói rõ trong văn bản
# -----------------------------------------------------------------------------
MM = r"\s?\d{1,3}(?:\.\d)?(?:\s?-\s?\d{1,3})?\s?mm"

MOUNT_PATTERNS = {
    "canon_rf":    [r"\bcanon\s+rf\b(?!-?\d{3}\b)", r"\brf[\s-]?mount", r"\brf-s(?=\d|\b)", r"\brf" + MM,
                    r"\beos\s+r\s+(?:mount|system)"],
    "canon_efm":   [r"\bef-?m\b", r"\bcanon\s+(?:eos\s+)?m[\s-]?mount"],
    "canon_efs":   [r"\bef-?s\b"],
    "canon_ef":    [r"\bcanon\s+ef\b(?!-[sm]\b)", r"\bef[\s-]?mount", r"\bef" + MM, r"\bef/ef-?s\b",
                    r"\bcanon\b.*\bef\s?\d{2,3}(?:-\d{2,3})?\b", r"\bfor\s+canon\s+eos\s+ef\b"],
    "canon_fd":    [r"\bcanon\s+fd\b", r"\bfd[\s-]?mount"],
    "nikon_z":     [r"\bnikon\s+z(?:[\s-]?mount)?\b", r"\bz[\s-]mount\b", r"\bnikkor\s+z\b"],
    "nikon_f":     [r"\bnikon\s+f(?:[\s-]?mount)?\b(?!/)", r"\bf[\s-]mount\b", r"\baf-[sp]\b",
                    r"\bnikon\s+f\s?\((?:fx|dx)\)", r"\bai-s\b"],
    "nikon_1":     [r"\bnikon\s+1\b(?!\d)", r"\b1\s+nikkor\b"],
    "sony_e":      [r"\bsony\s+f?e\b(?!-\d)", r"\bf?e[\s-]mount\b", r"\bemount\b", r"\bfe" + MM,
                    r"\bselp?\d{2,4}", r"\bnex\b", r"\bsony\b.*\bfe\b(?!-)"],
    "sony_a":      [r"\bsal\d{2,5}", r"\bsony\s+a[\s-]?mount\b", r"\ba[\s-]mount\b", r"\bsony/minolta\b",
                    r"\bminolta\s+(?:af|maxxum|a\b|alpha)"],
    "fuji_x":      [r"\bfuji(?:film)?\s+x(?:[\s-]?mount)?\b(?![-\s]?[a-z]{0,3}\d|\s+series)", r"\bx[\s-]mount\b",
                    r"\bxf" + MM, r"\bxc" + MM, r"\bfujinon\s+xf", r"\bxf\d{1,3}(?:-\d{1,3})?mmf"],
    "fuji_g":      [r"\bgfx\b", r"\bg[\s-]mount\b"],
    "mft":         [r"\bmicro\s*(?:four|4)[\s-]*(?:thirds|/\s?3)", r"\bm4/3\b", r"\bmft\b", r"\bm43\b",
                    r"\bm\.?\s?zuiko\b", r"\blumix\s+g\s?(?:x\s)?(?:ii\s)?(?:vario|\d)"],
    "four_thirds": [r"(?<!micro )(?<!micro)\bfour\s*thirds\b", r"(?<!\bm\.)(?<!\bm\. )(?<!\bm )\bzuiko\s+digital\b"],
    "l_mount":     [r"\bl[\s-]mount\b", r"\bleica\s+l\b"],
    "leica_m":     [r"\bleica\s+m(?:[\s-]?mount)?\b(?!-?\d)"],
    "pentax_k":    [r"\bpentax\s+k(?:a?f\d?)?(?:[\s-]?mount)?\b(?!-?\d)", r"\bk[\s-]mount\b", r"\bkaf\d?\b",
                    r"\bpk\s+mount"],
    "pentax_q":    [r"\bpentax\s+q\b"],
    "samsung_nx":  [r"\bsamsung\s+nx(?:[\s-]?mount)?\b(?!\d)", r"\bnx[\s-]mount\b"],
    "sigma_sa":    [r"\bsigma\s+sa\b", r"\bsa[\s-]mount\b"],
    "m42":         [r"\bm42\b"],
    "t_mount":     [r"\bt2?[\s-]mount\b", r"\bt-?2\s+(?:adapter|ring)"],
    "c_mount":     [r"\bc[\s-]mount\b"],
}
_MP = {m: [re.compile(p) for p in ps] for m, ps in MOUNT_PATTERNS.items()}


def find_mounts(text):
    """{mã_ngàm: (vị_trí, chuỗi_khớp)} cho mọi ngàm được nói rõ."""
    t = (text or "").lower()
    hits = {}
    for m, regs in _MP.items():
        for r in regs:
            mo = r.search(t)
            if mo:
                hits[m] = (mo.start(), mo.group(0))
                break
    if "four_thirds" in hits and "mft" in hits:
        t2 = re.sub(r"micro\s*(?:four|4)[\s-]*(?:thirds|/\s?3)", "", t)
        if not re.search(r"\bfour\s*thirds\b", t2):
            del hits["four_thirds"]
    # "Canon EF/EF-S" hay "for Canon EF EF-S": ống ngàm EF dùng được trên cả 2 loại thân -> coi là EF
    if "canon_ef" in hits and "canon_efs" in hits:
        if not re.search(r"\bef-?s\s?\d", t):          # không có ống EF-S cụ thể (vd "EF-S 18-55")
            del hits["canon_efs"]
    return hits


# Ống: hãng + "DSLR/SLR" -> ngàm DSLR duy nhất của hãng
SLR = r"(?:dslr|d-slr|digital\s+slr|slr|reflex)s?"
BRAND_SLR = [
    ("canon_ef",    [rf"\bcanon\b.*\b{SLR}\b", rf"\b{SLR}\b.*\bcanon\b", r"\bcanon\s+eos\s+(?:digital\s+)?rebel\b",
                     r"\bfor\s+canon\s+eos\s+(?:\d{1,4}d|[1-9]d|rebel)", r"\bcanon\s+eos\s+(?:digital|film)\b"]),
    ("nikon_f",     [rf"\bnikon\b.*\b{SLR}\b", rf"\b{SLR}\b.*\bnikon\b", r"\baf(?:-d)?\s+(?:zoom-)?(?:micro-)?nikkor\b",
                     r"\bfor\s+nikon\s+d\d{2,4}\b", r"\bnikon\s+af\b", r"\bnikkor\b.*\b\d+mm\s+f/?\d[\d.]*\s?d\b"]),
    ("sony_a",      [rf"\b(?:minolta|sony)\b.*\b{SLR}\b(?!.*\b(?:nex|e-?mount)\b)", r"\bminolta\b.*\baf\b",
                     r"\bmaxxum\b"]),
    ("pentax_k",    [rf"\bpentax\b.*\b{SLR}\b", r"\bpentax\s+(?:smc\s+)?(?:d\s?fa|da|fa)\b", r"\bpentax-(?:d\s?fa|da|fa)\b",
                     r"\bhd\s+pentax-"]),
    ("four_thirds", [rf"\bolympus\b.*\b{SLR}\b", r"(?<!micro\s)\b4/3\s+(?:digital\s+)?(?:cameras|dslr|system)",
                     r"\bolympus\b.*\be\s+series\b"]),
]
_BS = [(m, [re.compile(p) for p in ps]) for m, ps in BRAND_SLR]
MIRRORLESS_HINT = re.compile(r"\bmirrorless\b|\beos\s?[mr]\d*\b|\bnex\b|\bnikon\s+z\b|\bnikon\s+1\b")


def find_series_mount(text):
    """Ống/phụ kiện nhắc tên dòng THÂN MÁY ('for Fuji X-T2', 'for Nikon D3200'): suy ngàm từ dòng máy đó.
    Thân Canon APS-C (canon_efs) -> ống hãng thứ ba dùng ngàm EF (ống EF-S chính hãng đã bắt ở find_mounts)."""
    t = (text or "").lower()
    found = {}
    for brand, r, m, k, n in _SERIES:
        if brand.search(t):
            mo = r.search(t)
            if mo:
                m2 = "canon_ef" if m == "canon_efs" else m
                found.setdefault(m2, (mo.start(), mo.group(0)))
    return found


def find_slr_mount(text):
    t = (text or "").lower()
    if MIRRORLESS_HINT.search(t):
        return {}
    out = {}
    for m, regs in _BS:
        for r in regs:
            mo = r.search(t)
            if mo:
                out[m] = (mo.start(), mo.group(0)[:40])
                break
    return out


# -----------------------------------------------------------------------------
# 3. Thân máy: dòng máy -> (ngàm, khung). Thứ tự quan trọng: luật cụ thể trước.
# -----------------------------------------------------------------------------
# (điều kiện hãng, regex dòng máy, ngàm, khung, ghi chú)
BODY_SERIES = [
    # Canon
    ("canon|eos", r"\beos[\s-]?(?:r1|r3|r5|r6|r8|rp|ra)\b|\beos[\s-]?r\b(?!\d)", "canon_rf", "ff", "EOS R full-frame"),
    ("canon|eos", r"\beos[\s-]?(?:r7|r10|r50|r100)\b", "canon_rf", "apsc", "EOS R APS-C"),
    ("canon|eos", r"\beos[\s-]?m(?:\d{1,3})?(?:\s?mark\s?ii)?\b", "canon_efm", "apsc", "EOS M"),
    ("canon|eos", r"\b(?:eos[\s-]?)?(?:5ds\s?r?|5d|6d|1ds|1d\s?x|1d\s?c)(?:\s?(?:mark|mk)\s?(?:ii|iii|iv|2|3|4))?\b",
     "canon_ef", "ff", "DSLR full-frame"),
    # chỉ khớp TÊN máy phim cụ thể; đã bỏ mẫu "eos ... film|35mm" (dễ bắt nhầm "EOS Rebel T7 + 35mm f/1.8", Red Team T1)
    ("canon|eos", r"\beos[\s-]?1v\b|\b(?:elan|rebel\s+(?:g(?:ii)?|k2|ti|2000|x))\b", "canon_ef", "ff",
     "[phim] EOS"),
    ("canon", r"\b(?:ae-1(?:\s+program)?|a-1|at-1|av-1|al-1|ftb|t50|t70|t90)\b|(?<![\d.])f-1\b(?!\.)", "canon_fd", "ff",
     "[phim] Canon FD"),
    ("canon|eos", r"\b(?:eos[\s-]?)?1d(?:\s?(?:mark|mk)\s?(?:ii|iii|iv|2|3|4)\s?n?)?\b", "canon_ef", "khac",
     "APS-H (1D Mk I-IV)"),
    ("canon|eos", r"\b(?:eos[\s-]?)?(?:10d|d30|d60)\b", "canon_ef", "apsc", "APS-C đời đầu, không nhận EF-S"),
    ("canon|eos|rebel", r"\brebel\b|\bkiss\b|\beos[\s-]?(?:\d{3,4}d|[2-9]0da?|7d)\b|\b(?:[2-9]0da?|7d|\d{3,4}d)\b",
     "canon_efs", "apsc", "DSLR APS-C nhận EF-S"),
    # Nikon
    ("nikon", r"\bz\s?(?:50|30|fc)\b|\bz\s?50\s?ii\b", "nikon_z", "apsc", "Z DX"),
    ("nikon", r"\bz\s?(?:5|6|7|8|9|f)(?:\s?(?:ii|iii|2|3))?\b", "nikon_z", "ff", "Z FX"),
    ("nikon", r"\bd(?:3[sx]?|4s?|5|6|600|610|700|750|780|800e?|810a?|850)\b|\bdf\b", "nikon_f", "ff", "DSLR FX"),
    ("nikon", r"\bnikon\s+(?:f\d{1,3}|f100|fm\d?|fe\d?|n\d{2,4})\b", "nikon_f", "ff", "[phim] Nikon ngàm F"),
    ("nikon", r"\bd\d{2,4}[a-z]?\b|\bd-?\d{3,4}\b|\bd[12][hx]s?\b", "nikon_f", "apsc", "DSLR DX (gồm D1/D2)"),
    ("nikon", r"\bnikon\s+1\b|\bnikon\s+(?:j[1-5]|v[1-3]|s[12]|aw1)\b", "nikon_1", "khac", "Nikon 1"),
    ("fuji", r"\bfinepix\s+s[1235]\s?pro\b", "nikon_f", "apsc", "Fujifilm S Pro (ngàm F)"),
    # Sony E
    ("sony|alpha", r"\bilce-?(?:7|9|1)\w*|\ba7\s?(?:r|s|c)?\s?(?:ii|iii|iv|v|2|3|4|5|cr|cii)?\b|\ba9\s?(?:ii|iii)?\b"
                   r"|\ba1\b|\balpha\s+(?:7|9|1)(?:[rsc]|cr)?\b|\bfx3\b|\bzv-e1\b", "sony_e", "ff", "E full-frame"),
    ("sony|alpha", r"\bnex[\s-]?[a-z]?\d|\bqx1\b|\bilce-?[3-6]\d{3}|\ba[3-6]\d{3}\b|\bzv-e10\b|\bfx30\b|\balpha\s+[3-6]\d{3}\b",
     "sony_e", "apsc", "E APS-C"),
    # Sony A
    ("sony|alpha|minolta", r"\b(?:dslr-?)?a(?:850|900)\b|\b(?:slt-?|ilca-?)?a?99(?:v|\s?ii|m2)?\b", "sony_a", "ff",
     "A full-frame"),
    ("sony|alpha|minolta", r"\bdslr-?a\d{3}|\bslt-?a\d{2}|\bilca-?\d{2}|\ba(?:33|35|37|55|57|58|65|68|77)(?:v|\s?ii)?\b"
                           r"|\b(?:dslr-?)?a(?:100|200|230|290|300|330|350|380|390|450|500|550|560|580|700)[a-z]{0,2}\b"
                           r"|\bmaxxum\s+\d+d\b|\bdynax\s+\d+d\b", "sony_a", "apsc", "A APS-C"),
    ("minolta|maxxum|dynax", r"\b(?:maxxum|dynax)\s+\d{1,4}(?:xi|si|i)?\b", "sony_a", "ff",
     "[phim] Minolta Maxxum/Dynax (ngàm A)"),
    # Fujifilm
    ("fuji", r"\bx-?(?:t|e|pro|h|a|m)\d|\bx-?s\d{2}", "fuji_x", "apsc", "Fujifilm X (X-S10/S20; X-S1 là máy ống liền)"),
    ("fuji", r"\bgfx\b", "fuji_g", "khac", "GFX medium format"),
    # Olympus / OM / Panasonic
    ("olympus|om system|om-d", r"\bom-d\b|\be-m\d|\be-p[lm]?\d|\bpen-f\b|\bom-[15]\b(?!.*\b(?:film|35mm)\b)", "mft", "khac",
     "MFT (OM-1/OM-5 số; OM-1 phim 35mm ngàm OM thì loại)"),
    ("olympus", r"\b(?:evolt\s+)?e-?(?:1|3|5|30|300|330|400|410|420|450|500|510|520|600|620)\b", "four_thirds", "khac",
     "Four Thirds DSLR"),
    ("panasonic|lumix", r"\b(?:dmc-|dc-)?g(?:h|x|f|m)?\d{1,3}[a-z]{0,6}\b", "mft", "khac", "Lumix G (MFT)"),
    ("panasonic|lumix", r"\b(?:dc-)?s(?:1|1r|1h|5|5ii|5iix|9)\b", "l_mount", "ff", "Lumix S"),
    ("leica", r"\bsl\d?\b", "l_mount", "ff", "Leica SL"),
    ("leica", r"\b(?:cl|tl\d?)\b", "l_mount", "apsc", "Leica CL/TL"),
    ("leica", r"\bm(?:9|10|11|240|262)\b|\bm-[ep]\b|\bm\s+typ", "leica_m", "ff", "Leica M số"),
    ("leica", r"\bm8(?:\.2)?\b", "leica_m", "khac", "Leica M8 (APS-H, crop 1,33)"),
    ("leica", r"\bm[2-7]\b", "leica_m", "ff", "[phim] Leica M 35mm"),
    # Pentax
    ("pentax|asahi", r"\bspotmatic\b", "m42", "ff", "[phim] Spotmatic (ngàm M42)"),
    ("pentax", r"\bk-?1000\b|\bme\s+(?:super|f)\b|\bmx\b(?!-)|\bsuper\s+program\b|\bprogram\s+(?:a|plus)\b"
               r"|\b(?:zx|mz|pz)-\d+\b", "pentax_k", "ff", "[phim] Pentax ngàm K"),
    ("pentax", r"\bk-?1\b", "pentax_k", "ff", "K-1"),
    ("pentax", r"\bk-?(?:\d{1,2}|\d{2,3}d|\d{3,4}|s\d|r|x|p|f|01|m)(?:\s?i{2,3})?\b|\bkp\b|\*ist|\bk\d{3}d\b", "pentax_k", "apsc", "K APS-C"),
    ("pentax", r"\bpentax\s+q(?:\d+|-s1)?\b", "pentax_q", "khac", "Pentax Q"),
    # Samsung, Sigma
    ("samsung", r"\bnx\s?\d{1,4}(?![\d-]|\s?mm)[a-z]*\b(?!.*\bmini\b)|\bgalaxy\s+nx\b", "samsung_nx", "apsc",
     "Samsung NX (không bắt 'NX 60mm', 'NX 18-55mm' của ống)"),
    ("sigma", r"\bsd\s?(?:1|9|10|14|15)\b|\bsd\s+quattro\b", "sigma_sa", "apsc", "Sigma SD"),
]
_SERIES = [(re.compile(r"\b(?:" + b + r")"), re.compile(p), m, k, n) for b, p, m, k, n in BODY_SERIES]


def body_series_match(s):
    """Như body_series nhưng trả về đối tượng khớp (để biết vị trí). s đã viết thường."""
    for brand, r, m, k, n in _SERIES:
        if brand.search(s):
            mo = r.search(s)
            if mo:
                return mo
    return None


def body_series(title):
    """Trả về (ngàm, khung, chuỗi_khớp, ghi_chú) của luật dòng máy đầu tiên khớp, hoặc None.
    Chỉ đọc CHỦ THỂ của tiêu đề (subject): phần "for Canon EOS 7D...", "with ..." nói về máy KHÁC, không phải
    sản phẩm này (sửa T1, Red Team nội dung 3 lần 1; vd ống "Canon EF-S 55-250mm ... for Canon EOS 7D" từng ra thân)."""
    t = subject(title.lower())
    for brand, r, m, k, n in _SERIES:
        if not brand.search(t):
            continue
        mo = r.search(t)
        if mo:
            return m, k, mo.group(0), n
    return None


# -----------------------------------------------------------------------------
# 4. Khung (vòng ảnh) của ống kính
# -----------------------------------------------------------------------------
MOUNT_FIXED_KHUNG = {"canon_efs": "apsc", "canon_efm": "apsc", "fuji_x": "apsc", "samsung_nx": "apsc",
                     "mft": "khac", "four_thirds": "khac", "nikon_1": "khac", "pentax_q": "khac", "fuji_g": "khac"}
# Mã SEL / SAL của Sony KHÔNG cho biết khổ (Red Team T2): đã bỏ khỏi hai regex dưới, xem nhánh Sony trong lens_khung.
LENS_APSC = re.compile(r"\bef-?s\b|\brf-s(?=\d|\b)|\bdx\b|\bdt\b|\bdc\b|\bdi[\s-]?ii\b(?!i)|\bdi\s?iii-a\b|\bpentax[\s-]+(?:smc\s+)?da\b"
                       r"|\bhd\s+da\b|\bda\s?\*|\bda\s+\d|\baps-?c\b|\bsony\s+e\s+\d|\bcrop\b")
LENS_FF = re.compile(r"\bfe\b|\bfx\b(?!-)|\bdg\b|\bdi\b(?![\s-]?ii)|\bdi\s?iii\b(?!-a)|\bfull[\s-]?frame\b|\bd\s?fa\b"
                     r"|\bfa\b|\bcanon\s+ef\s?\d|^canon\b.*\bef\s?\d|\brf\s?\d|\bnikkor\s+z\b(?!.*\bdx\b)"
                     r"|\baf-[sp]\b(?!.*\bdx\b)|\b35mm\s+film\b"
                     # ống Nikon AF / AF-D đời trước AF-S đều là FX; dòng Zeiss Otus/Milvus/Classic cho DSLR là FF
                     r"|\bnikon\s+af\b(?!.*\bdx\b)|\baf(?:-d)?\s+(?:zoom-)?(?:micro-)?nikkor\b(?!.*\bdx\b)"
                     r"|\bzeiss\b.*\b(?:otus|milvus|distagon|planar|makro-planar|sonnar)\b")


# --- Ống Sony (Red Team T2, 08/10/2026) ---
# Áp cho ống ngàm sony_e / sony_a có tiêu đề mở đầu bằng "Sony". Thứ tự:
#   1. chữ trong phần đầu tiêu đề: "FE" -> ff; "DT", "E <tiêu cự>", "APS-C" -> apsc (trang Sony: tên ống FF bắt đầu bằng FE,
#      ống APS-C bắt đầu bằng E; ống DT là ống cho cảm biến APS-C — nguồn sony_e_apsc, sony_dt trong mount_rules.toml);
#   2. không có chữ nào -> tra mã SEL/SELP/SAL trong ai/config/sony_lens_codes.toml (mỗi mã có trang thông số Sony);
#   3. có mã mà mã không có trong bảng -> khong_ro (không đoán khổ theo mã).
# Không có chữ, không có mã -> dùng luật khung chung bên dưới.
SONY_CODES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "sony_lens_codes.toml")
SONY_CODES = {c: v["khung"] for c, v in tomllib.load(open(SONY_CODES_FILE, "rb"))["codes"].items()}
SONY_BRAND = re.compile(r"^\s*sony\b")
SONY_WORDS = [("ff", re.compile(r"\bfe\b(?!-)|\bfe\s?\d")),
              ("apsc", re.compile(r"\bdt\b|\b(?:sony\s+)?e\s+(?:pz\s+)?\d{1,3}(?:-\d{1,3})?\s?mm|\baps-?c\b"))]
SONY_CODE = re.compile(r"\b(?:selp?|sal)\d[0-9a-z]*\b")


def sony_lens_khung(t):
    """t = head(tiêu đề viết thường). Trả (khung, evidence) hoặc None nếu không có chữ hay mã nào."""
    hits = [(k, m.group(0)) for k, rx in SONY_WORDS for m in [rx.search(t)] if m]
    if hits:
        ks = {k for k, _ in hits}
        ev = " / ".join(w for _, w in hits)
        return (ks.pop(), f"sony chữ: {ev}") if len(ks) == 1 else ("khong_ro", f"sony mâu thuẫn: {ev}")
    codes = sorted({m.group(0).upper() for m in SONY_CODE.finditer(t)})
    if codes:
        ks = {SONY_CODES.get(c) for c in codes}
        if None in ks:
            return "khong_ro", f"sony mã chưa có nguồn: {'/'.join(c for c in codes if c not in SONY_CODES)}"
        return (ks.pop(), f"sony mã: {'/'.join(codes)}") if len(ks) == 1 else ("khong_ro", f"sony mã mâu thuẫn: {'/'.join(codes)}")
    return None


def lens_khung(title, mount):
    if mount in MOUNT_FIXED_KHUNG:
        return MOUNT_FIXED_KHUNG[mount], "theo ngàm"
    t = head(title.lower())
    if mount in ("sony_e", "sony_a") and SONY_BRAND.search(t):
        s = sony_lens_khung(t)
        if s:
            return s
    a, f = LENS_APSC.search(t), LENS_FF.search(t)
    if mount == "canon_rf" and re.search(r"\brf-s", t):
        return "apsc", "rf-s"
    if a and not f:
        return "apsc", a.group(0)
    if f and not a:
        return "ff", f.group(0)
    if a and f:
        return "khong_ro", f"mâu thuẫn: {a.group(0)} / {f.group(0)}"
    return "khong_ro", ""


def body_khung_from_title(title):
    t = title.lower()
    if re.search(r"\bfull[\s-]?frame\b|\bfx[\s-]format\b", t):
        return "ff"
    if re.search(r"\baps-?c\b|\bdx[\s-]format\b", t):
        return "apsc"
    return "khong_ro"


# -----------------------------------------------------------------------------
# 5. Hãng thứ ba hay bán nhiều bản ngàm dưới 1 parent_asin (QĐ 4)
# -----------------------------------------------------------------------------
# Hãng thứ ba = MỌI hãng KHÔNG thuộc danh sách chính hãng dưới đây (sửa N2, Red Team nội dung 3 lần 1: danh sách
# hãng thứ ba liệt kê tay bị sót Brightin Star, AstrHori, SIRUI...). Hãng xác định bằng phần ĐẦU tiêu đề.
# Chính hãng = hãng làm cả thân máy lẫn ống cho đúng ngàm của mình, nên mỗi ống chỉ có 1 ngàm:
#   Canon; Nikon (kể cả tiêu đề mở đầu bằng dòng ống "AF-S/AF-P ...", "AF ... Nikkor", "Nikkor"); Sony;
#   Fujifilm / Fuji / Fujinon; Olympus, OM System / OM Digital; Panasonic / Lumix; Leica; Pentax (cả "HD PENTAX",
#   "smc PENTAX") / Ricoh; Samsung; Minolta / Konica Minolta; Hasselblad.
# Sigma CỐ Ý không nằm trong danh sách: Sigma có làm thân (SA, L) nhưng bán cùng một ống cho nhiều ngàm.
# Zeiss cũng vậy (ống cho nhiều ngàm). Tiêu đề không mở đầu bằng tên hãng (vd "500mm f/8 ...") -> coi là hãng thứ ba.
FIRST_PARTY = re.compile(r"^\s*(?:canon|nikon|nikkor|af-[sp]\b|af(?:-d)?\s+(?:dx\s+)?(?:zoom-|micro-)?nikkor|sony|"
                         r"fujifilm|fuji|fujinon|olympus|om\s+(?:system|digital)|panasonic|lumix|leica|pentax|hd\s+pentax|"
                         r"smc\s+pentax|ricoh|samsung|minolta|konica\s+minolta|hasselblad)\b", re.I)


def is_third_party(title):
    return not FIRST_PARTY.search(title or "")


FILM_TAG = "[phim]"     # ghi chú của luật dòng máy phim trong BODY_SERIES bắt đầu bằng nhãn này

# Phần combo nói về ngàm chuyển / bộ chuyển đổi (không phải ngàm của ống): "& MC-11 Mount Converter ... for Sony E".
# Vòng / adapter ngàm T KHÔNG bỏ, vì theo QĐ 9 ngàm của ống ngàm T là ngàm của vòng.
_BUNDLE_SEP = re.compile(r"\s&\s|\s\+|\+\s|\swith\s|\sw/")
_ADAPTER_PART = re.compile(r"\b(?:adapter|converter|mc-\d+)\b")


def drop_adapter_bundle(t):
    for mo in _BUNDLE_SEP.finditer(t):
        seg = t[mo.end():]
        nxt = _BUNDLE_SEP.search(seg)
        part = seg[:nxt.start()] if nxt else seg
        if _ADAPTER_PART.search(part) and find_mounts(seg) and "t_mount" not in find_mounts(part) \
                and not re.search(r"\btele-?\s?converter|\bteleconverter", part):
            return t[:mo.start()]
    return t


# -----------------------------------------------------------------------------
# 6. Hàm tổng hợp cho 1 sản phẩm
# -----------------------------------------------------------------------------
def classify_item(title, cats, n_child_asin=0):
    """Trả về dict: item_type, mount, khung, mount_source, evidence, uncertain, uncertain_reason."""
    title = title or ""
    t = title.lower()
    h = head(t)
    g = category_group(cats)
    out = dict(item_type="phu_kien", mount="khong_co", khung="", mount_source="", evidence="",
               uncertain=False, uncertain_reason="", may_phim=False)

    # ---- Loại ----
    # 1) Tiêu đề trước: thân / ống nói rõ trong chủ thể của tiêu đề thì không cần danh mục
    #    (ống bán kèm combo nằm ở "Accessory Kits", thân bị xếp vào "Point & Shoot", máy phim SLR...).
    #    Ống theo tiêu đề chỉ áp cho danh mục "khác": danh mục ống / thân / máy ống liền đã có luật riêng bên dưới.
    if g != "non_photo" and title_body(t):
        typ = "than"
    elif g == "other" and title_lens(t):
        typ = "ong"
    # 2) Không rõ từ tiêu đề: dùng danh mục như cũ
    elif g == "lens_cat":
        if LENS_NEG.search(h):
            typ = "phu_kien"
        elif LENS_POS.search(t) or (re.search(r"\d\s?mm", t) and find_mounts(title)):
            typ = "ong"
        else:
            typ = "phu_kien"
    elif g == "body_cat":
        if ACC_WORDS.search(h):
            typ = "phu_kien"
        elif re.search(r"\blens\b", h) and LENS_POS.search(t) and not body_series(title):
            typ = "ong"           # ống kính nằm nhầm trong danh mục máy ảnh
        elif body_series(title) or find_mounts(h) or ILC_WORDS.search(t):
            typ = "than"
        else:
            typ = "khac"          # máy ống liền nằm trong danh mục DSLR/Digital Cameras (vd Olympus E-10, FinePix S)
    elif g in ("fixed_cam", "non_photo"):
        typ = "khac"
    else:
        typ = "phu_kien"
    if LENS_STYLE_CAM.search(t):
        typ = "khac"
    out["item_type"] = typ

    # ---- Ngàm + khung ----
    if typ == "than":
        s = body_series(title)
        # Máy phim (QĐ 16): luật dòng máy có nhãn [phim], hoặc chủ thể tiêu đề có chữ "film"
        out["may_phim"] = bool(s and s[3].startswith(FILM_TAG)) or bool(re.search(r"\bfilm\b", subject(t)))
        if s:
            out.update(mount=s[0], khung=s[1], mount_source="dong_may", evidence=s[2])
        else:
            tm = find_mounts(h)
            if len(tm) == 1:
                m = next(iter(tm))
                out.update(mount=m, khung=MOUNT_FIXED_KHUNG.get(m, body_khung_from_title(title)),
                           mount_source="tieu_de", evidence=tm[m][1])
            elif len(tm) > 1:
                out.update(mount="nhieu", mount_source="tieu_de", evidence="|".join(v[1] for v in tm.values()))
            else:
                out.update(mount="khong_ro")
    elif typ == "ong":
        tl = drop_adapter_bundle(t)        # bỏ phần combo nói về ngàm chuyển (vd "& MC-11 Mount Converter ... Sony E")
        tm = find_mounts(h) or find_mounts(tl)
        src = "tieu_de"
        if not tm:
            tm = find_series_mount(tl)
            src = "dong_may_nhac_toi"
        if not tm:
            tm = find_slr_mount(tl)
            src = "hang_slr"
        # QĐ 9: ống ngàm T -> ngàm của vòng T đi kèm; có vòng/adapter mà không rõ cho máy nào -> không rõ
        if "t_mount" in tm and len(tm) <= 2:
            ring = {m: v for m, v in tm.items() if m != "t_mount"} or find_series_mount(tl) or find_slr_mount(tl)
            if len(ring) == 1:
                tm, src = ring, "vong_t"
            elif re.search(r"\b(?:ring|adapter)\b", tl) or ring:
                tm, src = {}, "vong_t"
        if len(tm) == 1:
            m = next(iter(tm))
            k, kev = lens_khung(title, m)
            out.update(mount=m, khung=k, mount_source=src, evidence=tm[m][1] + (f" | khung: {kev}" if kev else ""))
        elif len(tm) > 1:
            out.update(mount="nhieu", mount_source=src, evidence="|".join(v[1] for v in tm.values()))
        else:
            out.update(mount="khong_ro")
        if out["mount"] not in ("khong_ro", "nhieu") and is_third_party(title) and n_child_asin > 1:
            out.update(uncertain=True, uncertain_reason="hang_thu_ba_nhieu_bien_the")
    elif typ == "phu_kien":
        tm = {} if (NO_MOUNT_ACC.search(h) and not MOUNT_ACC.search(h)) else find_mounts(title)
        src = "tieu_de"
        if not tm and MOUNT_ACC.search(h):           # teleconverter, ống nối: gắn qua ngàm
            tm, src = find_series_mount(t), "dong_may_nhac_toi"
            if not tm:
                tm, src = find_slr_mount(t), "hang_slr"
        if len(tm) == 1:
            m = next(iter(tm))
            out.update(mount=m, mount_source=src, evidence=tm[m][1])
        elif len(tm) == 2 and re.search(r"\badapt|\bconverter|\bbooster|\bto\b", t):
            a, b = sorted(tm, key=lambda m: tm[m][0])       # ngàm nói trước = phía ống, nói sau = phía thân
            out.update(mount=f"{a}>{b}", mount_source=src, evidence=f"{tm[a][1]} -> {tm[b][1]}")
        elif len(tm) >= 2:
            out.update(mount="nhieu", mount_source=src, evidence="|".join(v[1] for v in tm.values()))
    # khac: giữ khong_co
    if out["mount"] in ("khong_co", "khong_ro", "nhieu") or ">" in out["mount"]:
        out["khung"] = ""
    return out
