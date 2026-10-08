"""
Red Team nội dung 3, lần 1 — điểm N2 và N3 (CHẨN ĐOÁN, không sửa luật / dữ liệu).

N2: THIRD_PARTY (mount_detect.py) thiếu hãng? Đếm ống nhiều biến thể (n_child_asin > 1, có 1 ngàm, KHÔNG bị đánh dấu
    "không chắc") mà tiêu đề có từ khóa hãng nằm trong MAKERS của eval_external.py nhưng không có trong THIRD_PARTY.
    Tách hãng chính hãng (ống chỉ có 1 ngàm, không cần QĐ 4) với hãng thứ ba thật.
    Thêm: liệt kê từ đầu tiêu đề (thường là tên hãng) của các ống nhiều biến thể còn lại, để thấy hãng thứ ba
    không có trong cả hai danh sách.
N3: COMPACT_LINE có "finepix" nên FinePix S1–S5 Pro (ngàm Nikon F) không thành "thân theo tiêu đề".
    Đếm số sản phẩm FinePix S Pro, loại hiện tại, và loại nếu bỏ "finepix" khỏi COMPACT_LINE (vá tạm trong bộ nhớ).

Chỉ đọc ai/data/kg/item_attributes.csv. Chạy từ thư mục gốc repo:
  ai\\.venv\\Scripts\\python.exe ai/survey/redteam_n3/n2_n3_thirdparty_finepix.py > ai/data/survey/run_redteam_n3_n2n3.log
"""
import ast
import collections
import csv
import os
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "ai/pipeline"))
import mount_detect as md  # noqa: E402

ATTR = os.path.join(ROOT, "ai/data/kg/item_attributes.csv")
EVAL = os.path.join(ROOT, "ai/survey/content3/eval_external.py")

# Hãng sản xuất máy ảnh (ống của hãng chỉ có 1 ngàm -> QĐ 4 không cần áp)
FIRST_PARTY = {"canon", "nikon", "sony", "minolta", "konica", "fujifilm", "fuji", "fujinon", "olympus", "om",
               "panasonic", "lumix", "pentax", "ricoh", "samsung", "leica", "hasselblad", "kodak"}


