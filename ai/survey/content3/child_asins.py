"""Đếm số asin con (biến thể) xuất hiện trong review của mỗi thân máy/ống kính đã gán ngàm.
Đọc streaming Electronics.jsonl.gz (không sửa file gốc). Chỉ xét review của user sau k-core."""
import gzip, json, sys, time, collections
sys.stdout.reconfigure(encoding="utf-8")
S, OUT = sys.argv[1], sys.argv[2]
P = "ai/data/"
rows = [json.loads(l) for l in open(S, encoding="utf-8")]
target = {r["asin"]: r["type"] for r in rows if r["type"] in ("body", "lens") and len(r["rec"]) == 1}
users = set(json.load(open(P + "processed/user_map.json", encoding="utf-8")))
child = collections.defaultdict(collections.Counter)
t = time.time(); n = 0
with gzip.open(P + "raw/Electronics.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        n += 1
        i = line.find('"parent_asin": "')
        if i < 0 or line[i + 16:i + 26] not in target:
            continue
        d = json.loads(line)
        if d["parent_asin"] in target and d["user_id"] in users:
            child[d["parent_asin"]][d["asin"]] += 1
json.dump({k: dict(v) for k, v in child.items()}, open(OUT, "w", encoding="utf-8"))
print(f"đọc {n:,} dòng, {time.time()-t:.0f}s")
for typ in ("body", "lens"):
    ks = [k for k, v in target.items() if v == typ]
    multi = [k for k in ks if len(child.get(k, {})) > 1]
    print(f"{typ}: {len(ks)} item có ngàm; có >1 asin con trong review: {len(multi)} ({len(multi)/len(ks)*100:.1f}%)")

# Ống kính hãng thứ ba (Sigma, Tamron...) thường bán nhiều bản ngàm dưới cùng 1 parent_asin
import re
THIRD = re.compile(r"\b(sigma|tamron|tokina|rokinon|samyang|bower|opteka|yongnuo|meike|7artisans|ttartisan|viltrox|neewer|"
                   r"zeiss|voigtlander|lensbaby|vivitar|venus|laowa|irix|kenko|altura|jintu|lightdow)\b", re.I)
title = {r["asin"]: r["title"] for r in rows}
cnt = collections.Counter()
for k, v in target.items():
    if v == "lens":
        cnt[(bool(THIRD.search(title[k])), len(child.get(k, {})) > 1)] += 1
print("ống kính theo (hãng thứ ba?, >1 asin con):", dict(cnt))
