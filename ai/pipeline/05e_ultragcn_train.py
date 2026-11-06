"""
05e_ultragcn_train.py -- UltraGCN (Mao et al., CIKM 2021) trong vòng huấn luyện của nhóm (train_05: chấm NDCG@20 val
full ranking mỗi 10 epoch, dừng sau 5 lần chấm không tăng, trần 1.000 epoch, chạy tiếp từ last.pt).
Viết 06/11/2026 theo docs/reviews/v3_eval_plan.md mục 3 (UltraGCN không có trong RecBole / RecBole-GNN).

Đối chiếu: code của tác giả, repo RecZoo (https://github.com/xue-pai/UltraGCN, thư mục matching/gnn/UltraGCN, commit
88fae23, main.py + config/ultragcn_amazonelectronics_m1.ini). Cấu hình mặc định ở đây = file .ini Amazon Electronics:
  d 64, ii_neighbor_num 10, initial_weight 1e-3 (khởi tạo normal), Adam lr 1e-3, batch 2048,
  w1 1e-7, w2 1, w3 1e-7, w4 1, negative_num 75, negative_weight 75, gamma 5e-5, lambda 1e-7, sampling_sift_pos yes.
Công thức (đúng main.py):
  β_u = √(d_u+1)/d_u, β_i = 1/√(d_i+1)  (d = bậc trong train);
  L_C (cal_loss_L) = Σ_batch [ BCE(ŷ_ui, 1; w1 + w2·β_uβ_i) + negative_weight · mean_{j∈N⁻} BCE(ŷ_uj, 0; w3 + w4·β_uβ_j) ];
  L_I (cal_loss_I) = Σ_batch Σ_{j∈S(i)} −ω_ij · log σ(e_uᵀ e_j), S(i) = 10 láng giềng tốt nhất của i trên đồ thị
     item–item G = RᵀR (KHÔNG xóa đường chéo, như mặc định ii_diagonal_zero = False), ω_ij = G_ij · √(g_i+1)/g_i ·
     1/√(g_j+1), g = tổng hàng của G;
  norm_loss = ½ Σ_tham số ‖θ‖²;  loss = L_C + gamma · norm_loss + lambda · L_I (cộng theo TỔNG, như code tác giả).
  Âm mẫu: mỗi cặp 75 sản phẩm đều, có hoàn lại, trừ sản phẩm user có trong train (sampling_sift_pos = yes), lấy mới
  mỗi batch. Điểm xếp hạng ŷ_ui = e_uᵀ e_i.
Chỗ khác code tác giả (ghi để báo cáo):
  - chọn mô hình / dừng sớm theo giao thức nhóm (NDCG@20 val mỗi 10 epoch, kiên nhẫn 5 lần chấm, trần 1.000), không
    theo Recall@20 test mỗi epoch + kiên nhẫn 250 như file .ini (tác giả chấm trên tập test để dừng sớm);
  - âm mẫu bằng bộ sinh số torch trên GPU (lấy lại phần trùng train), tác giả dùng np.random.choice với xác suất 0
    cho item đã có — cùng phân phối (đều trên item chưa có), khác dãy số;
  - log σ viết bằng F.logsigmoid (ổn định số), tác giả viết .sigmoid().log() — cùng giá trị khi không tràn số;
  - top-10 láng giềng: hòa điểm xếp theo chỉ số item tăng dần (tác giả dùng torch.topk, thứ tự hòa không quy định);
    item có g_i = 0 (71 item chỉ có ở val / test) không có láng giềng (tác giả ra NaN nhưng không bao giờ dùng hàng đó
    vì item không có trong train);
  - train_05 vẫn lấy 1 âm mẫu j / cặp (numpy) nhưng UltraGCN KHÔNG dùng j (giữ vòng huấn luyện chung).
Chạy (chỉ val, không chấm test):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/05e_ultragcn_train.py --seed 1 --run-dir results/<...>/<tên>
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sps
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402
import train_05 as T   # noqa: E402

PIPE = Path(__file__).resolve().parent
CODE_FILES = [Path(__file__)]

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def ii_neighbors(u, i, n_users, n_items, k):
    """Láng giềng item–item: (idx [n_items, k] long, w [n_items, k] float); thiếu láng giềng thì idx 0, w 0."""
    R = sps.csr_matrix((np.ones(len(u), np.float64), (u, i)), shape=(n_users, n_items))
    G = (R.T @ R).tocsr()                                   # đếm đồng xuất hiện, giữ đường chéo
    g = np.asarray(G.sum(axis=1)).reshape(-1)
    bu = np.zeros(n_items)
    bu[g > 0] = np.sqrt(g[g > 0] + 1) / g[g > 0]
    bi = 1.0 / np.sqrt(g + 1)
    idx = np.zeros((n_items, k), np.int64)
    w = np.zeros((n_items, k), np.float32)
    for r in range(n_items):
        s, e = G.indptr[r], G.indptr[r + 1]
        if s == e:
            continue
        cols = G.indices[s:e]
        val = G.data[s:e] * bu[r] * bi[cols]
        o = np.lexsort((cols, -val))[:k]                    # điểm giảm dần, hòa -> chỉ số tăng dần
        idx[r, :len(o)] = cols[o]
        w[r, :len(o)] = val[o]
    return torch.as_tensor(idx), torch.as_tensor(w), int(G.nnz)


class UltraGCN(nn.Module):
    def __init__(self, n_users, n_items, cfg, du, di, ii_idx, ii_w, pair_keys):
        super().__init__()
        self.n_items, self.c = n_items, cfg
        self.user_embeds = nn.Embedding(n_users, cfg["dim"])
        self.item_embeds = nn.Embedding(n_items, cfg["dim"])
        nn.init.normal_(self.user_embeds.weight, std=cfg["initial_weight"])
        nn.init.normal_(self.item_embeds.weight, std=cfg["initial_weight"])
        bu = torch.zeros(n_users, dtype=torch.float64)
        bu[du > 0] = torch.sqrt(du[du > 0] + 1.0) / du[du > 0]
        self.register_buffer("beta_u", bu.float())
        self.register_buffer("beta_i", (1.0 / torch.sqrt(di + 1.0)).float())
        self.register_buffer("ii_idx", ii_idx)
        self.register_buffer("ii_w", ii_w)
        self.register_buffer("keys", pair_keys)              # u * n_items + i, đã sắp xếp (để loại item đã có)

    def sample_neg(self, u):
        n = self.c["negative_num"]
        neg = torch.randint(0, self.n_items, (len(u), n), device=u.device)
        uu = u.unsqueeze(1).expand_as(neg)
        bad = torch.ones_like(neg, dtype=torch.bool)
        while True:
            k = uu * self.n_items + neg
            pos = torch.searchsorted(self.keys, k).clamp_max(len(self.keys) - 1)
            bad = self.keys[pos] == k
            nb = int(bad.sum())
            if nb == 0:
                return neg
            neg[bad] = torch.randint(0, self.n_items, (nb,), device=u.device)

    def loss(self, u, i, j_unused):
        c = self.c
        neg = self.sample_neg(u)
        eu, ei, en = self.user_embeds(u), self.item_embeds(i), self.item_embeds(neg)
        pos_s = (eu * ei).sum(-1)
        neg_s = (eu.unsqueeze(1) * en).sum(-1)
        pw = c["w1"] + c["w2"] * self.beta_u[u] * self.beta_i[i]
        nw = c["w3"] + c["w4"] * self.beta_u[u].unsqueeze(1) * self.beta_i[neg]
        pos_l = F.binary_cross_entropy_with_logits(pos_s, torch.ones_like(pos_s), weight=pw, reduction="none")
        neg_l = F.binary_cross_entropy_with_logits(neg_s, torch.zeros_like(neg_s), weight=nw, reduction="none").mean(-1)
        L_c = (pos_l + c["negative_weight"] * neg_l).sum()
        norm = sum((p ** 2).sum() for p in self.parameters()) / 2
        nbr = self.item_embeds(self.ii_idx[i])                      # [b, K, d]
        L_i = (-self.ii_w[i] * F.logsigmoid((eu.unsqueeze(1) * nbr).sum(-1))).sum()
        return L_c + c["gamma"] * norm + c["lambda"] * L_i

    @torch.no_grad()
    def score_fn(self):
        eu, ei = self.user_embeds.weight, self.item_embeds.weight
        return lambda uids: eu[uids] @ ei.T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-dir", required=True)
    for k, v in (("w1", 1e-7), ("w2", 1.0), ("w3", 1e-7), ("w4", 1.0), ("gamma", 5e-5), ("lambda", 1e-7),
                 ("initial-weight", 1e-3)):
        ap.add_argument(f"--{k}", type=float, default=v)
    ap.add_argument("--negative-num", type=int, default=75)
    ap.add_argument("--negative-weight", type=float, default=75.0)
    ap.add_argument("--ii-neighbor-num", type=int, default=10)
    ap.add_argument("--max-epoch", type=int, default=1000)
    ap.add_argument("--eval-every", type=int, default=10)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--stop-after", type=int, default=None, help="(kiểm thử) dừng sau N epoch như bị ngắt")
    a = ap.parse_args()
    cfg = {"dim": 64, "lr": 1e-3, "batch": 2048, "initial_weight": a.initial_weight, "w1": a.w1, "w2": a.w2,
           "w3": a.w3, "w4": a.w4, "negative_num": a.negative_num, "negative_weight": a.negative_weight,
           "gamma": a.gamma, "lambda": a.__dict__["lambda"], "ii_neighbor_num": a.ii_neighbor_num,
           "sampling_sift_pos": True, "ii_diagonal_zero": False,
           "src": "RecZoo matching/gnn/UltraGCN@88fae23, config ultragcn_amazonelectronics_m1.ini",
           "seed": a.seed, "max_epoch": a.max_epoch, "eval_every": a.eval_every, "patience": a.patience,
           "select_metric": "val ndcg@20 full ranking"}
    if a.stop_after:
        cfg["_stop_after"] = a.stop_after

    def build(train, log):
        t = time.time()
        u, i = T.train_pairs(train)
        du = torch.as_tensor(np.bincount(u, minlength=C.N_USERS), dtype=torch.float64)
        di = torch.as_tensor(np.bincount(i, minlength=C.N_ITEMS), dtype=torch.float64)
        ii_idx, ii_w, nnz = ii_neighbors(u, i, C.N_USERS, C.N_ITEMS, cfg["ii_neighbor_num"])
        keys = torch.as_tensor(np.unique(u.astype(np.int64) * C.N_ITEMS + i))
        m = UltraGCN(C.N_USERS, C.N_ITEMS, cfg, du, di, ii_idx, ii_w, keys).to(E.DEVICE)
        log(f"UltraGCN: G = RᵀR {nnz:,} phần tử khác 0; item có láng giềng {(ii_w[:, 0] > 0).sum():,} / {C.N_ITEMS:,}; "
            f"{sum(p.numel() for p in m.parameters()):,} tham số; dựng {time.time() - t:.1f}s")
        return m, m.parameters()

    T.run("UltraGCN", cfg, build, a.run_dir, extra_argv=sys.argv, code_files=CODE_FILES)


if __name__ == "__main__":
    main()
