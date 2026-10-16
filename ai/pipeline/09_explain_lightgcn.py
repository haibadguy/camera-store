"""
09_explain_lightgcn.py -- Giải thích, Faithfulness và độ trễ cho HỆ THỐNG CUỐI = LightGCN + mặt nạ QĐ 4-9
(kế hoạch đăng ký trước docs/reviews/final_system_explain_plan.md, Nam duyệt 16/10/2026). Viết 16/10/2026.
CHỈ đo phần giải thích và độ trễ: KHÔNG chấm lại độ chính xác, không chọn mô hình. Top-10 lấy từ mảng ĐÃ LƯU
(test: results/cakg/test_final_20261015/lightgcn_s*/, val: results/cakg/finalcheck_val_20261015_nhap1/lightgcn_s*/),
kiểm sha256 với result.json.

Ví dụ (kế hoạch mục 2): u có D750, D500 (cả hai M = 1 với ống l). e_D750ᵀe_l = 1,2, e_D500ᵀe_l = 0,4 -> b* = D750.
Phản thực tế: bỏ cạnh (u, D750) khỏi đồ thị train (chuẩn hóa lại bậc), lan truyền lại 3 lớp với CÙNG tham số, chấm lại
riêng u (ứng viên, mặt nạ như lúc chấm); l rơi khỏi top-10 -> "cần thiết". Đối chứng: làm y hệt với D500.

Quy tắc (cố định):
  b* = argmax_{b ∈ B_u, M_bl = 1} e_bᵀe_l (embedding cuối của LightGCN cùng seed); hòa: iid nhỏ hơn.
  c* = nhãn mục đích của l; ≥ 2 nhãn: nhãn đầu theo thứ tự nút usecase (kg_node_index.json). c* không có trong đồ thị
       của LightGCN nên không ảnh hưởng điểm (vế này là sự kiện của đồ thị, không phải lý do của gợi ý).
Đo, mỗi seed 1–3:
  1. câu cho mọi ống trong top-10 sau mặt nạ của người có thân; kiểm sự kiện bằng eval_cakg.verify_explanation (lỗi = 0);
  2. PC tính lại từ top-10 đã lưu, phải TRÙNG mảng pc_counts đã lưu (kiểm, không phải số mới);
  3. Faithfulness trên tối đa 2.000 cặp có đường đủ 3 bước (seed 20261014): chấm lại "không bỏ gì" (cặp mà l không còn
     trong top-10 bị đếm và loại); bỏ (u, b*) -> FS_PN@10, ΔS; đối chứng bỏ (u, b'), b' lấy đều trong các thân khác của u
     có M_b'l = 1 -> C9-LG = FS_PN(b*) − FS_PN(b'), bootstrap theo cặp B = 2.000, seed 20261009; < 30 cặp: chỉ mô tả.
     Tách theo số thân lắp được của u (1 / ≥ 2).
Độ trễ (seed 1, như 08b_latency.py): 1.000 người (seed 20261014), 50 khởi động; GPU và CPU; p50 / p95 / p99 / max.

Chạy (từ thư mục camera-store):
  thử val: ai\\.venv\\Scripts\\python.exe ai/pipeline/09_explain_lightgcn.py --split val --label <nhãn>
  test   : ai\\.venv\\Scripts\\python.exe ai/pipeline/09_explain_lightgcn.py --split test --allow-test --label <nhãn>
Kết quả: results/final_system/explain_<split>_<nhãn>/ (thư mục mới; log tên mới).
"""

import argparse
import importlib
import json
import sys
import time
import tomllib
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

LAT = importlib.import_module("08b_latency")              # machine() (dùng lại, không sửa)
N5_TOML = C.ROOT / "ai" / "config" / "n5_final.toml"
SAVED = {"test": C.ROOT / "results" / "cakg" / "test_final_20261015",
         "val": C.ROOT / "results" / "cakg" / "finalcheck_val_20261015_nhap1"}
