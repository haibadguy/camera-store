"""Đo thử bộ nhớ GPU / thời gian cho kế hoạch nội dung 5 (docs/reviews/n5_eval_plan.md mục 9).

KHÔNG huấn luyện: trọng số khởi tạo ngẫu nhiên, chỉ chạy forward + backward vài bước (không optimizer.step),
không chấm val / test. Số đo chỉ để ước tính thời gian một epoch và đỉnh bộ nhớ.

  1. LightGCN 3 lớp, d = 64, lan truyền lại mỗi batch (như 05b), batch 2048 và 16384;
  2. R-GCN thật (RGCNConv của PyG, 2 lớp, d = 64) trên đồ thị nội dung 4 chuyển sang đồng nhất:
     (a) 18 quan hệ như kg_hetero.pt; (b) tách quan hệ theo cờ cạnh (has_spec→mount theo src_phu_kien / phia /
     ngam_khong_chac, compatible_with theo crop_unknown, cả chiều rev_); thử không phân rã và num_bases = 4;
  3. Xếp hạng toàn bộ: điểm 67.661 × 27.940 theo lô trên GPU, lấy hạng của item test (embedding ngẫu nhiên).

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content5/probe_gpu.py <đường dẫn log mới>
"""
import sys
import time
from pathlib import Path

import numpy as np
import psutil
import torch
import torch.nn.functional as F
from torch_geometric.nn import RGCNConv

sys.path.insert(0, "ai/pipeline")
sys.stdout.reconfigure(encoding="utf-8")
import common_05 as C  # noqa: E402

DEV = torch.device("cuda")
D = 64
N_STEPS = 5
log_lines: list[str] = []


def log(msg: str = "") -> None:
    print(msg, flush=True)
    log_lines.append(msg)


def mib(x):
    return f"{x / 2**20:,.0f} MiB"


def rss():
    return psutil.Process().memory_info().rss


def timed_steps(step_fn):
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    step_fn()  # bước khởi động, không tính giờ
    torch.cuda.synchronize()
    t = time.perf_counter()
    for _ in range(N_STEPS):
        step_fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t) / N_STEPS, torch.cuda.max_memory_allocated()


def bpr(u, p, n):
    return -F.logsigmoid((u * p).sum(1) - (u * n).sum(1)).mean()


