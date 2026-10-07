"""Kịch bản 'gợi ý ống kính cho người đã có thân máy' trên đầu ra của 03_mount_compat.py.
Với mỗi user có >=1 thân trong M (train) và item test là ống trong M: lấy mức tương thích TỐT NHẤT
giữa ống test và các thân user đã có. Tách nhóm theo QĐ 5.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content3/scenario_kgnew.py ai/data/kg_new"""
import csv, json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
D = sys.argv[1] if len(sys.argv) > 1 else "ai/data/kg_new"
P = "ai/data/processed/"
item_map = json.load(open(P + "item_map.json", encoding="utf-8"))
asin_of = {v: k for k, v in item_map.items()}
bidx = json.load(open(f"{D}/body_index.json", encoding="utf-8"))
lidx = json.load(open(f"{D}/lens_index.json", encoding="utf-8"))
level = {(r["body_asin"], r["lens_asin"]): r["level"] for r in csv.DictReader(open(f"{D}/compat_pairs.csv", encoding="utf-8"))}


def load(fn):
    return {int(p[0]): [int(x) for x in p[1:]] for p in (l.split() for l in open(P + fn)) if len(p) >= 2}


train, test = load("train.txt"), load("test.txt")
RANK = ["compatible_with", "crops_sensor", "requires_adapter", "unknown", "incompatible"]
users_body = {u: [asin_of[i] for i in its if asin_of[i] in bidx] for u, its in train.items()}
users_body = {u: b for u, b in users_body.items() if b}
grp = collections.Counter()
for u, bodies in users_body.items():
    lens = asin_of[test[u][0]]
    if lens not in lidx:
        continue
    best = min((level.get((b, lens), "incompatible") for b in bodies), key=RANK.index)
    grp[best] += 1
n = sum(grp.values())
print(f"user có >=1 thân trong M (train): {len(users_body):,} / {len(train):,}")
print(f"  trong đó item test là ống trong M: {n:,}")
for k in RANK:
    print(f"    {k:18s} {grp[k]:6,} ({grp[k] / n * 100:5.1f}%)")
print(f"  -> nhóm 'cùng ngàm, lắp trực tiếp' (M=1): {grp['compatible_with'] + grp['crops_sensor']:,}; "
      f"nhóm còn lại: {n - grp['compatible_with'] - grp['crops_sensor']:,}")
