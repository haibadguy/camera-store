"""
05c_rgcn_train.py -- R-GCN variant baseline (HeteroConv + SAGEConv per-relation).

Kien truc: HeteroConv voi mot SAGEConv rieng cho tung relation trong kg_hetero.pt.
Day la bien the di truyen cua R-GCN, khong phai implementation Schlichtkrull et al.
nguyen ban (co ghi ro trong doc).

Chay tu thu muc goc camera-store:
  python ai/pipeline/05c_rgcn_train.py

Output:
  results/rgcn_best.pt
  results/rgcn_results.json
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, SAGEConv

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# -- Hyperparameters -------------------------------------------------------
SEED        = C.SEED
EMB_DIM     = 64
N_LAYERS    = 2       # 2 layers (heterogeneous graph)
LR          = 2.5e-3
L2_REG      = 1e-4
BATCH_SIZE  = 16384
MAX_EPOCH   = 30
EVAL_EVERY  = 2
PATIENCE    = 4
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

np.random.seed(SEED)
torch.manual_seed(SEED)


# -- R-GCN Variant Model ---------------------------------------------------

class RGCNVariant(nn.Module):
    """
    Heterogeneous GNN: HeteroConv voi SAGEConv rieng cho tung relation.
    BPR training tren (user, interacted_with, item) edges.

    item.x = one-hot item_type [3] duoc project qua Linear truoc.
    mount.x, usecase.x = identity matrix.
    user: learnable embedding.
    """

    def __init__(self, n_users, n_items, emb_dim, n_layers, edge_types):
        super().__init__()
        self.n_users  = n_users
        self.n_items  = n_items
        self.emb_dim  = emb_dim
        self.n_layers = n_layers

        # Initial node embeddings
        self.user_emb     = nn.Embedding(n_users, emb_dim)
        self.item_emb     = nn.Embedding(n_items, emb_dim)
        self.item_proj    = nn.Linear(3, emb_dim, bias=False)   # item_type [3] -> emb_dim
        self.mount_proj   = nn.Linear(8, emb_dim, bias=False)   # mount one-hot [8]
        self.usecase_proj = nn.Linear(7, emb_dim, bias=False)   # usecase one-hot [7]

        nn.init.normal_(self.user_emb.weight, std=0.01)
        nn.init.normal_(self.item_emb.weight, std=0.01)

        # HeteroConv layers
        self.convs = nn.ModuleList()
        for _ in range(n_layers):
            conv_dict = {et: SAGEConv(emb_dim, emb_dim, normalize=True)
                         for et in edge_types}
            self.convs.append(HeteroConv(conv_dict, aggr="sum"))

        self.dropout = nn.Dropout(p=0.1)

    def get_init_embeddings(self, data):
        """Khoi tao embedding cho tat ca node types tu features."""
        return {
            "user":    self.user_emb.weight,
            "item":    self.item_emb.weight + self.item_proj(data["item"].x.to(DEVICE)),
            "mount":   self.mount_proj(data["mount"].x.to(DEVICE)),
            "usecase": self.usecase_proj(data["usecase"].x.to(DEVICE)),
        }

    def forward_embeddings(self, data):
        """Chay n_layers HeteroConv, tra ve dict {node_type: emb tensor}."""
        x_dict = self.get_init_embeddings(data)
        edge_index_dict = {et: data[et].edge_index.to(DEVICE)
                           for et in data.edge_types}

        for conv in self.convs:
            x_dict = conv(x_dict, edge_index_dict)
            x_dict = {k: self.dropout(F.relu(v)) for k, v in x_dict.items()}

        return x_dict

    def bpr_loss(self, data, users, pos_items, neg_items):
        x_dict = self.forward_embeddings(data)
        u   = x_dict["user"][users]
        pos = x_dict["item"][pos_items]
        neg = x_dict["item"][neg_items]

        pos_score = (u * pos).sum(dim=1)
        neg_score = (u * neg).sum(dim=1)
        loss = -F.logsigmoid(pos_score - neg_score).mean()

        # L2 tren initial embeddings (user + item)
        l2 = (self.user_emb.weight[users].norm(2).pow(2)
              + self.item_emb.weight[pos_items].norm(2).pow(2)
              + self.item_emb.weight[neg_items].norm(2).pow(2)) / len(users)
        return loss + L2_REG * l2


# -- Training --------------------------------------------------------------

def train_one_epoch(model, optimizer, data, train_pairs, sampler):
    model.train()
    rng = np.random.default_rng(SEED)
    rng.shuffle(train_pairs)

    total_loss = 0.0
    n_batches  = 0

    for start in range(0, len(train_pairs), BATCH_SIZE):
        batch     = train_pairs[start:start + BATCH_SIZE]
        users     = torch.tensor([x[0] for x in batch], dtype=torch.long, device=DEVICE)
        pos_items = torch.tensor([x[1] for x in batch], dtype=torch.long, device=DEVICE)
        neg_items = torch.tensor(
            [sampler.sample(x[0]) for x in batch], dtype=torch.long, device=DEVICE
        )

        optimizer.zero_grad()
        loss = model.bpr_loss(data, users, pos_items, neg_items)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        n_batches  += 1

    return total_loss / max(n_batches, 1)


@torch.no_grad()
def evaluate(model, data, pos_dict, neg_dict):
    model.eval()
    x_dict = model.forward_embeddings(data)
    user_emb = x_dict["user"].cpu().numpy()
    item_emb = x_dict["item"].cpu().numpy()
    rng = np.random.default_rng(SEED)

    def score_fn(uid, pos_iid, neg_iids):
        candidates = [pos_iid] + list(neg_iids)
        u = user_emb[uid]
        i = item_emb[candidates]
        return (u * i).sum(axis=1)

    return C.sampled_eval(score_fn, pos_dict, neg_dict, rng=rng)


# -- Main ------------------------------------------------------------------

def main():
    print("=" * 60, flush=True)
    print("MUC 5c: R-GCN VARIANT TRAINING", flush=True)
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

    # Load kg_hetero.pt
    import torch as _torch
    data = _torch.load(str(C.KG_PT), weights_only=False)
    data = data.to(DEVICE)

    print(f"  Edge types: {data.edge_types}", flush=True)
    print(f"  train pairs: {sum(len(v) for v in train_dict.values()):,}", flush=True)
    print(f"  CVR users:   {len(cvr_users):,}", flush=True)

    train_pairs = [(uid, iid) for uid, items in train_dict.items() for iid in items]
    sampler     = C.OnlineNegSampler(train_dict, C.N_ITEMS, np.random.default_rng(SEED))

    # Model
    model = RGCNVariant(
        n_users=C.N_USERS, n_items=C.N_ITEMS,
        emb_dim=EMB_DIM, n_layers=N_LAYERS,
        edge_types=data.edge_types,
    ).to(DEVICE)

    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    print(f"\nModel: R-GCN variant | n_layers={N_LAYERS} | emb_dim={EMB_DIM}", flush=True)
    print(f"Config: lr={LR} | l2={L2_REG} | batch={BATCH_SIZE} | patience={PATIENCE} eval cycles", flush=True)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Params: {total_params:,}", flush=True)

    best_val_ndcg10 = -1.0
    best_epoch      = 0
    patience_cnt    = 0
    best_state      = None

    print("\nTraining...", flush=True)
    t0 = time.time()

    for epoch in range(1, MAX_EPOCH + 1):
        ep_t0 = time.time()
        loss = train_one_epoch(model, optimizer, data, train_pairs, sampler)
        ep_time = time.time() - ep_t0

        if epoch % EVAL_EVERY == 0:
            eval_t0 = time.time()
            val_metrics = evaluate(model, data, val_pos, val_neg)
            eval_time = time.time() - eval_t0
            ndcg10  = val_metrics["ndcg@10"]
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
                    "state_dict":      best_state,
                    "config": {
                        "n_layers": N_LAYERS, "emb_dim": EMB_DIM,
                        "lr": LR, "l2": L2_REG, "batch_size": BATCH_SIZE,
                    },
                    "best_epoch":      best_epoch,
                    "best_val_ndcg10": best_val_ndcg10,
                    "seed":            SEED,
                    "edge_types":      [str(et) for et in data.edge_types],
                }, C.RESULTS_DIR / "rgcn_best.pt")
            else:
                patience_cnt += 1
                if patience_cnt >= PATIENCE:
                    print(f"\n  Early stopping at epoch {epoch} "
                          f"(best: epoch {best_epoch}, val NDCG@10={best_val_ndcg10:.4f})", flush=True)
                    break
        else:
            print(f"  Epoch {epoch:2d}/{MAX_EPOCH} | loss={loss:.4f} ({ep_time:.1f}s)", flush=True)

    model.load_state_dict(best_state)
    print(f"\nBest checkpoint: epoch {best_epoch}, val NDCG@10={best_val_ndcg10:.4f}", flush=True)

    # Test — sampled 1+99
    print("\nTest evaluation (sampled 1+99)...", flush=True)
    test_hit_ndcg = evaluate(model, data, test_pos, test_neg)
    C.print_results("R-GCN variant (sampled)", test_hit_ndcg)

    # Test — CVR full-catalog
    print("\nTest CVR (full-catalog)...", flush=True)
    model.eval()

    # Precompute embeddings ONCE with torch.no_grad() and detach()
    with torch.no_grad():
        x_dict = model.forward_embeddings(data)
        user_emb_np = x_dict["user"].detach().cpu().numpy()
        item_emb_T_np = x_dict["item"].detach().T.cpu().numpy()

    def score_fn_full(uid):
        return user_emb_np[uid] @ item_emb_T_np

    cvr_results = C.full_catalog_cvr(
        score_fn=score_fn_full,
        cvr_users=cvr_users,
        train_dict=train_dict,
        body_to_lenses=body_to_lenses,
        item_type=item_type,
    )
    C.print_results("R-GCN variant (CVR)", cvr_results)

    all_results = {**test_hit_ndcg, **cvr_results}

    # Save checkpoint
    out_pt = C.RESULTS_DIR / "rgcn_best.pt"
    torch.save({
        "state_dict":      best_state,
        "config": {
            "n_layers": N_LAYERS, "emb_dim": EMB_DIM,
            "lr": LR, "l2": L2_REG, "batch_size": BATCH_SIZE,
        },
        "best_epoch":      best_epoch,
        "best_val_ndcg10": best_val_ndcg10,
        "seed":            SEED,
        "edge_types":      [str(et) for et in data.edge_types],
    }, out_pt)
    print(f"\nSaved: {out_pt}", flush=True)

    out_json = C.RESULTS_DIR / "rgcn_results.json"
    with open(out_json, "w") as f:
        json.dump({
            "model": "R-GCN variant (HeteroConv+SAGEConv)",
            "note": "SAGEConv per-relation via HeteroConv. Not Schlichtkrull et al. exact formulation.",
            "config": {"n_layers": N_LAYERS, "emb_dim": EMB_DIM,
                       "lr": LR, "l2": L2_REG, "batch_size": BATCH_SIZE},
            "best_epoch": best_epoch,
            "best_val_ndcg10": best_val_ndcg10,
            "results": all_results,
        }, f, indent=2)
    print(f"Saved: {out_json}", flush=True)

    total_time = time.time() - t0
    print(f"\n=== HOAN TAT 05c | {total_time/60:.1f} phut ===", flush=True)


if __name__ == "__main__":
    main()
