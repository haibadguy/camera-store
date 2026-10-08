"""
05_common.py — Utilities dung chung cho tat ca scripts Muc 5.

Hai protocol danh gia:
  - Sampled (1+99): Hit@K, NDCG@K  -- tat ca users (N_USERS)
  - Full-catalog:   CVR@K           -- users co than may trong train, chi tinh ong "cham duoc" (QĐ 4-9)

Sửa 08/10/2026 (nội dung 4, content4_design mục 7): load_item_type đọc item_attributes.csv (4 mã);
load_body_to_lenses đọc cạnh compatible_with + crops_sensor của đồ thị; CVR theo QĐ 4-9.
"""

import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.sparse import load_npz

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# -- Constants ------------------------------------------------------------
ROOT          = Path(__file__).resolve().parent.parent.parent  # camera-store/
DATA_DIR      = ROOT / "ai" / "data"
RESULTS_DIR   = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

TRAIN_TXT     = DATA_DIR / "processed" / "train.txt"
VAL_TXT       = DATA_DIR / "processed" / "val.txt"
TEST_TXT      = DATA_DIR / "processed" / "test.txt"
VAL_NEG_JSON  = DATA_DIR / "processed" / "val_negatives.json"
TEST_NEG_JSON = DATA_DIR / "processed" / "test_negatives.json"
KG_PT         = DATA_DIR / "kg" / "kg_hetero.pt"
KG_STATS      = DATA_DIR / "kg" / "kg_stats.json"
ITEM_ATTR_CSV = DATA_DIR / "kg" / "item_attributes.csv"          # nội dung 3
M1_EDGE_CSVS  = [DATA_DIR / "kg" / "kg_edges_compatible_with.csv",  # nội dung 4: hai quan hệ này = M = 1
                 DATA_DIR / "kg" / "kg_edges_crops_sensor.csv"]
BODY_INDEX    = DATA_DIR / "kg" / "body_index.json"               # hàng của M (thân có 1 ngàm)
LENS_INDEX    = DATA_DIR / "kg" / "lens_index.json"               # cột của M (ống có 1 ngàm, không "không chắc")
UNKNOWN_NPZ   = DATA_DIR / "kg" / "unknown_mask.npz"              # cặp mức "không biết" (QĐ 3-8, 3-16)
ITEM_TYPE_CODE = {"than": 0, "ong": 1, "phu_kien": 2, "khac": 3}

USER_MAP_JSON = DATA_DIR / "processed" / "user_map.json"
ITEM_MAP_JSON = DATA_DIR / "processed" / "item_map.json"

# Lay so user/item tu file map cua Muc 2 (khong ghi cung).
# Dung len() nhu 04_build_knowledge_graph.py: id lien tuc 0..N-1.
with open(USER_MAP_JSON, encoding="utf-8") as _f:
    N_USERS = len(json.load(_f))
with open(ITEM_MAP_JSON, encoding="utf-8") as _f:
    N_ITEMS = len(json.load(_f))
K_LIST  = [5, 10, 20]
SEED    = 42


# -- Load functions -------------------------------------------------------

