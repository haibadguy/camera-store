"""
Red Team nội dung 3, lần 1 — điểm T4 (CHẨN ĐOÁN, không sửa luật / dữ liệu).

Câu hỏi: trong các cặp (thân máy phim, ống) đang là "không biết" do luật film_body_unknown (QĐ 16),
bao nhiêu cặp mà luật thường (coi thân như máy số, tức bỏ qua luật phim) cho "không lắp được" (incompatible)?

Cách làm:
  - Đọc ai/data/kg/item_attributes.csv (chỉ đọc), lấy thân / ống có 1 ngàm giống hệt 03_mount_compat.py.
  - Dùng chính lớp Rules của 03_mount_compat.py + ai/config/mount_rules.toml.
  - Với mỗi cặp (thân phim, ống): mức hiện tại (bfilm=True) và mức theo luật thường (bfilm=False).
  - Kiểm lại: số cặp film_body_unknown (ống không "không chắc") phải bằng 17.612 như mount_compat_log.txt.

Chạy từ thư mục gốc repo:
  ai\\.venv\\Scripts\\python.exe ai/survey/redteam_n3/t4_film_unknown.py > ai/data/survey/run_redteam_n3_t4.log
"""
import collections
import csv
import importlib.util
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ATTR = os.path.join(ROOT, "ai/data/kg/item_attributes.csv")
RULES = os.path.join(ROOT, "ai/config/mount_rules.toml")
PAIRS = os.path.join(ROOT, "ai/data/kg/compat_pairs.csv")

spec = importlib.util.spec_from_file_location("mc03", os.path.join(ROOT, "ai/pipeline/03_mount_compat.py"))
mc03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc03)


def is_single(m):          # giống 03_mount_compat.py
    return m not in ("khong_co", "khong_ro", "nhieu", "") and ">" not in m


rows = list(csv.DictReader(open(ATTR, encoding="utf-8")))
for r in rows:
    r["may_phim"] = r["may_phim"] == "True"
    r["uncertain"] = r["uncertain"] == "True"
bodies = [r for r in rows if r["item_type"] == "than" and is_single(r["mount"])]
lenses_all = [r for r in rows if r["item_type"] == "ong" and is_single(r["mount"])]
film = [b for b in bodies if b["may_phim"]]
print(f"thân 1 ngàm: {len(bodies)} | ống 1 ngàm: {len(lenses_all)} "
      f"(không chắc: {sum(l['uncertain'] for l in lenses_all)}) | thân máy phim: {len(film)}")
print(f"thân phim theo ngàm: {dict(collections.Counter(b['mount'] for b in film).most_common())}")

rules = mc03.Rules(RULES)
rule_level = {r["id"]: r["level"] for r in rules.rules}

cnt = collections.Counter()           # (nhóm ống, cùng/khác ngàm, mức thường) -> số cặp
rid_normal = collections.Counter()    # luật thường khớp (chỉ ống vào M)
per_body = collections.defaultdict(collections.Counter)
examples = collections.defaultdict(list)
check_cur = 0
for b in film:
    for l in lenses_all:
        bk, lk = b["khung"] or "khong_ro", l["khung"] or "khong_ro"
        cur, cur_rid, _ = rules.level(b["mount"], bk, l["mount"], lk, True)
        if cur_rid != "film_body_unknown":
            continue
        if not l["uncertain"]:
            check_cur += 1
        nor, nor_rid, _ = rules.level(b["mount"], bk, l["mount"], lk, False)
        grp = "ong_khong_chac" if l["uncertain"] else "ong_vao_M"
        same = "cung_ngam" if l["mount"] == b["mount"] else "khac_ngam"
        cnt[(grp, same, nor)] += 1
        if grp == "ong_vao_M":
            rid_normal[nor_rid or "(mặc định = incompatible)"] += 1
            per_body[b["parent_asin"]][nor] += 1
            key = (same, nor)
            if len(examples[key]) < 4:
                examples[key].append((b, l))

print(f"\nkiểm lại: số cặp film_body_unknown (ống vào M) = {check_cur:,} (log pipeline: 17,612)")
n_pairs_file = sum(1 for r in csv.DictReader(open(PAIRS, encoding="utf-8")) if r["rule_id"] == "film_body_unknown")
print(f"kiểm lại: số dòng film_body_unknown trong compat_pairs.csv (gồm cả ống không chắc) = {n_pairs_file:,}")

for grp in ["ong_vao_M", "ong_khong_chac"]:
    sub = {k: v for k, v in cnt.items() if k[0] == grp}
    tot = sum(sub.values())
    print(f"\n=== {grp}: {tot:,} cặp đang 'unknown' do luật phim; mức nếu bỏ qua luật phim ===")
    for same in ["cung_ngam", "khac_ngam"]:
        s = {k[2]: v for k, v in sub.items() if k[1] == same}
        print(f"  {same:9s}: tổng {sum(s.values()):6,} | " + ", ".join(f"{lv} {n:,}" for lv, n in sorted(s.items(), key=lambda x: -x[1])))
    inc = sum(v for k, v in sub.items() if k[2] == "incompatible")
    print(f"  -> luật thường cho incompatible: {inc:,}/{tot:,} = {inc / tot * 100:.1f}%")

print("\nluật thường khớp (ống vào M):")
for rid, n in rid_normal.most_common():
    print(f"  {rid:50s} {n:6,}  (mức {rule_level.get(rid, 'incompatible')})")

print("\ntheo từng thân phim (ống vào M): ASIN | ngàm/khung | incompatible / cùng-ngàm-lắp-được / khác | tiêu đề")
for b in sorted(film, key=lambda x: (x["mount"], x["parent_asin"])):
    c = per_body[b["parent_asin"]]
    direct = c["compatible_with"] + c["crops_sensor"]
    other = sum(c.values()) - c["incompatible"] - direct
    print(f"  {b['parent_asin']} | {b['mount']}/{b['khung']} | {c['incompatible']:4d} / {direct:4d} / {other:4d} | "
          f"{b['title'][:90]}")

print("\nví dụ cặp (ống vào M):")
for (same, nor), lst in sorted(examples.items()):
    print(f"  [{same} -> luật thường: {nor}]")
    for b, l in lst:
        print(f"    thân {b['parent_asin']} {b['mount']}: {b['title'][:50]}  ||  ống {l['parent_asin']} {l['mount']}/{l['khung']}: {l['title'][:60]}")
