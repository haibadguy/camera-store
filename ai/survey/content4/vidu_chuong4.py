"""
Lấy số cho chương 4 của báo cáo (chỉ ĐỌC đầu ra đã có, không ghi gì vào ai/data/kg/):
  (1) ví dụ xuyên suốt: một người dùng thật trong train có cả một thân và một ống nối với nhau bằng cạnh
      compatible_with; in mọi cạnh của đồ thị chạm tới thân và ống đó, và một ống ứng viên lắp được trên thân;
  (2) số sản phẩm có ít nhất một cạnh tri thức (mọi cạnh trừ interacted_with), để kiểm số 2.974 trong CHANGELOG.

Ví dụ trước: người dùng u có thân Rebel T6s (iid 12902) và ống EF 50mm f/1.8 STM (iid 20518) trong train
  -> in: u -interacted_with-> 12902, 20518; 12902 -compatible_with-> 20518 (luật canon_ef_efs_on_efs_body);
         12902 -has_spec-> canon_efs, apsc; 20518 -has_spec-> canon_ef, ff, 36-70, <=2.0; ...

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/content4/vidu_chuong4.py > ai/data/survey/run_c4_vidu_chuong4_<nhãn>.log
"""
import csv
import sys
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

KG = "ai/data/kg/"
TRAIN, VAL, TEST = "ai/data/processed/train.txt", "ai/data/processed/val.txt", "ai/data/processed/test.txt"
# Cặp ưu tiên: (thân, ống) trong 6B của log đồ thị và trong content4_design mục 1
PREFERRED = [(12902, 20518), (13343, 7056)]


def rows(name):
    return list(csv.DictReader(open(KG + name, encoding="utf-8")))


def read_pairs(path):
    out = defaultdict(list)
    for line in open(path, encoding="utf-8"):
        p = line.split()
        if len(p) >= 2:
            out[int(p[0])].extend(int(x) for x in p[1:])
    return out


attrs = {int(a["iid"]): a for a in rows("item_attributes.csv")}
title = {i: a["title"] for i, a in attrs.items()}
itype = {i: a["item_type"] for i, a in attrs.items()}

# ---- mọi cạnh tri thức, gom theo sản phẩm
edges = defaultdict(list)            # iid -> [chuỗi mô tả cạnh]
compat_by_body = defaultdict(dict)   # body -> {lens: (rel, rule_id, crop_unknown)}
for rel in ["compatible_with", "crops_sensor", "requires_adapter"]:
    for r in rows(f"kg_edges_{rel}.csv"):
        b, l = int(r["body_iid"]), int(r["lens_iid"])
        compat_by_body[b][l] = (rel, r["rule_id"], r["crop_unknown"])
        edges[b].append(f"-{rel}-> ong {l} (luật {r['rule_id']}, crop_unknown={r['crop_unknown']})")
        edges[l].append(f"<-{rel}- than {b}")
for r in rows("kg_edges_has_spec_mount.csv"):
    edges[int(r["iid"])].append(f"-has_spec-> mount {r['mount']} (src_phu_kien={r['src_phu_kien']}, "
                                f"phia={r['phia']}, ngam_khong_chac={r['ngam_khong_chac']})")
for r in rows("kg_edges_has_spec_sensor_format.csv"):
    edges[int(r["iid"])].append(f"-has_spec-> sensor_format {r['sensor_format']} (khung {r['khung']})")
for r in rows("kg_edges_has_spec_focal_range.csv"):
    edges[int(r["iid"])].append(f"-has_spec-> focal_range {r['focal_range']} (đọc f1={r['f1']}, f2={r['f2']})")
for r in rows("kg_edges_has_spec_aperture_class.csv"):
    edges[int(r["iid"])].append(f"-has_spec-> aperture_class {r['aperture_class']} (đọc a1={r['a1']}, a2={r['a2']})")
suit = defaultdict(list)
for r in rows("kg_edges_suitable_for.csv"):
    suit[int(r["iid"])].append(r["usecase"])
    edges[int(r["iid"])].append(f"-suitable_for-> usecase {r['usecase']}")

# ---- (2) số sản phẩm có ít nhất một cạnh tri thức
n_items = len(attrs)
n_kg = len(edges)
print("=== (2) Sản phẩm có ít nhất một cạnh tri thức (mọi quan hệ trừ interacted_with) ===")
print(f"  {n_kg:,} / {n_items:,} = {100 * n_kg / n_items:.2f}%")
by_type = defaultdict(int)
for i in edges:
    by_type[itype[i]] += 1
print(f"  theo loại: {dict(sorted(by_type.items()))}")

# ---- (1) ví dụ xuyên suốt
train, val, test = read_pairs(TRAIN), read_pairs(VAL), read_pairs(TEST)
print("\n=== (1) Ví dụ xuyên suốt ===")
for b, l in PREFERRED:
    us = sorted(u for u, its in train.items() if b in its and l in its)
    print(f"  cặp ưu tiên (thân {b}, ống {l}): số người dùng có cả hai trong train = {len(us)}; uid: {us[:10]}")

