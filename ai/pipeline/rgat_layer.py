"""
rgat_layer.py -- Lớp RGAT tự cài cho kênh phần cứng của CaKG-Rec (docs/cakg_design.md khối 2, công thức (3)–(6)).

Viết 14/10/2026, chép từ ai/survey/cakg/probe_cakg.py (RGATLayer, đã kiểm trùng RGATConv của PyG) và sửa theo HỎI 5
(Nam chốt 14/10): q^(r), k^(r) RIÊNG từng quan hệ như bài (Busbridge et al. 2019, Eq. 3), không dùng chung như PyG.

Ví dụ (thiết kế khối 2, log run_vidu_tinh_tay_20261014_lan2.log): thân b nhận tin từ ống l1, l2 qua quan hệ
rev_compatible_with và từ nút ngàm qua rev_has_spec_mount; d = 2, W^(r) = I, W_0 = I, q = (1; 0), k = (0; 1), bias 0;
h_b = (0,5; 0,5), h_l1 = (1; 0), h_l2 = (0; 1), h_ngàm = (1; 1):
  logit(b←l1) = LeakyReLU(q·h_b + k·h_l1) = 0,5;  logit(b←l2) = 1,5  ->  α = softmax(0,5; 1,5) = (0,2689; 0,7311)
  (WIRGAT: chuẩn hóa TRONG từng quan hệ; quan hệ ngàm chỉ có 1 hàng xóm nên α = 1)
  h_b' = ReLU( 0,2689·h_l1 + 0,7311·h_l2  +  1·h_ngàm  +  W_0 h_b ) = ReLU(1,7689; 2,2311).

Công thức (một đầu, D = 1), nút đích i, quan hệ r, hàng xóm N_i^r (cạnh j -> i loại r):
  (3) g_v^(r) = W^(r) h_v                                   (tính cho MỌI nút, mọi quan hệ một lần: [R, N, F'])
  (4) a_ij^(r) = LeakyReLU( q^(r)ᵀ g_i^(r) + k^(r)ᵀ g_j^(r) ), độ dốc 0,2
  (5) α_ij^(r) = softmax trên j ∈ N_i^r                      (within-relation, "WIRGAT")
  (6) out_i = Σ_r Σ_j α_ij^(r) g_j^(r) + bias                (phần tự giữ W_0 h_i và σ cộng ở HwEncoder)

Vì sao tự cài: RGATConv của PyG 2.8.0.post1 nhân W^(r) riêng cho TỪNG CẠNH ([số cạnh, 64, 64]); một lớp trên H_lõi
đỉnh 8.985 MiB > 6 GB (log run_probe_cakg_20261014_lan1.log). Ở đây g^(r) = W^(r) h tính cho mọi nút trước, rồi chỉ lấy
điểm q·g, k·g theo cạnh. Với mọi q^(r), k^(r) bằng nhau thì công thức trùng RGATConv (within-relation,
additive-self-attention, heads = 1, dim = 1, mod = None); kiểm ở ai/survey/cakg/test_cakg.py.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.utils import softmax as pyg_softmax


class RGATLayer(nn.Module):
    """WIRGAT, logit cộng, một đầu. weight [R, F, F'], q / k [R, F'] (riêng từng quan hệ), bias [F'].
    forward(h [N, F], edge_index [2, E] (hàng 0 = nguồn j, hàng 1 = đích i), edge_type [E]) -> (out [N, F'], α [E])."""

    def __init__(self, fin, fout, n_rel, negative_slope=0.2):
        super().__init__()
        self.R, self.slope = n_rel, negative_slope
        self.weight = nn.Parameter(torch.empty(n_rel, fin, fout))
        self.q = nn.Parameter(torch.empty(n_rel, fout))
        self.k = nn.Parameter(torch.empty(n_rel, fout))
        self.bias = nn.Parameter(torch.zeros(fout))
        for r in range(n_rel):                       # Xavier từng ma trận W^(r) (HỎI 10: khởi tạo Xavier)
            nn.init.xavier_uniform_(self.weight.data[r])
        nn.init.xavier_uniform_(self.q)
        nn.init.xavier_uniform_(self.k)

    def forward(self, h, edge_index, edge_type):
        src, dst = edge_index[0], edge_index[1]
        n = h.size(0)
        G = torch.einsum("nf,rfo->rno", h, self.weight)          # (3) g_v^(r) cho mọi nút, mọi quan hệ
        sq = (G * self.q[:, None, :]).sum(-1)                    # q^(r)ᵀ g_v^(r)  [R, N]
        sk = (G * self.k[:, None, :]).sum(-1)                    # k^(r)ᵀ g_v^(r)  [R, N]
        logit = F.leaky_relu(sq[edge_type, dst] + sk[edge_type, src], self.slope)     # (4)
        alpha = pyg_softmax(logit, dst * self.R + edge_type, num_nodes=n * self.R)    # (5) theo (đích, quan hệ)
        out = torch.zeros(n, G.size(-1), device=h.device, dtype=h.dtype)
        out = out.index_add(0, dst, alpha[:, None] * G[edge_type, src])                # (6)
        return out + self.bias, alpha


class HwEncoder(nn.Module):
    """Kênh phần cứng: h_v^(0) = embedding học được của nút v (Xavier); 2 lớp RGATLayer, mỗi lớp cộng phần tự giữ
    W_0^(l) h_v^(l) (khác bài RGAT, lấy theo R-GCN Eq. 2; thiết kế khối 2 (d)); ReLU sau lớp 1, không có sau lớp 2.
    forward(ei, et) -> (h [N, d], α lớp 2 [E])."""

    def __init__(self, n_nodes, n_rel, dim=64, n_layers=2):
        super().__init__()
        self.x = nn.Parameter(torch.empty(n_nodes, dim))
        nn.init.xavier_uniform_(self.x)
        self.convs = nn.ModuleList([RGATLayer(dim, dim, n_rel) for _ in range(n_layers)])
        self.roots = nn.ModuleList([nn.Linear(dim, dim, bias=False) for _ in range(n_layers)])
        for w in self.roots:
            nn.init.xavier_uniform_(w.weight)

    def forward(self, ei, et, x=None):
        h = self.x if x is None else x
        alpha = None
        for k, (conv, w0) in enumerate(zip(self.convs, self.roots)):
            out, alpha = conv(h, ei, et)
            h = out + w0(h)
            if k < len(self.convs) - 1:
                h = F.relu(h)
        return h, alpha
