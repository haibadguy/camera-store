"""
Red Team nội dung 3, lần 1 — điểm T2 (CHẨN ĐOÁN, không sửa luật / dữ liệu).

T2: LENS_APSC có \\bselp?\\d{2,4}(?!g?m) (mã SEL -> APS-C) và LENS_FF có \\bsal\\d (mã SAL -> FF).
    Mã SEL/SAL không cho biết khổ: SEL2470GM là FE (FF), SAL1855 là DT (APS-C).

Việc làm:
  1. Tìm ống (1 ngàm) mà khung đang lấy từ mẫu sel / sal (xét trên head(tiêu đề) như lens_khung).
  2. So với khung suy từ chữ trong tiêu đề: "FE" -> ff, "DT" -> apsc, "E <tiêu cự>" / "E PZ" -> apsc; không có -> không suy được.
  3. Chạy thử (vá tạm LENS_APSC / LENS_FF trong bộ nhớ, bỏ mẫu sel và sal): đếm ống đổi khung,
     và số cặp (thân, ống) đổi mức, nhất là compatible_with <-> crops_sensor, cờ crop_unknown, M.

Chạy từ thư mục gốc repo:
  ai\\.venv\\Scripts\\python.exe ai/survey/redteam_n3/t2_sony_sel_sal.py > ai/data/survey/run_redteam_n3_t2.log
"""
import collections
import re

from rt_common import md, load_rows, load_rules, check_baseline, classify_all, patched, is_single

rows = load_rows()
by_asin = {r["parent_asin"]: r for r in rows}
base = check_baseline(rows)

SEL_ALT, SAL_ALT = r"|\bselp?\d{2,4}(?!g?m)", r"|\bsal\d"
assert SEL_ALT in md.LENS_APSC.pattern and SAL_ALT in md.LENS_FF.pattern
SEL = re.compile(SEL_ALT[1:])
SAL = re.compile(SAL_ALT[1:])
APSC_NEW = re.compile(md.LENS_APSC.pattern.replace(SEL_ALT, ""))
FF_NEW = re.compile(md.LENS_FF.pattern.replace(SAL_ALT, ""))

# Khung theo chữ trong tiêu đề (toàn tiêu đề, viết thường)
W_FE = re.compile(r"\bfe\b(?!-)|\bfe\s?\d")
W_DT = re.compile(r"\bdt\b")
W_E = re.compile(r"\b(?:sony\s+)?e\s+(?:pz\s+)?\d{1,3}(?:-\d{1,3})?\s?mm")


def word_khung(t):
    fe, dt, e = W_FE.search(t), W_DT.search(t), W_E.search(t)
    if fe and not (dt or e):
        return "ff", fe.group(0)
    if (dt or e) and not fe:
        return "apsc", (dt or e).group(0)
    if fe and (dt or e):
        return "mau_thuan", f"{fe.group(0)} / {(dt or e).group(0)}"
    return "-", ""


lenses = [r for r in rows if r["item_type"] == "ong" and is_single(r["mount"])]
print(f"\nống 1 ngàm: {len(lenses)} | ngàm sony_e: {sum(r['mount'] == 'sony_e' for r in lenses)} | "
      f"sony_a: {sum(r['mount'] == 'sony_a' for r in lenses)}")

# ============================== 1-2. Ống dính mẫu sel / sal ==============================
print("\n" + "=" * 70)
print("1-2. Ống có mẫu sel / sal trong head(tiêu đề) (phần lens_khung đọc) và khung hiện tại")
print("=" * 70)
hit = []
for r in lenses:
    h = md.head(r["title"].lower())
    s, a = SEL.search(h), SAL.search(h)
    if s or a:
        hit.append((r, s, a))
ev_hit = [r for r in lenses if re.search(r"khung: (?:mâu thuẫn: )?(?:sel|sal)|/ sal", r["evidence"])]
print(f"số ống có mẫu sel/sal trong head: {len(hit)} (sel: {sum(1 for _, s, _ in hit if s)}, sal: {sum(1 for _, _, a in hit if a)})")
print(f"số ống mà evidence ghi khung lấy từ sel/sal (kể cả 'mâu thuẫn'): {len(ev_hit)}")
cmp = collections.Counter()
for r, s, a in sorted(hit, key=lambda x: (x[0]["mount"], x[0]["title"].lower())):
    t = r["title"].lower()
    wk, wev = word_khung(t)
    cur = r["khung"] or "khong_ro"
    verdict = ("không suy được từ chữ" if wk == "-" else "chữ mâu thuẫn" if wk == "mau_thuan"
               else "KHỚP" if wk == cur else "NGHI SAI")
    cmp[(("sel" if s else "sal"), cur, wk, verdict)] += 1
    print(f"  {r['parent_asin']} | {r['mount']:7s} | khung hiện tại {cur:9s} | mẫu '{(s or a).group(0)}' | "
          f"chữ: {wk} '{wev}' -> {verdict} | uncertain={r['uncertain']}")
    print(f"      ev '{r['evidence']}' | {r['title'][:120]}")