BR = "mat_na_qd49"
OUT_ROOT = C.ROOT / "results" / "final_system"
LAT_SEED = 20261014


# -- quy tắc b*, c* -------------------------------------------------------------

def pick_body(cand, eI, l):
    """b* = argmax_{b ∈ cand} e_bᵀe_l; hòa: iid nhỏ hơn. eI: mảng / tensor [N_ITEMS, d] (CPU). Trả về (b*, điểm từng b)."""
    sc = {b: float(eI[b] @ eI[l]) for b in cand}
    return min(cand, key=lambda b: (-sc[b], b)), sc


def pick_label(labels, order):
    """c* = nhãn đầu theo thứ tự nút usecase (order: danh sách tên nhãn); không có nhãn -> None."""
    return min(labels, key=order.index) if labels else None


class LGExplainer:
    def __init__(self, eI, bodies, pctx, usecase_order):
        self.eI, self.bodies, self.pctx, self.order = eI, bodies, pctx, usecase_order

    def explain(self, u, l):
        cand = sorted(self.pctx.bodies_for(u, l, self.bodies))
        if not cand:
            return None
        b, sc = pick_body(cand, self.eI, l)
        return {"u": u, "l": l, "b_star": b, "rho": self.pctx.rho[(b, l)],
                "c_star": pick_label(self.pctx.suit.get(l, []), self.order), "e_score": sc, "cand_bodies": cand}


# -- đồ thị train bỏ một cạnh ---------------------------------------------------

class AdjBuilder:
    """D^(-1/2) A D^(-1/2) như 05b.build_norm_adj, có thể bỏ một cặp (u, i) (cả hai chiều), chuẩn hóa lại bậc."""

    def __init__(self, train, device=E.DEVICE):
        import train_05 as T
        self.pu, self.pi = T.train_pairs(train)
        self.device = device

    def build(self, drop=None):
        pu, pi = self.pu, self.pi
        if drop is not None:
            keep = ~((pu == drop[0]) & (pi == drop[1]))
            assert int((~keep).sum()) == 1, f"cặp {drop} phải có đúng 1 lần trong train"
            pu, pi = pu[keep], pi[keep]
        rows = np.concatenate([pu, C.N_USERS + pi])
        cols = np.concatenate([C.N_USERS + pi, pu])
        N = C.N_USERS + C.N_ITEMS
        deg = np.bincount(rows, minlength=N).astype(np.float64)
        dis = np.zeros(N)
        dis[deg > 0] = deg[deg > 0] ** -0.5
        idx = torch.as_tensor(np.stack([rows, cols]))
        val = torch.as_tensor(dis[rows] * dis[cols], dtype=torch.float32)
        return torch.sparse_coo_tensor(idx, val, (N, N)).coalesce().to(self.device)


@torch.no_grad()
def propagate(m, adj):
    """Lan truyền LightGCN (05b.LightGCN.propagate) với ma trận kề adj, cùng tham số m."""
    E0 = torch.cat([m.user_emb.weight, m.item_emb.weight])
    acc, Ek = E0, E0
    for _ in range(m.n_layers):
        Ek = torch.sparse.mm(adj, Ek)
        acc = acc + Ek
    Ef = acc / (m.n_layers + 1)
    return Ef[:m.n_users], Ef[m.n_users:]


def one_user_topk(eU, eI, u, sp, row, pi, lens_t, cmask_t, K=10):
    """Top-K sau mặt nạ của riêng u (ứng viên như sp: bỏ item train, val khi chấm test; quy tắc hòa π), và điểm sau
    mặt nạ của mọi sản phẩm."""
    S = (eU[u:u + 1] @ eI.T)
    sub = E.Split(sp.name, sp.users[row:row + 1], sp.pos[row:row + 1],
                  np.array([0, sp.excl_ptr[row + 1] - sp.excl_ptr[row]]),
                  sp.excl_col[sp.excl_ptr[row]:sp.excl_ptr[row + 1]])
    f = EC.mask_scorer(lambda uids: S.clone(), lens_t, cmask_t)
    top = E.full_rank(f, sub, pi, k_max=K, k_list=[K])["top"][0]
    return top.tolist(), f(torch.as_tensor([u], device=S.device))[0]


