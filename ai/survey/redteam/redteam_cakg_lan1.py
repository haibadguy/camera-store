"""
redteam_cakg_lan1.py -- Red Team lần 1 nội dung 6–8 (CaKG-Rec): script chẩn đoán CHỈ ĐỌC. Viết 15/10/2026.
Không huấn luyện, không sửa code / cấu hình / kết quả, không chấm lại test. Ghi log tên mới (không ghi đè).

Chấm lại trên VAL (checkpoint chốt, đọc từ ai/config/cakg_final.toml, n5_final.toml):
  (1) checkpoint: sha256 best.pt = toml, nạp strict, NDCG@20 val chấm lại = result.json;
  (2) h_u: tính lại độc lập (trung bình h_b trên thân trong train có nút trong H) so với model.components()["hU"];
  (3) kênh phần cứng có tham gia không: β, tỉ lệ cặp có cổng mở, tỉ lệ cặp có điểm khác khi TẮT kênh phần cứng
      (mọi cặp dùng e_uᵀe_i), số người đổi top-10, tỉ phần "phần cứng" trong điểm các cặp cổng mở ở top-10;
  (4) kênh hành vi: Recall@10 / NDCG@10 val của CaKG-Rec đầy đủ, CaKG-Rec tắt kênh phần cứng, LightGCN cùng seed,
      tách người có thân / không có thân; người có thân tách theo item val có h hay không; loại sản phẩm top-10.
Đọc mảng ĐÃ LƯU (không tính lại điểm):
  (5) C6 trên val (results/cakg/finalcheck_val_20261015_nhap1, chạy và commit TRƯỚC test): bootstrap lại độc lập; theo
      từng seed; so hiệu val với hiệu test (bootstrap không ghép cặp, hai nhóm người khác nhau);
  (6) C4: CVR trước mặt nạ từng seed (val, test) so với ablation λ1 = 0;
  (7) PC@10 của ablation λ1 = 0 (val): đếm ống / đường ngắn / đường đủ, độ tập trung của ống trong top-10;
  (8) tập ứng viên trên mảng TEST đã lưu (dùng test vì phải kiểm "bỏ train + val khi chấm test"; chỉ đọc top-20):
      mọi mô hình, mọi nhánh, R-GCN 09/10: top-20 không chứa item train / val của người đó; cùng mảng users;
  (9) mặt nạ (val): top-20 sau mặt nạ QĐ 4-9 không có ống judge_lens True; số người có hàng mặt nạ khác 0;
  (10) C9: tách FS_PN theo số thân trong H của người dùng (mảng faithfulness_pairs.npz trên test, đã lưu).

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/survey/redteam/redteam_cakg_lan1.py --label 20261015_lan1
Log: ai/data/survey/redteam/run_redteam_cakg_<nhãn>.log
"""

import argparse
import importlib
import json
import sys
import tomllib
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
PIPE = ROOT / "ai" / "pipeline"
sys.path.insert(0, str(PIPE))
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

T06 = importlib.import_module("06_cakg_train")
FIN = tomllib.loads((ROOT / "ai" / "config" / "cakg_final.toml").read_text(encoding="utf-8"))
N5 = tomllib.loads((ROOT / "ai" / "config" / "n5_final.toml").read_text(encoding="utf-8"))
VALDIR = ROOT / "results" / "cakg" / "finalcheck_val_20261015_nhap1"
TESTDIR = ROOT / "results" / "cakg" / "test_final_20261015"
N5TEST = ROOT / "results" / "n5" / "test_final_20261009"
PRE, Q, EX = "truoc_mat_na", "mat_na_qd49", "mat_na_exists"


def hit(r, k=10):
    return (r <= k).astype(np.float64)


def ndcg(r, k=10):
    return np.where(r <= k, 1.0 / np.log2(r + 1.0), 0.0)


