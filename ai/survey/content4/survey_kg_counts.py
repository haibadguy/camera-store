"""Khảo sát cho nội dung 4 (chưa phải pipeline): ước tính số nút / cạnh của đồ thị và độ phủ của cách đo
tiêu cự / khẩu độ bằng Lensfun khi KHÔNG dùng chính thuộc tính đó để khớp (tránh vòng lặp).
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content4/survey_kg_counts.py
"""
import collections, csv, json, re, sys
sys.path.insert(0, "ai/survey/content3")
sys.stdout.reconfigure(encoding="utf-8")
import eval_external as ev  # noqa: E402

attrs = list(csv.DictReader(open("ai/data/kg/item_attributes.csv", encoding="utf-8")))
meta = {}
for line in open("ai/data/survey/meta_full_k5.jsonl", encoding="utf-8"):
    d = json.loads(line)
    meta[d["parent_asin"]] = d

typ = collections.Counter(a["item_type"] for a in attrs)
print("loại:", dict(typ))
single = lambda m: m not in ("khong_co", "khong_ro", "nhieu", "") and ">" not in m
for t in ["than", "ong", "phu_kien"]:
    ms = collections.Counter(a["mount"] for a in attrs if a["item_type"] == t and single(a["mount"]))
    print(f"{t}: có 1 ngàm {sum(ms.values())}, số ngàm khác nhau {len(ms)}")
    if t != "phu_kien":
        print("   khung:", dict(collections.Counter(a["khung"] for a in attrs if a["item_type"] == t and single(a["mount"]))))
print("phụ kiện ngàm chuyển (a>b):", sum(1 for a in attrs if ">" in a["mount"]))
allm = {a["mount"] for a in attrs if single(a["mount"])}
print("tất cả ngàm:", len(allm), sorted(allm))

# tiêu cự / khẩu độ trên ống (đọc ở phần chủ thể tiêu đề, cách đọc của eval_external.lens_sig)
lens = [a for a in attrs if a["item_type"] == "ong"]
sigs = {}
for a in lens:
    s = ev.lens_sig(ev.head_main(a["title"]))
    sigs[a["parent_asin"]] = s
ok = [s for s in sigs.values() if s]
print(f"\nống {len(lens)}: đọc được tiêu cự+khẩu độ ở phần đầu tiêu đề {len(ok)}")
zoom = sum(1 for s in ok if s[1])
print(f"  zoom {zoom}, prime {len(ok) - zoom}")

# Đối chiếu Amazon 'Focal Length Description' (trường có cấu trúc, do người bán nhập — không phải nguồn ngoài)
agree = dis = 0
ex = []
for a in lens:
    s = sigs[a["parent_asin"]]
    fd = (meta[a["parent_asin"]].get("details") or {}).get("Focal Length Description")
    if not s or not fd:
        continue
    nums = re.findall(r"\d+(?:\.\d+)?", fd)
    if not nums:
        continue
    mine = [x for x in (s[0], s[1]) if x]
    theirs = [ev._num(x) for x in nums[:2]]
    if mine == theirs:
        agree += 1
    else:
        dis += 1
        if len(ex) < 8:
            ex.append((a["title"][:70], mine, fd))
print(f"  so với Focal Length Description của Amazon: trùng {agree}, lệch {dis}")
for e in ex:
    print("    ", e)

# Độ phủ của cách đo không vòng lặp với Lensfun: khớp bằng hãng + các token chữ của tên + thuộc tính CÒN LẠI
cams, lf = ev.load_lensfun()


def alpha(name):
    return frozenset(t for t in ev.ctoks(name) if re.fullmatch(r"[a-z]+", t) and t not in ev.MAKERS and t not in ("mm", "f"))


by_aper = collections.defaultdict(list)   # để kiểm tiêu cự: khóa = (hãng, khẩu độ)
by_foc = collections.defaultdict(list)    # để kiểm khẩu độ: khóa = (hãng, tiêu cự)
for sig, e in lf:
    mk, f1, f2, a1, a2 = sig
    by_aper[(mk, a1, a2)].append((alpha(e["name"]), (f1, f2), e["name"]))
    by_foc[(mk, f1, f2)].append((alpha(e["name"]), (a1, a2), e["name"]))
nf = na = 0
fok = aok = 0
for a in lens:
    h = ev.head_main(a["title"])
    s, mk = sigs[a["parent_asin"]], ev.maker_of(h)
    if not s or not mk:
        continue
    tt = set(ev.ctoks(h))
    c = [x for x in by_aper.get((mk, s[2], s[3]), []) if x[0] <= tt and x[0]]
    if c and len({x[1] for x in c}) == 1:
        nf += 1; fok += c[0][1] == (s[0], s[1])
    c = [x for x in by_foc.get((mk, s[0], s[1]), []) if x[0] <= tt and x[0]]
    if c and len({x[1] for x in c}) == 1:
        na += 1; aok += c[0][1] == (s[2], s[3])
print(f"\nLensfun, khớp không dùng thuộc tính cần đo (chưa tách fix/holdout, chỉ để ước tính độ phủ):")
print(f"  tiêu cự: khớp được {nf}, trùng {fok}")
print(f"  khẩu độ: khớp được {na}, trùng {aok}")
