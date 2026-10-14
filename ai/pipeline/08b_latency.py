"""
08b_latency.py -- Đo độ trễ một yêu cầu gợi ý và VRAM suy luận của CaKG-Rec (kế hoạch docs/reviews/cakg_eval_plan.md
mục 10). Viết 14/10/2026. Theo kế hoạch: chạy SAU khi chấm test, trên checkpoint chốt seed 1; lúc cài chỉ chạy thử.

Một yêu cầu = điểm 27.940 sản phẩm của 1 người (từ biểu diễn đã tính sẵn) + bỏ item train + mặt nạ (15) QĐ 4-9 + top-10
(torch.topk) + dựng đường và câu giải thích cho các ống trong top-10. Không tính HTTP / FastAPI / Spring Boot.
  - tính sẵn biểu diễn mọi người / sản phẩm một lần (báo thời gian riêng, sau một lần khởi động);
  - 1.000 người chọn ngẫu nhiên (seed 20261014) trong 67.661 người; 50 yêu cầu khởi động không tính;
  - GPU: torch.cuda.synchronize() trước khi bấm giờ và trước khi dừng; đo cả GPU và CPU; p50, p95, p99, max;
  - ghi kèm: GPU, driver, CUDA, torch, RAM trống, đỉnh VRAM lúc đo.

Chạy: ai\\.venv\\Scripts\\python.exe ai/pipeline/08b_latency.py --run-dir results/cakg/<...>/<lần chạy> --label <nhãn>
"""

import argparse
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import psutil
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

X08 = importlib.import_module("08_explain")
SEED = 20261014


def machine():
    info = {"torch": torch.__version__, "cuda": torch.version.cuda,
            "ram_free_mib": round(psutil.virtual_memory().available / 2 ** 20)}
    if torch.cuda.is_available():
        info["gpu"] = torch.cuda.get_device_name(0)
        try:
            info["driver"] = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                                            capture_output=True, text=True).stdout.strip()
        except OSError:
            info["driver"] = None
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--n-users", type=int, default=1000)
    ap.add_argument("--warmup", type=int, default=50)
    a = ap.parse_args()
    out_dir = Path(a.run_dir) / f"latency_{a.label}"
    out_dir.mkdir(parents=True, exist_ok=False)
    log = E.Log(out_dir / f"latency_{E.now_tag()}.log")
    log(f"08b_latency | {a.run_dir} | git {E.git_state()} | máy {machine()}")
    train = C.load_train()
    model, cfg, sha = X08.load_cakg(a.run_dir, train, log=log)
    item_type = C.load_item_type()
    ctx = C.load_cvr_context()
    bodies = C.build_train_bodies(train, None, item_type)
    lens, cmask = E.certain_violation_mask(bodies, ctx)
    H = CK.build_h(drop_suitable_for=cfg["drop_suitable_for"])
    _, _, bodies_h = CK.user_body_matrix(train, item_type, H.item_loc, H.n_nodes)
    pctx = EC.PathContext(train, item_type)

    model.components()                                # khởi động (lần đầu gồm cả khởi tạo CUDA), không tính
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    t = time.perf_counter()
    comps = model.components()
    torch.cuda.synchronize()
    t_pre = time.perf_counter() - t
    log(f"Tính sẵn biểu diễn mọi người / sản phẩm (GPU): {t_pre * 1000:.1f} ms | đỉnh VRAM "
        f"{torch.cuda.max_memory_allocated() / 2 ** 20:.0f} MiB")
    xp = EC.Explainer(comps, H, bodies_h, pctx)
    rng = np.random.default_rng(SEED)
    users = rng.choice(C.N_USERS, a.warmup + a.n_users, replace=False).tolist()
    res = {"best_pt_sha256": sha, "machine": machine(), "precompute_ms_gpu": t_pre * 1000, "n_users": a.n_users,
           "warmup": a.warmup}
    for dev in (E.DEVICE, torch.device("cpu")):
        c = {k: (v.to(dev) if torch.is_tensor(v) else v) for k, v in comps.items()}
        sf = CK.CaKGRec.make_scorer(c, model.hidx.to(dev))
        lt = torch.as_tensor(lens, device=dev)
        cm = torch.as_tensor(cmask, device=dev)
        tr = {u: torch.as_tensor(sorted(train[u]), device=dev) for u in users}
        if dev.type == "cuda":
            torch.cuda.reset_peak_memory_stats()
        times, n_expl = [], 0
        for k, u in enumerate(users):
            if dev.type == "cuda":
                torch.cuda.synchronize()
            t = time.perf_counter()
            uid = torch.as_tensor([u], device=dev)
            s = sf(uid)[0]
            s[tr[u]] = -float("inf")
            s[lt[cm[u]]] = -float("inf")
            top = torch.topk(s, 10).indices.tolist()
            sents = []
            for l in top:
                if item_type[l] == 1 and u in bodies:
                    ex = xp.explain(u, l)
                    if ex is not None:
                        sents.append(EC.sentence(ex, pctx))
            if dev.type == "cuda":
                torch.cuda.synchronize()
            if k >= a.warmup:
                times.append(time.perf_counter() - t)
                n_expl += len(sents)
        ms = np.array(times) * 1000
        st = {f"p{q}": float(np.percentile(ms, q)) for q in (50, 95, 99)}
        st["max"] = float(ms.max())
        st["mean"] = float(ms.mean())
        st["n_sentences"] = n_expl
        if dev.type == "cuda":
            st["peak_vram_allocated_mib"] = torch.cuda.max_memory_allocated() / 2 ** 20
        res[dev.type] = st
        log(f"  {dev.type.upper():4s}: p50 {st['p50']:.2f} ms, p95 {st['p95']:.2f} ms, p99 {st['p99']:.2f} ms, "
            f"max {st['max']:.2f} ms ({a.n_users:,} yêu cầu sau {a.warmup} khởi động; {n_expl:,} câu giải thích)"
            + (f" | đỉnh VRAM {st['peak_vram_allocated_mib']:.0f} MiB" if "peak_vram_allocated_mib" in st else ""))
    (out_dir / "latency.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {out_dir / 'latency.json'}")
    log.close()


if __name__ == "__main__":
    main()
