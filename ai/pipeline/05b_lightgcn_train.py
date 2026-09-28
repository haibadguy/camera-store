"""
05b_lightgcn_train.py -- LightGCN baseline (pure user-item CF).

Chay tu thu muc goc camera-store:
  python ai/pipeline/05b_lightgcn_train.py

Output:
  results/lightgcn_best.pt
  results/lightgcn_results.json
"""

import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# -- Hyperparameters -------------------------------------------------------
SEED        = C.SEED
EMB_DIM     = 64
N_LAYERS    = 3
LR          = 2.5e-3
L2_REG      = 1e-4
BATCH_SIZE  = 16384
MAX_EPOCH   = 30
EVAL_EVERY  = 2      # epochs
PATIENCE    = 4      # eval cycles (= 8 epochs)
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


# -- Normalized Adjacency --------------------------------------------------

def build_norm_adj(train_dict, n_users, n_items):
    """
    Build D^(-1/2) A D^(-1/2) cho LightGCN.
    A = [[0, R], [R^T, 0]], R la user-item interaction matrix.
    Tra ve sparse FloatTensor [N+M, N+M].
    """
    print("Building normalized adjacency...", flush=True)
    rows, cols = [], []
    for uid, items in train_dict.items():
        for iid in items:
            rows.append(uid)
            cols.append(n_users + iid)
            rows.append(n_users + iid)
            cols.append(uid)

    N = n_users + n_items
    indices = torch.tensor([rows, cols], dtype=torch.long)
    values  = torch.ones(len(rows), dtype=torch.float32)
    A = torch.sparse_coo_tensor(indices, values, (N, N)).coalesce()

    # Degree vector D^(-1/2)
    deg = torch.sparse.sum(A, dim=1).to_dense()
    deg_inv_sqrt = deg.pow(-0.5)
    deg_inv_sqrt[deg_inv_sqrt == float("inf")] = 0.0

    # D^(-1/2) A D^(-1/2): scale rows and cols
    row_idx = indices[0]
    col_idx = indices[1]
    norm_vals = deg_inv_sqrt[row_idx] * values * deg_inv_sqrt[col_idx]

    norm_adj = torch.sparse_coo_tensor(indices, norm_vals, (N, N)).coalesce()
    print(f"  Norm adj: {N} x {N}, nnz={norm_adj._nnz():,}", flush=True)
    return norm_adj.to(DEVICE)


# -- LightGCN Model --------------------------------------------------------

class LightGCN(nn.Module):
    def __init__(self, n_users, n_items, emb_dim, n_layers, norm_adj):
        super().__init__()
        self.n_users  = n_users
        self.n_items  = n_items
        self.n_layers = n_layers
        self.norm_adj = norm_adj

        self.user_emb = nn.Embedding(n_users, emb_dim)
        self.item_emb = nn.Embedding(n_items, emb_dim)
        nn.init.normal_(self.user_emb.weight, std=0.01)
        nn.init.normal_(self.item_emb.weight, std=0.01)

    def get_all_embeddings(self):
        E = torch.cat([self.user_emb.weight, self.item_emb.weight], dim=0)
        layers = [E]
        for _ in range(self.n_layers):
            E = torch.sparse.mm(self.norm_adj, E)
            layers.append(E)
        E_final = torch.stack(layers, dim=0).mean(dim=0)
        return E_final[:self.n_users], E_final[self.n_users:]

    def bpr_loss(self, users, pos_items, neg_items):
        u_emb, i_emb = self.get_all_embeddings()
        u   = u_emb[users]
        pos = i_emb[pos_items]
        neg = i_emb[neg_items]
        pos_score = (u * pos).sum(dim=1)
        neg_score = (u * neg).sum(dim=1)
        loss = -F.logsigmoid(pos_score - neg_score).mean()
        # L2 regularization on initial embeddings only
        l2 = (self.user_emb.weight[users].norm(2).pow(2)
              + self.item_emb.weight[pos_items].norm(2).pow(2)
              + self.item_emb.weight[neg_items].norm(2).pow(2)) / len(users)
        return loss + L2_REG * l2


