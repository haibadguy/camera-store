"""
05_common.py — Utilities dung chung cho tat ca scripts Muc 5.

Hai protocol danh gia:
  - Sampled (1+99): Hit@K, NDCG@K  -- tat ca users (N_USERS)
  - Full-catalog:   CVR@K           -- users co body linked trong train
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch

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
COMPAT_CSV    = DATA_DIR / "kg" / "compatible_item_edges.csv"
KG_STATS      = DATA_DIR / "kg" / "kg_stats.json"

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
    """Load item_type from kg_hetero.pt. Returns np.array [N_ITEMS]: 0=body,1=lens,2=acc."""
    data = torch.load(KG_PT, weights_only=False)
    return data["item"].x.argmax(dim=1).numpy()


def load_body_to_lenses():
    """Load compatible_item_edges.csv -> {body_iid: set[lens_iid]}."""
    df = pd.read_csv(COMPAT_CSV)
    mapping = defaultdict(set)
    for _, row in df.iterrows():
        mapping[int(row["src_iid"])].add(int(row["dst_iid"]))
    return dict(mapping)


def build_train_bodies(train_dict, body_to_lenses, item_type):
    """
    Tra ve {uid: set[linked_body_iid]} chi voi user co body da link.
    'Da link' = co trong body_to_lenses.keys() (da xac dinh ngan).
    """
    linked_body_set = set(body_to_lenses.keys())
    result = {}
    for uid, items in train_dict.items():
        bodies = {iid for iid in items
                  if item_type[iid] == 0 and iid in linked_body_set}
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
                     item_type, k_list=None):
    """
    Protocol full-catalog cho CVR.
    score_fn(uid) -> np.array [N_ITEMS]: scores toan catalog.
    cvr_users: {uid: set[linked_body_iids]} -- chi user co body linked.
    CVR@K_u = violations / K (chia K, khong chia len(top_k_lenses)).
    User co 0 lens trong top-K -> CVR_u = 0.
    """
    if k_list is None:
        k_list = K_LIST
    k_max = max(k_list)
    cvr_per_k = {k: [] for k in k_list}

    for uid, linked_bodies in cvr_users.items():
        train_items = train_dict.get(uid, set())

        # Valid lenses = union tren tat ca body da link cua user
        valid_lenses = set()
        for b in linked_bodies:
            valid_lenses |= body_to_lenses.get(b, set())

        # Full-catalog scores, an train items
        scores = score_fn(uid).copy()
        for iid in train_items:
            if 0 <= iid < N_ITEMS:
                scores[iid] = -np.inf

        # Top-(k_max) ung vien toan catalog
        top_indices = np.argpartition(-scores, min(k_max, N_ITEMS - 1))[:k_max]
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        for k in k_list:
            top_k = top_indices[:k].tolist()
            violations = sum(
                1 for iid in top_k
                if item_type[iid] == 1       # chi lens
                and iid not in valid_lenses
            )
            cvr_per_k[k].append(violations / k)

    return {f"cvr@{k}": float(np.mean(cvr_per_k[k])) for k in k_list}


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

