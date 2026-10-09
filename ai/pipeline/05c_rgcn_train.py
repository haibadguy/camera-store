"""
05c_rgcn_train.py -- R-GCN (Schlichtkrull et al., ESWC 2018) bằng RGCNConv của PyG, trên đồ thị nội dung 4,
theo docs/reviews/n5_eval_plan.md mục 6.4, 7 (QĐ 5-3, 5-4, 5-5).

Viết lại 09/10/2026. Bản của Hải ("R-GCN variant") là HeteroConv + SAGEConv, không phải R-GCN (lỗi L1), và không chạy
được với đồ thị mới (L2); bỏ qua cờ cạnh (L3); ReLU + dropout ở lớp cuối (L16).

Ví dụ: ống EF 70-200 nhận tin từ người đã mua (quan hệ rev_interacted_with), các thân nối tới (rev_compatible_with),
nút ngàm canon_ef (rev_has_spec), nút "thể thao/chim" (rev_suitable_for). Mỗi quan hệ r có W_r riêng; tin của hàng
xóm loại r nhân W_r rồi lấy trung bình trong loại đó; cộng mọi loại với phần tự giữ W_0 h_i (bài Eq. 2):
  h_i^(l+1) = σ( Σ_r Σ_{j∈N_i^r} (1/|N_i^r|) W_r h_j + W_0 h_i ).

Cài đặt (mục 6.4):
  - đồ thị đồng nhất 95.646 nút, 18 quan hệ như kg_hetero.pt; bỏ 134 cạnh has_spec → mount có cờ ngam_khong_chac
    (và 134 cạnh ngược) -> 1.116.682 cạnh; user–item chỉ là cạnh train (script kiểm trùng train.txt);
  - mỗi nút một embedding học được (Xavier/glorot), không dùng item.x;
  - 2 lớp RGCNConv, d 64, phân rã cơ sở B = 2, aggr mean, root_weight, ReLU chỉ giữa hai lớp;
  - edge dropout 0,4 mỗi bước khi huấn luyện (không dropout phần W_0);
  - điểm user–item: DistMult f(u, i) = Σ_d e_u,d · r_d · e_i,d, r ∈ ℝ^64 khởi tạo glorot như tham số của RGCNConv;
  - loss BPR (QĐ 5-3) + 0,01 · ‖r‖² (L2 trên bộ giải mã, bài §5.2); Adam, lr dò {0,01; 0,001}; batch 2048;
  - tối đa 100 epoch, chấm NDCG@20 val mỗi 5 epoch, dừng sau 5 lần chấm không tăng.

Chạy (từ thư mục camera-store; chỉ val, không chấm test):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/05c_rgcn_train.py --lr 0.01 --seed 1 --run-dir results/n5/<nhãn>/<tên>
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import RGCNConv
from torch_geometric.utils import dropout_edge

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402
import train_05 as T   # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

N_UNSURE_EXPECTED = 134          # số ống "không chắc" (QĐ 3-4), mỗi ống 1 cạnh has_spec → mount


def load_homogeneous(train, log):
    """kg_hetero.pt -> (edge_index [2, E], edge_type [E], tên quan hệ, số nút, offset từng loại nút).
    Bỏ cạnh has_spec → mount / rev_has_spec có ngam_khong_chac = 1 (QĐ 5-4). Kiểm cạnh user–item = train.txt."""
    data = torch.load(str(C.KG_PT), weights_only=False)
    offs, n = {}, 0
    for nt in data.node_types:
        offs[nt] = n
        n += data[nt].num_nodes
    assert data["user"].num_nodes == C.N_USERS and data["item"].num_nodes == C.N_ITEMS
    srcs, dsts, rels, names = [], [], [], []
    n_drop = {}
    for r, et in enumerate(data.edge_types):
        s, rel, d = et
        st = data[et]
        ei = st.edge_index
        keep = torch.ones(ei.size(1), dtype=torch.bool)
        if "ngam_khong_chac" in st:
            keep = st.ngam_khong_chac.view(-1) == 0
            n_drop[f"{s}-{rel}-{d}"] = int((~keep).sum())
        if et == ("user", "interacted_with", "item"):
            u, i = T.train_pairs(train)
            a = np.sort(u * C.N_ITEMS + i)
            b = np.sort(ei[0].numpy().astype(np.int64) * C.N_ITEMS + ei[1].numpy())
            assert np.array_equal(a, b), "cạnh interacted_with của kg_hetero.pt khác train.txt"
        srcs.append(ei[0, keep] + offs[s])
        dsts.append(ei[1, keep] + offs[d])
        rels.append(torch.full((int(keep.sum()),), r, dtype=torch.long))
        names.append(f"{s}-{rel}-{d}")
    assert n_drop == {"item-has_spec-mount": N_UNSURE_EXPECTED, "mount-rev_has_spec-item": N_UNSURE_EXPECTED}, n_drop
    ei = torch.stack([torch.cat(srcs), torch.cat(dsts)])
    et = torch.cat(rels)
    log(f"Đồ thị đồng nhất: {n:,} nút, {len(names)} quan hệ, {ei.size(1):,} cạnh; bỏ cạnh ngam_khong_chac: {n_drop}; "
        f"cạnh interacted_with trùng train.txt: có")
    return ei, et, names, n, offs


class RGCN(nn.Module):
    def __init__(self, n_nodes, dim, n_rel, num_bases, ei, et, off_u, off_i, edge_drop, l2_dec):
        super().__init__()
        self.ei, self.et = ei, et
        self.off_u, self.off_i = off_u, off_i
        self.edge_drop, self.l2_dec = edge_drop, l2_dec
        self.x = nn.Parameter(torch.empty(n_nodes, dim))
        nn.init.xavier_uniform_(self.x)
        self.convs = nn.ModuleList([RGCNConv(dim, dim, n_rel, num_bases=num_bases, aggr="mean", root_weight=True)
                                    for _ in range(2)])
        self.r = nn.Parameter(torch.empty(1, dim))
        nn.init.xavier_uniform_(self.r)

    def encode(self):
        ei, et = self.ei, self.et
        if self.training and self.edge_drop > 0:
            ei, keep = dropout_edge(ei, p=self.edge_drop, training=True)
            et = et[keep]
        h = F.relu(self.convs[0](self.x, ei, et))
        h = self.convs[1](h, ei, et)                       # lớp cuối: không ReLU, không dropout
        return h[self.off_u:self.off_u + C.N_USERS], h[self.off_i:self.off_i + C.N_ITEMS]

    def loss(self, u, i, j):
        hu, hi = self.encode()
        eu = hu[u] * self.r
        bpr = F.softplus(-((eu * hi[i]).sum(1) - (eu * hi[j]).sum(1))).mean()
        return bpr + self.l2_dec * self.r.pow(2).sum()

    @torch.no_grad()
    def score_fn(self):
        hu, hi = self.encode()
        hur = hu * self.r
        return lambda uids: hur[uids] @ hi.T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lr", type=float, required=True, help="dò {0.01, 0.001}")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--max-epoch", type=int, default=100)
    ap.add_argument("--eval-every", type=int, default=5)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--stop-after", type=int, default=None, help="(kiểm thử) dừng sau N epoch như bị ngắt")
    a = ap.parse_args()
    cfg = {"dim": 64, "n_layers": 2, "num_bases": 2, "aggr": "mean", "root_weight": True, "edge_dropout": 0.4,
           "decoder": "DistMult", "l2_decoder": 0.01, "loss": "BPR", "lr": a.lr, "batch": 2048,
           "drop_ngam_khong_chac": True, "init": "xavier_uniform", "seed": a.seed, "max_epoch": a.max_epoch,
           "eval_every": a.eval_every, "patience": a.patience, "select_metric": "val ndcg@20 full ranking"}
    if a.stop_after:
        cfg["_stop_after"] = a.stop_after

    def build(train, log):
        ei, et, names, n, offs = load_homogeneous(train, log)
        m = RGCN(n, cfg["dim"], len(names), cfg["num_bases"], ei.to(E.DEVICE), et.to(E.DEVICE), offs["user"],
                 offs["item"], cfg["edge_dropout"], cfg["l2_decoder"]).to(E.DEVICE)
        log(f"R-GCN: {sum(p.numel() for p in m.parameters()):,} tham số")
        return m, m.parameters()

    T.run("R-GCN (RGCNConv)", cfg, build, a.run_dir, extra_argv=sys.argv)


if __name__ == "__main__":
    main()