# -- Training --------------------------------------------------------------

def train_one_epoch(model, optimizer, train_pairs, sampler):
    model.train()
    rng = np.random.default_rng(SEED)
    rng.shuffle(train_pairs)

    total_loss = 0.0
    n_batches  = 0

    for start in range(0, len(train_pairs), BATCH_SIZE):
        batch = train_pairs[start:start + BATCH_SIZE]
        users     = torch.tensor([x[0] for x in batch], dtype=torch.long, device=DEVICE)
        pos_items = torch.tensor([x[1] for x in batch], dtype=torch.long, device=DEVICE)
        neg_items = torch.tensor(
            [sampler.sample(x[0]) for x in batch], dtype=torch.long, device=DEVICE
        )

        optimizer.zero_grad()
        loss = model.bpr_loss(users, pos_items, neg_items)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        n_batches  += 1

    return total_loss / max(n_batches, 1)


@torch.no_grad()
def evaluate(model, pos_dict, neg_dict, split="val"):
    model.eval()
    rng = np.random.default_rng(SEED)

    # Compute embeddings ONCE for the entire evaluation
    u_emb, i_emb = model.get_all_embeddings()
    u_np = u_emb.cpu().numpy()
    i_np = i_emb.cpu().numpy()

    def score_fn(uid, pos_iid, neg_iids):
        candidates = [pos_iid] + list(neg_iids)
        u = u_np[uid]
        i = i_np[candidates]
        return (u * i).sum(axis=1)

    return C.sampled_eval(score_fn, pos_dict, neg_dict, rng=rng)


# -- Main ------------------------------------------------------------------

