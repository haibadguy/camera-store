"""
run_recbole.py — chạy một mô hình của RecBole 1.2.1 trên ĐÚNG cách chia của nhóm (file benchmark do to_recbole.py
sinh ra), xếp hạng toàn bộ, ghi log / kết quả vào một thư mục chạy riêng. Viết 06/11/2026 (nhận xét cô 06/11, A3;
docs/reviews/v3_eval_plan.md mục RecBole).

CHẠY BẰNG VENV RIÊNG E:\\DATN\\venvs\\recbole (không phải ai/.venv; xem ai/recbole/README.md):
  E:\\DATN\\venvs\\recbole\\Scripts\\python.exe ai/recbole/run_recbole.py --model LightGCN --seed 1 \\
      --run-dir results/recbole/<nhãn>/<tên> [--epochs 300] [--probe-epochs N]

Giao thức (khớp n5_eval_plan mục 3, 7.1; chỗ khác ghi ở README và v3_eval_plan):
  - train / valid / test = 3 file benchmark (không để RecBole tự chia); không lọc người / sản phẩm;
  - xếp hạng toàn bộ (eval_args.mode = full); RecBole tự bỏ sản phẩm đã có: chấm valid bỏ train, chấm test bỏ
    train + valid (giống QĐ 5-1);
  - chọn checkpoint theo NDCG@20 valid, chấm mỗi 10 epoch, dừng khi 5 lần chấm liên tiếp không tăng
    (RecBole dừng khi số lần không tăng > stopping_step, nên stopping_step = 4);
  - LightGCN: d 64, 3 lớp, Adam lr 1e-3, batch 2048, reg_weight = λ = 1e-3 với require_pow = True
    (= λ · ½ Σ‖e⁰‖² / batch, đúng công thức 05b), 1 âm mẫu đều / cặp train.
--probe-epochs N: chỉ đo thời gian (N epoch, không chấm giữa chừng, chấm valid 1 lần để đo giây / lần chấm,
không chấm test) — dùng để ước tính giờ GPU, không phải kết quả.

Ghi ra run-dir: config_used.json (cấu hình RecBole đầy đủ + phiên bản + sha256 đầu vào + git), recbole.log (log
gốc của RecBole), run_<thời điểm>.log, result.json (giây / epoch, đường NDCG@20 valid, số valid / test của
RecBole), và với LightGCN: emb_best.npz (embedding sau lan truyền của checkpoint tốt nhất, sắp theo mã của nhóm)
để chấm lại bằng bộ chấm của nhóm (ai/recbole/cross_eval.py, chạy bằng ai/.venv).
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "ai" / "data" / "recbole"
DATASET = "camera_loo"

MODEL_CFG = {   # siêu tham số theo mô hình; chỉ LightGCN đã chốt (= n5_final.toml), còn lại là mặc định để đo giờ
    "LightGCN": {"embedding_size": 64, "n_layers": 3, "reg_weight": 1e-3, "require_pow": True},
    "BPR": {"embedding_size": 64},
    "ItemKNN": {"k": 100, "shrink": 0.0},
    "KGIN": {"embedding_size": 64, "n_factors": 4, "context_hops": 3, "node_dropout_rate": 0.5,
             "mess_dropout_rate": 0.1, "sim_regularity": 1e-4, "reg_weight": 1e-5, "ind": "distance",
             "temperature": 0.2},
    "SimGCL": {"embedding_size": 64, "n_layers": 2, "reg_weight": 1e-4, "lambda": 0.5, "eps": 0.1,
               "temperature": 0.2},
    "KGAT": {"embedding_size": 64, "kg_embedding_size": 64, "layers": [64, 32, 16], "mess_dropout": 0.1,
             "reg_weight": 1e-5, "aggregator_type": "bi"},
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_state():
    def run(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"commit": run("rev-parse", "HEAD"), "dirty": bool(run("status", "--porcelain", "--untracked-files=no"))}


class Log:
    def __init__(self, path):
        assert not Path(path).exists(), f"log đã có, không ghi đè: {path}"
        self.f = open(path, "w", encoding="utf-8")

    def __call__(self, msg):
        print(msg, flush=True)
        self.f.write(msg + "\n")
        self.f.flush()


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--probe-epochs", type=int, default=None)
    ap.add_argument("--set", action="append", default=[], help="ghi đè siêu tham số, dạng khóa=giá_trị_json")
    ap.add_argument("--gnn", default=None, help="thư mục mã nguồn RecBole-GNN (clone, không phải gói pip) -> dùng "
                    "Config / dataset / mô hình của RecBole-GNN (SimGCL, XSimGCL, ...)")
    a = ap.parse_args()
    run_dir = (ROOT / a.run_dir).resolve()
    assert not (run_dir / "result.json").exists(), f"đã có kết quả, không chạy đè: {run_dir}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log = Log(run_dir / f"run_{time.strftime('%Y%m%d_%H%M%S')}.log")

    import torch
    _orig_load = torch.load

    def _load(*args, **kw):          # RecBole 1.2.1 lưu cả đối tượng Config trong checkpoint; torch >= 2.6 mặc định
        kw.setdefault("weights_only", False)   # weights_only=True nên không nạp lại được -> tắt (file do chính ta ghi)
        return _orig_load(*args, **kw)
    torch.load = _load

    import recbole
    from recbole.utils import init_logger, init_seed
    gnn_commit = None
    if a.gnn:
        sys.path.insert(0, str(Path(a.gnn).resolve()))
        from recbole_gnn.config import Config
        from recbole_gnn.utils import create_dataset, data_preparation, get_model, get_trainer
        gnn_commit = subprocess.run(["git", "-C", a.gnn, "rev-parse", "HEAD"], capture_output=True,
                                    text=True).stdout.strip()
    else:
        from recbole.config import Config
        from recbole.data import create_dataset, data_preparation
        from recbole.utils import get_model, get_trainer

    probe = a.probe_epochs is not None
    mcfg = dict(MODEL_CFG.get(a.model, {}))
    for kv in a.set:
        k, v = kv.split("=", 1)
        mcfg[k] = json.loads(v)
    is_kg = a.model in ("KGIN", "KGAT", "CKE", "CFKG", "KGCN", "KGNNLS", "MCCLK", "RippleNet", "KTUP", "MKR")
    load_col = {"inter": ["user_id", "item_id"]}
    if is_kg:
        load_col.update({"kg": ["head_id", "relation_id", "tail_id"], "link": ["item_id", "entity_id"]})
    cfg = {
        "data_path": str(DATA), "benchmark_filename": ["train", "valid", "test"],
        "USER_ID_FIELD": "user_id", "ITEM_ID_FIELD": "item_id", "TIME_FIELD": None, "RATING_FIELD": None,
        "load_col": load_col,
        "user_inter_num_interval": "[0,inf)", "item_inter_num_interval": "[0,inf)", "rm_dup_inter": None,
        "filter_inter_by_user_or_item": False,
        "eval_args": {"group_by": "user", "order": "RO", "split": {"RS": [0.8, 0.1, 0.1]}, "mode": "full"},
        "metrics": ["Recall", "NDCG", "Hit"], "topk": [5, 10, 20], "valid_metric": "NDCG@20",
        "metric_decimal_place": 8, "eval_batch_size": 4096,
        "epochs": a.probe_epochs if probe else a.epochs, "train_batch_size": 2048, "learner": "adam",
        "learning_rate": 1e-3, "train_neg_sample_args": {"distribution": "uniform", "sample_num": 1,
                                                         "dynamic": False, "candidate_num": 0},
        "eval_step": 10 ** 6 if probe else 10, "stopping_step": 4,
        "seed": a.seed, "reproducibility": True, "device": "cuda" if torch.cuda.is_available() else "cpu",
        "checkpoint_dir": str(run_dir / "ckpt"), "log_root": str(run_dir / "recbole_log") + "/",
        "show_progress": False, "save_dataset": False, "save_dataloaders": False, "log_wandb": False,
        **mcfg,
    }
    if is_kg:
        cfg.update({"HEAD_ENTITY_ID_FIELD": "head_id", "TAIL_ENTITY_ID_FIELD": "tail_id",
                    "RELATION_ID_FIELD": "relation_id", "ENTITY_ID_FIELD": "entity_id",
                    "kg_reverse_r": False, "entity_kg_num_interval": "[0,inf)",
                    "relation_kg_num_interval": "[0,inf)"})
    config = Config(model=a.model, dataset=DATASET, config_dict=cfg)
    init_seed(config["seed"], config["reproducibility"])
    init_logger(config)
    inputs = {p.name: sha256(p) for p in sorted((DATA / DATASET).glob(f"{DATASET}.*"))}
    meta = {"model": a.model, "seed": a.seed, "probe_epochs": a.probe_epochs, "argv": sys.argv,
            "git": git_state(), "recbole": recbole.__version__, "recbole_gnn_commit": gnn_commit, "torch": torch.__version__,
            "python": platform.python_version(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "inputs_sha256": inputs, "config": {k: (v if isinstance(v, (int, float, str, bool, list, dict,
                                                                            type(None))) else str(v))
                                                for k, v in config.final_config_dict.items()}}
    (run_dir / "config_used.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str),
                                              encoding="utf-8")
    log(f"{a.model} seed {a.seed} | RecBole {recbole.__version__} torch {torch.__version__} | {meta['gpu']} | "
        f"git {meta['git']}")

    t0 = time.time()
    dataset = create_dataset(config)
    train_data, valid_data, test_data = data_preparation(config, dataset)
    uf, itf = config["USER_ID_FIELD"], config["ITEM_ID_FIELD"]
    n_u, n_i = dataset.user_num - 1, dataset.item_num - 1        # trừ [PAD]
    chk = {"n_users": n_u, "n_items": n_i, "n_train": len(train_data.dataset), "n_valid": len(valid_data.dataset),
           "n_test": len(test_data.dataset), "sec_load": round(time.time() - t0, 1)}
    log(f"Dữ liệu: {chk}")
    assert (n_u, n_i, chk["n_train"], chk["n_valid"], chk["n_test"]) == (67661, 27940, 460193, 67661, 67661), chk

    model = get_model(config["model"])(config, train_data._dataset).to(config["device"])
    trainer = get_trainer(config["MODEL_TYPE"], config["model"])(config, model)
    ep_sec, ev_sec, curve = [], [], []
    _tr, _va = trainer._train_epoch, trainer._valid_epoch

    def sync():
        if torch.cuda.is_available():
            torch.cuda.synchronize()

    def timed_train(*args, **kw):
        sync(); t = time.time(); r = _tr(*args, **kw); sync()
        ep_sec.append(round(time.time() - t, 3))
        log(f"  epoch {len(ep_sec)} | {ep_sec[-1]:.2f}s | loss {r if not isinstance(r, tuple) else tuple(map(float, r))}")
        return r

    def timed_valid(*args, **kw):
        sync(); t = time.time(); r = _va(*args, **kw); sync()
        ev_sec.append(round(time.time() - t, 3))
        curve.append({"epoch": len(ep_sec), "valid_ndcg@20": float(r[0]), "sec_eval": ev_sec[-1]})
        log(f"  chấm valid ở epoch {len(ep_sec)}: NDCG@20 {float(r[0]):.6f} ({ev_sec[-1]:.1f}s)")
        return r
    trainer._train_epoch, trainer._valid_epoch = timed_train, timed_valid
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    t_fit = time.time()
    trainer.fit(train_data, None if probe else valid_data, saved=not probe, show_progress=False)
    t_fit = time.time() - t_fit
    res = {"model": a.model, "seed": a.seed, "data_checks": chk, "epochs_run": len(ep_sec), "sec_per_epoch": ep_sec,
           "median_sec_per_epoch": sorted(ep_sec)[len(ep_sec) // 2] if ep_sec else None,
           "sec_fit_total": round(t_fit, 1),
           "peak_vram_mib": round(torch.cuda.max_memory_allocated() / 2 ** 20, 1) if torch.cuda.is_available() else None}
    if probe:
        sync(); t = time.time()
        vr = trainer.evaluate(valid_data, load_best_model=False, show_progress=False); sync()
        res.update(probe=True, sec_one_valid_eval=round(time.time() - t, 2),
                   note="chỉ đo thời gian, không phải kết quả (mô hình chưa huấn luyện xong)")
        log(f"Đo thời gian: trung vị {res['median_sec_per_epoch']}s / epoch, một lần chấm valid "
            f"{res['sec_one_valid_eval']}s")
    else:
        res["curve"] = curve
        res["best_epoch"] = max(curve, key=lambda c: c["valid_ndcg@20"])["epoch"] if curve else None
        res["stopped_early"] = len(ep_sec) < a.epochs
        res["chua_chac_hoi_tu"] = not res["stopped_early"]
        vr = trainer.evaluate(valid_data, load_best_model=True, show_progress=False)
        tr = trainer.evaluate(test_data, load_best_model=True, show_progress=False)
        res["valid_recbole"] = {k: float(v) for k, v in vr.items()}
        res["test_recbole"] = {k: float(v) for k, v in tr.items()}
        res["checkpoint"] = str(Path(trainer.saved_model_file).relative_to(ROOT)).replace("\\", "/")
        log(f"valid (RecBole): {res['valid_recbole']}")
        log(f"test  (RecBole): {res['test_recbole']}")
        if a.model == "LightGCN":                           # embedding của checkpoint tốt nhất, theo mã của nhóm
            model.eval()
            with torch.no_grad():
                ue, ie = model.forward()
            import numpy as np
            u_tok = dataset.field2token_id[uf]
            i_tok = dataset.field2token_id[itf]
            u_idx = np.array([u_tok[str(u)] for u in range(n_u)])
            i_idx = np.array([i_tok[str(i)] for i in range(n_i)])
            np.savez(run_dir / "emb_best.npz", user=ue.cpu().numpy()[u_idx], item=ie.cpu().numpy()[i_idx])
            res["emb_best_sha256"] = sha256(run_dir / "emb_best.npz")
    res["git_at_finish"] = git_state()
    (run_dir / "result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Xong: {run_dir / 'result.json'}")


if __name__ == "__main__":
    main()
