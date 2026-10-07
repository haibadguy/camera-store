"""KHẢO SÁT v2 (không phải pipeline). Đầu vào: meta_full_k5.jsonl. Đầu ra: survey2_items.jsonl + bảng số.
Loại sản phẩm: categories (như script 03 nhưng chặt hơn) + lọc từ khóa phụ kiện trên tiêu đề.
Ngàm theo nguồn:
  T   = tiêu đề nói rõ ngàm (mountlex.find_mounts)
  SLR = (ống kính) tiêu đề nói hãng + DSLR/SLR (mountlex.find_slr_mounts)
  SER = (thân máy) dòng máy trong tiêu đề -> ngàm
  CM  = details['Compatible Mountings']
  TX  = features + description nói rõ ngàm (chỉ thống kê, không dùng)"""
import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, __import__("os").path.dirname(__file__))
from mountlex import find_mounts, find_slr_mounts, cm_mounts

F, OUT = sys.argv[1], sys.argv[2]

SERIES = [
    (r"\bcanon\b.*\beos\s?r(?:\d{1,2}|p|a)?\b|\beos\s?r(?:\d{1,2}|p|a)\b", "Canon RF"),
    (r"\beos\s?m(?:\d{1,3})?\b", "Canon EF-M"),
    (r"\b(?:canon|eos)\b.*(?:\brebel\b|\beos[\s-]?(?:\d{1,4}d|[1-9]d[sx]?|1v|elan|kiss)\b|\b(?:[1-9]d|\d{2,4}d)\s+(?:mark|mk))", "Canon EF"),
    (r"\bnikon\s+z\s?(?:\d|fc|f\b)|\bz\s?(?:5|6|7|8|9|30|50|fc)\s?(?:ii|iii)?\b.*\bmirrorless|\bnikon\s+z\b", "Nikon Z"),
    (r"\bnikon\s+d\d{1,4}[a-z]?\b|\bnikon\s+df\b|\bnikon\s+f\d{1,3}\b|\bnikon\s+n\d{2,4}\b", "Nikon F"),
    (r"\bnikon\s+1\b", "Nikon 1"),
    (r"\bsony\b.*(?:\b(?:ilce|nex)[\s-]?\d|\ba[3-6]\d{3}\b|\ba7[rsc]?\b|\ba7\s?(?:ii|iii|iv)\b|\ba7[rsc]\s?(?:ii|iii|iv|v)\b|\ba9\b|\bzv-e1\d?\b|\bfx30?\b|\balpha\s+(?:7|9|1)\b)", "Sony E"),
    (r"\bslt-?a\d{2}v?\b|\bdslr-?a\d{3}\b|\bilca-?\d|\bsony\b.*\ba(?:33|35|37|55|57|58|65|68|77|99)(?:v|\s?ii)?\b|\bmaxxum\b|\bdynax\b", "Sony A"),
    (r"\bfuji(?:film)?\b.*\bx-?(?:t|e|pro|h|s|a|m)\d", "Fujifilm X"),
    (r"\bgfx\b", "Fujifilm G"),
    (r"\bom-d\b|\be-m\d|\be-p[lm]?\d|\bpen-f\b|\bom system\b", "Micro Four Thirds"),
    (r"\b(?:lumix\s+)?(?:dmc-|dc-)g(?:h|x|f)?\d|\blumix\s+g(?:h|x|f)?\d", "Micro Four Thirds"),
    (r"\blumix\s+(?:dc-)?s\d|\bdc-s\d|\bleica\s+(?:sl|cl|tl)\d?\b", "L-Mount"),
    (r"\bolympus\b.*\b(?:evolt\s+)?e-?(?:1|3|5|30|300|330|400|410|420|450|500|510|520|600|620)\b", "Four Thirds"),
    (r"\bpentax\b.*(?:\bk-?\d{1,2}\b|\bkp\b|\bk-s\d|\bk-r\b|\bk-x\b|\bk10d\b|\bk20d\b|\bk200d\b|\*ist)", "Pentax K"),
    (r"\bpentax\s+q", "Pentax Q"),
    (r"\bsamsung\s+nx\s?\d", "Samsung NX"),
    (r"\bleica\s+m\d|\bleica\s+m-[ep]\b", "Leica M"),
]
SERIES = [(re.compile(p), m) for p, m in SERIES]


def series_mounts(title):
    t = title.lower(); out = {}
    for r, m in SERIES:
        mo = r.search(t)
        if mo and m not in out:
            out[m] = mo.group(0)[:30]
    return out


ACC_WORDS = re.compile(r"\b(?:case|bag|pouch|battery|batteries|charger|diffuser|grip|strap|hood|caps?|filters?|adapter|"
                       r"protector|cover|skin|console|propellers?|remote|cable|tripod|bracket|cage|mount\s+plate|"
                       r"screen|eyecup|viewfinder|flash|speedlite|harness|sling|sticker|decal|cleaning|kit\s+only)\b")
