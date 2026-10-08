"""
05a_popularity.py -- Popularity (Global) và Popularity-MountAware, theo docs/reviews/n5_eval_plan.md mục 6.1, 6.2.

Viết lại 09/10/2026 (lỗi L4, L6, L7, L8, L14 của kế hoạch mục 2).

Ví dụ: điểm của sản phẩm = số người dùng có nó trong train. Người dùng có thân Canon EOS (EF-S) trong train:
MountAware đặt −∞ cho ống mà common_05.judge_lens = True ("chắc chắn vi phạm", vd ống Nikon F); ống không phán
được (ngoài M, "không chắc", có cặp "không biết") và mọi sản phẩm không phải ống giữ nguyên. Người không có thân:
không lọc gì (Nam chốt 08/10 khuya). Bản của Hải loại MỌI ống ngoài tập M = 1 của người dùng, kể cả người không có thân.

Phép kiểm theo kế hoạch: CVR@K của MountAware phải bằng 0 (script DỪNG nếu khác 0).

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/05a_popularity.py --split val --out results/n5/<nhãn mới>
Chỉ nhận --split val: test được chấm một lần bằng script chạy test (kế hoạch mục 7.2 bước 5), chưa viết.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def build_pop_scores(train):
    """Số người dùng có sản phẩm trong train (train đã gộp lặp nên = số cặp)."""
    counts = np.zeros(C.N_ITEMS, dtype=np.float64)
    for items in train.values():
        for iid in items:
            counts[iid] += 1.0
    return counts


def global_scorer(pop):
    p = torch.as_tensor(pop, dtype=torch.float32, device=E.DEVICE)
    return lambda uids: p.unsqueeze(0).expand(len(uids), -1).clone()


def mountaware_scorer(pop, lens_cols, viol_mask):
    """viol_mask[u, j] = True: ống lens_cols[j] chắc chắn vi phạm với thân của u -> −∞."""
    p = torch.as_tensor(pop, dtype=torch.float32, device=E.DEVICE)
    cols = torch.as_tensor(lens_cols, device=E.DEVICE)
    mask = torch.as_tensor(viol_mask, device=E.DEVICE)

    def f(uids):
        S = p.unsqueeze(0).expand(len(uids), -1).clone()
        sub = S[:, cols]
        sub[mask[uids]] = -float("inf")
        S[:, cols] = sub
        return S
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["val"], required=True)
    ap.add_argument("--out", required=True, help="thư mục kết quả mới (đã có thì DỪNG)")
    a = ap.parse_args()
    out = Path(a.out)
    assert not out.exists(), f"thư mục đã có, không ghi đè: {out}"
    out.mkdir(parents=True)
    log = E.Log(out / f"run_{E.now_tag()}.log")
    git = E.git_state()
    log(f"05a Popularity | split {a.split} | git {git} | thiết bị {E.DEVICE}")

    ev = E.EvalContext(a.split)
    pop = build_pop_scores(ev.train)
    log(f"người dùng {len(ev.split.users):,} | cặp train {int(pop.sum()):,} | sản phẩm có lượt > 0 "
        f"{int((pop > 0).sum()):,} | số giá trị điểm khác nhau {len(np.unique(pop)):,} | người có thân "
        f"{len(ev.bodies):,}")
    log(f"kịch bản ({a.split}): " + ", ".join(f"{g} {int((ev.scn_lab == g).sum()):,}"
                                           for g in ("lap_duoc", "khong_lap_duoc", "khong_phan_duoc"))
        + f" | không lắp được có cặp requires_adapter {int(ev.scn_adp.sum()):,}")

    lens_cols, viol = E.certain_violation_mask(ev.bodies, ev.ctx)
    n_users_filtered = int(viol.any(1).sum())
    in_m = np.isin(ev.split.pos, lens_cols)
    n_pos_filtered = int(viol[ev.split.users[in_m], np.searchsorted(lens_cols, ev.split.pos[in_m])].sum())
    log(f"MountAware: {n_users_filtered:,} người dùng có ít nhất 1 ống bị lọc; tổng (người, ống) bị lọc "
        f"{int(viol.sum()):,}; người có item {a.split} bị lọc {n_pos_filtered:,}")

    results = {"split": a.split, "git": git, "inputs_sha256": E.inputs_sha256(), "tie_seed": E.TIE_SEED,
               "n_users_filtered_mountaware": n_users_filtered, "models": {}}
    for name, scorer in (("Popularity", global_scorer(pop)),
                         ("Popularity-MountAware", mountaware_scorer(pop, lens_cols, viol))):
        log(f"\n=== {name} ===")
        pref = "pop_" if name == "Popularity" else "popma_"
        res = E.evaluate(scorer, ev, log=log, save_dir=out, prefix=pref)
        results["models"][name] = res
        if name == "Popularity-MountAware":
            bad = {k: res["cvr"][f"cvr_n_violations@{k}"] for k in E.K_LIST}
            bad_l = {f"{g}@{k}": v["lens_only_cvr"][f"cvr@{k}"]
                     for g, v in res["scenario"].items() if v["n_users"] for k in E.K_LIST}
            log(f"kiểm: số vi phạm của MountAware (toàn catalog) = {bad}; CVR kịch bản chỉ ống = {bad_l}")
            assert all(v == 0 for v in bad.values()), "CVR của MountAware khác 0 -> lỗi code"
            assert all(v == 0 or np.isnan(v) for v in bad_l.values()), "CVR kịch bản của MountAware khác 0"

    (out / "result.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"\n-> {out / 'result.json'}")
    log.close()


if __name__ == "__main__":
    main()