def faithfulness_lg(m, adjb, ev, pairs, lens_t, cmask_t, eU0, eI0, rng, K=10):
    """Trả về mảng theo cặp: base_ok (l còn trong top-K khi chấm lại không bỏ gì), drop / dS (bỏ (u, b*)),
    has_ctrl / drop_ctrl / dS_ctrl (bỏ (u, b')), n_cand (số thân lắp được của u)."""
    sp = ev.split
    row_of = {int(u): r for r, u in enumerate(sp.users.tolist())}
    keys = ["u", "l", "b_star", "n_cand", "base_ok", "drop", "dS", "has_ctrl", "b_ctrl", "drop_ctrl", "dS_ctrl"]
    out = {k: [] for k in keys}
    for ex in pairs:
        u, l, b = ex["u"], ex["l"], ex["b_star"]
        r = row_of[u]
        top0, s0 = one_user_topk(eU0, eI0, u, sp, r, ev.pi, lens_t, cmask_t, K)
        others = [x for x in ex["cand_bodies"] if x != b]
        b2 = int(rng.choice(others)) if others else -1          # rút đối chứng cho MỌI cặp (thứ tự rng cố định)
        out["u"].append(u), out["l"].append(l), out["b_star"].append(b), out["n_cand"].append(len(ex["cand_bodies"]))
        ok = l in top0
        out["base_ok"].append(int(ok))
        if not ok:
            for k in ("drop", "dS", "has_ctrl", "b_ctrl", "drop_ctrl", "dS_ctrl"):
                out[k].append(0)
            continue
        eU, eI = propagate(m, adjb.build((u, b)))
        t1, s1 = one_user_topk(eU, eI, u, sp, r, ev.pi, lens_t, cmask_t, K)
        out["drop"].append(int(l not in t1))
        out["dS"].append(float(s0[l] - s1[l]))
        out["has_ctrl"].append(int(b2 >= 0))
        out["b_ctrl"].append(b2)
        if b2 >= 0:
            eU, eI = propagate(m, adjb.build((u, b2)))
            t2, s2 = one_user_topk(eU, eI, u, sp, r, ev.pi, lens_t, cmask_t, K)
            out["drop_ctrl"].append(int(l not in t2))
            out["dS_ctrl"].append(float(s0[l] - s2[l]))
        else:
            out["drop_ctrl"].append(0)
            out["dS_ctrl"].append(0.0)
    return {k: np.asarray(v) for k, v in out.items()}


def summarize(fs, B=2000, seed=E.BOOT_SEED, min_pairs=EC.C9_MIN_PAIRS):
    ok = fs["base_ok"] == 1
    res = {"n_pairs_sampled": int(len(ok)), "n_excluded_base_not_in_top10": int((~ok).sum()), "n_pairs": int(ok.sum()),
           "fs_pn": float(fs["drop"][ok].mean()) if ok.any() else float("nan"),
           "dS_mean": float(fs["dS"][ok].mean()) if ok.any() else float("nan")}
    for nm, sel in (("mot_than", ok & (fs["n_cand"] == 1)), ("tu_hai_than", ok & (fs["n_cand"] >= 2))):
        res[f"n_pairs_{nm}"] = int(sel.sum())
        res[f"fs_pn_{nm}"] = float(fs["drop"][sel].mean()) if sel.any() else float("nan")
    m = ok & (fs["has_ctrl"] == 1)
    res["n_pairs_with_ctrl_body"] = int(m.sum())
    if m.any():
        res["c9_lg"] = E.bootstrap_paired(
            {"expl": (fs["drop"][m].astype(float), None), "ctrl": (fs["drop_ctrl"][m].astype(float), None),
             "dS_expl": (fs["dS"][m], None), "dS_ctrl": (fs["dS_ctrl"][m], None)},
            pairs=[("expl", "ctrl"), ("dS_expl", "dS_ctrl")], B=B, seed=seed)
    res["c9_chi_mo_ta"] = res["n_pairs_with_ctrl_body"] < min_pairs
    return res