LENS_POS = re.compile(r"\d\s?mm(?:\b|(?=f)).*?(?:(?:\b|(?<=mm))f\s?/?\s?\d|\bt\s?\d(?:\.\d)?\b|\b1:\d)|(?:\bf\s?/?\s?\d|\b1:\d).*?\d\s?mm\b")
LENS_NEG = re.compile(r"\b(?:hood|lens\s*caps?|caps?|filters?|adapter|tele-?\s?converter|converter|conversion|close-?\s?up|"
                      r"add-?on|attachment|snap-?on|clip|iphone|smartphone|phone|band|follow\s+focus|gear|tumbler|mug|"
                      r"cup|pouch|case|bag|cleaning|extension\s+tube|wrap|skin|sticker|protector|macro\s+lens\s+set|"
                      r"auxiliary)\b|\b0\.\d{1,2}\s?x\b|\b\d(?:\.\d)?\s?x\s+(?:hd\s+)?(?:telephoto|wide|tele|fisheye)")


CUT = re.compile(r"\s(?:with|w/|\+|&|plus|and|bundle|includes?|kit)\s|\s\+|,|\(|\s-\s")


def head(t):
    """Phần đầu tiêu đề (trước with/+/&/bundle...): nơi nói sản phẩm chính là gì."""
    return CUT.split(t, maxsplit=1)[0]


def classify(cats, title):
    p = " > ".join(cats); t = title.lower(); h = head(t)
    if "Lenses > Camera Lenses" in p:
        if LENS_NEG.search(h):
            return "lens_cat_but_accessory"
        return "lens" if LENS_POS.search(t) else "lens_cat_no_focal"
    if ("Digital Cameras > DSLR Cameras" in p or "Digital Cameras > Mirrorless Cameras" in p
            or p.endswith("Camera & Photo > Digital Cameras")):
        return "body_cat_but_accessory" if ACC_WORDS.search(h) else "body"
    if any(k in p for k in ["Point & Shoot Digital", "Instant Cameras", "Film Cameras", "Underwater Photography > Cameras",
                            "Video > Camcorders", "Sports & Action Video"]):
        return "camera_fixed_or_video"
    return "accessory_or_other"


stats = collections.defaultdict(collections.Counter)
rows = []
with open(F, encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        cats = d.get("categories") or []
        title = d.get("title") or ""
        typ = classify(cats, title)
        det = d.get("details") or {}
        cm_raw = det.get("Compatible Mountings")
        cm = set(cm_mounts(cm_raw)[0]) if cm_raw else set()
        T = find_mounts(title)
        SLRm = find_slr_mounts(title) if typ.startswith("lens") else {}
        SER = series_mounts(title) if typ.startswith("body") else {}
        TX = find_mounts(" ".join(d.get("features") or []) + " " + " ".join(d.get("description") or []))
        # quy tắc đề xuất: tiêu đề (T) trước; thiếu thì SER (thân) / SLR (ống); CM chỉ là phương án dự phòng
        prim = set(T) | set(SER) if typ.startswith("body") else set(T)
        if not prim and SLRm:
            prim = set(SLRm)
        rec = prim if prim else set()
        rec_cm = rec if rec else cm
        r = dict(asin=d["parent_asin"], type=typ, cats=" > ".join(cats[2:]), title=title, store=d.get("store"),
                 cm_raw=cm_raw, CM=sorted(cm), T=T, SLR=SLRm, SER=SER, TX=sorted(TX), rec=sorted(rec), rec_cm=sorted(rec_cm),
                 rating_number=d.get("rating_number"))
        rows.append(r)
        s = stats[typ]
        s["n"] += 1
        for name, ms in [("CM", cm), ("T", set(T)), ("SLR", set(SLRm)), ("SER", set(SER)), ("TX", set(TX))]:
            s[name] += len(ms) == 1
        s["rec_1"] += len(rec) == 1; s["rec_multi"] += len(rec) > 1
        s["recCM_1"] += len(rec_cm) == 1; s["recCM_multi"] += len(rec_cm) > 1
        if len(rec) == 1 and len(cm) == 1:
            s["rec&CM"] += 1; s["rec==CM"] += rec == cm
        if len(T) == 1 and len(cm) == 1:
            s["T&CM"] += 1; s["T==CM"] += set(T) == cm

with open(OUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

cols = ["n", "CM", "T", "SLR", "SER", "TX", "rec_1", "rec_multi", "recCM_1", "recCM_multi", "T&CM", "T==CM", "rec&CM", "rec==CM"]
print("(mỗi cột nguồn = số item mà nguồn đó cho ĐÚNG 1 ngàm)")
print("loại".ljust(24) + "".join(c.rjust(11) for c in cols))
tot = collections.Counter()
for g in sorted(stats):
    print(g.ljust(24) + "".join(str(stats[g][c]).rjust(11) for c in cols)); tot.update(stats[g])
print("TỔNG".ljust(24) + "".join(str(tot[c]).rjust(11) for c in cols))

# phân bố ngàm theo quy tắc đề xuất (không CM)
for typ in ["body", "lens"]:
    c = collections.Counter(r["rec"][0] for r in rows if r["type"] == typ and len(r["rec"]) == 1)
    print(f"\nPhân bố ngàm ({typ}, quy tắc đề xuất, không dùng CM):", c.most_common())
