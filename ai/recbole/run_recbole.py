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
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "ai" / "data" / "recbole"
DATASET = "camera_loo"

MODEL_CFG = {   # chỉ LightGCN đã chốt (= n5_final.toml); mô hình khác: mặc định yaml của RecBole / RecBole-GNN
    "LightGCN": {"embedding_size": 64, "n_layers": 3, "reg_weight": 1e-3, "require_pow": True},
    # BPR: embedding 64; ItemKNN: k 100, shrink 0; KGIN: d 64, 4 ý định, 2 tầng, node dropout 0,5;
    # SimGCL (RecBole-GNN): 2 lớp, reg 1e-4, lambda 0,5, eps 0,1, τ 0,2. Ghi đè bằng --set khóa=giá_trị_json.
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


def group_mode(a, run_dir, log, config, dataset, train_data, valid_data, model, trainer, chk):
    """v3 (quyết định HỎI 6, 06/11/2026): huấn luyện bằng Trainer của RecBole, nhưng chấm val (chọn checkpoint, dừng
    sớm) bằng bộ chấm của NHÓM (eval_05.full_rank: full ranking, bỏ sản phẩm train, quy tắc hòa π) thay cho bộ chấm
    RecBole (~119 s / lần, mục 7.2 kế hoạch). Không chấm test. Ví dụ: ở epoch 10, 20, ... gọi full_sort_predict của mô
    hình cho mọi người dùng val, đổi cột từ mã RecBole sang mã nhóm, lấy NDCG@20 -> RecBole dùng số này để dừng sớm
    (quy tắc RecBole: bằng điểm tốt nhất vẫn tính là tăng; dừng khi > stopping_step = 4 lần không tăng).
    Chạy tiếp: ở mỗi lần chấm (callback_fn của fit, sau khi RecBole cập nhật tốt nhất + lưu checkpoint) ghi
    last_state.pth = mô hình, Adam, epoch kế tiếp, cur_step, best, đường dẫn checkpoint tốt nhất, lịch sử, trạng thái
    random / numpy / torch / CUDA. Gọi lại đúng lệnh -> nạp last_state.pth, đặt lại các bộ sinh số ngay trước fit.
    Ghi result.json cùng dạng train_05 (history, best_epoch, val = eval_05.evaluate trên checkpoint tốt nhất)."""
    import random

    import numpy as np
    import torch
    from recbole.data.interaction import Interaction

    sys.path.insert(0, str(ROOT / "ai" / "pipeline"))
    import common_05 as C
    import eval_05 as E

    def sync():
        if torch.cuda.is_available():
            torch.cuda.synchronize()

    uf, itf = config["USER_ID_FIELD"], config["ITEM_ID_FIELD"]
    u_tok, i_tok = dataset.field2token_id[uf], dataset.field2token_id[itf]
    dev = config["device"]
    u_map = torch.as_tensor(np.array([u_tok[str(u)] for u in range(C.N_USERS)]), device=dev)
    i_map = torch.as_tensor(np.array([i_tok[str(i)] for i in range(C.N_ITEMS)]), device=dev)
    t = time.time()
    ev = E.EvalContext("val", C.load_train())
    log(f"Bộ chấm nhóm: {len(ev.split.users):,} người val, {C.N_ITEMS:,} sản phẩm ({time.time() - t:.1f}s)")

    @torch.no_grad()
    def score_batch(uids):
        s = model.full_sort_predict(Interaction({uf: u_map[uids.to(dev)]}).to(dev))
        return s.view(len(uids), -1)[:, i_map]

    def ndcg20():
        model.eval()
        fr = E.full_rank(score_batch, ev.split, ev.pi)
        return float(np.where(fr["rank"] <= 20, 1.0 / np.log2(fr["rank"] + 1.0), 0.0).mean())

    def loader_gens(dl, name="train", out=None, depth=0):
        """Bộ sinh số RIÊNG của dataloader RecBole (AbstractDataLoader: torch.Generator seed = config["seed"], dùng để
        xáo thứ tự mỗi epoch), kể cả dataloader con (vd KnowledgeBasedDataLoader). Không nằm trong trạng thái torch
        chung -> phải lưu riêng, không thì chạy tiếp xáo khác (kiểm 06/11: lệch từ epoch 11 khi dừng ở epoch 10)."""
        out = {} if out is None else out
        if isinstance(getattr(dl, "generator", None), torch.Generator):
            out[name] = dl.generator
        if depth < 3:
            for k, v in vars(dl).items():
                if v is not dl and isinstance(getattr(v, "generator", None), torch.Generator):
                    loader_gens(v, f"{name}.{k}", out, depth + 1)
        return out

    gens = loader_gens(train_data)
    assert gens, "không thấy torch.Generator của dataloader train"
    last = run_dir / "last_state.pth"
    hist, best = [], {"epoch": 0, "score": -1.0}
    rng_state = None
    if last.exists():
        ck = torch.load(last, map_location="cpu", weights_only=False)
        model.load_state_dict(ck["state_dict"])
        model.load_other_parameter(ck.get("other_parameter"))
        trainer.optimizer.load_state_dict(ck["optimizer"])
        trainer.start_epoch, trainer.cur_step = ck["start_epoch"], ck["cur_step"]
        trainer.best_valid_score, trainer.saved_model_file = ck["best_valid_score"], ck["saved_model_file"]
        hist, best, rng_state = ck["history"], ck["best"], ck["rng"]
        assert Path(trainer.saved_model_file).exists(), trainer.saved_model_file
        log(f"Chạy tiếp từ last_state.pth: bắt đầu epoch {trainer.start_epoch + 1}, tốt nhất {best['score']:.5f} ở "
            f"epoch {best['epoch']}, {trainer.cur_step} lần chấm không tăng")
    _tr = trainer._train_epoch

    def timed_train(train_data_, epoch_idx, *args, **kw):
        sync(); t0 = time.time(); r = _tr(train_data_, epoch_idx, *args, **kw); sync()
        loss = float(sum(r)) if isinstance(r, tuple) else float(r)
        hist.append({"epoch": epoch_idx + 1, "loss": loss, "sec": round(time.time() - t0, 2)})
        log(f"  epoch {epoch_idx + 1:>4}/{a.epochs} | loss {loss:.5f} | {hist[-1]['sec']:.1f}s")
        return r

    def group_valid(*_args, **_kw):
        sync(); t0 = time.time(); nd = ndcg20(); sync()
        hist[-1].update({"val_ndcg@20": nd, "sec_eval": round(time.time() - t0, 2)})
        if nd >= best["score"]:                                   # đúng quy tắc RecBole (>=) để khớp checkpoint đã lưu
            best.update(epoch=hist[-1]["epoch"], score=nd)
        log(f"  chấm val (bộ chấm nhóm) epoch {hist[-1]['epoch']}: NDCG@20 {nd:.5f} ({hist[-1]['sec_eval']:.1f}s)"
            f"{' *tốt nhất*' if best['epoch'] == hist[-1]['epoch'] else ''}")
        return nd, {"ndcg@20": nd}

    def save_last(epoch_idx, _score):
        st = {"start_epoch": epoch_idx + 1, "cur_step": trainer.cur_step, "best_valid_score": trainer.best_valid_score,
              "saved_model_file": trainer.saved_model_file, "state_dict": model.state_dict(),
              "other_parameter": model.other_parameter(), "optimizer": trainer.optimizer.state_dict(),
              "history": hist, "best": best,
              "rng": {"random": random.getstate(), "numpy": np.random.get_state(), "torch": torch.get_rng_state(),
                      "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
                      "loader_generators": {k: g.get_state() for k, g in gens.items()}}}
        tmp = Path(str(last) + ".tmp")
        torch.save(st, tmp)
        os.replace(tmp, last)
        if a.stop_after_evals and sum("val_ndcg@20" in h for h in hist) >= a.stop_after_evals:
            log(f"Dừng giả lập sau {a.stop_after_evals} lần chấm (kiểm thử chạy tiếp)")
            sys.exit(0)

    trainer._train_epoch, trainer._valid_epoch = timed_train, group_valid
    if rng_state is not None:                                     # đặt lại bộ sinh số ngay trước vòng huấn luyện
        random.setstate(rng_state["random"])
        np.random.set_state(rng_state["numpy"])
        torch.set_rng_state(rng_state["torch"])
        if rng_state["cuda"] is not None and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(rng_state["cuda"])
        assert set(rng_state["loader_generators"]) == set(gens), (list(rng_state["loader_generators"]), list(gens))
        for k, g in gens.items():
            g.set_state(rng_state["loader_generators"][k])
    log(f"Bộ sinh số riêng của dataloader được lưu khi chạy tiếp: {list(gens)}")
    t_fit = time.time()
    trainer.fit(train_data, valid_data, saved=True, show_progress=False, callback_fn=save_last)
    t_fit = time.time() - t_fit
    n_ep = hist[-1]["epoch"]
    stopped = n_ep < a.epochs
    log(f"Kết thúc: {'dừng sớm' if stopped else 'CHẠM TRẦN -> chưa chắc hội tụ'} ở epoch {n_ep}; tốt nhất epoch "
        f"{best['epoch']}, NDCG@20 val {best['score']:.5f}")
    ck = torch.load(trainer.saved_model_file, map_location=dev, weights_only=False)
    model.load_state_dict(ck["state_dict"])
    model.load_other_parameter(ck.get("other_parameter"))
    assert ck["epoch"] + 1 == best["epoch"], (ck["epoch"], best)
    model.eval()
    log("Chấm đầy đủ trên val (bộ chấm nhóm) với checkpoint tốt nhất:")
    res_val = E.evaluate(score_batch, ev, log=log, save_dir=run_dir, prefix="val_")
    secs = [h["sec"] for h in hist]
    out = {"model": a.model, "impl": "RecBole" + (" + RecBole-GNN" if a.gnn else ""), "seed": a.seed,
           "cfg": {k: config[k] for k in ("embedding_size", "learning_rate", "train_batch_size", "epochs", "eval_step",
                                          "stopping_step", "seed") if k in config.final_config_dict},
           "set": a.set, "split": "val", "eval": "bộ chấm nhóm (eval_05), quy tắc dừng RecBole (>=, stopping_step 4)",
           "data_checks": chk, "best_epoch": best["epoch"], "best_val_ndcg@20_during_training": best["score"],
           "epochs_run": n_ep, "stopped_early": stopped, "chua_chac_hoi_tu": not stopped,
           "median_sec_per_epoch": float(np.median(secs)), "sec_fit_this_call": round(t_fit, 1), "history": hist,
           "checkpoint": rel_or_abs(trainer.saved_model_file),
           "git_at_finish": git_state(), "val": res_val}
    log(f"NDCG@20 val chấm lại từ checkpoint: {res_val['full']['ndcg@20']:.5f} (lúc huấn luyện {best['score']:.5f})")
    (run_dir / "result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    log(f"Xong: {run_dir / 'result.json'}")


def rel_or_abs(p):
    """Đường dẫn tính từ thư mục camera-store nếu nằm trong đó, không thì đường dẫn tuyệt đối (vd chạy thử ở thư mục tạm)."""
    p = Path(p).resolve()
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


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
    ap.add_argument("--group-eval", action="store_true",
                    help="v3 (HỎI 6): chấm val trong vòng huấn luyện bằng bộ chấm của nhóm (eval_05, quy tắc hòa π), "
                         "KHÔNG chấm test, lưu trạng thái chạy tiếp last_state.pth ở mỗi lần chấm, result.json cùng "
                         "dạng train_05 (history, val)")
    ap.add_argument("--stop-after-evals", type=int, default=None, help="(kiểm thử chạy tiếp) thoát sau N lần chấm")
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
    patches = []
    try:
        import torch_scatter  # noqa: F401
    except ImportError:       # KGIN (RecBole) cần torch_scatter.scatter_mean; không có bản cho torch 2.14 (06/11)
        import types          # -> thay bằng torch_geometric.utils.scatter(reduce="mean"): cùng phép tính (trung bình
        from torch_geometric.utils import scatter as _pyg_scatter   # theo chỉ số, hàng không có phần tử = 0)
        ts_mod = types.ModuleType("torch_scatter")

        def _scatter_mean(src, index, dim=0, out=None, dim_size=None):
            assert out is None
            return _pyg_scatter(src, index, dim=dim, dim_size=dim_size, reduce="mean")
        ts_mod.scatter_mean = _scatter_mean
        sys.modules["torch_scatter"] = ts_mod
        patches.append("torch_scatter.scatter_mean = torch_geometric.utils.scatter(reduce='mean')")
    if a.gnn:
        try:
            import torch_sparse  # noqa: F401
        except ImportError:   # không có bản torch_sparse cho torch 2.14 (06/11). RecBole-GNN tự lùi về edge_index
            import types      # thường khi thiếu torch_sparse (data/dataset.py), chỉ layers.py import cứng `matmul`
            stub = types.ModuleType("torch_sparse")   # -> module giả: chỉ để import qua; gọi tới là báo lỗi ngay

            def _no_sparse(*_a, **_k):
                raise RuntimeError("torch_sparse chưa cài: chỉ chạy được đường edge_index của RecBole-GNN")
            stub.matmul = _no_sparse
            sys.modules["torch_sparse"] = stub
            patches.append("torch_sparse giả (chỉ matmul báo lỗi); RecBole-GNN dùng edge_index thường")
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
        # KG chỉ phủ sản phẩm máy ảnh (2.972 / 27.940). Chế độ benchmark bỏ qua _data_filtering (không xóa tương tác
        # nào, kiểm bằng assert số dòng bên dưới); .link chỉ chứa item có trong .kg (to_recbole_kg.py) -> item ngoài KG
        # vẫn là thực thể nhưng không có cạnh tri thức.
        cfg.update({"HEAD_ENTITY_ID_FIELD": "head_id", "TAIL_ENTITY_ID_FIELD": "tail_id",
                    "RELATION_ID_FIELD": "relation_id", "ENTITY_ID_FIELD": "entity_id",
                    "kg_reverse_r": False, "entity_kg_num_interval": "[0,inf)",
                    "relation_kg_num_interval": "[0,inf)"})
    config = Config(model=a.model, dataset=DATASET, config_dict=cfg)
    init_seed(config["seed"], config["reproducibility"])
    init_logger(config)
    inputs = {p.name: sha256(p) for p in sorted((DATA / DATASET).glob(f"{DATASET}.*"))}
    meta = {"model": a.model, "seed": a.seed, "probe_epochs": a.probe_epochs, "argv": sys.argv,
            "git": git_state(), "recbole": recbole.__version__, "recbole_gnn_commit": gnn_commit, "patches": patches, "torch": torch.__version__,
            "python": platform.python_version(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "inputs_sha256": inputs, "config": {k: (v if isinstance(v, (int, float, str, bool, list, dict,
                                                                            type(None))) else str(v))
                                                for k, v in config.final_config_dict.items()}}
    cu = run_dir / "config_used.json"
    if cu.exists():                                   # chạy tiếp (--group-eval): không ghi đè bản của lần gọi đầu
        cu = run_dir / f"config_used_{time.strftime('%Y%m%d_%H%M%S')}.json"
    cu.write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    log(f"{a.model} seed {a.seed} | RecBole {recbole.__version__} torch {torch.__version__} | {meta['gpu']} | "
        f"git {meta['git']}")

    t0 = time.time()
    dataset = create_dataset(config)
    train_data, valid_data, test_data = data_preparation(config, dataset)
    uf, itf = config["USER_ID_FIELD"], config["ITEM_ID_FIELD"]
    n_u, n_i = dataset.user_num - 1, dataset.item_num - 1        # trừ [PAD]
    chk = {"n_users": n_u, "n_items": n_i, "n_train": len(train_data._dataset), "n_valid": len(valid_data.dataset),
           "n_test": len(test_data.dataset), "sec_load": round(time.time() - t0, 1)}
    log(f"Dữ liệu: {chk}")
    assert (n_u, n_i, chk["n_train"], chk["n_valid"], chk["n_test"]) == (67661, 27940, 460193, 67661, 67661), chk

    model = get_model(config["model"])(config, train_data._dataset).to(config["device"])
    trainer = get_trainer(config["MODEL_TYPE"], config["model"])(config, model)
    if a.group_eval:
        assert not probe, "--group-eval không dùng với --probe-epochs"
        return group_mode(a, run_dir, log, config, dataset, train_data, valid_data, model, trainer, chk)
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
        res["checkpoint"] = rel_or_abs(trainer.saved_model_file)
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