def load_train():
    """Load train.txt -> {uid: set[iid]}. Format: 'uid iid1 iid2 ...'"""
    train = {}
    with open(TRAIN_TXT, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            uid = int(parts[0])
            train[uid] = set(int(x) for x in parts[1:])
    return train


def load_pos(split: str):
    """Load val.txt or test.txt -> {uid: pos_iid}."""
    path = VAL_TXT if split == "val" else TEST_TXT
    pos = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            pos[int(parts[0])] = int(parts[1])
    return pos


def load_negatives(split: str):
    """Load *_negatives.json -> {uid: [99 iids]}. Keys are strings -> convert to int."""
    path = VAL_NEG_JSON if split == "val" else TEST_NEG_JSON
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


def load_item_type():
    """item_attributes.csv (nội dung 3) -> np.array [N_ITEMS]: 0 thân, 1 ống, 2 phụ kiện, 3 khác (máy ống liền...)."""
    out = np.full(N_ITEMS, -1, dtype=np.int64)
    with open(ITEM_ATTR_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[int(r["iid"])] = ITEM_TYPE_CODE[r["item_type"]]
    assert (out >= 0).all(), "item_attributes.csv thiếu sản phẩm"
    return out


def load_body_to_lenses():
    """M = 1: cạnh compatible_with + crops_sensor của đồ thị (kg_edges_*.csv) -> {body_iid: set[lens_iid]}.
    Không gồm requires_adapter (M = 0, QĐ 3-2), cặp "không biết" và ống "không chắc" (không có cạnh, QĐ 4-5)."""
    mapping = defaultdict(set)
    for path in M1_EDGE_CSVS:
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                mapping[int(r["body_iid"])].add(int(r["lens_iid"]))
    return dict(mapping)


@dataclass
class CvrContext:
    """Dữ liệu để phán một ống trong top-K (QĐ 4-9).
    lenses_in_m : ống nằm trong M (1 ngàm, không "không chắc")
    bodies_in_m : thân nằm trong M (1 ngàm)
    m1          : cặp (thân, ống) có M = 1
    unknown     : cặp (thân, ống) mức "không biết" """
    lenses_in_m: set
    bodies_in_m: set
    m1: set
    unknown: set


def load_cvr_context(body_to_lenses=None):
    if body_to_lenses is None:
        body_to_lenses = load_body_to_lenses()
    item_map = json.load(open(ITEM_MAP_JSON, encoding="utf-8"))
    b_idx = json.load(open(BODY_INDEX, encoding="utf-8"))
    l_idx = json.load(open(LENS_INDEX, encoding="utf-8"))
    b_iid = {j: item_map[a] for a, j in b_idx.items()}
    l_iid = {j: item_map[a] for a, j in l_idx.items()}
    U = load_npz(UNKNOWN_NPZ).tocoo()
    return CvrContext(
        lenses_in_m=set(l_iid.values()),
        bodies_in_m=set(b_iid.values()),
        m1={(b, l) for b, ls_ in body_to_lenses.items() for l in ls_},
        unknown={(b_iid[int(r)], l_iid[int(c)]) for r, c in zip(U.row, U.col)},
    )


def judge_lens(lens, bodies, ctx):
    """Phán một ống trong top-K của người dùng có các thân `bodies` (QĐ 4-9).
    Trả về True = vi phạm, False = không vi phạm, None = không chấm được.

    Ví dụ (QĐ 4-9): thân D3500 (Nikon F) + máy phim FM, ống Canon EF; nếu (D3500, EF) có M = 0 và (FM, EF) là
    "không biết" thì không thân nào M = 1, có một cặp "không biết" -> None.
    Thân không nằm trong M (không xác định được ngàm) không có giá trị M với ống nào: không phải M = 1, cũng không
    phải M = 0 -> không phán "vi phạm" được qua thân đó."""
    if lens not in ctx.lenses_in_m or not bodies:
        return None
    if any((b, lens) in ctx.m1 for b in bodies):                                       # (a)
        return False
    if all(b in ctx.bodies_in_m and (b, lens) not in ctx.unknown for b in bodies):     # (b) mọi thân M = 0
        return True
    return None


def build_train_bodies(train_dict, body_to_lenses, item_type):
    """
    Trả về {uid: set[body_iid]}: mọi thân máy (item_type 0) người dùng có trong train (QĐ 4-9: xét các thân
    người dùng có trong train), kể cả thân không có ống M = 1 nào (vd máy phim) và thân ngoài M.
    Người dùng không có thân nào thì không có trong kết quả. `body_to_lenses` giữ lại cho đúng chữ ký cũ, không dùng.
    """
    result = {}
    for uid, items in train_dict.items():
        bodies = {iid for iid in items if item_type[iid] == 0}
        if bodies:
            result[uid] = bodies
    return result


# -- Metric computation ---------------------------------------------------

def _rank_of_pos(pos_score, neg_scores, rng):
    """
    1-indexed rank cua positive item trong 100 candidates.
    Tie-break: cong noise nho vao neg_scores (seed co dinh -> reproducible).
    """
    noise = rng.uniform(0, 1e-9, len(neg_scores))
    n_better = int((neg_scores + noise > pos_score).sum())
    return n_better + 1


def compute_hit_ndcg(ranks, k_list=None):
    """
    ranks: np.array [N_users], 1-indexed.
    NDCG@K = 1/log2(rank+1) neu pos trong top-K, else 0.
    Recall@K = Hit@K (1 positive/user), bao cao Hit de gon.
    """
    if k_list is None:
        k_list = K_LIST
    results = {}
    ranks = np.array(ranks)
    for k in k_list:
        hit  = (ranks <= k).astype(float)
        ndcg = np.where(ranks <= k, 1.0 / np.log2(ranks + 1), 0.0)
        results[f"hit@{k}"]  = float(hit.mean())
        results[f"ndcg@{k}"] = float(ndcg.mean())
    return results


def sampled_eval(score_fn, pos_dict, neg_dict, k_list=None, rng=None):
    """
    Protocol sampled 1+99.
    score_fn(uid, pos_iid, neg_iids) -> np.array [100]:
      index 0 = score cua pos_iid, index 1..99 = scores cua neg_iids.
    """
    if k_list is None:
        k_list = K_LIST
    if rng is None:
        rng = np.random.default_rng(SEED)

    ranks = []
    for uid, pos_iid in pos_dict.items():
        neg_iids = neg_dict[uid]
        scores = np.array(score_fn(uid, pos_iid, neg_iids), dtype=float)
        pos_score  = scores[0]
        neg_scores = scores[1:]
        ranks.append(_rank_of_pos(pos_score, neg_scores, rng))

    return compute_hit_ndcg(np.array(ranks), k_list)


def full_catalog_cvr(score_fn, cvr_users, train_dict, body_to_lenses,
                     item_type, k_list=None, ctx=None):
    """
    Protocol full-catalog cho CVR (QĐ 4-9).
    score_fn(uid) -> np.array [số sản phẩm]: scores toàn catalog (ẩn sản phẩm đã có trong train).
    cvr_users: {uid: set[body_iid]} từ build_train_bodies.
    Mỗi ống trong top-K được phán bằng judge_lens: vi phạm / không vi phạm / không chấm được. Phụ kiện, thân,
    máy "khác" không tính.
    Gộp kiểu micro: CVR@K = tổng vi phạm / tổng ống chấm được, trên mọi người dùng. Người dùng có top-K không chứa
    ống nào chấm được thì bỏ khỏi phép tính (không tính CVR = 0).
    Trả kèm: cvr_n_users@K (số người dùng được tính), cvr_n_lenses@K (số ống chấm được),
    cvr_n_violations@K, cvr_n_users_with_body (số người dùng có thân trong train). CVR@K = nan nếu không có ống nào.
    """
    if k_list is None:
        k_list = K_LIST
    if ctx is None:
        ctx = load_cvr_context(body_to_lenses)
    k_max = max(k_list)
    n_users = {k: 0 for k in k_list}
    n_lenses = {k: 0 for k in k_list}
    n_viol = {k: 0 for k in k_list}

    for uid, bodies in cvr_users.items():
        train_items = train_dict.get(uid, set())

        # Full-catalog scores, an train items
        scores = np.array(score_fn(uid), dtype=float).copy()
        n_cat = len(scores)
        for iid in train_items:
            if 0 <= iid < n_cat:
                scores[iid] = -np.inf

        # Top-(k_max) ung vien toan catalog
        top_indices = np.argpartition(-scores, min(k_max, n_cat - 1))[:k_max]
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        verdict = {int(iid): (judge_lens(int(iid), bodies, ctx) if item_type[iid] == 1 else None)
                   for iid in top_indices}
        for k in k_list:
            v = [verdict[int(iid)] for iid in top_indices[:k] if verdict[int(iid)] is not None]
            if v:
                n_users[k] += 1
                n_lenses[k] += len(v)
                n_viol[k] += sum(v)

    out = {}
    for k in k_list:
        out[f"cvr@{k}"] = float(n_viol[k] / n_lenses[k]) if n_lenses[k] else float("nan")
        out[f"cvr_n_users@{k}"] = n_users[k]
        out[f"cvr_n_lenses@{k}"] = n_lenses[k]
        out[f"cvr_n_violations@{k}"] = n_viol[k]
    out["cvr_n_users_with_body"] = len(cvr_users)
    return out


# -- Report ---------------------------------------------------------------

# -- Online Negative Sampler (dung chung cho BPR training) ---------------

class OnlineNegSampler:
    """Sample 1 negative item khong nam trong lich su train cua user."""
    def __init__(self, train_dict, n_items, rng):
        self.train_dict = train_dict
        self.n_items    = n_items
        self.rng        = rng

    def sample(self, uid):
        train_items = self.train_dict.get(uid, set())
        while True:
            neg = int(self.rng.integers(0, self.n_items))
            if neg not in train_items:
                return neg


# -- Report ---------------------------------------------------------------

def print_results(name, results):
    print(f"\n{'='*55}")
    print(f"  {name}")
    print(f"{'='*55}")
    for k in K_LIST:
        hit  = results.get(f"hit@{k}",  "N/A")
        ndcg = results.get(f"ndcg@{k}", "N/A")
        cvr  = results.get(f"cvr@{k}",  "N/A")
        h = f"{hit:.4f}"  if isinstance(hit,  float) else hit
        n = f"{ndcg:.4f}" if isinstance(ndcg, float) else ndcg
        c = f"{cvr:.4f}"  if isinstance(cvr,  float) else cvr
        print(f"  @{k:<3}  Hit={h}  NDCG={n}  CVR={c}")