chosen = None
for b, l in PREFERRED:
    us = sorted(u for u, its in train.items() if b in its and l in its)
    if us:
        chosen = (us[0], b, l)
        break
if chosen is None:
    # dự phòng: người dùng có uid nhỏ nhất có một cặp (thân, ống) compatible_with trong train
    for u in sorted(train):
        its = set(train[u])
        hit = sorted((b, l) for b in its if b in compat_by_body for l in its
                     if compat_by_body[b].get(l, ("",))[0] == "compatible_with")
        if hit:
            chosen = (u, *hit[0])
            break
    print("  (không có người dùng nào có cặp ưu tiên; dùng cách dự phòng)")

u, b, l = chosen
print(f"\nChọn: người dùng uid {u} (chỉ số trong user_map.json), thân {b}, ống {l}")
print(f"  train của uid {u} ({len(train[u])} sản phẩm):")
for i in train[u]:
    print(f"    [{itype[i]} {i}] {attrs[i]['parent_asin']} | {title[i][:90]}")
for name, d in (("val", val), ("test", test)):
    for i in d.get(u, []):
        print(f"  {name}: [{itype[i]} {i}] {attrs[i]['parent_asin']} | {title[i][:90]} "
              f"(không có cạnh interacted_with trong đồ thị)")

for i in (b, l):
    a = attrs[i]
    print(f"\n  -- {itype[i]} {i} | {a['parent_asin']} | {title[i]}")
    print(f"     item_attributes: mount={a['mount']} khung={a['khung']} may_phim={a['may_phim']} "
          f"mount_source={a['mount_source']} uncertain={a['uncertain']}")
    own = [e for e in edges[i] if "compatible_with-> ong" not in e and "crops_sensor-> ong" not in e
           and "requires_adapter-> ong" not in e]
    for e in own:
        print(f"     {e}")
    if i == b:
        cnt = defaultdict(int)
        for _, (rel, _, _) in compat_by_body[b].items():
            cnt[rel] += 1
        print(f"     số cạnh thân -> ống của thân này: {dict(cnt)}")

print(f"\n  Cạnh giữa thân {b} và ống {l}: {compat_by_body[b].get(l)}")

# ống ứng viên: lắp được trên thân b (compatible_with / crops_sensor), người dùng chưa có trong train, có nhãn chân dung
cands = sorted(x for x, (rel, _, _) in compat_by_body[b].items()
               if rel in ("compatible_with", "crops_sensor") and x not in set(train[u]) and "chan_dung" in suit[x])
print(f"\n  Ống lắp được trên thân {b}, người dùng chưa có trong train, có nhãn chan_dung: {len(cands)} ống")
for x in cands[:15]:
    print(f"    [ong {x}] {attrs[x]['parent_asin']} | {title[x][:80]} | {compat_by_body[b][x][0]}, "
          f"luật {compat_by_body[b][x][1]} | nhãn {suit[x]}")
pick = next((x for x in cands if "70-200" in title[x] and "canon ef" in title[x].lower()), cands[0] if cands else None)
if pick is not None:
    print(f"\n  -- ống ứng viên {pick} | {attrs[pick]['parent_asin']} | {title[pick]}")
    a = attrs[pick]
    print(f"     item_attributes: mount={a['mount']} khung={a['khung']} uncertain={a['uncertain']}")
    for e in edges[pick]:
        if e.startswith("<-"):
            continue
        print(f"     {e}")
    print(f"     cạnh từ thân {b}: {compat_by_body[b][pick]}")

# các sản phẩm khác trong train của người dùng: cạnh tri thức đi ra (không in danh sách cạnh đi vào)
print(f"\n  Cạnh đi ra của các sản phẩm còn lại trong train của uid {u}:")
for i in train[u]:
    if i in (b, l):
        continue
    out = [e for e in edges[i] if not e.startswith("<-") and "-> ong" not in e]
    print(f"    [{itype[i]} {i}] {title[i][:70]}: {out if out else 'không có cạnh tri thức'}")
# sản phẩm val / test có nối với sản phẩm train của người dùng qua cạnh thân -> ống không
for name, d in (("val", val), ("test", test)):
    for i in d.get(u, []):
        links = [(i, x, compat_by_body[i][x][0]) for x in train[u] if x in compat_by_body.get(i, {})]
        links += [(x, i, compat_by_body[x][i][0]) for x in train[u] if i in compat_by_body.get(x, {})]
        print(f"  {name} [{itype[i]} {i}]: cạnh thân -> ống với sản phẩm train của uid {u}: {links}; "
              f"cạnh đi ra: {[e for e in edges[i] if not e.startswith('<-') and '-> ong' not in e]}")
