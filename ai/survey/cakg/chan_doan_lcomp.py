"""Chẩn đoán sau đợt dò λ1 (val), CHỈ ĐỌC và TÍNH: không sửa mô hình, không huấn luyện mô hình, không chấm test.
Viết 15/10/2026. Log ghi ra file TÊN MỚI trong ai/data/survey/cakg/.

(a) Vì sao λ1 ∈ {0,01; 0,1; 1} gần như không đổi NDCG@20 val:
    a1. đường l_comp, BPR, NDCG@20 val theo epoch (result.json của 3 lần chạy);
    a2. vùng mà kênh phần cứng tham gia điểm: người val có h_u, item val có h, cặp có cổng mở;
    a3. so 3 lần chạy theo từng người (mảng val_rank_full.npy đã lưu, kiểm sha256): NDCG@20 tách theo
        "cổng mở ở item val" / "không";
    a4. trên checkpoint tốt nhất của mỗi lần: β_h của người / sản phẩm có h, phần phần cứng trong điểm top-10.
(b) L_comp đứng ở ~1,0597: cận dưới hay lỗi?
    b1. tính lại L_comp của 3 checkpoint bằng numpy độc lập (float64) -> so với số trong log huấn luyện;
    b2. cận dưới tầm thường của công thức (12): mỗi cặp dương ℓ ≥ log(1 + N_b e^{−2/τ}) (cos ∈ [−1, 1]);
        và (để so) cận log P_b nếu các dương khác cũng nằm ở mẫu số (kiểu SupCon) — công thức (12) KHÔNG có;
    b3. "sàn thực nghiệm": tối ưu TRỰC TIẾP vector tự do (không qua RGAT) cho riêng L_comp, d = 64 và 256, 3 seed;
    b4. tách đóng góp của L_comp cuối theo nhóm cặp để tìm nguồn của sàn;
    b5. ví dụ nhỏ: K ngàm, mỗi ngàm 1 thân + n ống, chỉ lắp được trong cùng ngàm; xếp K cụm thành đơn hình đều
        (cos giữa hai cụm = −1/(K−1)) -> ℓ = log(1 + (K−1) n e^{−(1 + 1/(K−1))/τ}); kiểm bằng tối ưu vector tự do.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/cakg/chan_doan_lcomp.py --label 20261015_lan1
"""
import argparse
import collections
import importlib
import json
import math
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header, sha256_file  # noqa: E402
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402

X08 = importlib.import_module("08_explain")
SW = "results/cakg/val_sweep_20261014"
RUNS = ["val_cakg_lam1-1e-02_s1", "val_cakg_lam1-1e-01_s1", "val_cakg_lam1-1e+00_s1"]
TAU = 0.2
DEV = E.DEVICE


def ndcg20(rank):
    return np.where(rank <= 20, 1.0 / np.log2(rank + 1.0), 0.0)


