"""Xem ví dụ thật từ survey2_items.jsonl.
Cách chạy: python inspect_items.py ai/data/survey/survey2_items.jsonl <chế độ>
Chế độ: lens_norec | body_norec | check | lens_acc | body_acc | cmvalues | cm_vs_rec | asin=<ASIN,...>"""
import json, sys, collections, random
sys.stdout.reconfigure(encoding="utf-8")
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
what = sys.argv[2]
def show(r):
    print(f"  {r['asin']} [{r['type']}] rec={r['rec']} CM={r['cm_raw']!r} T={list(r['T'])} SLR={list(r['SLR'])} SER={list(r['SER'])} | {r['title'][:120]}")
rng = random.Random(42)
if what == "lens_norec":
    L = [r for r in rows if r["type"] == "lens" and not r["rec"]]
    print(len(L)); [show(r) for r in rng.sample(L, 25)]
if what == "body_norec":
    L = [r for r in rows if r["type"] == "body" and not r["rec"]]
    print(len(L)); [show(r) for r in rng.sample(L, 25)]
if what == "check":
    for typ in ["lens", "body"]:
        L = [r for r in rows if r["type"] == typ and len(r["rec"]) == 1]
        print(f"== {typ}: {len(L)} có ngàm theo quy tắc; mẫu 25 (seed 42)")
        [show(r) for r in rng.sample(L, 25)]
if what == "lens_acc":
    L = [r for r in rows if r["type"] == "lens_cat_but_accessory"]
    print(len(L)); [show(r) for r in rng.sample(L, 20)]
    L = [r for r in rows if r["type"] == "lens_cat_no_focal"]
    print(len(L)); [show(r) for r in rng.sample(L, 15)]
if what == "body_acc":
    L = [r for r in rows if r["type"] == "body_cat_but_accessory"]
    print(len(L)); [show(r) for r in L]
if what == "cmvalues":
    # máy ảnh ống liền (không thay ống kính) mà Compatible Mountings vẫn ghi 1 ngàm
    L = [r for r in rows if r["type"] == "camera_fixed_or_video" and len(r["CM"]) == 1]
    print(len(L), collections.Counter(r["CM"][0] for r in L).most_common(8))
    [show(r) for r in rng.sample(L, 10)]
if what == "cm_vs_rec":
    # thân/ống mà quy tắc (tiêu đề) và Compatible Mountings cho 2 ngàm khác nhau
    for typ in ["lens", "body"]:
        L = [r for r in rows if r["type"] == typ and len(r["rec"]) == 1 and len(r["CM"]) == 1 and r["rec"] != r["CM"]]
        print(f"== {typ}: {len(L)}"); [show(r) for r in L]
if what.startswith("asin="):
    want = what[5:].split(",")
    [show(r) for r in rows if r["asin"] in want]
