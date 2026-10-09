"""Độ phủ ở mức tương tác / người dùng của quy tắc ngàm đề xuất (survey2_items.jsonl).
Kịch bản 'gợi ý ống kính cho người đã có thân máy': user có >=1 thân máy biết ngàm trong train và item test là ống kính biết ngàm."""
import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
P = "ai/data/processed/"
rows = {json.loads(l)["asin"]: json.loads(l) for l in open(sys.argv[1], encoding="utf-8")}
item_map = json.load(open(P + "item_map.json", encoding="utf-8"))
iid2 = {v: rows[k] for k, v in item_map.items()}

def load(fn):
    d = {}
    for line in open(P + fn, encoding="utf-8"):
        p = line.split()
        if len(p) >= 2:
            d[int(p[0])] = [int(x) for x in p[1:]]
    return d
train, val, test = load("train.txt"), load("val.txt"), load("test.txt")
n_inter = sum(map(len, train.values())) + sum(map(len, val.values())) + sum(map(len, test.values()))

for key in ["rec", "rec_cm"]:
    def mount(i, typ):
        r = iid2[i]
        return r[key][0] if r["type"] == typ and len(r[key]) == 1 else None
    body = {i: mount(i, "body") for i in iid2}; body = {i: m for i, m in body.items() if m}
    lens = {i: mount(i, "lens") for i in iid2}; lens = {i: m for i, m in lens.items() if m}
    inter_b = inter_l = 0
    for d in (train, val, test):
        for its in d.values():
            for i in its:
                inter_b += i in body; inter_l += i in lens
    users_body = {u: {body[i] for i in its if i in body} for u, its in train.items()}
    users_body = {u: ms for u, ms in users_body.items() if ms}
    scen = [(u, test[u][0]) for u in users_body if test[u][0] in lens]
    compat = sum(1 for u, i in scen if lens[i] in users_body[u])
    test_lens_any = sum(1 for u in test if test[u][0] in lens)
    print(f"\n=== Quy tắc: {key} ({'không dùng' if key=='rec' else 'có dùng'} Compatible Mountings làm dự phòng) ===")
    print(f"thân máy có ngàm: {len(body):,} | ống kính có ngàm: {len(lens):,} | tổng {len(body)+len(lens):,} / {len(iid2):,} item ({(len(body)+len(lens))/len(iid2)*100:.2f}%)")
    print(f"tương tác (train+val+test={n_inter:,}) vào thân có ngàm: {inter_b:,} ; vào ống có ngàm: {inter_l:,} ; tổng {(inter_b+inter_l)/n_inter*100:.2f}%")
    print(f"user có >=1 thân máy biết ngàm trong train: {len(users_body):,} / {len(train):,}")
    print(f"  trong đó item TEST là ống kính biết ngàm: {len(scen):,}  (cùng ngàm với thân đã có: {compat:,}; khác ngàm: {len(scen)-compat:,})")
    print(f"user có item TEST là ống kính biết ngàm (bất kể có thân hay không): {test_lens_any:,}")
    print("ống kính theo ngàm:", collections.Counter(lens.values()).most_common(8))
