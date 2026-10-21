"""
diag_mismatch.py -- Chẩn đoán các người dùng mà top-10 của dịch vụ lệch thứ tự với top-10 đã lưu lúc chấm test
(check_service.py --stage all). Viết 21/10/2026. Chỉ đọc, không sửa gì.

Với mỗi ca lệch, mỗi cặp sản phẩm đổi chỗ (A, B): in điểm eU[u]·eI[A], eU[u]·eI[B] tính theo 3 cách
  - CPU, một hàng (cách dịch vụ chấm);
  - GPU, một hàng;
  - GPU, lô 1.024 người như eval_05.full_rank lúc chấm test (người xếp tăng dần, lô bắt đầu ở bội của 1.024);
và π (khóa hòa). Ví dụ: u 59388 (seed 1), A = 20741, B = 25355 chênh ~4,8e-7 điểm: một bước làm tròn float32 ở mức ~5,47.

Chạy: ai\\.venv\\Scripts\\python.exe ai/service/diag_mismatch.py --check-dirs results/service/check_all_s1_<nhãn> ... --label <nhãn>
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-dirs", nargs="+", required=True)
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    out = C.RESULTS_DIR / "service" / f"diag_mismatch_{a.label}"
    out.mkdir(parents=True, exist_ok=False)
    log = E.Log(out / f"diag_{E.now_tag()}.log")
    log(f"diag_mismatch | git {E.git_state()} | script sha256 {E.sha256(__file__)}")
    pi = E.tie_keys()
    rows = []
    for d in a.check_dirs:
        s = json.loads((C.ROOT / d / "summary.json").read_text(encoding="utf-8"))
        meta = s["emb_meta"]
        z = np.load(C.ROOT / "results" / "service" / f"emb_s{meta['seed']}_20261021" / "embeddings.npz")
        assert E.sha256(C.ROOT / "results" / "service" / f"emb_s{meta['seed']}_20261021" / "embeddings.npz") == \
            meta["embeddings_sha256"]
        eU, eI = torch.as_tensor(z["eU"]), torch.as_tensor(z["eI"])
        mm = s["all"]["mismatch_users"]
        log(f"\n{d}: seed {meta['seed']}, {len(mm)} người lệch")
        for r in mm:
            u, at, st = r["u"], r["api_top"], r["saved_top"]
            assert sorted(at) == sorted(st), "lệch không phải chỉ đổi thứ tự (tập top-10 khác)"
            start = (u // 1024) * 1024
            ways = {"cpu_1hang": (eU[u:u + 1] @ eI.T)[0],
                    "gpu_1hang": (eU[u:u + 1].to(E.DEVICE) @ eI.T.to(E.DEVICE))[0].cpu(),
                    "gpu_lo1024": (eU[start:start + 1024].to(E.DEVICE) @ eI.T.to(E.DEVICE)).cpu()[u - start]}
            pos = [k for k in range(10) if at[k] != st[k]]
            log(f"  u {u}: vị trí lệch (hạng) {[k + 1 for k in pos]}; API {[at[k] for k in pos]}, đã lưu {[st[k] for k in pos]}")
            items = sorted({at[k] for k in pos})
            for nm, row in ways.items():
                v = {i: float(row[i]) for i in items}
                log(f"    {nm:11s}: " + ", ".join(f"{i}: {v[i]!r}" for i in items)
                    + f" | chênh lớn nhất {max(v.values()) - min(v.values()):.3e}")
            log(f"    π: " + ", ".join(f"{i}: {int(pi[i])}" for i in items))
            rows.append({"seed": meta["seed"], "u": u, "items": items,
                         "scores": {nm: {str(i): float(row[i]) for i in items} for nm, row in ways.items()},
                         "pi": {str(i): int(pi[i]) for i in items}})
    (out / "summary.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {out / 'summary.json'}")
    log.close()


if __name__ == "__main__":
    main()
