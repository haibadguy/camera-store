"""
06_cakg_train.py -- Huấn luyện CaKG-Rec trên train, chấm val (docs/cakg_design.md; kế hoạch đăng ký trước
docs/reviews/cakg_eval_plan.md mục 4). Viết 14/10/2026. Mô hình: cakg_model.py. KHÔNG chấm test.

Ví dụ một bước: batch 2048 bộ ba (u, i, j) như LightGCN (j lấy đều trong sản phẩm u chưa có trong train);
  L = BPR (điểm có cổng, công thức 9) + λ1 · L_comp (InfoNCE trên toàn bộ 537 × 1.033 cặp của M) + λ2 · L2(e⁰ của batch).

Cấu hình cố định (kế hoạch mục 4.1): kênh hành vi như LightGCN chốt (d 64, L 3, Adam lr 1e-3, batch 2048, λ2 = 1e-3,
Xavier); RGAT 2 lớp WIRGAT, 1 đầu, d 64, có W_0, không dropout, q / k riêng từng quan hệ; gộp kênh h' = 64; τ = 0,2;
H_lõi. Dò trên val (seed 1): λ1 ∈ {0,01; 0,1; 1,0}. Ablation (seed 1, cấu hình chốt): λ1 = 0; --drop-suitable-for.
Ngân sách như QĐ 5-5: tối đa 300 epoch, chấm NDCG@20 val (TRƯỚC mặt nạ, dùng để chọn) mỗi 10 epoch, dừng sau 5 lần
chấm không tăng. Mỗi lần chấm in thêm NDCG@20 val SAU mặt nạ QĐ 4-9 (theo dõi, không dùng để chọn). Cuối lần chạy:
chấm đầy đủ val với best.pt, trước mặt nạ (val_*) và sau mặt nạ (val_mask_*).

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/06_cakg_train.py --lam1 0.1 --seed 1 --run-dir results/cakg/<nhãn>/<tên>
Chạy lại đúng lệnh đó sau khi bị ngắt -> chạy tiếp từ lần chấm val gần nhất (train_05.run).
"""

import argparse
import importlib
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import train_05 as T     # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PIPE = Path(__file__).resolve().parent
L05B = importlib.import_module("05b_lightgcn_train")       # build_norm_adj (dùng lại, không sửa)
CODE_FILES = [Path(__file__), PIPE / "cakg_model.py", PIPE / "rgat_layer.py", PIPE / "05b_lightgcn_train.py",
              *CK.HW_INPUT_FILES]


def mask_scorer(score_batch, lens_t, cmask_t):
    """(15)/(17): ŷ' = ŷ + 𝓜 — đặt −∞ cho ống trong M bị chặn (cmask_t [n_users, n_lens] bool, cột theo lens_t)."""
    def f(uids):
        S = score_batch(uids)
        S[:, lens_t] = S[:, lens_t].masked_fill(cmask_t[uids], -float("inf"))
        return S
    return f


class MaskCache:
    """Mặt nạ QĐ 4-9 (eval_05.certain_violation_mask) cho người dùng của ev, dựng một lần."""
    def __init__(self):
        self.t = None

    def get(self, ev):
        if self.t is None:
            lens, cmask = E.certain_violation_mask(ev.bodies, ev.ctx)
            self.t = (torch.as_tensor(lens, device=E.DEVICE), torch.as_tensor(cmask, device=E.DEVICE))
        return self.t


