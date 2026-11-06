"""
cross_eval.py — chấm lại embedding LightGCN do RecBole học (emb_best.npz của run_recbole.py) bằng BỘ CHẤM CỦA NHÓM
(ai/pipeline/eval_05.full_rank: xếp hạng toàn bộ, quy tắc hòa π, bỏ train khi chấm val, bỏ train + item val khi chấm
test). Viết 06/11/2026. Mục đích: tách hai nguồn lệch khi so số RecBole với số nhóm:
  (a) lệch do CÁCH CHẤM (RecBole tự chấm vs bộ chấm nhóm, cùng một mô hình) -> so result.json["valid_recbole"] với
      số chấm lại ở đây;
  (b) lệch do HUẤN LUYỆN (hai cài đặt LightGCN) -> so số chấm lại ở đây với số nhóm (results/n5/...).
Thêm cận hòa điểm: hạng thấp nhất / cao nhất có thể khi đổi quy tắc hòa (rank − n_tie, rank + n_tie).

Chạy bằng ai/.venv (cần code ai/pipeline):
  ai\\.venv\\Scripts\\python.exe ai/recbole/cross_eval.py --run-dir results/recbole/<nhãn>/<tên> [--split val|test]
Ghi: <run-dir>/cross_eval_<split>_<thời điểm>.json và log cùng tên.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai" / "pipeline"))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402

GROUP = {   # số nhóm, LightGCN λ = 1e-3 (n5_final.toml): val seed 1 = lần dò; test = 05_test_final 09/10
    "val": [ROOT / "results/n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1/result.json",
            ROOT / "results/n5/final_20261009/lightgcn_l2-1e-03_s2/result.json",
            ROOT / "results/n5/final_20261009/lightgcn_l2-1e-03_s3/result.json"],
    "test": [ROOT / f"results/n5/test_final_20261009/lightgcn_s{s}/result.json" for s in (1, 2, 3)],
}
KEYS = ["recall@10", "ndcg@10", "recall@20", "ndcg@20"]


def ndcg_hit(rank, k):
    return float(np.where(rank <= k, 1.0 / np.log2(rank + 1.0), 0.0).mean()), float((rank <= k).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--split", choices=["val", "test"], required=True)
    a = ap.parse_args()
    run_dir = (ROOT / a.run_dir).resolve()
    tag = time.strftime("%Y%m%d_%H%M%S")
    log = E.Log(run_dir / f"cross_eval_{a.split}_{tag}.log")
    rb = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    z = np.load(run_dir / "emb_best.npz")
    eu = torch.as_tensor(z["user"], device=E.DEVICE)
    ei = torch.as_tensor(z["item"], device=E.DEVICE)
    assert eu.shape == (C.N_USERS, 64) and ei.shape == (C.N_ITEMS, 64), (eu.shape, ei.shape)
    log(f"emb_best.npz sha256 {E.sha256(run_dir / 'emb_best.npz')} (result.json ghi {rb.get('emb_best_sha256')}) "
        f"| git {E.git_state()}")
    train = C.load_train()
    sp = E.load_eval_split(a.split, train)
    fr = E.full_rank(lambda u: eu[u] @ ei.T, sp, E.tie_keys())
    pu = E.per_user_metrics(fr["rank"], fr["top"], sp.pos)
    ours = E.mean_metrics(pu)
    rank, n_tie = fr["rank"], fr["n_tie"]
    lo, hi = np.maximum(1, rank - n_tie), rank + n_tie
    bounds = {}
    for k in (10, 20):
        nl, hl = ndcg_hit(lo, k)
        nh, hh = ndcg_hit(hi, k)
        bounds[f"ndcg@{k}"] = [nh, nl]
        bounds[f"recall@{k}"] = [hh, hl]
    rb_key = "valid_recbole" if a.split == "val" else "test_recbole"
    rbm = rb[rb_key]
    grp = []
    for p in GROUP[a.split]:
        d = json.loads(p.read_text(encoding="utf-8"))
        grp.append((d.get("val") or d)["full"] if a.split == "val" else d["full"])
    g_mean = {k: float(np.mean([g[k] for g in grp])) for k in KEYS}
    g_sd = {k: float(np.std([g[k] for g in grp], ddof=1)) for k in KEYS}
    out = {"split": a.split, "n_users": int(len(rank)), "n_users_tie_at_target": int((n_tie > 0).sum()),
           "max_n_tie": int(n_tie.max()),
           "recbole_self_eval": {k: rbm[k] for k in KEYS},
           "group_evaluator_on_recbole_emb": {k: float(ours[k]) for k in KEYS},
           "tie_bounds_group_evaluator": bounds,
           "group_lightgcn_seed1": {k: float(grp[0][k]) for k in KEYS},
           "group_lightgcn_mean_3seeds": g_mean, "group_lightgcn_sd_3seeds": g_sd,
           "diff_eval_protocol (recbole_self - group_eval, cùng mô hình)":
               {k: rbm[k] - float(ours[k]) for k in KEYS},
           "diff_impl_seed1 (group_eval(recbole) - group seed1)":
               {k: float(ours[k]) - float(grp[0][k]) for k in KEYS},
           "diff_impl_vs_mean (group_eval(recbole) - group mean 3 seeds)":
               {k: float(ours[k]) - g_mean[k] for k in KEYS},
           "inputs_sha256": E.inputs_sha256()}
    for k, v in out.items():
        if k != "inputs_sha256":
            log(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    (run_dir / f"cross_eval_{a.split}_{tag}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                                              encoding="utf-8")
    log("Xong.")


if __name__ == "__main__":
    main()