# -- độ trễ ---------------------------------------------------------------------

def latency(m, train, ev_bodies, item_type, ctx, pctx, order, log, n_users=1000, warmup=50):
    lens, cmask = E.certain_violation_mask(ev_bodies, ctx)
    propagate(m, m.adj)                                       # khởi động, không tính
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    t = time.perf_counter()
    eU, eI = propagate(m, m.adj)
    torch.cuda.synchronize()
    t_pre = time.perf_counter() - t
    log(f"Tính sẵn embedding mọi người / sản phẩm (GPU): {t_pre * 1000:.1f} ms | đỉnh VRAM "
        f"{torch.cuda.max_memory_allocated() / 2 ** 20:.0f} MiB")
    xp = LGExplainer(eI.cpu(), ev_bodies, pctx, order)
    users = np.random.default_rng(LAT_SEED).choice(C.N_USERS, warmup + n_users, replace=False).tolist()
    res = {"machine": LAT.machine(), "precompute_ms_gpu": t_pre * 1000, "n_users": n_users, "warmup": warmup}
    for dev in (E.DEVICE, torch.device("cpu")):
        eUd, eIT = eU.to(dev), eI.to(dev).T.contiguous()
        lt, cm = torch.as_tensor(lens, device=dev), torch.as_tensor(cmask, device=dev)
        tr = {u: torch.as_tensor(sorted(train[u]), device=dev) for u in users}
        if dev.type == "cuda":
            torch.cuda.reset_peak_memory_stats()
        times, n_s = [], 0
        for k, u in enumerate(users):
            if dev.type == "cuda":
                torch.cuda.synchronize()
            t = time.perf_counter()
            s = eUd[u] @ eIT
            s[tr[u]] = -float("inf")
            s[lt[cm[u]]] = -float("inf")
            top = torch.topk(s, 10).indices.tolist()
            sents = []
            for l in top:
                if item_type[l] == 1 and u in ev_bodies:
                    ex = xp.explain(u, l)
                    if ex is not None:
                        sents.append(EC.sentence(ex, pctx))
            if dev.type == "cuda":
                torch.cuda.synchronize()
            if k >= warmup:
                times.append(time.perf_counter() - t)
                n_s += len(sents)
        ms = np.array(times) * 1000
        st = {f"p{q}": float(np.percentile(ms, q)) for q in (50, 95, 99)}
        st.update(max=float(ms.max()), mean=float(ms.mean()), n_sentences=n_s)
        if dev.type == "cuda":
            st["peak_vram_allocated_mib"] = torch.cuda.max_memory_allocated() / 2 ** 20
        res[dev.type] = st
        log(f"  {dev.type.upper():4s}: p50 {st['p50']:.2f} ms, p95 {st['p95']:.2f} ms, p99 {st['p99']:.2f} ms, "
            f"max {st['max']:.2f} ms ({n_users:,} yêu cầu sau {warmup} khởi động; {n_s:,} câu)"
            + (f" | đỉnh VRAM {st['peak_vram_allocated_mib']:.0f} MiB" if "peak_vram_allocated_mib" in st else ""))
    return res


# -- chính ------------------------------------------------------------------------

