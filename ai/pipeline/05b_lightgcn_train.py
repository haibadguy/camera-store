"""
05b_lightgcn_train.py -- LightGCN (He et al., SIGIR 2020), dò trên val theo docs/reviews/n5_eval_plan.md mục 6.3, 7.

Viết lại 09/10/2026 (bản của Hải: lr 2.5e-3, batch 16384, 30 epoch, khởi tạo normal 0,01, chấm sampled; lỗi L5, L9,
L10, L11, L13, L14 của kế hoạch mục 2).

Ví dụ: u có train {A, B}; mỗi bước lấy cặp (u, A) và 1 âm mẫu C mà u chưa có; loss BPR = −ln σ(ŷ_uA − ŷ_uC),
ŷ_ui = e_uᵀ e_i, với e = trung bình embedding của lớp 0..3 trên đồ thị user–item (chỉ cạnh train).

Cấu hình (mục 7.1): d 64, K 3 lớp, α_k = 1/(K+1), Xavier, Adam lr 0,001, batch 2048, không dropout;
λ dò {1e-5, 1e-4, 1e-3}; tối đa 300 epoch, chấm NDCG@20 val mỗi 10 epoch, dừng sau 5 lần chấm không tăng.
Hạng L2 theo code của tác giả (kuandeng/LightGCN `create_bpr_loss`, gusye1234/LightGCN-PyTorch `bpr_loss`):
λ · ½(‖e_u⁰‖² + ‖e_i⁰‖² + ‖e_j⁰‖²) / số cặp trong batch, chỉ embedding lớp 0.

Chạy (từ thư mục camera-store; chỉ val, không chấm test):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/05b_lightgcn_train.py --l2 1e-4 --seed 1 --run-dir results/n5/<nhãn>/<tên>
Chạy lại đúng lệnh đó sau khi bị ngắt -> chạy tiếp từ lần chấm val gần nhất.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402
import train_05 as T   # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def build_norm_adj(train, n_users, n_items):
    """D^(-1/2) A D^(-1/2), A = [[0, R], [Rᵀ, 0]], R = ma trận user–item của train."""
    u, i = T.train_pairs(train)
    rows = np.concatenate([u, n_users + i])
    cols = np.concatenate([n_users + i, u])
    N = n_users + n_items
    deg = np.bincount(rows, minlength=N).astype(np.float64)
    dis = np.zeros(N)
    dis[deg > 0] = deg[deg > 0] ** -0.5
    idx = torch.as_tensor(np.stack([rows, cols]))
    val = torch.as_tensor(dis[rows] * dis[cols], dtype=torch.float32)
    return torch.sparse_coo_tensor(idx, val, (N, N)).coalesce()


class LightGCN(nn.Module):
    def __init__(self, n_users, n_items, dim, n_layers, adj, l2):
        super().__init__()
        self.n_users, self.n_layers, self.l2, self.adj = n_users, n_layers, l2, adj
        self.user_emb = nn.Embedding(n_users, dim)
        self.item_emb = nn.Embedding(n_items, dim)
        nn.init.xavier_uniform_(self.user_emb.weight)      # bài §4.1.2: Xavier
        nn.init.xavier_uniform_(self.item_emb.weight)

    def propagate(self):
        E0 = torch.cat([self.user_emb.weight, self.item_emb.weight])
        acc, Ek = E0, E0
        for _ in range(self.n_layers):
            Ek = torch.sparse.mm(self.adj, Ek)
            acc = acc + Ek
        Ef = acc / (self.n_layers + 1)                     # α_k = 1/(K+1)
        return Ef[:self.n_users], Ef[self.n_users:]

    def loss(self, u, i, j):
        eu, ei = self.propagate()
        bpr = F.softplus(-((eu[u] * ei[i]).sum(1) - (eu[u] * ei[j]).sum(1))).mean()   # = −ln σ(·), trung bình
        reg = 0.5 * (self.user_emb(u).pow(2).sum() + self.item_emb(i).pow(2).sum()
                     + self.item_emb(j).pow(2).sum()) / len(u)
        return bpr + self.l2 * reg

    @torch.no_grad()
    def score_fn(self):
        eu, ei = self.propagate()
        return lambda uids: eu[uids] @ ei.T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l2", type=float, required=True, help="λ, dò {1e-5, 1e-4, 1e-3}")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--max-epoch", type=int, default=300)
    ap.add_argument("--eval-every", type=int, default=10)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--stop-after", type=int, default=None, help="(kiểm thử) dừng sau N epoch như bị ngắt")
    a = ap.parse_args()
    cfg = {"dim": 64, "n_layers": 3, "lr": 1e-3, "batch": 2048, "l2": a.l2, "init": "xavier_uniform",
           "seed": a.seed, "max_epoch": a.max_epoch, "eval_every": a.eval_every, "patience": a.patience,
           "select_metric": "val ndcg@20 full ranking"}
    if a.stop_after:
        cfg["_stop_after"] = a.stop_after

    def build(train, log):
        adj = build_norm_adj(train, C.N_USERS, C.N_ITEMS).to(E.DEVICE)
        log(f"Ma trận kề chuẩn hóa {C.N_USERS + C.N_ITEMS:,} nút, {adj._nnz():,} phần tử khác 0 (= 2 × cặp train)")
        m = LightGCN(C.N_USERS, C.N_ITEMS, cfg["dim"], cfg["n_layers"], adj, cfg["l2"]).to(E.DEVICE)
        return m, m.parameters()

    T.run("LightGCN", cfg, build, a.run_dir, extra_argv=sys.argv)


if __name__ == "__main__":
    main()
