"""
Red Team nội dung 3, lần 1 — điểm T1 (CHẨN ĐOÁN, không sửa luật / dữ liệu).

T1: body_series() chạy trên TOÀN tiêu đề (gồm cả phần "for ...", "with ..."), và luật "[phim] EOS" có mẫu
    \\beos\\b.*\\b(?:film|35mm)\\b đứng trước luật Canon APS-C -> nghi nhận nhầm máy số thành máy phim.

Việc làm:
  1. In 17 thân may_phim=True: tiêu đề, chủ thể (subject), evidence, luật dòng máy khớp, nguồn của cờ máy phim.
  2. Chạy thử (vá tạm mount_detect trong bộ nhớ, không ghi file) trên mọi sản phẩm của item_attributes.csv:
       A  : body_series chạy trên subject(tiêu đề) thay vì toàn tiêu đề;
       B  : luật "[phim] EOS" bỏ mẫu \\beos\\b.*\\b(?:film|35mm)\\b, chỉ giữ tên máy phim cụ thể có sẵn
            (EOS 1V, Elan, Rebel G/GII/K2/Ti/2000/X); không thêm tên mới;
       A+B: cả hai.
     Đếm số sản phẩm đổi loại / đổi ngàm / đổi khung / đổi cờ máy phim, in ví dụ.

Chạy từ thư mục gốc repo:
  ai\\.venv\\Scripts\\python.exe ai/survey/redteam_n3/t1_film_body_series.py > ai/data/survey/run_redteam_n3_t1.log
"""
import collections
import re

from rt_common import md, load_rows, check_baseline, classify_all, series_from, patched, is_single

rows = load_rows()
by_asin = {r["parent_asin"]: r for r in rows}
base = check_baseline(rows)

# ============================== 1. 17 thân máy phim ==============================
print("\n" + "=" * 70)
print("1. Thân có may_phim=True (đang làm mọi cặp của thân thành 'không biết', QĐ 16)")
print("=" * 70)
film = [r for r in rows if r["item_type"] == "than" and r["may_phim"] == "True"]
print(f"số thân may_phim=True: {len(film)} (trong đó 1 ngàm, vào M: {sum(is_single(r['mount']) for r in film)})")
for r in sorted(film, key=lambda r: (r["mount"], r["parent_asin"])):
    t = r["title"].lower()
    s = md.body_series(r["title"])
    subj = md.subject(t)
    from_rule = bool(s and s[3].startswith(md.FILM_TAG))
    from_subj = bool(re.search(r"\bfilm\b", subj))
    s_subj = md.body_series(subj)
    print(f"\n  {r['parent_asin']} | {r['mount']}/{r['khung']} | evidence: '{r['evidence']}' | luật: {s[3] if s else '-'}")
    print(f"    cờ phim từ: luật [phim] = {from_rule}, chữ 'film' trong chủ thể = {from_subj}")
    print(f"    danh mục : {r['categories']}")
    print(f"    tiêu đề  : {r['title'][:230]}")
    print(f"    chủ thể  : {subj[:150]}")
    print(f"    body_series(chủ thể): {(s_subj[0], s_subj[1], s_subj[2], s_subj[3]) if s_subj else None}")

# ============================== 2. Chạy thử ==============================
EOS_FILM_OLD = r"\beos[\s-]?1v\b|\beos\b.*\b(?:film|35mm)\b|\b(?:elan|rebel\s+(?:g(?:ii)?|k2|ti|2000|x))\b"
EOS_FILM_NEW = r"\beos[\s-]?1v\b|\b(?:elan|rebel\s+(?:g(?:ii)?|k2|ti|2000|x))\b"
bs_B = []
for b, p, m, k, n in md.BODY_SERIES:
    if n == "[phim] EOS":
        assert p == EOS_FILM_OLD, p
        p = EOS_FILM_NEW
    bs_B.append((b, p, m, k, n))
assert bs_B != md.BODY_SERIES

orig_body_series = md.body_series


def body_series_on_subject(title):
    return orig_body_series(md.subject(title.lower()))


