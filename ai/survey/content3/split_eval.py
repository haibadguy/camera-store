"""Chia đôi tập sản phẩm khớp được với nguồn ngoài (eval_external.py) thành 2 nửa:
  fix     : được xem ca sai để sửa quy tắc phân loại (phiên sau)
  holdout : KHÔNG được xem trước khi sửa xong; chỉ dùng để đo lại sau khi sửa
Phân tầng theo loại của đáp án (than / khac / ong). Seed cố định.
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content3/split_eval.py
Đầu ra: ai/survey/content3/eval_split.csv (parent_asin, tang, nua)"""
import csv, random, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
SEED = 20261008
SRC = "ai/data/survey/eval_external_matches.csv"
OUT = "ai/survey/content3/eval_split.csv"
PRIORITY = ["lensfun", "wikidata", "openmvg"]      # nguồn ưu tiên khi lấy loại đáp án

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
by_item = collections.defaultdict(dict)
for r in rows:
    by_item[r["parent_asin"]][r["nguon"]] = r


def stratum(srcs):
    for s in PRIORITY:
        if s in srcs and srcs[s]["loai_dap_an"]:
            return srcs[s]["loai_dap_an"]
    return "than"     # chỉ khớp openMVG: openMVG chỉ có máy ảnh (không có loại thân/ống liền)


strata = collections.defaultdict(list)
for asin in sorted(by_item):
    strata[stratum(by_item[asin])].append(asin)
rng = random.Random(SEED)
out = []
for t in sorted(strata):
    items = strata[t][:]
    rng.shuffle(items)
    half = len(items) // 2
    out += [(a, t, "fix") for a in items[:half]] + [(a, t, "holdout") for a in items[half:]]
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parent_asin", "tang", "nua"])
    w.writerows(sorted(out))
c = collections.Counter((t, n) for _, t, n in out)
print(f"{len(out)} sản phẩm ->", dict(sorted(c.items())))
print("fix:", sum(n == "fix" for _, _, n in out), "| holdout:", sum(n == "holdout" for _, _, n in out))