def lcomp_np(hb, hl, M, U, tau=TAU):
    hb = hb / np.linalg.norm(hb, axis=1, keepdims=True)
    hl = hl / np.linalg.norm(hl, axis=1, keepdims=True)
    S = hb @ hl.T / tau
    neg = ~M & ~U
    terms = []
    for b in range(M.shape[0]):
        if not M[b].any():
            continue
        sn = S[b, neg[b]]
        mx = sn.max()
        lse = mx + np.log(np.exp(sn - mx).sum())
        sp = S[b, M[b]]
        terms.append(np.logaddexp(sp, lse) - sp)
    return np.concatenate(terms)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--steps", type=int, default=4000)
    a = ap.parse_args()
    log = Log(os.path.join("ai/data/survey/cakg", f"run_chan_doan_lcomp_{a.label}.log"))
    header(log, __file__)

    # ── a1 ──
    log("\n(a1) Đường học (result.json):")
    res = {}
    for n in RUNS:
        r = json.load(open(f"{SW}/{n}/result.json", encoding="utf-8"))
        res[n] = r
        h = r["history"]
        pick = lambda key, eps: " ".join(f"{x['epoch']}:{x[key]:.4f}" for x in h if x["epoch"] in eps and key in x)  # noqa
        log(f"  {n}: NDCG@20 val tốt nhất {r['val']['full']['ndcg@20']:.5f} (epoch {r['best_epoch']}), "
            f"CVR@10 val trước mặt nạ {r['val']['cvr']['cvr@10']:.4f}")
        log(f"    l_comp  {pick('l_comp', {1, 2, 3, 4, 5, 10, 20, 50, 100, 200, 300})}")
        log(f"    bpr     {pick('bpr', {1, 10, 50, 100, 200, 300})}")
        log(f"    ndcg@20 {pick('val_ndcg@20', {10, 50, 100, 150, 200, 250, 290, 300})}")
        lc = [x["l_comp"] for x in h]
        first = next(x["epoch"] for x in h if x["l_comp"] - lc[-1] < 0.005)
        log(f"    l_comp cách giá trị cuối < 0,005 từ epoch {first}; cuối {lc[-1]:.5f}")

    # ── a2–a3 ──
    train = C.load_train()
    item_type = C.load_item_type()
    H = CK.build_h()
    _, has_hu, bodies_h = CK.user_body_matrix(train, item_type, H.item_loc, H.n_nodes)
    has_hu = has_hu.numpy()
    users = np.load(f"{SW}/{RUNS[0]}/val_users.npy")
    val = C.load_pos("val")
    pos = np.array([val[u] for u in users.tolist()])
    item_h = np.zeros(C.N_ITEMS, bool)
    item_h[list(H.item_loc)] = True
    gate = has_hu[users] & item_h[pos]
    log(f"\n(a2) Người val có h_u: {int(has_hu[users].sum()):,} / {len(users):,} ({has_hu[users].mean() * 100:.2f}%); "
        f"item val có h: {int(item_h[pos].sum()):,} ({item_h[pos].mean() * 100:.2f}%); cổng mở ở item val (cả hai có h): "
        f"{int(gate.sum()):,} người ({gate.mean() * 100:.2f}%)")
    log("(a3) NDCG@20 val theo từng người (val_rank_full.npy, sha256 kiểm với result.json):")
    ranks = {}
    for n in RUNS:
        fn = f"{SW}/{n}/val_rank_full.npy"
        assert sha256_file(fn) == res[n]["val"]["arrays_sha256"]["val_rank_full.npy"]
        assert np.array_equal(np.load(f"{SW}/{n}/val_users.npy"), users)
        ranks[n] = np.load(fn)
        nd = ndcg20(ranks[n])
        log(f"  {n}: toàn bộ {nd.mean():.5f} | cổng mở ({int(gate.sum()):,} người) {nd[gate].mean():.5f} | "
            f"còn lại {nd[~gate].mean():.5f} | phần đóng góp của nhóm cổng mở vào NDCG toàn bộ "
            f"{nd[gate].sum() / len(nd):.5f}")
    base = ndcg20(ranks[RUNS[1]])
    for n in (RUNS[0], RUNS[2]):
        d = ndcg20(ranks[n]) - base
        log(f"  {n} − λ1 = 0,1: hiệu NDCG@20 toàn bộ {d.mean():+.5f} = cổng mở {d[gate].sum() / len(d):+.5f} + còn lại "
            f"{d[~gate].sum() / len(d):+.5f}; người có hạng khác: {(ranks[n] != ranks[RUNS[1]]).mean() * 100:.1f}%")

    # ── a4, b1 ──
    M, U, bl, ll, bg, lg = CK.lcomp_tensors(H.item_loc)
    Mn, Un = M.numpy(), U.numpy()
    log("\n(a4) β_h và phần phần cứng (checkpoint tốt nhất, chế độ eval); (b1) L_comp tính lại bằng numpy float64:")
    hw_runs = {}
    for n in RUNS:
        m, cfg, sha = X08.load_cakg(f"{SW}/{n}", train, log=lambda s: None)
        c = m.components()
        hb = c["h"][bl.to(DEV)].double().cpu().numpy()
        hl = c["h"][ll.to(DEV)].double().cpu().numpy()
        hw_runs[n] = (hb, hl)
        t = lcomp_np(hb, hl, Mn, Un)
        with torch.no_grad():
            lt = float(CK.l_comp(c["h"], m.M, m.U, m.bl, m.ll, TAU))
        last = res[n]["history"][-1]["l_comp"]
        bu = c["betaU"][c["has_hu"], 1].cpu().numpy()
        bi = c["betaI"][c["has_hi"], 1].cpu().numpy()
        # phần phần cứng trong điểm của các cặp cổng mở trong top-10 val (trước mặt nạ)
        top = np.load(f"{SW}/{n}/val_top20_full.npy")[:, :10]
        uu = np.repeat(users, 10)
        ii = top.reshape(-1)
        hu_t = c["has_hu"].cpu().numpy()
        hi_t = c["has_hi"].cpu().numpy()
        g = hu_t[uu] & hi_t[ii]
        zU, zI = c["zU"].cpu(), c["zI"].cpu()
        uu_g, ii_g = torch.as_tensor(uu[g]), torch.as_tensor(ii[g])
        hwp = (zU[uu_g, 64:] * zI[ii_g, 64:]).sum(1).numpy()
        tot = (zU[uu_g] * zI[ii_g]).sum(1).numpy()
        log(f"  {n}: L_comp numpy {t.mean():.5f} (torch {lt:.5f}; log epoch 300, trung bình các bước {last:.5f}); "
            f"β_h người có h_u: TB {bu.mean():.3f} [p10 {np.percentile(bu, 10):.3f}, p90 {np.percentile(bu, 90):.3f}]; "
            f"β_h sản phẩm có h: TB {bi.mean():.3f}; cặp cổng mở trong top-10 val {int(g.sum()):,} / {len(g):,}; "
            f"phần phần cứng / điểm: trung vị {np.median(hwp / tot):.3f}")
        del m
        torch.cuda.empty_cache()

    # ── b2 ──
    neg = ~Mn & ~Un
    Pb, Nb = Mn.sum(1), neg.sum(1)
    w = Pb[Pb > 0]
    triv = (w * np.log1p(Nb[Pb > 0] * math.exp(-2 / TAU))).sum() / w.sum()
    sup = (w * np.log(w)).sum() / w.sum()
    log(f"\n(b2) Cận dưới tầm thường của (12) (dương cos = 1, mọi âm cos = −1, mỗi thân riêng rẽ): "
        f"TB trên cặp dương của log(1 + N_b e^(−2/τ)) = {triv:.5f}")
    log(f"     (để so) nếu các dương khác cũng ở mẫu số (SupCon), cận log P_b trung bình theo cặp dương = {sup:.5f} — "
        f"công thức (12) và code không có dương khác ở mẫu số (cakg_model.l_comp), nên cận này KHÔNG áp dụng")
    log(f"     thân có dương: {int((Pb > 0).sum())}; P_b trung vị {np.median(w):g}; N_b trung vị {np.median(Nb[Pb > 0]):g}")

    # ── b3 ──
    log(f"\n(b3) Sàn thực nghiệm: tối ưu trực tiếp vector tự do h_b (537), h_l (1.033) cho riêng L_comp (Adam lr 0,05, "
        f"{a.steps} bước), không qua RGAT:")
    Mt, Ut = M.to(DEV), U.to(DEV)
    idx_b = torch.arange(len(bg), device=DEV)
    idx_l = torch.arange(len(bg), len(bg) + len(lg), device=DEV)
    best = {}
    for d in (64, 256):
        for seed in (0, 1, 2):
            g_ = torch.Generator(device=DEV).manual_seed(seed)
            X = torch.randn(len(bg) + len(lg), d, device=DEV, generator=g_).requires_grad_(True)
            opt = torch.optim.Adam([X], lr=0.05)
            for s in range(a.steps):
                opt.zero_grad()
                loss = CK.l_comp(X, Mt, Ut, idx_b, idx_l, TAU)
                loss.backward()
                opt.step()
                if s == a.steps // 2:
                    mid = float(loss)
            with torch.no_grad():
                fin = float(CK.l_comp(X, Mt, Ut, idx_b, idx_l, TAU))
            best[(d, seed)] = (fin, X.detach())
            log(f"  d {d}, seed {seed}: L_comp sau {a.steps // 2} bước {mid:.5f}, sau {a.steps} bước {fin:.5f}")
    (dmin, smin), (vmin, Xbest) = min(best.items(), key=lambda kv: kv[1][0])
    log(f"  thấp nhất: {vmin:.5f} (d {dmin}, seed {smin}); CaKG-Rec λ1 = 1 đạt 1,0597 (log)")

    # ── b4 ──
    log("\n(b4) Nguồn của sàn: tách L_comp cuối (λ1 = 1) và vector tự do tốt nhất theo nhóm cặp dương")
    attrs = {int(r["iid"]): r for r in CK._rows("item_attributes.csv")}
    rho = {}
    for f_, key in (("kg_edges_compatible_with.csv", "compatible_with"), ("kg_edges_crops_sensor.csv", "crops_sensor")):
        for r in CK._rows(f_):
            rho[(int(r["body_iid"]), int(r["lens_iid"]))] = key + ("_crop_unknown" if r.get("crop_unknown") == "1" else "")
    rows_, cols = np.nonzero(Mn)
    for name, (hb, hl) in (("CaKG λ1 = 1", hw_runs[RUNS[2]]),
                           ("vector tự do", (Xbest[:len(bg)].double().cpu().numpy(),
                                              Xbest[len(bg):].double().cpu().numpy()))):
        t = lcomp_np(hb, hl, Mn, Un)                    # cùng thứ tự hàng-trước với np.nonzero
        grp = collections.defaultdict(list)
        for k, (r, c_) in enumerate(zip(rows_, cols)):
            b, l = bg[r], lg[c_]
            grp[f"ngàm thân {attrs[b]['mount']}"].append(t[k])
            grp[f"loại cặp {rho[(b, l)]}"].append(t[k])
        log(f"  [{name}] L_comp = {t.mean():.5f}; theo nhóm (số cặp, TB ℓ, phần đóng góp vào L_comp):")
        for k_ in sorted(grp, key=lambda k: -sum(grp[k]))[:12]:
            v = np.array(grp[k_])
            log(f"    {k_:42s} {len(v):6,}  {v.mean():.4f}  {v.sum() / len(t):.4f}")
        hbn = hb / np.linalg.norm(hb, axis=1, keepdims=True)
        hln = hl / np.linalg.norm(hl, axis=1, keepdims=True)
        S = hbn @ hln.T
        log(f"    cos(thân, ống) TB: cặp dương {S[Mn].mean():.3f}; cặp âm {S[neg].mean():.3f} (p1 {np.percentile(S[neg], 1):.3f}, "
            f"p99 {np.percentile(S[neg], 99):.3f})")
        # ví dụ: thân canon_efs có nhiều cặp dương nhất
        r_ex = max((r for r in range(len(bg)) if attrs[bg[r]]["mount"] == "canon_efs"), key=lambda r: Mn[r].sum())
        sp, sn = S[r_ex, Mn[r_ex]] / TAU, S[r_ex, neg[r_ex]] / TAU
        lse = np.log(np.exp(sn).sum())
        log(f"    ví dụ thân {bg[r_ex]} ({attrs[bg[r_ex]]['title'][:40]}, canon_efs): {Mn[r_ex].sum()} dương, "
            f"{neg[r_ex].sum()} âm; s/τ dương TB {sp.mean():.2f}; log Σ_âm e^(s/τ) = {lse:.2f}; "
            f"ℓ TB {np.mean(np.logaddexp(sp, lse) - sp):.4f}")
    # ── b5 ──
    log("\n(b5) Ví dụ nhỏ: K ngàm, mỗi ngàm 1 thân + n ống (M = 1 chỉ trong cùng ngàm), τ = 0,2")
    for K, n in ((2, 5), (3, 5), (5, 5), (10, 5), (23, 5), (23, 45)):
        N = (K - 1) * n
        f = math.log1p(N * math.exp(-(1 + 1 / (K - 1)) / TAU))
        Mt2 = torch.zeros(K, K * n, dtype=torch.bool, device=DEV)
        for k in range(K):
            Mt2[k, k * n:(k + 1) * n] = True
        X = torch.randn(K + K * n, 64, device=DEV, generator=torch.Generator(device=DEV).manual_seed(0)).requires_grad_(True)
        opt = torch.optim.Adam([X], lr=0.05)
        ib, il = torch.arange(K, device=DEV), torch.arange(K, K + K * n, device=DEV)
        for _ in range(3000):
            opt.zero_grad()
            CK.l_comp(X, Mt2, torch.zeros_like(Mt2), ib, il, TAU).backward()
            opt.step()
        with torch.no_grad():
            got = float(CK.l_comp(X, Mt2, torch.zeros_like(Mt2), ib, il, TAU))
            hb = F.normalize(X[:K], dim=1)
            cs = (hb @ hb.T)[~torch.eye(K, dtype=torch.bool, device=DEV)].mean()
        log(f"  K {K:>2}, n {n:>2} (N = {N:>4} âm / thân): công thức đơn hình {f:.5f}; tối ưu vector tự do {got:.5f}; "
            f"cos TB giữa các thân {float(cs):+.3f} (−1/(K−1) = {-1 / (K - 1):+.3f})")
    log.save()


if __name__ == "__main__":
    main()