def load_makers():
    tree = ast.parse(open(EVAL, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "MAKERS" for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit("không tìm thấy MAKERS")


def is_single(m):
    return m not in ("khong_co", "khong_ro", "nhieu", "") and ">" not in m


rows = list(csv.DictReader(open(ATTR, encoding="utf-8")))

# ============================== N2 ==============================
print("=" * 70)
print("N2. Hãng trong MAKERS (eval_external.py) nhưng không có trong THIRD_PARTY (mount_detect.py)")
print("=" * 70)
makers = load_makers()
missing = sorted(k for k in makers if not md.THIRD_PARTY.fullmatch(k))
print(f"MAKERS: {len(makers)} từ khóa; thiếu trong THIRD_PARTY: {len(missing)}")
print(f"  chính hãng máy ảnh: {[k for k in missing if k in FIRST_PARTY]}")
print(f"  hãng thứ ba / khác: {[k for k in missing if k not in FIRST_PARTY]}")

lenses = [r for r in rows if r["item_type"] == "ong" and is_single(r["mount"])]
multi = [r for r in lenses if int(r["n_child_asin"] or 0) > 1]
multi_ok = [r for r in multi if r["uncertain"] != "True"]
print(f"\nống 1 ngàm: {len(lenses)} | nhiều biến thể (n_child_asin > 1): {len(multi)} | "
      f"trong đó KHÔNG bị đánh dấu 'không chắc' (vẫn vào M): {len(multi_ok)}")

pat = {k: re.compile(r"\b" + re.escape(k) + r"\b", re.I) for k in missing}
per_kw = collections.defaultdict(list)
for r in multi_ok:
    for k in missing:
        if pat[k].search(r["title"]):
            per_kw[k].append(r)
print("\nsố ống nhiều biến thể, vào M, tiêu đề có từ khóa (1 ống có thể có nhiều từ khóa):")
for k in sorted(per_kw, key=lambda k: (k in FIRST_PARTY, -len(per_kw[k]))):
    tag = "chính hãng" if k in FIRST_PARTY else "HÃNG THỨ BA"
    print(f"  {k:12s} {len(per_kw[k]):4d}  ({tag})")
third = {r["parent_asin"]: r for k, v in per_kw.items() if k not in FIRST_PARTY for r in v}
print(f"\n-> hãng thứ ba có trong MAKERS mà thiếu trong THIRD_PARTY: {len(third)} ống")
for r in third.values():
    print(f"   {r['parent_asin']} | {r['mount']} | biến thể {r['n_child_asin']} | {r['title'][:100]}")
tp_kw = [k for k in missing if k not in FIRST_PARTY]
any_tp = [r for r in lenses if any(pat[k].search(r["title"]) for k in tp_kw)]
print(f"   (mọi ống 1 ngàm có {tp_kw}, không kể số biến thể: {len(any_tp)})")
for r in any_tp:
    print(f"   {r['parent_asin']} | {r['mount']} | biến thể {r['n_child_asin']} | {r['title'][:100]}")

# Ống nhiều biến thể, vào M, theo từ đầu tiêu đề (gần đúng tên hãng)
first_word = collections.Counter()
by_word = collections.defaultdict(list)
for r in multi_ok:
    w = re.sub(r"[^a-z0-9-]", "", (r["title"].split() or [""])[0].lower())
    first_word[w] += 1
    by_word[w].append(r)
print("\nống nhiều biến thể, vào M, theo TỪ ĐẦU TIÊU ĐỀ (để thấy hãng không có trong cả MAKERS lẫn THIRD_PARTY):")
for w, n in first_word.most_common():
    tag = "chính hãng" if w in FIRST_PARTY else ("MAKERS" if w in makers else "-")
    print(f"  {w:15s} {n:4d}  [{tag}]")
other = [r for w, lst in by_word.items() if w not in FIRST_PARTY for r in lst]
print(f"\n-> từ đầu tiêu đề KHÔNG phải hãng máy ảnh: {len(other)} ống (cần đọc tiêu đề để biết hãng nào bán nhiều ngàm):")
for r in sorted(other, key=lambda r: r["title"].lower()):
    print(f"   {r['parent_asin']} | {r['mount']:10s} | bt {r['n_child_asin']:>2} | {r['title'][:95]}")

# ============================== N3 ==============================
print("\n" + "=" * 70)
print("N3. FinePix S Pro (S1/S2/S3/S5 Pro, ngàm Nikon F) và COMPACT_LINE")
print("=" * 70)
FPX = re.compile(r"\b(?:finepix\s+)?s[1-5]\s?pro\b", re.I)
cands = [r for r in rows if FPX.search(r["title"]) and re.search(r"\bfuji|finepix", r["title"], re.I)]
print(f"sản phẩm có 'S1–S5 Pro' + Fuji/FinePix trong tiêu đề: {len(cands)}")

orig = md.COMPACT_LINE
patched = re.compile(orig.pattern.replace("finepix|", ""))
assert patched.pattern != orig.pattern


def run(r):
    cats = r["categories"].split(" > ") if r["categories"] else []
    return md.classify_item(r["title"], cats, int(r["n_child_asin"] or 0))


blocked = 0
for r in cands:
    t = r["title"].lower()
    md.COMPACT_LINE = orig
    now = run(r)
    tb_now = md.title_body(t)
    md.COMPACT_LINE = patched
    new = run(r)
    tb_new = md.title_body(t)
    md.COMPACT_LINE = orig
    same = (now["item_type"], now["mount"]) == (r["item_type"], r["mount"])
    is_blocked = tb_new and not tb_now and new["item_type"] != now["item_type"]
    blocked += is_blocked
    print(f"\n  {r['parent_asin']} | nhóm danh mục: {md.category_group(r['categories'].split(' > '))} | {r['categories'][-60:]}")
    print(f"    tiêu đề: {r['title'][:110]}")
    print(f"    hiện tại (item_attributes): {r['item_type']}/{r['mount']}  (chạy lại khớp: {same})")
    print(f"    title_body: hiện tại {tb_now} -> bỏ 'finepix' {tb_new} | loại nếu bỏ 'finepix': {new['item_type']}/{new['mount']}/{new['khung']}"
          f"  {'<- BỊ COMPACT_LINE CHẶN' if is_blocked else ''}")
print(f"\n-> số FinePix S Pro bị COMPACT_LINE chặn (đổi loại khi bỏ 'finepix'): {blocked}/{len(cands)}")