print("\ntổng hợp (mẫu, khung hiện tại, khung theo chữ, kết luận): số ống")
for k, n in sorted(cmp.items()):
    print(f"  {k}: {n}")

# ============================== 3. Chạy thử bỏ sel / sal ==============================
print("\n" + "=" * 70)
print("3. Chạy thử: bỏ mẫu sel khỏi LENS_APSC và sal khỏi LENS_FF (vá tạm trong bộ nhớ)")
print("=" * 70)
with patched(LENS_APSC=APSC_NEW, LENS_FF=FF_NEW):
    res = classify_all(rows)
changed = [a for a in res if res[a] != base[a]]
other_fields = [a for a in changed if any(res[a][f] != base[a][f] for f in ("item_type", "mount", "may_phim", "uncertain"))]
print(f"sản phẩm đổi bất kỳ trường nào: {len(changed)} | đổi loại/ngàm/cờ phim/uncertain: {len(other_fields)}")
kch = [a for a in changed if res[a]["khung"] != base[a]["khung"]]
print(f"ống đổi khung: {len(kch)} | " + ", ".join(f"{x or '-'}->{y or '-'}: {n}" for (x, y), n in
                                               collections.Counter((base[a]['khung'], res[a]['khung']) for a in kch).most_common()))
for a in sorted(kch, key=lambda a: (base[a]["mount"], by_asin[a]["title"].lower())):
    wk, _ = word_khung(by_asin[a]["title"].lower())
    print(f"  {a} | {base[a]['mount']:7s} | {base[a]['khung']} -> {res[a]['khung']} (theo chữ: {wk}) | "
          f"ev '{res[a]['evidence']}' | {by_asin[a]['title'][:90]}")

# Cặp (thân, ống) đổi mức
rules = load_rules()
bodies = [r for r in rows if r["item_type"] == "than" and is_single(r["mount"])]
lens_ch = [by_asin[a] for a in kch if by_asin[a]["item_type"] == "ong" and is_single(by_asin[a]["mount"])]
trans = collections.Counter()
m_change = cu_change = 0
ex = collections.defaultdict(list)
for b in bodies:
    bk, film = b["khung"] or "khong_ro", b["may_phim"] == "True"
    for l in lens_ch:
        a = l["parent_asin"]
        lv0, rid0, cu0 = rules.level(b["mount"], bk, l["mount"], base[a]["khung"] or "khong_ro", film)
        lv1, rid1, cu1 = rules.level(b["mount"], bk, l["mount"], res[a]["khung"] or "khong_ro", film)
        if (lv0, cu0) == (lv1, cu1):
            continue
        grp = "ống không chắc" if l["uncertain"] == "True" else "ống vào M"
        key = (grp, f"{lv0}{'+crop_unknown' if cu0 else ''}", f"{lv1}{'+crop_unknown' if cu1 else ''}")
        trans[key] += 1
        if grp == "ống vào M":
            m_change += (lv0 in ("compatible_with", "crops_sensor")) != (lv1 in ("compatible_with", "crops_sensor"))
        if len(ex[key]) < 3:
            ex[key].append(f"thân {b['parent_asin']} {b['mount']}/{bk} {b['title'][:40]} || ống {a} "
                           f"{base[a]['khung']}->{res[a]['khung']} {l['title'][:50]}")
print(f"\ncặp (thân 1 ngàm x ống đổi khung) đổi mức hoặc cờ crop_unknown: {sum(trans.values())}")
for k, n in sorted(trans.items(), key=lambda x: -x[1]):
    print(f"  [{k[0]}] {k[1]} -> {k[2]}: {n}")
    for e in ex[k]:
        print(f"      vd: {e}")
print(f"-> số ô M đổi (0<->1, ống vào M): {m_change}")

