"""
07_kgat_train.py -- Huấn luyện baseline KGAT trên train, chấm val (docs/cakg_design.md khối 9; kế hoạch đăng ký trước
docs/reviews/cakg_eval_plan.md mục 4.1). Viết 14/10/2026. Mô hình và các sai khác so với code tác giả: kgat_model.py.
KHÔNG chấm test.

Đồ thị cộng tác: toàn bộ kg_hetero.pt (18 quan hệ, interacted_with = cạnh train), bỏ 134 cạnh ngam_khong_chac mỗi chiều
(05c_rgcn_train.load_homogeneous, dùng lại, không sửa): 95.646 nút, 1.116.682 cạnh.
Cấu hình (kế hoạch mục 4.1): d 64, lớp [64, 32, 16], Bi-Interaction, batch CF 1024 / KG 2048, L2 1e-5 (cả hai pha),
message dropout 0,1, attention tính lại 1 lần / epoch (không gradient) và dùng cho lan truyền epoch sau, Xavier.
Dò trên val (seed 1): lr ∈ {1e-3; 1e-4}. Ngân sách như QĐ 5-5 (300 epoch, chấm NDCG@20 val mỗi 10, dừng sau 5 lần
không tăng).

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/07_kgat_train.py --lr 1e-3 --seed 1 --run-dir results/cakg/<nhãn>/<tên>
Chạy lại đúng lệnh đó sau khi bị ngắt -> chạy tiếp từ lần chấm val gần nhất (Adam của pha KG và π lưu trong last.pt).
"""

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import kgat_model as KM  # noqa: E402
import train_05 as T     # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PIPE = Path(__file__).resolve().parent
L05C = importlib.import_module("05c_rgcn_train")           # load_homogeneous (dùng lại, không sửa)
CODE_FILES = [Path(__file__), PIPE / "kgat_model.py", PIPE / "05c_rgcn_train.py"]
N_EDGES_EXPECTED = 1_116_682


def make_cfg(lr, seed, max_epoch=300, eval_every=10, patience=5):
    return {"dim": 64, "layers": [64, 32, 16], "aggregator": "bi-interaction", "lr": lr, "batch": 1024,
            "batch_kg": 2048, "l2_cf": 1e-5, "l2_kg": 1e-5, "mess_dropout": 0.1, "node_dropout": 0.0,
            "attention": "recomputed once per epoch, no grad, used for propagation next epoch",
            "drop_ngam_khong_chac": True, "init": "xavier_uniform", "pretrain": False, "seed": seed,
            "max_epoch": max_epoch, "eval_every": eval_every, "patience": patience,
            "select_metric": "val ndcg@20 full ranking"}


def build_kgat(cfg, train, log=print, device=E.DEVICE):
    ei, et, names, n, offs = L05C.load_homogeneous(train, log)
    assert ei.size(1) == N_EDGES_EXPECTED and n == 95_646, (ei.size(1), n)
    m = KM.KGAT(n, len(names), ei.to(device), et.to(device), offs["user"], C.N_USERS, offs["item"], C.N_ITEMS,
                dims=(cfg["dim"], *cfg["layers"]), mess_dropout=cfg["mess_dropout"], l2_cf=cfg["l2_cf"],
                l2_kg=cfg["l2_kg"], cf_batch=cfg["batch"], kg_batch=cfg["batch_kg"], lr=cfg["lr"]).to(device)
    log(f"KGAT: {sum(p.numel() for p in m.parameters()):,} tham số; {len(m._heads):,} đầu bộ ba; "
        f"{m.n_kg_batches} batch KG / epoch")
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lr", type=float, required=True, help="dò {1e-3, 1e-4}")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--max-epoch", type=int, default=300)
    ap.add_argument("--eval-every", type=int, default=10)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--stop-after", type=int, default=None, help="(kiểm thử) dừng sau N epoch như bị ngắt")
    a = ap.parse_args()
    cfg = make_cfg(a.lr, a.seed, a.max_epoch, a.eval_every, a.patience)
    if a.stop_after:
        cfg["_stop_after"] = a.stop_after

    def build(train, log):
        m = build_kgat(cfg, train, log)
        return m, m.parameters()

    T.run("KGAT", cfg, build, a.run_dir, extra_argv=sys.argv, code_files=CODE_FILES)


if __name__ == "__main__":
    main()
