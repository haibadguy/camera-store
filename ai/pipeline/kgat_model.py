"""
kgat_model.py -- Baseline KGAT (Wang et al., KDD 2019) cho nội dung 7 (docs/cakg_design.md khối 9; kế hoạch đăng ký
trước docs/reviews/cakg_eval_plan.md mục 4.1). Viết 14/10/2026. Script huấn luyện: 07_kgat_train.py.
Kiểm thử dựng tay: ai/survey/cakg/test_kgat.py.

Ví dụ (thiết kế khối 9, log run_vidu_tinh_tay_20261014_lan2.log): nút h (ống) có 2 hàng xóm t1 = (1; 0), t2 = (0; 1)
cùng quan hệ r; e_h = (0,5; 0,5), e_r = (0,1; 0), W_r = I: tanh(W_r e_h + e_r) = (0,53705; 0,46212);
π thô = (W_r e_t)ᵀ tanh(...) = 0,53705 và 0,46212; softmax trên mọi bộ ba có đầu h -> 0,51872 và 0,48128;
tin gộp e_N(h) = 0,51872·t1 + 0,48128·t2.

Công thức theo bài (§3.1–3.4) và chi tiết theo code tác giả (xiangwang1223/knowledge_graph_attention_network, master:
Model/KGAT.py, utility/loader_kgat.py, utility/load_data.py, Main.py, parser.py; đọc lại 14/10/2026):
  (27) TransR: g(h,r,t) = ‖W_r e_h + e_r − W_r e_t‖²; L_KG = mean softplus(g(h,r,t) − g(h,r,t'))
       + λ · (l2(W_r e_h) + l2(e_r) + l2(W_r e_t) + l2(W_r e_t')) / 2048        (l2(x) = Σx²/2 như tf.nn.l2_loss)
  (28) π(h,r,t) = (W_r e_t)ᵀ tanh(W_r e_h + e_r), softmax trên MỌI bộ ba có đầu h (mọi quan hệ, kể cả interacted_with);
       e_N(h) = Σ π(h,r,t) e_t
  (29) Bi-Interaction: e⁽ˡ⁾ = LeakyReLU(W_1(e + e_N) + b_1) + LeakyReLU(W_2(e ⊙ e_N) + b_2), độ dốc 0,2; message
       dropout 0,1 sau mỗi lớp (khi huấn luyện); lớp sau nhận e⁽ˡ⁾ chưa chuẩn hóa
  (30) e* = e⁽⁰⁾ ‖ norm(e⁽¹⁾) ‖ norm(e⁽²⁾) ‖ norm(e⁽³⁾) ∈ ℝ^{64+64+32+16 = 176} (lớp 0 không chuẩn hóa, như code);
       ŷ = e*_uᵀ e*_i; L_CF = mean softplus(ŷ_uj − ŷ_ui) + λ (l2(e*_u) + l2(e*_i) + l2(e*_j)) / 1024
  Tối ưu xen kẽ mỗi epoch: pha CF (Adam 1) -> pha KG (Adam 2, cùng lr, len(cạnh) // 2048 + 1 = 546 batch) -> tính lại π.

Sai khác so với code tác giả (ghi trong báo cáo; Nam chốt HỎI 9 và kế hoạch mục 4.1, 13 điểm 4):
  1. π tính lại MỘT lần / epoch, không gradient (như code), nhưng π mới ĐƯỢC DÙNG cho lan truyền ở epoch sau (code tác
     giả đổi thuộc tính Python self.A_in, không dựng lại SparseTensor hằng nên lan truyền luôn dùng Laplacian ban đầu
     D⁻¹A). Epoch 1 dùng π tính từ embedding khởi tạo.
  2. Pha CF dùng vòng huấn luyện chung train_05.run (mỗi epoch duyệt mọi cặp train một lần, 1 âm mẫu đều / cặp, như
     LightGCN); code tác giả lấy người dùng đều rồi một item dương ngẫu nhiên, n_train // 1024 + 1 batch.
  3. Pha KG: batch 2048 = args.batch_size_kg (code: bộ lấy mẫu lại dùng batch_size_kg tính từ dữ liệu
     n_triples // (n_train // batch_size), số batch dùng args.batch_size_kg); đầu h lấy đều trên các đầu khác nhau
     (không hoàn lại trong một batch), một (r, t) dương đều trong các bộ ba của h, đuôi âm đều trên mọi nút, bỏ khi
     (t', r) là bộ ba thật của h — như code.
  4. Khởi tạo Xavier từng ma trận (W_r theo từng quan hệ, bias như ma trận [1, d]); code dùng xavier_initializer của
     tf.contrib (3 chiều nhân fan với số quan hệ). Không pretrain BPR-MF (README khuyên), để so công bằng.
  5. Dừng sớm theo NDCG@20 val mỗi 10 epoch, 5 lần không tăng, tối đa 300 epoch (QĐ 5-5); code: recall@20, 1000 epoch.
  6. Bỏ 134 cạnh ngam_khong_chac (mỗi chiều) như R-GCN (QĐ 5-4); node dropout không dùng (như code).
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.utils import softmax as pyg_softmax


def l2_loss(x):
    """tf.nn.l2_loss: Σ x² / 2."""
    return x.pow(2).sum() / 2


class KGAT(nn.Module):
    def __init__(self, n_nodes, n_rel, ei, et, off_u, n_users, off_i, n_items, dims=(64, 64, 32, 16),
                 mess_dropout=0.1, l2_cf=1e-5, l2_kg=1e-5, cf_batch=1024, kg_batch=2048, lr=1e-3, slope=0.2):
        super().__init__()
        d = dims[0]
        self.n, self.R = n_nodes, n_rel
        self.off_u, self.n_users, self.off_i, self.n_items = off_u, n_users, off_i, n_items
        self.mess_dropout, self.l2_cf, self.l2_kg = mess_dropout, l2_cf, l2_kg
        self.cf_batch, self.kg_batch, self.slope = cf_batch, kg_batch, slope
        self.E = nn.Parameter(torch.empty(n_nodes, d))
        self.Er = nn.Parameter(torch.empty(n_rel, d))
        self.Wr = nn.Parameter(torch.empty(n_rel, d, d))
        nn.init.xavier_uniform_(self.E)
        nn.init.xavier_uniform_(self.Er)
        for r in range(n_rel):
            nn.init.xavier_uniform_(self.Wr.data[r])
        self.W1 = nn.ModuleList([nn.Linear(dims[k], dims[k + 1]) for k in range(len(dims) - 1)])
        self.W2 = nn.ModuleList([nn.Linear(dims[k], dims[k + 1]) for k in range(len(dims) - 1)])
        for lin in [*self.W1, *self.W2]:
            nn.init.xavier_uniform_(lin.weight)
            nn.init.xavier_uniform_(lin.bias.data.view(1, -1))
        # bộ ba (h, r, t): h = nguồn của cạnh, t = đích; tin đi t -> h (e_N(h) gộp các đuôi t)
        self.head, self.tail, self.et = ei[0].contiguous(), ei[1].contiguous(), et.contiguous()
        self.register_buffer("pi", torch.zeros(ei.size(1), device=ei.device))
        self._A = None
        # pha KG: bộ ba theo đầu (CSR), khóa (h, r, t) đã sắp để loại âm mẫu là bộ ba thật
        h_np, r_np, t_np = (x.cpu().numpy().astype(np.int64) for x in (ei[0], et, ei[1]))
        order = np.argsort(h_np, kind="stable")
        self._kg_h, self._kg_r, self._kg_t = h_np[order], r_np[order], t_np[order]
        self._heads, start = np.unique(self._kg_h, return_index=True)
        self._ptr = np.append(start, len(self._kg_h))
        self._keys = np.unique((h_np * n_rel + r_np) * n_nodes + t_np)
        self.n_kg_batches = len(h_np) // kg_batch + 1                # như Main.py: len(all_h_list) // batch_size_kg + 1
        self.to(ei.device)                                         # tham số cùng thiết bị với đồ thị trước khi tính π
        self.kg_opt = torch.optim.Adam(self.parameters(), lr=lr)     # Adam thứ hai (opt2 của code), cùng lr
        with torch.no_grad():
            self.pi.copy_(self.attention())                         # epoch 1: π từ embedding khởi tạo

    # -- attention và lan truyền ---------------------------------------------
    @torch.no_grad()
    def attention(self, E=None):
        """(28): π(h,r,t) = (W_r e_t)ᵀ tanh(W_r e_h + e_r), softmax theo đầu h trên mọi bộ ba của h."""
        E = self.E if E is None else E
        score = torch.empty(self.head.numel(), device=E.device)
        for r in range(self.R):
            ix = torch.nonzero(self.et == r).view(-1)
            if len(ix) == 0:
                continue
            wt = E[self.tail[ix]] @ self.Wr[r]                    # vector hàng nhân W_r, như tf.matmul(e, trans_W[r])
            wh = E[self.head[ix]] @ self.Wr[r]
            score[ix] = (wt * torch.tanh(wh + self.Er[r])).sum(1)
        return pyg_softmax(score, self.head, num_nodes=self.n)

    def adjacency(self):
        if self._A is None:
            self._A = torch.sparse_coo_tensor(torch.stack([self.head, self.tail]), self.pi,
                                              (self.n, self.n)).coalesce().to_sparse_csr()
        return self._A

    def set_attention(self, pi):
        self.pi.copy_(pi)
        self._A = None

    def _load_from_state_dict(self, *args, **kwargs):
        super()._load_from_state_dict(*args, **kwargs)
        self._A = None                                            # π nạp từ checkpoint -> dựng lại ma trận

    def propagate(self):
        """(29), (30): e* mọi nút [n, 176]."""
        A = self.adjacency()
        ego, out = self.E, [self.E]
        for w1, w2 in zip(self.W1, self.W2):
            side = A @ ego                                        # e_N(h) = Σ_t π(h,r,t) e_t
            ego = F.leaky_relu(w1(ego + side), self.slope) + F.leaky_relu(w2(ego * side), self.slope)
            ego = F.dropout(ego, self.mess_dropout, self.training)
            out.append(F.normalize(ego, dim=1))
        return torch.cat(out, 1)

    # -- pha CF (gọi bởi train_05.run) ---------------------------------------
    def loss(self, u, i, j):
        Z = self.propagate()
        zu, zi, zj = Z[self.off_u + u], Z[self.off_i + i], Z[self.off_i + j]
        bpr = F.softplus(-((zu * zi).sum(1) - (zu * zj).sum(1))).mean()
        return bpr + self.l2_cf * (l2_loss(zu) + l2_loss(zi) + l2_loss(zj)) / self.cf_batch

    @torch.no_grad()
    def score_fn(self):
        Z = self.propagate()
        zu, ziT = Z[self.off_u:self.off_u + self.n_users], Z[self.off_i:self.off_i + self.n_items].T
        return lambda uids: zu[uids] @ ziT

    # -- pha KG + cập nhật attention (gọi sau các bước CF của mỗi epoch) ------
    def sample_kg(self, rng):
        """Một batch KG như code tác giả: đầu đều trên các đầu khác nhau, 1 (r, t) dương / đầu, đuôi âm đều trên mọi nút
        với (h, r, t') không phải bộ ba thật."""
        B = self.kg_batch
        hk = rng.choice(len(self._heads), B, replace=B > len(self._heads))
        h = self._heads[hk]
        lo, hi = self._ptr[hk], self._ptr[hk + 1]
        p = lo + (rng.random(B) * (hi - lo)).astype(np.int64)
        r, t = self._kg_r[p], self._kg_t[p]
        tn = rng.integers(0, self.n, size=B)
        bad = np.arange(B)
        while len(bad):
            k = (h[bad] * self.R + r[bad]) * self.n + tn[bad]
            pos = np.searchsorted(self._keys, k)
            hit = (pos < len(self._keys)) & (self._keys[np.minimum(pos, len(self._keys) - 1)] == k)
            bad = bad[hit]
            tn[bad] = rng.integers(0, self.n, size=len(bad))
        return h, r, t, tn

    def kg_loss(self, h, r, t, tn):
        W = self.Wr[r]
        eh = torch.bmm(self.E[h].unsqueeze(1), W).squeeze(1)
        et_ = torch.bmm(self.E[t].unsqueeze(1), W).squeeze(1)
        en = torch.bmm(self.E[tn].unsqueeze(1), W).squeeze(1)
        er = self.Er[r]
        pos = (eh + er - et_).pow(2).sum(1)
        neg = (eh + er - en).pow(2).sum(1)
        base = F.softplus(-(neg - pos)).mean()
        return base + self.l2_kg * (l2_loss(eh) + l2_loss(er) + l2_loss(et_) + l2_loss(en)) / self.kg_batch, base

    def after_epoch(self, np_rng, log=None):
        import time
        dev = self.E.device
        t0 = time.time()
        tot = torch.zeros((), device=dev)
        for _ in range(self.n_kg_batches):
            h, r, t, tn = (torch.as_tensor(x, device=dev) for x in self.sample_kg(np_rng))
            self.kg_opt.zero_grad(set_to_none=True)
            loss, _ = self.kg_loss(h, r, t, tn)
            loss.backward()
            self.kg_opt.step()
            tot += loss.detach()
        self.kg_opt.zero_grad(set_to_none=True)
        kg = float(tot) / self.n_kg_batches
        t1 = time.time()
        old = self.pi.clone()
        self.set_attention(self.attention())                      # dùng cho lan truyền ở epoch sau
        if dev.type == "cuda":
            torch.cuda.synchronize()
        return {"kg_loss": kg, "sec_kg": round(t1 - t0, 2), "sec_att": round(time.time() - t1, 2),
                "pi_max_abs_change": float((self.pi - old).abs().max())}

    def aux_state_dict(self):
        return {"kg_opt": self.kg_opt.state_dict()}

    def load_aux_state_dict(self, d):
        self.kg_opt.load_state_dict(d["kg_opt"])