def diff_report(name, res):
    print("\n" + "-" * 70)
    print(f"Chạy thử {name}")
    print("-" * 70)
    changed = {a for a in res if res[a] != base[a]}
    print(f"số sản phẩm có ít nhất 1 trường đổi (item_type/mount/khung/may_phim/mount_source/evidence/uncertain): {len(changed)}")
    for fld, label in [("item_type", "đổi LOẠI"), ("mount", "đổi NGÀM"), ("khung", "đổi KHUNG"), ("may_phim", "đổi CỜ MÁY PHIM")]:
        ch = [a for a in changed if res[a][fld] != base[a][fld]]
        trans = collections.Counter((base[a]["item_type"], base[a][fld], res[a][fld]) for a in ch)
        print(f"\n  {label}: {len(ch)} sản phẩm")
        for (typ, x, y), n in trans.most_common():
            print(f"     [{typ}] {x or '(trống)'} -> {y or '(trống)'}: {n}")
        for a in sorted(ch)[:10]:
            b0, b1 = base[a], res[a]
            print(f"     {a} | {b0['item_type']}/{b0['mount']}/{b0['khung']}/phim={b0['may_phim']} -> "
                  f"{b1['item_type']}/{b1['mount']}/{b1['khung']}/phim={b1['may_phim']} | ev '{b0['evidence']}' -> '{b1['evidence']}'")
            print(f"        {by_asin[a]['title'][:150]}")
    other = [a for a in changed if all(res[a][f] == base[a][f] for f in ("item_type", "mount", "khung", "may_phim"))]
    print(f"\n  chỉ đổi evidence / mount_source / uncertain (loại, ngàm, khung, cờ phim giữ nguyên): {len(other)}")
    for a in sorted(other)[:10]:
        print(f"     {a} | {base[a]['item_type']}/{base[a]['mount']} | ev '{base[a]['evidence']}' -> '{res[a]['evidence']}' | "
              f"{by_asin[a]['title'][:80]}")
    # ảnh hưởng tới tập thân vào M
    b0 = {a for a in base if base[a]["item_type"] == "than" and is_single(base[a]["mount"])}
    b1 = {a for a in res if res[a]["item_type"] == "than" and is_single(res[a]["mount"])}
    f0 = {a for a in b0 if base[a]["may_phim"] == "True"}
    f1 = {a for a in b1 if res[a]["may_phim"] == "True"}
    print(f"\n  thân 1 ngàm: {len(b0)} -> {len(b1)} (vào: {len(b1 - b0)}, ra: {len(b0 - b1)}) | "
          f"thân phim 1 ngàm: {len(f0)} -> {len(f1)} (thêm {sorted(f1 - f0)}, bớt {sorted(f0 - f1)})")
    l0 = {a for a in base if base[a]["item_type"] == "ong" and is_single(base[a]["mount"])}
    l1 = {a for a in res if res[a]["item_type"] == "ong" and is_single(res[a]["mount"])}
    print(f"  ống 1 ngàm: {len(l0)} -> {len(l1)} (vào: {len(l1 - l0)}, ra: {len(l0 - l1)})")
    return changed


with patched(body_series=body_series_on_subject):
    resA = classify_all(rows)
diff_report("A: body_series trên subject()", resA)

with patched(_SERIES=series_from(bs_B)):
    resB = classify_all(rows)
diff_report("B: luật [phim] EOS bỏ mẫu .*(film|35mm)", resB)

with patched(_SERIES=series_from(bs_B)):
    # body_series gốc đọc md._SERIES lúc gọi, nên wrapper dùng đúng bảng đã vá
    with patched(body_series=body_series_on_subject):
        resAB = classify_all(rows)
diff_report("A+B", resAB)

# ============================== 3. Chiều ngược lại: máy phim bị sót ==============================
print("\n" + "=" * 70)
print("3. Thêm: thân 1 ngàm nằm trong danh mục 'Film Cameras' hoặc tiêu đề có 'film' / '35mm' nhưng may_phim=False")
print("=" * 70)
miss = [r for r in rows if r["item_type"] == "than" and is_single(r["mount"]) and r["may_phim"] != "True"
        and ("Film Cameras" in r["categories"] or re.search(r"\bfilm\b|\b35\s?mm\b(?!\s*(?:f/|lens|-))", r["title"].lower()))]
print(f"số thân: {len(miss)}")
for r in miss:
    print(f"  {r['parent_asin']} | {r['mount']}/{r['khung']} | ev '{r['evidence']}' | {r['categories'][-45:]} | {r['title'][:120]}")
slr = [r for r in rows if "Film Cameras > SLR Cameras" in r["categories"]]
print(f"\nsản phẩm trong danh mục 'Film Cameras > SLR Cameras': {len(slr)} | theo loại/ngàm/cờ phim: "
      f"{dict(collections.Counter((r['item_type'], r['mount'], r['may_phim']) for r in slr).most_common())}")
for r in slr:
    if not (r["item_type"] == "than" and r["may_phim"] == "True"):
        print(f"  {r['parent_asin']} | {r['item_type']}/{r['mount']} | {r['title'][:120]}")
