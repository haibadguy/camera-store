"""
Script: 03_mount_compat.py  (nội dung 3, bản mới — thay phần xác định ngàm và ma trận M của 03_entity_linking_matrix.py)

Việc làm:
  1. Đọc metadata gốc (title, categories, details) của các sản phẩm sau k-core.
  2. Đếm số asin con (biến thể) của mỗi sản phẩm trong file review gốc (dùng cho QĐ 4).
  3. Xác định loại (than / ong / phu_kien / khac), ngàm, khung (ff/apsc/khac) cho từng sản phẩm — mount_detect.py.
  4. Xếp mức tương thích cho mọi cặp (thân, ống) theo ai/config/mount_rules.toml.
  5. Xuất ma trận M nhị phân (1 = lắp trực tiếp), ma trận đánh dấu "không biết", danh sách cặp theo mức.

Quyết định áp dụng (STATUS.md, 07/10/2026): QĐ 1 (không dùng Compatible Mountings), QĐ 2 (4 mức), QĐ 3 (M chỉ thân x ống),
QĐ 4 (ống hãng thứ ba nhiều biến thể -> không chắc, loại khỏi M), QĐ 8 (cặp "không biết" lưu ma trận riêng).

Chạy từ thư mục gốc repo:
  ai\\.venv\\Scripts\\python.exe ai/pipeline/03_mount_compat.py --out-dir ai/data/kg_new
  (ghi vào ai/data/kg cần thêm --overwrite nếu ở đó đã có file)

Đầu ra (trong --out-dir):
  item_attributes.csv     mọi sản phẩm: iid, parent_asin, item_type, mount, khung, mount_source, evidence, uncertain...
  compatibility_matrix.npz  M  [n_body x n_lens] int8, 1 = compatible_with hoặc crops_sensor
  unknown_mask.npz          U  [n_body x n_lens] int8, 1 = mức "unknown" (loại khỏi ràng buộc cứng và CVR)
  body_index.json / lens_index.json   parent_asin -> chỉ số hàng / cột của M
  compat_pairs.csv        mọi cặp có mức khác incompatible (kể cả ống "không chắc", cột lens_uncertain;
                          cột crop_unknown = 1: lắp trực tiếp nhưng chưa rõ có cắt khung, QĐ 11)
  mount_compat_stats.json, mount_compat_log.txt
"""
import argparse
import collections
import csv
import gzip
import json
import os
import sys
import time
import tomllib

import numpy as np
from scipy.sparse import csr_matrix, save_npz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mount_detect import classify_item  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

RAW_META = "ai/data/raw/meta_Electronics.jsonl.gz"
RAW_REVIEWS = "ai/data/raw/Electronics.jsonl.gz"
ITEM_MAP = "ai/data/processed/item_map.json"
USER_MAP = "ai/data/processed/user_map.json"
OUT_FILES = ["item_attributes.csv", "compatibility_matrix.npz", "unknown_mask.npz", "body_index.json",
             "lens_index.json", "compat_pairs.csv", "mount_compat_stats.json", "mount_compat_log.txt"]
DIRECT = {"compatible_with", "crops_sensor"}

log_lines = []


def log(msg=""):
    print(msg)
    log_lines.append(str(msg))


# ── Bước 1: metadata tối thiểu (có cache) ─────────────────────────────────────
def load_meta(items, cache):
    if os.path.exists(cache):
        rows = [json.loads(l) for l in open(cache, encoding="utf-8")]
        if {r["parent_asin"] for r in rows} == items:
            log(f"-> dùng cache metadata: {cache} ({len(rows):,} dòng)")
            return {r["parent_asin"]: r for r in rows}
        log("-> cache metadata không khớp item_map, đọc lại file gốc")
    t = time.time()
    meta = {}
    with gzip.open(RAW_META, "rt", encoding="utf-8") as f:
        for line in f:
            i = line.find('"parent_asin": "')
            if i < 0 or line[i + 16:i + 26] not in items:
                continue
            d = json.loads(line)
            if d["parent_asin"] in items:
                meta[d["parent_asin"]] = {
                    "parent_asin": d["parent_asin"], "title": d.get("title") or "",
                    "categories": d.get("categories") or [], "store": d.get("store") or "",
                    "cm_raw": (d.get("details") or {}).get("Compatible Mountings") or ""}
    assert set(meta) == items, f"thiếu metadata cho {len(items - set(meta))} sản phẩm"
    with open(cache, "w", encoding="utf-8") as f:
        for r in meta.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log(f"-> đọc metadata gốc: {len(meta):,} sản phẩm, {time.time() - t:.0f}s, cache -> {cache}")
    return meta