def load_saved(split, seed):
    d = SAVED[split] / f"lightgcn_s{seed}"
    r = json.loads((d / "result.json").read_text(encoding="utf-8"))[BR]
    out = {}
    for nm in ("users", "top20_full"):
        fn = d / f"{split}_{BR}_{nm}.npy"
        assert E.sha256(fn) == r["arrays_sha256"][fn.name], f"sha256 khác result.json: {fn}"
        out[nm] = np.load(fn)
    for k in (5, 10):
        fn = d / f"{split}_{BR}_pc_counts_at{k}.npy"
        assert E.sha256(fn) == r["arrays_sha256_extra"][fn.name], f"sha256 khác result.json: {fn}"
        out[f"pc_counts_at{k}"] = np.load(fn)
    out["path_coverage"] = r["path_coverage"]
    out["checkpoint"] = r.get("checkpoint")
    return d, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="val", choices=["val", "test"])
    ap.add_argument("--allow-test", action="store_true", help="chỉ dùng ở lần chạy test MỘT lần của kế hoạch")
    ap.add_argument("--label", required=True)
    ap.add_argument("--max-faith", type=int, default=2000)
    ap.add_argument("--seeds", default="1,2,3")
    a = ap.parse_args()
    git = E.git_state()
    if a.split == "test" and (not a.allow_test or git["dirty"]):
        sys.exit("DỪNG: chạy trên test cần --allow-test và cây git sạch (final_system_explain_plan.md mục 5).")
    out_dir = OUT_ROOT / f"explain_{a.split}_{a.label}"
    out_dir.mkdir(parents=True, exist_ok=False)
    log = E.Log(out_dir / f"explain_lg_{E.now_tag()}.log")
    log(f"09_explain_lightgcn | tập {a.split} | git {git} | script sha256 {E.sha256(__file__)} | KHÔNG chấm lại độ chính "
        f"xác; top-10 từ mảng đã lưu ({SAVED[a.split].relative_to(C.ROOT)})")
    train = C.load_train()
    ev = E.EvalContext(a.split, train)
    pctx = EC.PathContext(train, ev.item_type)
    H = CK.build_h()
    has = EC.h_edge_checker(H)
    order = list(H.node_names["usecase"])
    masks = EC.masks_on_device(ev)
    adjb = AdjBuilder(train)
    n5 = tomllib.loads(N5_TOML.read_text(encoding="utf-8"))
    res = {"split": a.split, "git": git, "plan": "docs/reviews/final_system_explain_plan.md", "seeds": {}}
    for rr in n5["lightgcn"]["runs"]:
        s = rr["seed"]
        if str(s) not in a.seeds.split(","):
            continue
        d_saved, sv = load_saved(a.split, s)
        assert sv["checkpoint"]["dir"] == rr["dir"], (sv["checkpoint"], rr["dir"])
        assert np.array_equal(sv["users"], ev.split.users)
        m, _, sha = EC.load_lightgcn(C.ROOT / rr["dir"], train, expect_sha=rr["best_pt_sha256"])
        log(f"\n=== LightGCN seed {s}: {rr['dir']} (best.pt sha256 khớp n5_final.toml) | top-20 sau mặt nạ: "
            f"{d_saved.relative_to(C.ROOT)} (sha256 khớp result.json) ===")
        top = sv["top20_full"]
        # PC: tính lại từ top đã lưu, phải trùng mảng đã lưu
        pc, pc_pu = EC.pc_from_top(ev.split.users, top, ev.bodies, ev.item_type, ev.ctx, pctx)
        same = all(np.array_equal(pc_pu[k], sv[f"pc_counts_at{k}"]) for k in (5, 10))
        log(f"  PC@10 {pc['pc@10']:.4f}, PC_ngắn@10 {pc['pc_ngan@10']:.4f}, PC@5 {pc['pc@5']:.4f} | trùng mảng pc_counts "
            f"đã lưu: {'CÓ' if same else 'KHÔNG'}")
        assert same, "PC tính lại khác mảng đã lưu"
        # Câu + kiểm sự kiện
        eU0, eI0 = propagate(m, m.adj)
        xp = LGExplainer(eI0.cpu(), ev.bodies, pctx, order)
        expls, n_err, n_lens = [], 0, 0
        t = time.time()
        for r, u in enumerate(ev.split.users.tolist()):
            if u not in ev.bodies:
                continue
            for l in top[r, :10].tolist():
                if ev.item_type[l] != 1:
                    continue
                n_lens += 1
                ex = xp.explain(u, l)
                if ex is None:
                    continue
                sent = EC.sentence(ex, pctx)
                err = EC.verify_explanation(ex, sent, pctx, has)
                n_err += len(err)
                if err and n_err <= 20:
                    log(f"  LỖI (u {u}, l {l}): {err}")
                ex["sentence"], ex["errors"] = sent, err
                expls.append(ex)
        n_full = sum(e["c_star"] is not None for e in expls)
        n_tie = sum(len(e["cand_bodies"]) > 1 and sorted(e["e_score"].values())[-1] == sorted(e["e_score"].values())[-2]
                    for e in expls)
        log(f"  câu: {len(expls):,} / {n_lens:,} ống (người có thân, top-10 sau mặt nạ); đủ 3 bước {n_full:,}; "
            f"lỗi sự kiện {n_err}; b* phải phá hòa {n_tie} ({time.time() - t:.1f}s)")
        # Faithfulness
        pairs = EC.sample_faith_pairs(expls, a.max_faith)
        t = time.time()
        fs = faithfulness_lg(m, adjb, ev, pairs, *masks["qd49"], eU0, eI0, np.random.default_rng(EC.FAITH_SEED))
        sm = summarize(fs)
        log(f"  Faithfulness ({time.time() - t:.1f}s): lấy {sm['n_pairs_sampled']:,} cặp (seed {EC.FAITH_SEED}); chấm lại "
            f"không bỏ gì mà l rơi khỏi top-10: {sm['n_excluded_base_not_in_top10']} (loại); còn {sm['n_pairs']:,}")
        log(f"  FS_PN@10 = {sm['fs_pn']:.4f}, ΔS = {sm['dS_mean']:.5f} | 1 thân: {sm['n_pairs_mot_than']:,} cặp, FS_PN "
            f"{sm['fs_pn_mot_than']:.4f} | ≥ 2 thân: {sm['n_pairs_tu_hai_than']:,} cặp, FS_PN {sm['fs_pn_tu_hai_than']:.4f}")
        if "c9_lg" in sm:
            for k_, v in sm["c9_lg"].items():
                log(f"    C9-LG {k_}: {v[0]:.4f} [{v[1]:.4f}; {v[2]:.4f}] ({sm['n_pairs_with_ctrl_body']:,} cặp có b')")
        if sm["c9_chi_mo_ta"]:
            log(f"  C9-LG: dưới {EC.C9_MIN_PAIRS} cặp có đối chứng thân -> CHỈ MÔ TẢ")
        sd = out_dir / f"lightgcn_s{s}"
        sd.mkdir()
        with open(sd / "explanations.jsonl", "x", encoding="utf-8") as f:
            for e in expls:
                f.write(json.dumps({k: (v if not isinstance(v, dict) else {str(b): c for b, c in v.items()})
                                    for k, v in e.items()}, ensure_ascii=False) + "\n")
        np.savez(sd / "faithfulness_pairs.npz", **fs)
        res["seeds"][s] = {"run_dir": rr["dir"], "best_pt_sha256": sha, "saved_dir": str(d_saved.relative_to(C.ROOT)),
                           "n_lenses_body_users_top10": n_lens, "n_explanations": len(expls), "n_full_path": n_full,
                           "n_fact_errors": n_err, "n_bstar_tie_broken": n_tie, "path_coverage_recomputed": pc,
                           "pc_matches_saved": same, "faithfulness": sm,
                           "explanations_sha256": E.sha256(sd / "explanations.jsonl")}
        if s == 1:
            log("\nĐộ trễ (seed 1):")
            res["latency"] = latency(m, train, ev.bodies, ev.item_type, ev.ctx, pctx, order, log)
        del m
        torch.cuda.empty_cache()
    (out_dir / "summary.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {out_dir / 'summary.json'}")
    log.close()


if __name__ == "__main__":
    main()
