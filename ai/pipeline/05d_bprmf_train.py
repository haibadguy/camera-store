"""
05d_bprmf_train.py -- BPR-MF (Rendle et al., UAI 2009) bằng CODE NHÓM: đúng lớp LightGCN của 05b_lightgcn_train.py với
K = 0 lớp lan truyền (e = e⁰), cùng loss BPR, cùng hạng L2, cùng vòng huấn luyện train_05 (âm mẫu, chấm val, dừng sớm).
Viết 06/11/2026 theo docs/reviews/v3_eval_plan.md mục 3 và quyết định HỎI 5 của Nam (06/11: số chính là code nhóm;
BPR của RecBole chỉ để đối chiếu). Không sửa 05b (hàng đợi v3 đang dùng).

Ví dụ: u có train {A, B}; mỗi bước lấy cặp (u, A) và 1 âm mẫu C mà u chưa có; ŷ_uA = e_uᵀ e_A với e là embedding gốc
(không lan truyền); loss = −ln σ(ŷ_uA − ŷ_uC) + λ · ½(‖e_u‖² + ‖e_A‖² + ‖e_C‖²) / số cặp trong batch.
Cấu hình (như LightGCN, mục 3): d 64, Xavier, Adam lr 0,001, batch 2048; λ2 dò {1e-5, 1e-4, 1e-3}; trần 1.000 epoch,
chấm NDCG@20 val mỗi 10 epoch, dừng sau 5 lần chấm không tăng.
Chạy (chỉ val, không chấm test):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/05d_bprmf_train.py --l2 1e-4 --seed 1 --run-dir results/<...>/<tên>
"""
import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402
import train_05 as T   # noqa: E402

LG = importlib.import_module("05b_lightgcn_train")
PIPE = Path(__file__).resolve().parent
CODE_FILES = [Path(__file__), PIPE / "05b_lightgcn_train.py"]

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l2", type=float, required=True, help="λ2, dò {1e-5, 1e-4, 1e-3}")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--max-epoch", type=int, default=1000)
    ap.add_argument("--eval-every", type=int, default=10)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--stop-after", type=int, default=None, help="(kiểm thử) dừng sau N epoch như bị ngắt")
    a = ap.parse_args()
    cfg = {"dim": 64, "n_layers": 0, "lr": 1e-3, "batch": 2048, "l2": a.l2, "init": "xavier_uniform",
           "seed": a.seed, "max_epoch": a.max_epoch, "eval_every": a.eval_every, "patience": a.patience,
           "select_metric": "val ndcg@20 full ranking", "impl": "05b LightGCN với n_layers = 0"}
    if a.stop_after:
        cfg["_stop_after"] = a.stop_after

    def build(train, log):
        m = LG.LightGCN(C.N_USERS, C.N_ITEMS, cfg["dim"], 0, None, cfg["l2"]).to(E.DEVICE)   # 0 lớp: không cần ma trận kề
        log(f"BPR-MF = LightGCN 0 lớp: {sum(p.numel() for p in m.parameters()):,} tham số")
        return m, m.parameters()

    T.run("BPR-MF", cfg, build, a.run_dir, extra_argv=sys.argv, code_files=CODE_FILES)


if __name__ == "__main__":
    main()