def build_cakg(cfg, train, log=print, device=E.DEVICE):
    """Dựng CaKG-Rec theo cfg (dùng chung cho huấn luyện, chấm lại checkpoint, giải thích). In số kiểm."""
    item_type = C.load_item_type()
    H = CK.build_h(drop_suitable_for=cfg["drop_suitable_for"])
    log(f"Đồ thị con H ({cfg['hw_graph']}{', bỏ suitable_for' if cfg['drop_suitable_for'] else ''}): "
        f"{H.n_nodes:,} nút ({len(H.item_loc):,} item), {H.ei.size(1):,} cạnh, {len(H.rel_names)} quan hệ; "
        f"cạnh xuôi: {H.counts}")
    assert H.n_nodes == CK.H_LOI_N_NODES and len(H.item_loc) == CK.H_LOI_N_ITEMS
    assert H.counts == CK.H_LOI_EXPECTED, "số cạnh H khác log run_probe_cakg_20261014_lan1.log"
    A_ub, has_hu, _ = CK.user_body_matrix(train, item_type, H.item_loc, H.n_nodes)
    lc = CK.lcomp_tensors(H.item_loc)
    M, U = lc[0], lc[1]
    log(f"Người có h_u (có thân trong train có nút trong H): {int(has_hu.sum()):,}; item có h: {len(H.item_loc):,}; "
        f"L_comp: dương {int(M.sum()):,}, âm {int((~M & ~U).sum()):,}, bỏ (U) {int(U.sum()):,}")
    adj = L05B.build_norm_adj(train, C.N_USERS, C.N_ITEMS).to(device)
    m = CK.CaKGRec(adj, H, A_ub, has_hu, lc, dim=cfg["dim"], n_layers=cfg["n_layers"], l2=cfg["l2"],
                   lam1=cfg["lam1"], tau=cfg["tau"]).to(device)
    n_extra = sum(p.numel() for n_, p in m.named_parameters() if not n_.startswith(("user_emb", "item_emb")))
    log(f"CaKG-Rec: {sum(p.numel() for p in m.parameters()):,} tham số, trong đó RGAT + gộp kênh {n_extra:,}")
    return m


def make_cfg(lam1, seed, drop_suitable_for=False, max_epoch=300, eval_every=10, patience=5):
    return {"dim": 64, "n_layers": 3, "lr": 1e-3, "batch": 2048, "l2": 1e-3, "init": "xavier_uniform",
            "hw_graph": "H_loi", "rgat_layers": 2, "rgat_heads": 1, "rgat_attention": "WIRGAT additive",
            "rgat_qk": "per_relation", "rgat_root_weight": True, "rgat_dropout": 0.0, "leaky_slope": 0.2,
            "fusion_hidden": 64, "fusion_gate": "pair", "h_u": "mean of train bodies in H", "tau": 0.2,
            "lam1": lam1, "drop_suitable_for": drop_suitable_for, "seed": seed, "max_epoch": max_epoch,
            "eval_every": eval_every, "patience": patience, "select_metric": "val ndcg@20 full ranking (truoc mat na)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lam1", type=float, required=True, help="λ1, dò {0.01, 0.1, 1.0}; ablation 0")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--drop-suitable-for", action="store_true", help="ablation C8: bỏ quan hệ suitable_for khỏi H")
    ap.add_argument("--max-epoch", type=int, default=300)
    ap.add_argument("--eval-every", type=int, default=10)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--stop-after", type=int, default=None, help="(kiểm thử) dừng sau N epoch như bị ngắt")
    a = ap.parse_args()
    cfg = make_cfg(a.lam1, a.seed, a.drop_suitable_for, a.max_epoch, a.eval_every, a.patience)
    if a.stop_after:
        cfg["_stop_after"] = a.stop_after
    masks = MaskCache()

    def monitor(model, ev):
        fr = E.full_rank(mask_scorer(model.score_fn(), *masks.get(ev)), ev.split, ev.pi)
        r = fr["rank"]
        return {"val_ndcg@20_mask": float(np.where(r <= 20, 1.0 / np.log2(r + 1.0), 0.0).mean())}

    def build(train, log):
        m = build_cakg(cfg, train, log)
        return m, m.parameters()

    T.run("CaKG-Rec", cfg, build, a.run_dir, extra_argv=sys.argv, monitor=monitor,
          final_evals={"val_mask": lambda model, ev: mask_scorer(model.score_fn(), *masks.get(ev))},
          code_files=CODE_FILES)


if __name__ == "__main__":
    main()