# ============================== 4. Khung "thật" của các ống dính sel/sal ==============================
# Khung tra tay theo tên ống của Sony. "web" = đã mở kết quả tìm kiếm trang thông số Sony ngày 08/10/2026;
# "tieu_de" = tiêu đề có FE / DT / E; "hieu_biet" = theo hiểu biết, CHƯA đối chiếu nguồn.
TRUTH = {
    "B0042GFYHW": ("ff", "web: sony.ie/.../sal85f28 '85MM F2.8 SAM' (không phải DT)"),
    "B000VUIXOE": ("apsc", "web: sony.ca/.../sal16105 'DT 16-105MM'"),
    "B00836H3Z8": ("apsc", "web: sony.ie/.../sal18135 'DT 18-135MM'"),
    "B000VUFDPG": ("apsc", "tieu_de: DT"),
    "B000DZKOJ4": ("ff", "hieu_biet: SAL70200G, ống G, không DT"),
    "B0013GQ2WU": ("ff", "hieu_biet: SAL70300G, ống G, không DT"),
    "B001FORGMK": ("ff", "hieu_biet: SAL70400G, ống G, không DT"),
    "B077VYV7PH": ("ff", "web: sony.com.tw/.../sel85f18 'FE 85mm F1.8'"),
    "B00WUI6QJO": ("apsc", "web: sony.ca/.../sel35f18 'E 35MM F1.8 OSS'"),
    "B003M0D0P2": ("apsc", "hieu_biet: SEL16F28 = E 16mm"),
    "B003NRHAH8": ("apsc", "hieu_biet: SEL16F28 = E 16mm"),
    "B0042GFYLI": ("apsc", "hieu_biet: SEL18200 = E 18-200mm"),
    "B003U8Q7TC": ("apsc", "hieu_biet: SEL1855 = E 18-55mm"),
    "B0096W1PG6": ("apsc", "hieu_biet: SELP1650 = E PZ 16-50mm"),
    "B00HSMDVJ0": ("apsc", "hieu_biet: SELP1650 = E PZ 16-50mm"),
    "B07WZVKZHK": ("apsc", "tieu_de: APS-C"),
    "B009Z3PBZC": ("apsc", "tieu_de: Sony E 10-18mm"),
    "B0199BFAY6": ("apsc", "tieu_de: E 16-70mm"),
    "B00EZK11A4": ("apsc", "tieu_de: E 16-70mm"),
    "B07C7PKTB4": ("apsc", "tieu_de: E PZ 18-105mm"),
    "B006HC8D04": ("apsc", "tieu_de: E 24mm"),
    "B00FYOF61K": ("ff", "tieu_de: FE"), "B06X9CV5VK": ("ff", "tieu_de: FE"), "B00ZY8CII0": ("ff", "tieu_de: FE"),
    "B0CFX2LJCB": ("ff", "tieu_de: FE"), "B00U29GN6O": ("ff", "tieu_de: FE"), "B0199BF87K": ("ff", "tieu_de: FE"),
    "B078GGJLCD": ("ff", "tieu_de: FE"), "B0B49YVGCH": ("ff", "tieu_de: FE"),
}
print("\n" + "=" * 70)
print("4. So khung hiện tại với khung tra tay (TRUTH) của 29 ống dính sel/sal")
print("=" * 70)
assert set(TRUTH) == {r["parent_asin"] for r, _, _ in hit}, set(TRUTH) ^ {r["parent_asin"] for r, _, _ in hit}
cls = collections.Counter()
for r, s, a in hit:
    cur = r["khung"] or "khong_ro"
    tk, src = TRUTH[r["parent_asin"]]
    c = "đúng" if cur == tk else ("không rõ (mất thông tin)" if cur == "khong_ro" else "SAI")
    cls[("sel" if s else "sal", c)] += 1
    if c != "đúng":
        print(f"  {c:25s} | {r['parent_asin']} | {r['mount']} | hiện tại {cur} | thật {tk} ({src}) | {r['title'][:70]}")
print("tổng hợp:", dict(cls))

trans2 = collections.Counter()
ex2 = collections.defaultdict(list)
for b in bodies:
    bk, film = b["khung"] or "khong_ro", b["may_phim"] == "True"
    for r, _, _ in hit:
        a = r["parent_asin"]
        lv0, _, cu0 = rules.level(b["mount"], bk, r["mount"], r["khung"] or "khong_ro", film)
        lv1, _, cu1 = rules.level(b["mount"], bk, r["mount"], TRUTH[a][0], film)
        if (lv0, cu0) != (lv1, cu1):
            key = (f"{lv0}{'+crop_unknown' if cu0 else ''}", f"{lv1}{'+crop_unknown' if cu1 else ''}")
            trans2[key] += 1
            if len(ex2[key]) < 3:
                ex2[key].append(f"thân {b['parent_asin']} {b['mount']}/{bk} || ống {a} {r['khung'] or 'khong_ro'}->{TRUTH[a][0]} {r['title'][:50]}")
print(f"\ncặp (thân 1 ngàm x 29 ống) đổi mức nếu khung = TRUTH (mọi ống này đều vào M): {sum(trans2.values())}")
for k, n in sorted(trans2.items(), key=lambda x: -x[1]):
    print(f"  {k[0]} -> {k[1]}: {n}")
    for e in ex2[k]:
        print(f"      vd: {e}")
