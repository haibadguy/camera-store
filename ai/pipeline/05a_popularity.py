"""
05a_popularity.py -- Popularity baseline (Global + MountAware).

Chay tu thu muc goc camera-store:
  python ai/pipeline/05a_popularity.py

Output:
  results/popularity_global.json
  results/popularity_mountaware.json
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def build_pop_scores(train_dict):
    """Dem tan suat xuat hien cua moi item trong train -> np.array [N_ITEMS]."""
    counts = np.zeros(C.N_ITEMS, dtype=np.float64)
    for items in train_dict.values():
        for iid in items:
            if 0 <= iid < C.N_ITEMS:
                counts[iid] += 1.0
    return counts


def run_popularity(mode: str, pop_scores, pos_dict, neg_dict,
                   cvr_users, train_dict, body_to_lenses, item_type):
    """
    mode: 'global' hoac 'mount_aware'.
    Global:      rank candidates theo pop_scores, khong filter ngan.
    MountAware:  lens khong trong valid_lenses_u nhan score = -inf khi sampled eval.
                 CVR tinh full-catalog (giong Global -- chi ranking khac nhau).
    """
    rng = np.random.default_rng(C.SEED)

    # -- Sampled eval (Hit / NDCG) -----------------------------------------
    def score_fn_sampled(uid, pos_iid, neg_iids):
        candidates = [pos_iid] + list(neg_iids)
        scores = pop_scores[candidates].copy()

        if mode == "mount_aware":
            # Lay valid lenses cua user nay
            linked_bodies = cvr_users.get(uid, set())
            valid_lenses = set()
            for b in linked_bodies:
                valid_lenses |= body_to_lenses.get(b, set())
            # Chi filter lens; body/accessory giu nguyen
            for idx, iid in enumerate(candidates):
                if item_type[iid] == 1 and iid not in valid_lenses:
                    scores[idx] = -np.inf

        return scores

    hit_ndcg = C.sampled_eval(
        score_fn=score_fn_sampled,
        pos_dict=pos_dict,
        neg_dict=neg_dict,
        rng=rng,
    )

    # -- Full-catalog CVR --------------------------------------------------
    def score_fn_full(uid):
        scores = pop_scores.copy()
        if mode == "mount_aware":
            linked_bodies = cvr_users.get(uid, set())
            valid_lenses = set()
            for b in linked_bodies:
                valid_lenses |= body_to_lenses.get(b, set())
            for iid in range(C.N_ITEMS):
                if item_type[iid] == 1 and iid not in valid_lenses:
                    scores[iid] = -np.inf
        return scores

    cvr = C.full_catalog_cvr(
        score_fn=score_fn_full,
        cvr_users=cvr_users,
        train_dict=train_dict,
        body_to_lenses=body_to_lenses,
        item_type=item_type,
    )

    return {**hit_ndcg, **cvr}


def main():
    print("=" * 60)
    print("MUC 5a: POPULARITY BASELINE")
    print("=" * 60)

    print("\nLoading data...")
    train_dict   = C.load_train()
    test_pos     = C.load_pos("test")
    test_neg     = C.load_negatives("test")
    item_type    = C.load_item_type()
    body_to_lenses = C.load_body_to_lenses()
    cvr_users    = C.build_train_bodies(train_dict, body_to_lenses, item_type)

    print(f"  train users:       {len(train_dict):,}")
    print(f"  test users:        {len(test_pos):,}")
    print(f"  CVR users (body):  {len(cvr_users):,}")

    print("\nBuilding popularity scores...")
    pop_scores = build_pop_scores(train_dict)
    top5 = np.argsort(-pop_scores)[:5]
    print(f"  Top-5 items by frequency: {top5.tolist()}")
    print(f"  Max freq: {int(pop_scores.max())} | Items with freq>0: {int((pop_scores>0).sum())}")

    # -- Global -----------------------------------------------------------
    print("\nRunning Popularity-Global...")
    global_results = run_popularity(
        mode="global",
        pop_scores=pop_scores,
        pos_dict=test_pos,
        neg_dict=test_neg,
        cvr_users=cvr_users,
        train_dict=train_dict,
        body_to_lenses=body_to_lenses,
        item_type=item_type,
    )
    C.print_results("Popularity-Global", global_results)

    out_global = C.RESULTS_DIR / "popularity_global.json"
    with open(out_global, "w") as f:
        json.dump({"model": "Popularity-Global", "results": global_results}, f, indent=2)
    print(f"\nSaved: {out_global}")

    # -- MountAware -------------------------------------------------------
    print("\nRunning Popularity-MountAware...")
    ma_results = run_popularity(
        mode="mount_aware",
        pop_scores=pop_scores,
        pos_dict=test_pos,
        neg_dict=test_neg,
        cvr_users=cvr_users,
        train_dict=train_dict,
        body_to_lenses=body_to_lenses,
        item_type=item_type,
    )
    C.print_results("Popularity-MountAware", ma_results)

    out_ma = C.RESULTS_DIR / "popularity_mountaware.json"
    with open(out_ma, "w") as f:
        json.dump({"model": "Popularity-MountAware", "results": ma_results}, f, indent=2)
    print(f"Saved: {out_ma}")

    print("\n=== HOAN TAT 05a ===")
    print("CVR duoc tinh tren", len(cvr_users), "users co body linked trong train.")


if __name__ == "__main__":
    main()