# ── Bước 2: số asin con mỗi sản phẩm (có cache) ───────────────────────────────
def load_child_counts(items, users, cache):
    if os.path.exists(cache):
        d = json.load(open(cache, encoding="utf-8"))
        if set(d) <= items:
            log(f"-> dùng cache asin con: {cache}")
            return {k: len(v) for k, v in d.items()}
    t = time.time()
    child = collections.defaultdict(set)
    with gzip.open(RAW_REVIEWS, "rt", encoding="utf-8") as f:
        for line in f:
            i = line.find('"parent_asin": "')
            if i < 0 or line[i + 16:i + 26] not in items:
                continue
            d = json.loads(line)
            if d["parent_asin"] in items and d["user_id"] in users:
                child[d["parent_asin"]].add(d["asin"])
    json.dump({k: sorted(v) for k, v in child.items()}, open(cache, "w", encoding="utf-8"))
    log(f"-> đọc review gốc để đếm asin con: {time.time() - t:.0f}s, cache -> {cache}")
    return {k: len(v) for k, v in child.items()}


# ── Bước 4: bộ áp luật ───────────────────────────────────────────────────────
class Rules:
    def __init__(self, path):
        cfg = tomllib.load(open(path, "rb"))
        self.rules = cfg["rule"]
        self.default = cfg["meta"]["default_level"]
        self.order = cfg["meta"]["khung_order"]
        self.cache = {}

    @staticmethod
    def _match(pattern, value):
        if pattern == "*":
            return True
        if isinstance(pattern, list):
            return value in pattern
        return pattern == value

    def _covers(self, lens_k, body_k):
        if lens_k == body_k and lens_k != "khong_ro":
            return True
        if lens_k in self.order and body_k in self.order:
            return self.order.index(lens_k) <= self.order.index(body_k)
        return lens_k == "ff" and body_k == "khac"      # vd APS-H: ống FF phủ được

    def level(self, bm, bk, lm, lk):
        key = (bm, bk, lm, lk)
        if key in self.cache:
            return self.cache[key]
        res = (self.default, "", False)
        for r in self.rules:
            if not self._match(r["body_mount"], bm) or not self._match(r["body_khung"], bk):
                continue
            if r["lens_mount"] == "=":
                if lm != bm:
                    continue
            elif not self._match(r["lens_mount"], lm):
                continue
            if r["lens_khung"] == "covers_body":
                if not self._covers(lk, bk):
                    continue
            elif not self._match(r["lens_khung"], lk):
                continue
            res = (r["level"], r["id"], bool(r.get("crop_unknown", False)))
            break
        self.cache[key] = res
        return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="ai/data/kg")
    ap.add_argument("--interim", default="ai/data/interim")
    ap.add_argument("--rules", default="ai/config/mount_rules.toml")
    ap.add_argument("--overwrite", action="store_true", help="cho phép ghi đè file đã có trong --out-dir")
    args = ap.parse_args()

    existing = [f for f in OUT_FILES if os.path.exists(os.path.join(args.out_dir, f))]
    if existing and not args.overwrite:
        sys.exit(f"DỪNG: {args.out_dir} đã có {existing}. Thêm --overwrite nếu chắc chắn muốn ghi đè.")
    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(args.interim, exist_ok=True)

    log("=" * 60)
    log("NỘI DUNG 3 — LOẠI SẢN PHẨM, NGÀM, MA TRẬN TƯƠNG THÍCH")
    log("=" * 60)
    item_map = json.load(open(ITEM_MAP, encoding="utf-8"))
    users = set(json.load(open(USER_MAP, encoding="utf-8")))
    items = set(item_map)
    log(f"-> {len(items):,} sản phẩm, {len(users):,} người dùng")

    meta = load_meta(items, os.path.join(args.interim, "meta_k5_min.jsonl"))
    nchild = load_child_counts(items, users, os.path.join(args.interim, "child_asins_k5.json"))

    # ── Bước 3: phân loại từng sản phẩm ──
    attrs = []
    for asin in sorted(items, key=lambda a: item_map[a]):
        m = meta[asin]
        a = classify_item(m["title"], m["categories"], nchild.get(asin, 0))
        a.update(iid=item_map[asin], parent_asin=asin, n_child_asin=nchild.get(asin, 0), cm_raw=m["cm_raw"],
                 categories=" > ".join(m["categories"]), title=m["title"])
        attrs.append(a)

    cols = ["iid", "parent_asin", "item_type", "mount", "khung", "mount_source", "evidence", "uncertain",
            "uncertain_reason", "n_child_asin", "cm_raw", "categories", "title"]
    with open(os.path.join(args.out_dir, "item_attributes.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for a in attrs:
            w.writerow({c: a[c] for c in cols})

    def is_single(m):
        return m not in ("khong_co", "khong_ro", "nhieu", "") and ">" not in m

    bodies = [a for a in attrs if a["item_type"] == "than" and is_single(a["mount"])]
    lenses_all = [a for a in attrs if a["item_type"] == "ong" and is_single(a["mount"])]
    lenses = [a for a in lenses_all if not a["uncertain"]]
    log("\nTHỐNG KÊ LOẠI / NGÀM")
    type_cnt = collections.Counter(a["item_type"] for a in attrs)
    log(f"• loại: {dict(type_cnt)}")
    for typ in ["than", "ong", "phu_kien"]:
        c = collections.Counter(a["mount_source"] or a["mount"] for a in attrs if a["item_type"] == typ)
        log(f"• {typ}: nguồn ngàm / trạng thái: {dict(c.most_common())}")
    log(f"• thân có 1 ngàm: {len(bodies):,} | ống có 1 ngàm: {len(lenses_all):,} "
        f"(trong đó 'không chắc' QĐ 4: {len(lenses_all) - len(lenses):,}) -> ống vào M: {len(lenses):,}")
    log(f"• khung thân: {dict(collections.Counter(a['khung'] for a in bodies))}")
    log(f"• khung ống : {dict(collections.Counter(a['khung'] for a in lenses_all))}")
    log(f"• ngàm thân : {dict(collections.Counter(a['mount'] for a in bodies).most_common())}")
    log(f"• ngàm ống  : {dict(collections.Counter(a['mount'] for a in lenses_all).most_common())}")

    # ── Bước 4: mức tương thích ──
    rules = Rules(args.rules)
    b_idx = {a["parent_asin"]: i for i, a in enumerate(bodies)}
    l_idx = {a["parent_asin"]: j for j, a in enumerate(lenses)}
    Mr, Mc, Ur, Uc = [], [], [], []
    level_cnt, rule_cnt = collections.Counter(), collections.Counter()
    crop_unknown_cnt = 0
    with open(os.path.join(args.out_dir, "compat_pairs.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["body_asin", "body_iid", "lens_asin", "lens_iid", "level", "rule_id", "lens_uncertain", "crop_unknown"])
        for b in bodies:
            for l in lenses_all:
                lev, rid, cu = rules.level(b["mount"], b["khung"] or "khong_ro", l["mount"], l["khung"] or "khong_ro")
                if l["uncertain"]:
                    level_cnt["(ống không chắc) " + lev] += 1
                else:
                    level_cnt[lev] += 1
                    rule_cnt[rid or "(mặc định)"] += 1
                    crop_unknown_cnt += cu
                    if lev in DIRECT:
                        Mr.append(b_idx[b["parent_asin"]]); Mc.append(l_idx[l["parent_asin"]])
                    elif lev == "unknown":
                        Ur.append(b_idx[b["parent_asin"]]); Uc.append(l_idx[l["parent_asin"]])
                if lev != "incompatible":
                    w.writerow([b["parent_asin"], b["iid"], l["parent_asin"], l["iid"], lev, rid, int(l["uncertain"]), int(cu)])

    shape = (len(bodies), len(lenses))
    M = csr_matrix((np.ones(len(Mr), dtype=np.int8), (Mr, Mc)), shape=shape, dtype=np.int8)
    U = csr_matrix((np.ones(len(Ur), dtype=np.int8), (Ur, Uc)), shape=shape, dtype=np.int8)
    assert M.multiply(U).nnz == 0, "một cặp không thể vừa M=1 vừa unknown"
    save_npz(os.path.join(args.out_dir, "compatibility_matrix.npz"), M)
    save_npz(os.path.join(args.out_dir, "unknown_mask.npz"), U)
    json.dump(b_idx, open(os.path.join(args.out_dir, "body_index.json"), "w", encoding="utf-8"), indent=1)
    json.dump(l_idx, open(os.path.join(args.out_dir, "lens_index.json"), "w", encoding="utf-8"), indent=1)

    total = shape[0] * shape[1]
    log("\nMA TRẬN M (thân x ống, không gồm ống 'không chắc')")
    log(f"• kích thước: {shape[0]:,} x {shape[1]:,} = {total:,} cặp")
    log(f"• M = 1: {M.nnz:,} ({M.nnz / total * 100:.2f}%) | không biết: {U.nnz:,} ({U.nnz / total * 100:.2f}%)")
    log(f"• số cặp theo mức: {dict(level_cnt.most_common())}")
    log(f"• trong các cặp M = 1, gắn cờ 'chưa rõ có cắt khung' (QĐ 11): {crop_unknown_cnt:,}")
    log(f"• số cặp theo luật: {dict(rule_cnt.most_common())}")

    stats = {
        "n_items": len(attrs), "item_type": dict(type_cnt),
        "n_bodies_in_M": shape[0], "n_lenses_in_M": shape[1],
        "n_lenses_uncertain": len(lenses_all) - len(lenses),
        "M_nnz": int(M.nnz), "unknown_nnz": int(U.nnz), "pairs_total": total,
        "M_crop_unknown": crop_unknown_cnt,
        "pairs_by_level": dict(level_cnt), "pairs_by_rule": dict(rule_cnt),
        "rules_file": args.rules,
    }
    json.dump(stats, open(os.path.join(args.out_dir, "mount_compat_stats.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    with open(os.path.join(args.out_dir, "mount_compat_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    log(f"\n-> đã ghi {len(OUT_FILES)} file vào {args.out_dir}")


if __name__ == "__main__":
    main()