def boot_ci(x, B=2000, seed=1):
    """Bootstrap trung bình của x (theo phần tử), khoảng 95% phân vị. Cài riêng (không dùng eval_05) để đối chiếu."""
    rng = np.random.default_rng(seed)
    n = len(x)
    m = np.array([x[rng.integers(0, n, n)].mean() for _ in range(B)])
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def load_cakg(d, train):
    cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))["cfg"]
    m = T06.build_cakg(cfg, train, log=lambda s: None)
    sd = torch.load(d / "best.pt", map_location=E.DEVICE, weights_only=False)["model"]
    m.load_state_dict(sd, strict=True)
    m.eval()
    return m, cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = E.Log(ROOT / "ai" / "data" / "survey" / "redteam" / f"run_redteam_cakg_{a.label}.log")
    log(f"redteam_cakg_lan1 | git {E.git_state()} | script sha256 {E.sha256(Path(__file__))} | {E.DEVICE}")
    train = C.load_train()
    ev = E.EvalContext("val", train)
    sp = ev.split
    users = sp.users
    body = np.array([u in ev.bodies for u in users.tolist()])
    item_type = ev.item_type
    log(f"val: {len(users):,} người; người có thân {int(body.sum()):,}")

    # ---------------- (1)–(4): chấm lại trên val ----------------
    runs = [("cakg_s1", FIN["cakg"]["runs"][0]), ("cakg_s2", FIN["cakg"]["runs"][1]), ("cakg_s3", FIN["cakg"]["runs"][2]),
            ("abl_lam1_0_s1", FIN["ablation"][0]), ("abl_bo_suitable_for_s1", FIN["ablation"][1])]
    lg_runs = {r["seed"]: ROOT / r["dir"] for r in N5["lightgcn"]["runs"]}
    lg_rank, lg_top = {}, {}
    for s, d in lg_runs.items():
        m, _, sha = EC.load_lightgcn(d, train)
        fr = E.full_rank(m.score_fn(), sp, ev.pi)
        lg_rank[s], lg_top[s] = fr["rank"], fr["top"]
        old = np.load(VALDIR / f"lightgcn_s{s}" / f"val_{PRE}_rank_full.npy")
        log(f"LightGCN s{s}: best.pt sha256 {sha[:12]}…; NDCG@20 val {ndcg(fr['rank'], 20).mean():.5f}; "
            f"hạng khác mảng finalcheck_val ở {int((old != fr['rank']).sum())} người")
        del m
        torch.cuda.empty_cache()

    _, _, bodies_h = None, None, None
    H = CK.build_h()
    _, has_hu_ref, bodies_h = CK.user_body_matrix(train, item_type, H.item_loc, H.n_nodes)
    for name, r in runs:
        d = ROOT / r["dir"]
        log(f"\n=== {name} ({r['dir']}) ===")
        sha = E.sha256(d / "best.pt")
        log(f"(1) best.pt sha256 {'KHỚP' if sha == r['best_pt_sha256'] else 'KHÁC'} toml; nạp strict=True")
        m, cfg = load_cakg(d, train)
        c = m.components()
        full = m.make_scorer(c, m.hidx)
        fr = E.full_rank(full, sp, ev.pi)
        res = json.loads((d / "result.json").read_text(encoding="utf-8"))
        log(f"(1) NDCG@20 val chấm lại {ndcg(fr['rank'], 20).mean():.6f} | result.json {res['val']['full']['ndcg@20']:.6f}"
            f" | toml {r['val_ndcg20']:.6f}")

        # (2) h_u tính lại độc lập
        h = c["h"].cpu().numpy()
        hU = c["hU"].cpu().numpy()
        has_hu = c["has_hu"].cpu().numpy()
        bh = H.item_loc
        bodies_h2 = {u: sorted(i for i in its if item_type[i] == 0 and i in bh) for u, its in train.items()}
        bodies_h2 = {u: v for u, v in bodies_h2.items() if v}
        err = 0.0
        for u, bs in bodies_h2.items():
            ref = h[[bh[b] for b in bs]].mean(0)
            err = max(err, float(np.abs(ref - hU[u]).max()))
        no = np.ones(C.N_USERS, bool)
        no[list(bodies_h2)] = False
        log(f"(2) h_u: {len(bodies_h2):,} người có thân trong H (has_hu = {int(has_hu.sum()):,}); "
            f"lệch tối đa so với tính lại {err:.2e}; người không có thân trong H: has_hu True {int(has_hu[no].sum())}, "
            f"‖h_u‖ lớn nhất {float(np.abs(hU[no]).max()):.2e}; khớp user_body_matrix {bodies_h2 == bodies_h}")

        # (3) β, cổng, tắt kênh phần cứng
        bU, bI = c["betaU"][:, 1].cpu().numpy(), c["betaI"][:, 1].cpu().numpy()
        has_hi = c["has_hi"].cpu().numpy()
        log(f"(3) β_h phía người (có h_u): TB {bU[has_hu].mean():.4f}, trung vị {np.median(bU[has_hu]):.4f}, "
            f"[{bU[has_hu].min():.4f}; {bU[has_hu].max():.4f}] | phía item (có h): TB {bI[has_hi].mean():.4f}, "
            f"trung vị {np.median(bI[has_hi]):.4f}, [{bI[has_hi].min():.4f}; {bI[has_hi].max():.4f}]")
        log(f"    cặp có cổng mở: {int(has_hu.sum()):,} người × {int(has_hi.sum()):,} item = "
            f"{has_hu.sum() * has_hi.sum() / (C.N_USERS * C.N_ITEMS):.4%} mọi cặp")
        eU, eI = c["eU"], c["eI"]

        def off(uids):
            return eU[uids] @ eI.T
        fo = E.full_rank(off, sp, ev.pi)
        # tỉ lệ cặp ứng viên có điểm khác khi tắt kênh phần cứng (người có h_u)
        gu = np.flatnonzero(has_hu[users])
        n_diff = n_gate = n_cand = 0
        for s in range(0, len(gu), 1024):
            rr = gu[s:s + 1024]
            ut = torch.as_tensor(users[rr], device=E.DEVICE)
            S1, S0 = full(ut), off(ut)
            cand = torch.ones_like(S1, dtype=torch.bool)
            for j, ridx in enumerate(rr.tolist()):
                cand[j, torch.as_tensor(sp.excl_col[sp.excl_ptr[ridx]:sp.excl_ptr[ridx + 1]], device=E.DEVICE)] = False
            n_diff += int(((S1 != S0) & cand).sum())
            n_gate += int((c["has_hi"][None, :] & cand).sum())
            n_cand += int(cand.sum())
        top_changed = np.array([set(fr["top"][i, :10].tolist()) != set(fo["top"][i, :10].tolist())
                                for i in range(len(users))])
        log(f"    người val có h_u: {len(gu):,}; trong cặp ứng viên của họ: điểm khác khi tắt kênh phần cứng "
            f"{n_diff:,} / {n_cand:,} = {n_diff / n_cand:.4%} (cặp cổng mở {n_gate:,}); top-10 đổi ở "
            f"{int(top_changed[has_hu[users]].sum()):,} / {len(gu):,} người có h_u, {int(top_changed[~has_hu[users]].sum())}"
            f" người không có h_u")
        # tỉ phần phần cứng trong điểm, cặp cổng mở ở top-10 (đầy đủ)
        uu = users[gu]
        tt = fr["top"][gu, :10]
        sel = has_hi[tt]
        U_ = np.repeat(uu, 10).reshape(-1, 10)[sel]
        I_ = tt[sel]
        Ut, It = torch.as_tensor(U_, device=E.DEVICE), torch.as_tensor(I_, device=E.DEVICE)
        beh = (c["betaU"][Ut, 0] * c["betaI"][It, 0] * (eU[Ut] * eI[It]).sum(1)).cpu().numpy()
        hI = c["h"][m.item_loc[It]]
        hw = (c["betaU"][Ut, 1] * c["betaI"][It, 1] * (c["hU"][Ut] * hI).sum(1)).cpu().numpy()
        share = np.abs(hw) / (np.abs(beh) + np.abs(hw))
        log(f"    top-10 (đầy đủ) của người có h_u: {sel.sum():,} cặp cổng mở / {sel.size:,}; phần phần cứng / điểm: "
            f"trung vị {np.median(share):.3f}, TB {share.mean():.3f}; phần phần cứng > 0 ở {(hw > 0).mean():.3f}")
        # (4) kênh hành vi và nhóm người
        s_ = int(name[-1]) if name.startswith("cakg_s") else 1
        grp = {"mọi người": np.ones(len(users), bool), "không có thân": ~body, "có thân": body,
               "có h_u": has_hu[users]}
        pos_h = has_hi[sp.pos]
        grp["có h_u, item val có h"] = has_hu[users] & pos_h
        grp["có h_u, item val không có h"] = has_hu[users] & ~pos_h
        for g, msk in grp.items():
            log(f"(4) {g:<28} n={int(msk.sum()):>6} | R@10 đầy đủ {hit(fr['rank'])[msk].mean():.5f}  tắt phần cứng "
                f"{hit(fo['rank'])[msk].mean():.5f}  LightGCN s{s_} {hit(lg_rank[s_])[msk].mean():.5f} | NDCG@10 "
                f"{ndcg(fr['rank'])[msk].mean():.5f} / {ndcg(fo['rank'])[msk].mean():.5f} / "
                f"{ndcg(lg_rank[s_])[msk].mean():.5f}")
        for lab, top in (("đầy đủ", fr["top"]), ("tắt phần cứng", fo["top"]), (f"LightGCN s{s_}", lg_top[s_])):
            t = item_type[top[body, :10]]
            log(f"    top-10 người có thân, {lab:<14}: thân {(t == 0).sum(1).mean():.2f} ống {(t == 1).sum(1).mean():.2f} "
                f"phụ kiện {(t == 2).sum(1).mean():.2f} khác {(t == 3).sum(1).mean():.2f}")
        del m, c
        torch.cuda.empty_cache()
    pt = item_type[sp.pos[body]]
    log(f"\nItem val của người có thân: thân {(pt == 0).sum()}, ống {(pt == 1).sum()}, phụ kiện {(pt == 2).sum()}, "
        f"khác {(pt == 3).sum()}")

    # ---------------- (5) C6 trên val, theo seed, val vs test ----------------
    log("\n=== (5) C6 (kịch bản chỉ ống, nhóm lắp được) ===")

    def lens_hits(base, split, name, br):
        su = np.load(base / name / f"{split}_{br}_scn_users.npy")
        return su, hit(np.load(base / name / f"{split}_{br}_rank_lens_only.npy"))

    out5 = {}
    for split, base in (("val", VALDIR), ("test", TESTDIR)):
        evs = ev if split == "val" else E.EvalContext("test", train)
        lab = {int(u): g for u, g in zip(evs.split.users.tolist(), evs.scn_lab.tolist())}
        per = {}
        for mdl, br in (("cakg", Q), ("lightgcn", Q), ("lightgcn", PRE)):
            hs = []
            for s in (1, 2, 3):
                su, hh = lens_hits(base, split, f"{mdl}_s{s}", br)
                g = np.array([lab[int(u)] == "lap_duoc" for u in su])
                hs.append(hh[g])
            per[f"{mdl}|{br}"] = np.array(hs)
            usr = su[g]
        out5[split] = (per, usr)
        a_, bq, bp = per[f"cakg|{Q}"], per[f"lightgcn|{Q}"], per[f"lightgcn|{PRE}"]
        log(f"[{split}] nhóm lắp được: {a_.shape[1]} người")
        for lab_, b_ in (("CaKG (mặt nạ) − LightGCN + mặt nạ", bq), ("CaKG (mặt nạ) − LightGCN", bp)):
            dlt = a_.mean(0) - b_.mean(0)
            pe = E.bootstrap_paired({"a": (a_.mean(0), None), "b": (b_.mean(0), None)}, pairs=[("a", "b")])["a - b"]
            mine = boot_ci(dlt)
            log(f"  {lab_:<36} hiệu {pe[0]:+.5f} [{pe[1]:+.5f}; {pe[2]:+.5f}] (eval_05.bootstrap_paired, seed "
                f"{E.BOOT_SEED}); cài riêng seed 1: [{mine[1]:+.5f}; {mine[2]:+.5f}] | theo seed: "
                + " ".join(f"s{s + 1} {a_[s].mean() - b_[s].mean():+.4f}" for s in range(3)))
        log("  R@10 theo seed: " + " | ".join(f"{k} " + " ".join(f"{x:.4f}" for x in v.mean(1)) for k, v in per.items()))
    (pv, uv), (ptt, ut) = out5["val"], out5["test"]
    log(f"  người chung giữa nhóm lắp được val và test: {len(set(uv.tolist()) & set(ut.tolist()))}")
    rng = np.random.default_rng(20261009)
    for lab_, kb in (("vs LightGCN + mặt nạ", f"lightgcn|{Q}"), ("vs LightGCN", f"lightgcn|{PRE}")):
        dv = pv[f"cakg|{Q}"].mean(0) - pv[kb].mean(0)
        dt = ptt[f"cakg|{Q}"].mean(0) - ptt[kb].mean(0)
        bs = np.array([dv[rng.integers(0, len(dv), len(dv))].mean() - dt[rng.integers(0, len(dt), len(dt))].mean()
                       for _ in range(2000)])
        log(f"  hiệu(val) − hiệu(test), {lab_:<22}: {dv.mean() - dt.mean():+.5f} "
            f"[{np.percentile(bs, 2.5):+.5f}; {np.percentile(bs, 97.5):+.5f}] (bootstrap độc lập hai nhóm, B 2000)")
    for split in ("val", "test"):
        p = out5[split][0]
        log(f"  [{split}] tác dụng riêng của mặt nạ trên LightGCN (LightGCN + mặt nạ − LightGCN): "
            f"{(p[f'lightgcn|{Q}'].mean(0) - p[f'lightgcn|{PRE}'].mean(0)).mean():+.5f}")

    # ---------------- (6) C4 theo seed ----------------
    log("\n=== (6) C4: CVR_strict@10 trước mặt nạ, người có thân, từng lần chạy ===")
    for split, base in (("val", VALDIR), ("test", TESTDIR)):
        row = []
        for nm in ("cakg_s1", "cakg_s2", "cakg_s3", "abl_lam1_0_s1", "abl_bo_suitable_for_s1", "lightgcn_s1",
                   "lightgcn_s2", "lightgcn_s3"):
            nv = np.load(base / nm / f"{split}_{PRE}_cvr_n_viol_at10.npy").sum()
            nl = np.load(base / nm / f"{split}_{PRE}_cvr_n_lenses_at10.npy").sum()
            row.append(f"{nm} {nv / nl:.4f} ({nv}/{nl})")
        log(f"  [{split}] " + " | ".join(row))

    # ---------------- (7) PC@10 ablation λ1 = 0 (val) ----------------
    log("\n=== (7) Path Coverage @10 sau mặt nạ QĐ 4-9, người có thân (val) ===")
    pctx = EC.PathContext(train, item_type)
    for nm in ("cakg_s1", "abl_lam1_0_s1", "abl_bo_suitable_for_s1", "lightgcn_s1"):
        cnt = np.load(VALDIR / nm / f"val_{Q}_pc_counts_at10.npy")[body].sum(0)
        top = np.load(VALDIR / nm / f"val_{Q}_top20_full.npy")[body, :10]
        lens = top[item_type[top] == 1]
        uniq, ct = np.unique(lens, return_counts=True)
        o = np.argsort(-ct)
        has_suit = np.isin(lens, list(pctx.suit))
        log(f"  {nm:<24} ống {cnt[1]:,} | chấm được {cnt[2]:,} | đường ngắn {cnt[3]:,} | đường đủ {cnt[4]:,} | "
            f"PC {cnt[4] / cnt[1]:.4f} PC_ngắn {cnt[3] / cnt[1]:.4f} | ống có suitable_for {has_suit.mean():.3f} | "
            f"ống khác nhau {len(uniq):,}; 5 ống nhiều nhất chiếm {ct[o[:5]].sum() / ct.sum():.3f} "
            f"({', '.join(f'{int(uniq[i])}×{int(ct[i])}' for i in o[:5])})")

    # ---------------- (8) tập ứng viên trên mảng test đã lưu ----------------
    log("\n=== (8) Tập ứng viên trên mảng TEST đã lưu (chỉ đọc top-20; không chấm lại) ===")
    evt = E.EvalContext("test", train)
    tu = evt.split.users
    val_pos = C.load_pos("val")
    keys = np.unique(np.concatenate([np.array([u * C.N_ITEMS + i for u, its in train.items() for i in its], np.int64),
                                     np.array([u * C.N_ITEMS + i for u, i in val_pos.items()], np.int64)]))
    is_lens = item_type == 1

    def bad_count(top, us):
        k = us[:, None].astype(np.int64) * C.N_ITEMS + top
        return int(np.isin(k, keys).sum())
    for d in sorted(p for p in TESTDIR.iterdir() if p.is_dir() and not p.name.startswith("explain")):
        for br in (PRE, Q, EX):
            f = d / f"test_{br}_top20_full.npy"
            if not f.exists():
                continue
            us = np.load(d / f"test_{br}_users.npy")
            same = np.array_equal(us, tu)
            b1 = bad_count(np.load(f), us)
            su = np.load(d / f"test_{br}_scn_users.npy")
            tl = np.load(d / f"test_{br}_top20_lens_only.npy")
            b2 = bad_count(tl, su)
            log(f"  {d.name:<24} {br:<14} users = tập test {same}; top-20 có item train/val: {b1}; "
                f"chỉ ống: có item train/val {b2}, có sản phẩm không phải ống {int((~is_lens[tl]).sum())}")
    for s in (1, 2, 3):
        d = N5TEST / f"rgcn_s{s}"
        us = np.load(d / "users.npy")
        log(f"  R-GCN s{s} (09/10)          users = tập test {np.array_equal(us, tu)}; top-20 có item train/val: "
            f"{bad_count(np.load(d / 'top20_full.npy'), us)}")

    # ---------------- (9) mặt nạ (val) ----------------
    log("\n=== (9) Mặt nạ QĐ 4-9 (val) ===")
    lens_m, cmask = E.certain_violation_mask(ev.bodies, ev.ctx)
    log(f"  người có hàng mặt nạ khác 0: {int(cmask.any(1).sum()):,} (người có thân {len(ev.bodies):,})")
    for nm in ("cakg_s1", "lightgcn_s1"):
        top = np.load(VALDIR / nm / f"val_{Q}_top20_full.npy")
        nv = 0
        for r, u in enumerate(users.tolist()):
            bs = ev.bodies.get(u)
            if bs:
                nv += sum(C.judge_lens(int(i), bs, ev.ctx) is True for i in top[r] if item_type[i] == 1)
        log(f"  {nm}: ống vi phạm chắc chắn trong top-20 sau mặt nạ: {nv}")

    # ---------------- (10) C9 tách theo số thân ----------------
    log("\n=== (10) Faithfulness trên test (mảng faithfulness_pairs.npz đã lưu, không chạy lại) ===")
    for s in (1, 2, 3):
        fs = np.load(TESTDIR / f"explain_s{s}" / "faithfulness_pairs.npz")
        nb = np.array([len(bodies_h.get(int(u), [])) for u in fs["u"]])
        one = nb == 1
        multi_noctrl = (nb >= 2) & (fs["has_ctrl_body"] == 0)
        ctrl = fs["has_ctrl_body"] == 1
        dS, dSc = fs["dS"], fs["dS_ctrl_body"]
        log(f"  s{s}: cặp {len(nb)} | 1 thân trong H (bỏ b* đóng cổng): {one.sum()} cặp, FS_PN {fs['drop'][one].mean():.4f}"
            f" | ≥2 thân, không có đối chứng: {multi_noctrl.sum()} cặp, FS_PN {fs['drop'][multi_noctrl].mean():.4f}"
            f" | có đối chứng thân: {ctrl.sum()} cặp, FS_PN giải thích {fs['drop'][ctrl].mean():.4f}, đối chứng "
            f"{fs['drop_ctrl_body'][ctrl].mean():.4f}; ΔS giải thích ≥ ΔS đối chứng ở {(dS[ctrl] >= dSc[ctrl]).mean():.3f}"
            f" số cặp")
    log("\nXong.")
    log.close()


if __name__ == "__main__":
    main()
