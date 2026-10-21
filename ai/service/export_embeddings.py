"""
export_embeddings.py -- Tính sẵn embedding cuối của LightGCN (hệ thống cuối = LightGCN + mặt nạ QĐ 4-9) cho dịch vụ mô
hình (nội dung 10). Viết 21/10/2026. KHÔNG huấn luyện lại: nạp best.pt đã chốt trong ai/config/n5_final.toml (kiểm
sha256), lan truyền 3 lớp đúng như lúc chấm test (eval_cakg.load_lightgcn + 05b LightGCN.propagate), ghi eU, eI ra file.

Ví dụ: seed 1 -> best.pt results/n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1 (sha256 d857e24c…), eU [67.661 x 64],
eI [27.940 x 64]; dịch vụ chỉ cần eU[u] · eIᵀ để chấm 27.940 sản phẩm cho người u, không cần GPU.

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/service/export_embeddings.py --seed 1 --label <nhãn>
Kết quả: results/service/emb_s<seed>_<nhãn>/ (thư mục mới): embeddings.npz, meta.json, log tên mới.
"""

import argparse
import json
import sys
import time
import tomllib
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

N5_TOML = C.ROOT / "ai" / "config" / "n5_final.toml"
OUT_ROOT = C.RESULTS_DIR / "service"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1, choices=[1, 2, 3])
    ap.add_argument("--label", required=True)
    ap.add_argument("--device", default=str(E.DEVICE), help="thiết bị lan truyền (mặc định: cuda nếu có, như lúc chấm test)")
    a = ap.parse_args()
    out_dir = OUT_ROOT / f"emb_s{a.seed}_{a.label}"
    out_dir.mkdir(parents=True, exist_ok=False)
    log = E.Log(out_dir / f"export_{E.now_tag()}.log")
    git = E.git_state()
    log(f"export_embeddings | seed {a.seed} | thiết bị {a.device} | git {git} | script sha256 {E.sha256(__file__)}")
    n5 = tomllib.loads(N5_TOML.read_text(encoding="utf-8"))
    rr = next(r for r in n5["lightgcn"]["runs"] if r["seed"] == a.seed)
    train = C.load_train()
    dev = torch.device(a.device)
    m, cfg, sha = EC.load_lightgcn(C.ROOT / rr["dir"], train, expect_sha=rr["best_pt_sha256"], device=dev)
    log(f"best.pt {rr['dir']} sha256 {sha} (khớp n5_final.toml) | cfg {cfg}")
    t = time.perf_counter()
    with torch.no_grad():
        eU, eI = m.propagate()
    if dev.type == "cuda":
        torch.cuda.synchronize()
    log(f"lan truyền 3 lớp: {(time.perf_counter() - t) * 1000:.1f} ms | eU {tuple(eU.shape)}, eI {tuple(eI.shape)}")
    fn = out_dir / "embeddings.npz"
    np.savez(fn, eU=eU.cpu().numpy(), eI=eI.cpu().numpy())
    meta = {"model": "LightGCN + mặt nạ QĐ 4-9", "seed": a.seed, "run_dir": rr["dir"], "best_pt_sha256": sha,
            "cfg": cfg, "device_propagate": a.device, "n_users": int(eU.shape[0]), "n_items": int(eI.shape[0]),
            "dim": int(eU.shape[1]), "git": git, "torch": torch.__version__, "created": E.now_tag(),
            "embeddings_sha256": E.sha256(fn)}
    assert meta["n_users"] == C.N_USERS and meta["n_items"] == C.N_ITEMS
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {fn} (sha256 {meta['embeddings_sha256']})")
    log.close()


if __name__ == "__main__":
    main()
