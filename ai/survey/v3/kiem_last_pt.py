"""
kiem_last_pt.py — kiểm last.pt của các lần chạy cũ chạm trần 300 epoch có đủ trạng thái để CHẠY TIẾP đúng nghĩa
(điều kiện Nam đặt 06/11 cho PA2, docs/reviews/v3_eval_plan.md mục 12, HỎI 2 + 4). Viết 06/11/2026. Chỉ đọc.

Một lần chạy ĐẠT khi:
  1. last.pt có đủ khóa: model, opt, np_rng, torch_rng, cuda_rng, state (KGAT thêm aux = Adam pha TransR);
  2. opt (Adam) có trạng thái cho MỌI tham số: exp_avg, exp_avg_sq, step; step = số bước đã học (kiểm bằng số batch / epoch
     × số epoch); lr trong param_groups = lr của cấu hình;
  3. np_rng là trạng thái PCG64 của numpy; torch_rng là ByteTensor; cuda_rng là danh sách ByteTensor (chạy trên GPU);
  4. state: epoch = epochs_run của result.json = max_epoch (300), chưa dừng sớm, best / best_epoch khớp result.json,
     history đủ 300 dòng; best.pt có epoch = best_epoch;
  5. code: sha256 hiện tại của các file code ghi trong config.json (code_sha256, nếu có) trùng; và git diff giữa commit
     của lần chạy và HEAD không đổi file mô hình (danh sách theo mô hình, bên dưới).
Không đạt thì lần đó phải CHẠY LẠI TỪ ĐẦU (điều kiện của Nam).

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/v3/kiem_last_pt.py <nhãn>
Ghi: results/v3/kiem_last_pt_<nhãn>.json (lên git) và in ra màn hình.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
R = ROOT / "results"
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Các lần chạy PA2 có thể chạy tiếp (đã chạm 300, theo quyết định 06/11: LightGCN λ2 1e-3, CaKG-Rec v2 A, KGAT lr 1e-4)
RUNS = {
    "LightGCN": ["n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1", "n5/final_20261009/lightgcn_l2-1e-03_s2",
                 "n5/final_20261009/lightgcn_l2-1e-03_s3"],
    "CaKG-Rec": ["cakg/val_sweep_v2_20261016/val_v2_A_lens_gate_s1",
                 "cakg/val_sweep_v2seeds_20261016/val_v2_A_lens_gate_s2",
                 "cakg/val_sweep_v2seeds_20261016/val_v2_A_lens_gate_s3"],
    "KGAT": ["cakg/val_sweep_20261014/val_kgat_lr-1e-04_s1"],
}
# File code quyết định quá trình học của từng mô hình (git diff commit-lần-chạy..HEAD phải rỗng)
MODEL_FILES = {
    "LightGCN": ["ai/pipeline/05b_lightgcn_train.py", "ai/pipeline/common_05.py", "ai/pipeline/eval_05.py"],
    "CaKG-Rec": ["ai/pipeline/06_cakg_train.py", "ai/pipeline/cakg_model.py", "ai/pipeline/rgat_layer.py",
                 "ai/pipeline/05b_lightgcn_train.py", "ai/pipeline/common_05.py", "ai/pipeline/eval_05.py",
                 "ai/pipeline/eval_cakg.py", "ai/pipeline/train_05.py"],
    "KGAT": ["ai/pipeline/07_kgat_train.py", "ai/pipeline/kgat_model.py", "ai/pipeline/05c_rgcn_train.py",
             "ai/pipeline/common_05.py", "ai/pipeline/eval_05.py", "ai/pipeline/train_05.py"],
}
N_TRAIN = 460193


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def check(model, rel):
    d = R / rel
    cfgj = json.loads((d / "config.json").read_text(encoding="utf-8"))
    res = json.loads((d / "result.json").read_text(encoding="utf-8"))
    cfg = cfgj["cfg"]
    ck = torch.load(d / "last.pt", map_location="cpu", weights_only=False)
    bp = torch.load(d / "best.pt", map_location="cpu", weights_only=False)
    out, bad = {"run": rel, "model": model}, []

    need = ["model", "opt", "np_rng", "torch_rng", "cuda_rng", "state"] + (["aux"] if model == "KGAT" else [])
    out["keys"] = sorted(ck)
    bad += [f"thiếu khóa {k}" for k in need if k not in ck]

    # Adam
    opt = ck.get("opt", {})
    n_params = sum(len(g["params"]) for g in opt.get("param_groups", []))
    stt = opt.get("state", {})
    steps = set()
    for k, v in stt.items():
        if not {"exp_avg", "exp_avg_sq", "step"} <= set(v):
            bad.append(f"Adam: tham số {k} thiếu exp_avg / exp_avg_sq / step")
        steps.add(int(v["step"]) if "step" in v else -1)
    out["adam"] = {"n_params": n_params, "n_state": len(stt), "steps": sorted(steps),
                   "lr": sorted({g["lr"] for g in opt.get("param_groups", [])})}
    names = list(ck["model"].keys())
    pnames = [n for n in names if n != "pi"] if model == "KGAT" else None   # KGAT: pi là buffer, không phải tham số
    missing = sorted(set(range(n_params)) - set(stt))
    out["adam"]["thieu_trang_thai"] = [pnames[i] if pnames else i for i in missing]
    if model == "KGAT":
        # Er, Wr chỉ có trong loss TransR (pha KG, Adam riêng kg_opt) -> Adam pha CF không bao giờ có trạng thái cho
        # chúng; chạy mới từ đầu cũng vậy. Chấp nhận đúng 2 tham số này.
        if out["adam"]["thieu_trang_thai"] != ["Er", "Wr"]:
            bad.append(f"Adam CF thiếu trạng thái: {out['adam']['thieu_trang_thai']} (chỉ chấp nhận Er, Wr)")
    elif missing or n_params == 0:
        bad.append(f"Adam: {len(stt)} trạng thái cho {n_params} tham số")
    if out["adam"]["lr"] != [cfg["lr"]]:
        bad.append(f"Adam lr {out['adam']['lr']} ≠ cấu hình {cfg['lr']}")
    nb = -(-N_TRAIN // cfg["batch"])          # số batch / epoch (ceil)
    exp_steps = nb * cfg["max_epoch"]
    out["adam"]["steps_mong_doi"] = exp_steps
    if model != "CaKG-Rec" and steps != {exp_steps}:
        # CaKG-Rec: có tham số chỉ nhận gradient ở một số batch? -> chỉ ghi, không đánh trượt (xem steps)
        bad.append(f"Adam step {sorted(steps)} ≠ {nb} batch × {cfg['max_epoch']} epoch = {exp_steps}")
    if model == "CaKG-Rec" and max(steps) != exp_steps:
        bad.append(f"Adam step lớn nhất {max(steps)} ≠ {exp_steps}")

    # RNG
    nr = ck.get("np_rng")
    out["np_rng"] = nr.get("bit_generator") if isinstance(nr, dict) else str(type(nr))
    if not (isinstance(nr, dict) and nr.get("bit_generator") == "PCG64"):
        bad.append("np_rng không phải trạng thái PCG64")
    tr = ck.get("torch_rng")
    if not (isinstance(tr, torch.Tensor) and tr.dtype == torch.uint8 and tr.numel() > 0):
        bad.append("torch_rng không hợp lệ")
    cr = ck.get("cuda_rng")
    out["cuda_rng_n"] = len(cr) if isinstance(cr, (list, tuple)) else None
    if not (isinstance(cr, (list, tuple)) and len(cr) >= 1 and all(isinstance(x, torch.Tensor) for x in cr)):
        bad.append("cuda_rng thiếu (lần chạy cũ không ở GPU?)")
    if model == "KGAT":
        aux = ck.get("aux")
        out["aux_keys"] = sorted(aux) if isinstance(aux, dict) else None
        if not aux:
            bad.append("KGAT: aux (Adam pha TransR) rỗng")
        else:
            ks = aux["kg_opt"]["state"]
            kst = {pnames[i]: int(v["step"]) for i, v in ks.items()}
            out["kg_opt"] = kst
            if sorted(kst) != ["E", "Er", "Wr"] or len(set(kst.values())) != 1 or next(iter(kst.values())) % 300:
                bad.append(f"KGAT: kg_opt trạng thái {kst} (mong đợi E, Er, Wr cùng step, chia hết 300 epoch)")

    # trạng thái huấn luyện
    s = ck.get("state", {})
    out["state"] = {k: s.get(k) for k in ("epoch", "best", "best_epoch", "bad", "stopped")}
    out["state"]["n_history"] = len(s.get("history", []))
    if not (s.get("epoch") == res["epochs_run"] == cfg["max_epoch"] == 300):
        bad.append(f"epoch last.pt {s.get('epoch')} / result {res['epochs_run']} / max {cfg['max_epoch']}")
    if s.get("stopped") or res["stopped_early"]:
        bad.append("đã dừng sớm (không cần chạy tiếp)")
    if not (s.get("best_epoch") == res["best_epoch"] and abs(s.get("best", -1) - res["best_val_ndcg@20_during_training"]) < 1e-12):
        bad.append("best / best_epoch của last.pt khác result.json")
    if out["state"]["n_history"] != 300:
        bad.append(f"history {out['state']['n_history']} dòng")
    if bp.get("epoch") != res["best_epoch"]:
        bad.append(f"best.pt epoch {bp.get('epoch')} ≠ best_epoch {res['best_epoch']}")
    if set(bp["model"]) != set(ck["model"]):
        bad.append("best.pt và last.pt khác tập tham số")

    # code
    cur = {}
    for name, h in (cfgj.get("code_sha256") or {}).items():      # code (ai/pipeline) và file KG đầu vào (ai/data/kg)
        p = next((q for q in (ROOT / "ai" / "pipeline" / name, ROOT / "ai" / "data" / "kg" / name) if q.exists()), None)
        if p is None:
            cur[name] = "không thấy file"
            continue
        b = p.read_bytes()
        lf = b.replace(b"\r\n", b"\n")
        cur[name] = ("trùng" if hashlib.sha256(b).hexdigest() == h else
                     "trùng (chỉ khác ký tự xuống dòng CRLF/LF)" if h in (hashlib.sha256(lf).hexdigest(),
                                                                          hashlib.sha256(lf.replace(b"\n", b"\r\n")).hexdigest())
                     else "KHÁC")
    out["code_sha256"] = cur
    bad += [f"{n}: {v}" for n, v in cur.items() if not v.startswith("trùng")]
    c0 = cfgj["git"]["commit"]
    changed = [f for f in git("diff", "--name-only", c0, "HEAD", "--", *MODEL_FILES[model]).splitlines() if f]
    out["git_run"] = cfgj["git"]
    out["file_doi_tu_lan_chay"] = changed
    tv = [f for f in changed if not f.endswith("train_05.py")]
    bad += [f"file mô hình đổi từ {c0[:7]}: {f}" for f in tv]
    if cfgj["git"].get("dirty"):
        bad.append("lần chạy cũ chạy trên cây git bẩn")
    out["last_pt_sha256"] = sha256(d / "last.pt")
    out["best_pt_sha256"] = sha256(d / "best.pt")
    out["loi"] = bad
    out["dat"] = not bad
    return out


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "lan1"
    outp = R / "v3" / f"kiem_last_pt_{tag}.json"
    assert not outp.exists(), f"đã có, không ghi đè: {outp}"
    outp.parent.mkdir(parents=True, exist_ok=True)
    rows = [check(m, r) for m, rs in RUNS.items() for r in rs]
    for o in rows:
        print(f"{'ĐẠT ' if o['dat'] else 'TRƯỢT'} {o['run']}: Adam {o['adam']['n_state']}/{o['adam']['n_params']} tham số, "
              f"step {o['adam']['steps']} (mong đợi {o['adam']['steps_mong_doi']}), lr {o['adam']['lr']}; np_rng "
              f"{o['np_rng']}; cuda_rng {o['cuda_rng_n']}; state {o['state']}"
              + (f"; aux {o['aux_keys']}" if 'aux_keys' in o else "")
              + f"; file đổi từ lần chạy: {o['file_doi_tu_lan_chay'] or 'không'}")
        for b in o["loi"]:
            print(f"      - {b}")
    js = {"head": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain", "--untracked-files=no")),
          "torch": torch.__version__, "numpy": np.__version__, "runs": rows}
    outp.write_text(json.dumps(js, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"-> {outp}  | ĐẠT {sum(o['dat'] for o in rows)}/{len(rows)}")


if __name__ == "__main__":
    main()