def main():
    print("=" * 60, flush=True)
    print("MUC 5b: LIGHTGCN TRAINING", flush=True)
    print(f"Device: {DEVICE}", flush=True)
    print("=" * 60, flush=True)

    # Load data
    print("\nLoading data...", flush=True)
    train_dict     = C.load_train()
    val_pos        = C.load_pos("val")
    val_neg        = C.load_negatives("val")
    test_pos       = C.load_pos("test")
    test_neg       = C.load_negatives("test")
    item_type      = C.load_item_type()
    body_to_lenses = C.load_body_to_lenses()
    cvr_users      = C.build_train_bodies(train_dict, body_to_lenses, item_type)

    # Flatten train pairs: [(uid, iid), ...]
    train_pairs = [(uid, iid) for uid, items in train_dict.items() for iid in items]
    print(f"  train pairs: {len(train_pairs):,}", flush=True)
    print(f"  val users:   {len(val_pos):,}", flush=True)
    print(f"  CVR users:   {len(cvr_users):,}", flush=True)

    # Build norm adj
    norm_adj = build_norm_adj(train_dict, C.N_USERS, C.N_ITEMS)

    # Model + optimizer
    model = LightGCN(C.N_USERS, C.N_ITEMS, EMB_DIM, N_LAYERS, norm_adj).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    sampler   = C.OnlineNegSampler(train_dict, C.N_ITEMS, np.random.default_rng(SEED))

    print(f"\nModel: LightGCN | n_layers={N_LAYERS} | emb_dim={EMB_DIM}", flush=True)
    print(f"Config: lr={LR} | l2={L2_REG} | batch={BATCH_SIZE} | patience={PATIENCE} eval cycles", flush=True)

    best_val_ndcg10 = -1.0
    best_epoch      = 0
    patience_cnt    = 0
    best_state      = None

    # Training loop
    print("\nTraining...", flush=True)
    t0 = time.time()

    for epoch in range(1, MAX_EPOCH + 1):
        ep_t0 = time.time()
        loss = train_one_epoch(model, optimizer, train_pairs, sampler)
        ep_time = time.time() - ep_t0

        if epoch % EVAL_EVERY == 0:
            eval_t0 = time.time()
            val_metrics = evaluate(model, val_pos, val_neg, "val")
            eval_time = time.time() - eval_t0
            ndcg10 = val_metrics["ndcg@10"]
            elapsed = time.time() - t0

            print(f"  Epoch {epoch:2d}/{MAX_EPOCH} | loss={loss:.4f} ({ep_time:.1f}s) | "
                  f"val Hit@10={val_metrics['hit@10']:.4f} NDCG@10={ndcg10:.4f} "
                  f"(eval {eval_time:.1f}s) | total {elapsed:.0f}s", flush=True)

            if ndcg10 > best_val_ndcg10:
                best_val_ndcg10 = ndcg10
                best_epoch      = epoch
                patience_cnt    = 0
                best_state      = {k: v.clone() for k, v in model.state_dict().items()}
                # Save checkpoint immediately
                torch.save({
                    "state_dict":       best_state,
                    "config": {
                        "n_layers": N_LAYERS, "emb_dim": EMB_DIM,
                        "lr": LR, "l2": L2_REG, "batch_size": BATCH_SIZE,
                    },
                    "best_epoch":       best_epoch,
                    "best_val_ndcg10":  best_val_ndcg10,
                    "seed":             SEED,
                }, C.RESULTS_DIR / "lightgcn_best.pt")
            else:
                patience_cnt += 1
                if patience_cnt >= PATIENCE:
                    print(f"\n  Early stopping at epoch {epoch} "
                          f"(best: epoch {best_epoch}, val NDCG@10={best_val_ndcg10:.4f})", flush=True)
                    break
        else:
            print(f"  Epoch {epoch:2d}/{MAX_EPOCH} | loss={loss:.4f} ({ep_time:.1f}s)", flush=True)

    # Load best checkpoint
    model.load_state_dict(best_state)
    print(f"\nBest checkpoint: epoch {best_epoch}, val NDCG@10={best_val_ndcg10:.4f}", flush=True)

    # Test evaluation — sampled 1+99
    print("\nTest evaluation (sampled 1+99)...", flush=True)
    test_hit_ndcg = evaluate(model, test_pos, test_neg, "test")
    C.print_results("LightGCN (sampled)", test_hit_ndcg)

    # Test evaluation — CVR full-catalog
    print("\nTest CVR (full-catalog, 2,488 users)...", flush=True)
    model.eval()

    # Precompute embeddings ONCE with torch.no_grad() and detach()
    with torch.no_grad():
        u_emb, i_emb = model.get_all_embeddings()
        u_np = u_emb.detach().cpu().numpy()
        i_np_T = i_emb.detach().T.cpu().numpy()

    def score_fn_full(uid):
        return u_np[uid] @ i_np_T

    cvr_results = C.full_catalog_cvr(
        score_fn=score_fn_full,
        cvr_users=cvr_users,
        train_dict=train_dict,
        body_to_lenses=body_to_lenses,
        item_type=item_type,
    )
    C.print_results("LightGCN (CVR)", cvr_results)

    # Combine results
    all_results = {**test_hit_ndcg, **cvr_results}

    # Save checkpoint
    out_pt = C.RESULTS_DIR / "lightgcn_best.pt"
    torch.save({
        "state_dict":       best_state,
        "config": {
            "n_layers": N_LAYERS, "emb_dim": EMB_DIM,
            "lr": LR, "l2": L2_REG, "batch_size": BATCH_SIZE,
        },
        "best_epoch":       best_epoch,
        "best_val_ndcg10":  best_val_ndcg10,
        "seed":             SEED,
    }, out_pt)
    print(f"\nSaved: {out_pt}", flush=True)

    out_json = C.RESULTS_DIR / "lightgcn_results.json"
    with open(out_json, "w") as f:
        json.dump({
            "model": "LightGCN",
            "config": {"n_layers": N_LAYERS, "emb_dim": EMB_DIM,
                       "lr": LR, "l2": L2_REG, "batch_size": BATCH_SIZE},
            "best_epoch": best_epoch,
            "best_val_ndcg10": best_val_ndcg10,
            "results": all_results,
        }, f, indent=2)
    print(f"Saved: {out_json}", flush=True)

    total_time = time.time() - t0
    print(f"\n=== HOAN TAT 05b | {total_time/60:.1f} phut ===", flush=True)


if __name__ == "__main__":
    main()