def probe_lightgcn(train, n_pairs, g):
    rows, cols = [], []
    for u, its in train.items():
        for i in its:
            rows += [u, C.N_USERS + i]
            cols += [C.N_USERS + i, u]
    N = C.N_USERS + C.N_ITEMS
    idx = torch.tensor([rows, cols])
    deg = torch.bincount(idx[0], minlength=N).float()
    dis = deg.pow(-0.5)
    dis[torch.isinf(dis)] = 0
    A = torch.sparse_coo_tensor(idx, dis[idx[0]] * dis[idx[1]], (N, N)).coalesce().to(DEV)
    E0 = torch.nn.Parameter(torch.randn(N, D, device=DEV) * 0.01)

    for bs in (2048, 16384):
        def step():
            E, layers = E0, [E0]
            for _ in range(3):
                E = torch.sparse.mm(A, E)
                layers.append(E)
            Ef = torch.stack(layers).mean(0)
            u = torch.randint(0, C.N_USERS, (bs,), device=DEV, generator=g)
            p = torch.randint(0, C.N_ITEMS, (bs,), device=DEV, generator=g) + C.N_USERS
            n = torch.randint(0, C.N_ITEMS, (bs,), device=DEV, generator=g) + C.N_USERS
            E0.grad = None
            bpr(Ef[u], Ef[p], Ef[n]).backward()
        sec, peak = timed_steps(step)
        nb = -(-n_pairs // bs)
        log(f"LightGCN batch {bs:>6}: {sec * 1000:,.0f} ms/bước × {nb} bước = {sec * nb:,.1f} s/epoch "
            f"(chưa tính lấy mẫu âm) | đỉnh GPU {mib(peak)}")
    del A, E0
    torch.cuda.empty_cache()


def homogeneous(split_flags: bool):
    data = torch.load(str(C.KG_PT), weights_only=False)
    offs, n = {}, 0
    for nt in data.node_types:
        offs[nt] = n
        n += data[nt].num_nodes
    srcs, dsts, rels, names = [], [], [], []
    for et in data.edge_types:
        s, r, d = et
        st = data[et]
        ei = st.edge_index
        if split_flags and "ngam_khong_chac" in st:
            key = st.src_phu_kien * 100 + st.phia * 10 + st.ngam_khong_chac
        elif split_flags and "crop_unknown" in st:
            key = st.crop_unknown.long()
        else:
            key = torch.zeros(ei.size(1), dtype=torch.long)
        for k in key.unique().tolist():
            m = key == k
            srcs.append(ei[0, m] + offs[s])
            dsts.append(ei[1, m] + offs[d])
            rels.append(torch.full((int(m.sum()),), len(names)))
            names.append(f"{s}-{r}-{d}#{k}")
    return (torch.stack([torch.cat(srcs), torch.cat(dsts)]), torch.cat(rels), names, n, offs)


def probe_rgcn(g):
    for split_flags in (False, True):
        ei, et, names, n_nodes, offs = homogeneous(split_flags)
        R = len(names)
        log(f"\nR-GCN, đồ thị đồng nhất: {n_nodes:,} nút, {ei.size(1):,} cạnh, {R} quan hệ "
            f"({'tách theo cờ cạnh' if split_flags else 'như kg_hetero.pt'})")
        ei, et = ei.to(DEV), et.to(DEV)
        for nb in (None, 4):
            torch.manual_seed(0)
            x = torch.nn.Parameter(torch.randn(n_nodes, D, device=DEV) * 0.01)
            convs = torch.nn.ModuleList([RGCNConv(D, D, R, num_bases=nb) for _ in range(2)]).to(DEV)
            n_par = x.numel() + sum(p.numel() for p in convs.parameters())
            r_vec = torch.nn.Parameter(torch.ones(D, device=DEV))  # DistMult cho interacted_with

            def enc():
                h = x
                for i, c in enumerate(convs):
                    h = c(h, ei, et)
                    if i < len(convs) - 1:
                        h = F.relu(h)
                return h

            for bs in (2048, 16384):
                def step():
                    h = enc()
                    u = torch.randint(0, C.N_USERS, (bs,), device=DEV, generator=g) + offs["user"]
                    p = torch.randint(0, C.N_ITEMS, (bs,), device=DEV, generator=g) + offs["item"]
                    q = torch.randint(0, C.N_ITEMS, (bs,), device=DEV, generator=g) + offs["item"]
                    x.grad = None
                    for c in convs:
                        c.zero_grad()
                    bpr(h[u] * r_vec, h[p], h[q]).backward()
                sec, peak = timed_steps(step)
                nbt = -(-460193 // bs)
                log(f"  num_bases {str(nb):>4} | tham số {n_par:,} | batch {bs:>6}: {sec * 1000:,.0f} ms/bước × {nbt} "
                    f"= {sec * nbt:,.1f} s/epoch | đỉnh GPU {mib(peak)}")
            with torch.no_grad():
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats()
                t = time.perf_counter()
                enc()
                torch.cuda.synchronize()
                log(f"  num_bases {str(nb):>4} | một lần mã hóa (eval, no_grad): {(time.perf_counter() - t) * 1000:,.0f} ms"
                    f" | đỉnh GPU {mib(torch.cuda.max_memory_allocated())}")
            del x, convs
            torch.cuda.empty_cache()


def probe_full_rank(train, test):
    U = torch.randn(C.N_USERS, D, device=DEV)
    V = torch.randn(C.N_ITEMS, D, device=DEV)
    # mặt nạ train dạng CSR trên GPU: (hàng, cột)
    r = torch.tensor([u for u, its in train.items() for _ in its], device=DEV)
    c = torch.tensor([i for its in train.values() for i in its], device=DEV)
    pos = torch.tensor([test[u] for u in range(C.N_USERS)], device=DEV)
    for bs in (1024, 4096):
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        t = time.perf_counter()
        ranks = []
        for s in range(0, C.N_USERS, bs):
            e = min(s + bs, C.N_USERS)
            S = U[s:e] @ V.T
            m = (r >= s) & (r < e)
            S[r[m] - s, c[m]] = -float("inf")
            sp = S[torch.arange(e - s, device=DEV), pos[s:e]]
            ranks.append(1 + (S > sp[:, None]).sum(1))
            S.topk(20, dim=1)
        torch.cuda.synchronize()
        rk = torch.cat(ranks)
        log(f"xếp hạng toàn bộ, lô {bs}: {time.perf_counter() - t:,.2f} s cho {C.N_USERS:,} người dùng | "
            f"đỉnh GPU {mib(torch.cuda.max_memory_allocated())} | hạng trung vị (ngẫu nhiên) {int(rk.median())}")


def main(out_log: Path) -> None:
    assert not out_log.exists(), f"log đã có, không ghi đè: {out_log}"
    log(f"GPU {torch.cuda.get_device_name(0)} | torch {torch.__version__} | RAM trống {mib(psutil.virtual_memory().available)}")
    log("Trọng số ngẫu nhiên, không optimizer.step, không chấm val / test.\n")
    g = torch.Generator(device=DEV).manual_seed(0)
    train = C.load_train()
    test = C.load_pos("test")
    n_pairs = sum(len(v) for v in train.values())
    probe_lightgcn(train, n_pairs, g)
    probe_rgcn(g)
    log("")
    probe_full_rank(train, test)
    log(f"\nRSS đỉnh tiến trình (cuối chương trình) ≈ {mib(rss())}")
    out_log.parent.mkdir(parents=True, exist_ok=True)
    out_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"-> {out_log}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
