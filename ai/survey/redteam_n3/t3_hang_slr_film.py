"""
Red Team nội dung 3, lần 1 — điểm T3 (CHẨN ĐOÁN, không sửa luật / dữ liệu).

T3: luật "hãng + SLR" (BRAND_SLR trong mount_detect.py) gán minolta|sony + SLR -> sony_a, olympus + SLR -> four_thirds...
    nghi suy rộng sang ống máy phim cũ (Minolta MD / Rokkor, Olympus OM, Canon FD...).

Việc làm: trong các ống (1 ngàm) có mount_source = hang_slr, đếm và in các ống có md, mc, rokkor, om, fd, film hoặc
manual trong tiêu đề, kèm luật BRAND_SLR khớp. Đánh giá tay từng ca (ngàm thật) ghi ở phụ lục docs.

Chạy từ thư mục gốc repo:
  ai\\.venv\\Scripts\\python.exe ai/survey/redteam_n3/t3_hang_slr_film.py > ai/data/survey/run_redteam_n3_t3.log
"""
import collections
import re

from rt_common import md, load_rows, is_single

rows = load_rows()
hs_all = [r for r in rows if r["item_type"] == "ong" and r["mount_source"] == "hang_slr"]
hs = [r for r in hs_all if is_single(r["mount"])]
print(f"ống mount_source=hang_slr: {len(hs_all)} | 1 ngàm: {len(hs)} | không chắc (QĐ 4): "
      f"{sum(r['uncertain'] == 'True' for r in hs)}")
print(f"theo ngàm: {dict(collections.Counter(r['mount'] for r in hs).most_common())}")

KW = {k: re.compile(p) for k, p in [("md", r"\bmd\b"), ("mc", r"\bmc\b"), ("rokkor", r"\brokkor"), ("om", r"\bom\b"),
                                     ("fd", r"\bfd\b"), ("film", r"\bfilm\b"), ("manual", r"\bmanual\b")]}


def which_rule(t):
    """Luật BRAND_SLR (mẫu regex) khớp đầu tiên, giống find_slr_mount."""
    for m, regs in md._BS:
        for r in regs:
            mo = r.search(t)
            if mo:
                return m, r.pattern, mo.group(0)[:50]
    return None


hit = []
for r in hs:
    t = md.drop_adapter_bundle(r["title"].lower())
    ks = [k for k, p in KW.items() if p.search(t)]
    if ks:
        hit.append((r, ks))
print(f"\nống hang_slr (1 ngàm) có ít nhất 1 từ {list(KW)}: {len(hit)}")
print("theo từ khóa (1 ống có thể nhiều từ): " +
      ", ".join(f"{k} {sum(k in ks for _, ks in hit)}" for k in KW))
print("theo ngàm: " + str(dict(collections.Counter(r["mount"] for r, _ in hit).most_common())))

for m in sorted({r["mount"] for r, _ in hit}):
    lst = sorted([x for x in hit if x[0]["mount"] == m], key=lambda x: x[0]["title"].lower())
    print(f"\n--- gán {m}: {len(lst)} ống ---")
    for r, ks in lst:
        rule = which_rule(md.drop_adapter_bundle(r["title"].lower()))
        print(f"  {r['parent_asin']} | {r['mount']}/{r['khung'] or '-'} | từ: {','.join(ks)} | unc={r['uncertain']} | "
              f"bt {r['n_child_asin']} | luật: '{rule[2] if rule else '-'}'")
        print(f"      {r['title'][:200]}")

# Thêm: ống hang_slr có tên hệ ngàm phim khác (ngoài 7 từ trên) — để thấy ca sót của bộ lọc từ khóa
OTHER = re.compile(r"\b(?:zuiko|pentacon|praktica|yashica|contax|c/y|konica|ar\b|minolta\s+(?:sr|mc|md|x-?\d)|"
                   r"nikkor-?[a-z]?\s+(?:ai|non-ai)|non-ai|pre-ai|k-?mount|m42|screw|t-?mount|vintage|old|classic)")
extra = [r for r in hs if r not in [x[0] for x in hit] and OTHER.search(r["title"].lower())]
print(f"\nThêm: ống hang_slr không có 7 từ trên nhưng có tên hệ cũ / 'vintage' (bộ lọc phụ): {len(extra)}")
for r in extra:
    print(f"  {r['parent_asin']} | {r['mount']} | {r['title'][:160]}")

# Thêm: toàn bộ ống hang_slr gán sony_a / four_thirds (2 luật Red Team nêu)
for m in ["sony_a", "four_thirds"]:
    lst = sorted([r for r in hs if r["mount"] == m], key=lambda r: r["title"].lower())
    print(f"\nThêm: mọi ống hang_slr gán {m}: {len(lst)}")
    for r in lst:
        rule = which_rule(md.drop_adapter_bundle(r["title"].lower()))
        print(f"  {r['parent_asin']} | {r['khung'] or '-'} | luật: '{rule[2] if rule else '-'}' | {r['title'][:140]}")

# Thêm: trên TOÀN dữ liệu (mọi loại, mọi nguồn ngàm), sản phẩm có md / rokkor / om / fd trong tiêu đề đang được gán gì
OLD = re.compile(r"\bminolta\s+md\b|\bmd\s+mount|\brokkor|\bom\b(?![\s-]?(?:d|1|5|system))|\bom[\s-]mount|\bfd\b|\bzuiko\b(?!\s+digital)")
old = [r for r in rows if r["item_type"] in ("ong", "phu_kien", "than") and OLD.search(r["title"].lower())]
print(f"\nThêm: sản phẩm (thân/ống/phụ kiện) có Minolta MD / Rokkor / OM / FD / Zuiko (không 'digital') trong tiêu đề: {len(old)}")
print("theo (loại, nguồn ngàm, ngàm): " + str(dict(collections.Counter(
    (r["item_type"], r["mount_source"] or "-", r["mount"]) for r in old).most_common())))
for r in sorted(old, key=lambda r: (r["item_type"], r["mount"])):
    if r["item_type"] == "ong" or (r["item_type"] == "phu_kien" and r["mount"] not in ("khong_co",)):
        print(f"  {r['parent_asin']} | {r['item_type']}/{r['mount']} ({r['mount_source'] or '-'}) | {r['title'][:140]}")
