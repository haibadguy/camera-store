"""
06_val_sweep.py -- Dò siêu tham số trên val, seed 1, cho mô hình mới của nội dung 6–8 (docs/reviews/cakg_eval_plan.md
mục 4.1, 4.2 bước 3). Viết 14/10/2026 theo khuôn 05_val_sweep.py. KHÔNG chấm test.

Nhóm lần chạy (--group):
  cakg: CaKG-Rec λ1 ∈ {0,01; 0,1; 1,0}  (06_cakg_train.py; tối đa 300 epoch, chấm val mỗi 10 epoch, dừng sau 5 lần
        chấm không tăng). Chỉ số chọn: NDCG@20 full ranking val TRƯỚC mặt nạ (QĐ 5-6).
  kgat: KGAT lr ∈ {1e-3; 1e-4} (07_kgat_train.py; cùng ngân sách). Chỉ số chọn: NDCG@20 full ranking val.
Thêm 15/10/2026 (kế hoạch mục 4.2 bước 5), tham số đọc từ ai/config/cakg_final.toml (đã commit trước khi chạy):
  final:    CaKG-Rec và KGAT cấu hình chốt, seed 2, 3 (4 lần chạy);
  ablation: CaKG-Rec λ1 = 0 và CaKG-Rec bỏ suitable_for, seed 1 (2 lần chạy; kế hoạch mục 6).
  Hai nhóm này ghi vào results/cakg/final_<nhãn>/ (nhãn phải khớp final_dir của toml); cuối cùng kiểm cfg = cfg chốt
  (trừ seed và phần ablation) và sha256 code + đầu vào = lần chạy seed 1 cùng mô hình. Không chọn "tốt nhất".
Mỗi lần chạy là một tiến trình con ghi vào results/cakg/val_sweep_<nhãn>/<tên lần chạy>/ với log riêng
train_<thời điểm>.log. Log của chính script này: sweep_<nhóm>_<thời điểm>.log (tên mới mỗi lần gọi).

Chạy tiếp: bị ngắt (Ctrl+C, mất điện, máy ngủ...) thì gõ lại ĐÚNG lệnh cũ (cùng --group, --label):
  - lần chạy đã có result.json: bỏ qua;
  - lần chạy dở: tiếp từ lần chấm val gần nhất (last.pt);
  - lần chạy chưa bắt đầu: chạy mới.
Cuối cùng in bảng NDCG@20 val (trước / sau mặt nạ), cấu hình tốt nhất, cờ "ở biên lưới", và kiểm mọi lần chạy cùng
sha256 code + đầu vào (config.json). KHÔNG ghi cakg_final.toml (bước 4 của kế hoạch do Nam chốt và commit).

Thêm 16/10/2026 (docs/reviews/cakg_v2_plan.md): nhóm v2 = CaKG-Rec v2, 3 biến thể (A lens_gate, B loo_hu,
C body_hardneg), λ1 = 0,1, seed 1, ghi vào results/cakg/val_sweep_<nhãn>/ (nhãn nên bắt đầu bằng "v2_"). Chọn biến thể
và điều kiện DỪNG ở 06v2_select.py.

Thêm 16/10/2026 chiều (kế hoạch v2 mục 4.3): nhóm v2seeds = seed 2, 3 của biến thể 06v2_select.py đã chọn
(--select-dir <thư mục select_...>), đúng tham số của lần chạy seed 1; cuối cùng kiểm cfg trừ seed và sha256 code +
đầu vào = lần chạy seed 1. Kiểm DỪNG 2: 06v2_dung2.py.

Lệnh (PowerShell, từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/06_val_sweep.py --group cakg --label 20261014
"""

import argparse
import json
import tomllib
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PIPE = Path(__file__).resolve().parent
OUT_DIR = C.RESULTS_DIR / "cakg"
GROUPS = {  # nhóm -> (tên tham số dò, [(tên lần chạy, script, tham số riêng, giá trị dò)])
    "cakg": ("lam1", [
        ("val_cakg_lam1-1e-02_s1", "06_cakg_train.py", ["--lam1", "0.01", "--seed", "1"], 0.01),
        ("val_cakg_lam1-1e-01_s1", "06_cakg_train.py", ["--lam1", "0.1", "--seed", "1"], 0.1),
        ("val_cakg_lam1-1e+00_s1", "06_cakg_train.py", ["--lam1", "1.0", "--seed", "1"], 1.0),
    ]),
    "kgat": ("lr", [
        ("val_kgat_lr-1e-03_s1", "07_kgat_train.py", ["--lr", "1e-3", "--seed", "1"], 1e-3),
        ("val_kgat_lr-1e-04_s1", "07_kgat_train.py", ["--lr", "1e-4", "--seed", "1"], 1e-4),
    ]),
    # CaKG-Rec v2 (docs/reviews/cakg_v2_plan.md, thêm 16/10/2026): 3 biến thể, λ1 = 0,1 (cấu hình chốt v1), seed 1.
    # Chọn biến thể / điều kiện DỪNG: 06v2_select.py (KHÔNG theo dòng "tốt nhất" của script này).
    "v2": ("variant", [
        ("val_v2_A_lens_gate_s1", "06_cakg_train.py", ["--lam1", "0.1", "--seed", "1", "--variant", "lens_gate"],
         "lens_gate"),
        ("val_v2_B_loo_hu_s1", "06_cakg_train.py", ["--lam1", "0.1", "--seed", "1", "--variant", "loo_hu"], "loo_hu"),
        ("val_v2_C_body_hardneg_s1", "06_cakg_train.py", ["--lam1", "0.1", "--seed", "1", "--variant", "body_hardneg"],
         "body_hardneg"),
    ]),
}


FINAL_TOML = C.ROOT / "ai" / "config" / "cakg_final.toml"


def v2seeds_runs(select_dir):
    """CaKG-Rec v2, kế hoạch mục 4.3 (thêm 16/10/2026): seed 2, 3 của biến thể mà 06v2_select.py đã chọn
    (select.json["decision"]["chosen"]), ĐÚNG tham số của lần chạy seed 1 trong nhóm v2, chỉ đổi --seed.
    Trả về (select.json, thư mục lần chạy seed 1, [(tên, script, tham số, biến thể)])."""
    sel = json.loads((Path(select_dir) / "select.json").read_text(encoding="utf-8"))
    v = sel["decision"]["chosen"]
    assert v is not None and not sel["decision"]["dung"], "06v2_select.py ra DỪNG: không chạy seed 2, 3 (kế hoạch 4.2)"
    name1, script, args1, _ = next(r for r in GROUPS["v2"][1] if r[3] == v)
    d1 = C.ROOT / sel["variants"][v]["dir"]
    assert d1.name == name1 and (d1 / "result.json").exists(), d1
    k = args1.index("--seed")
    assert args1[k + 1] == "1"
    runs = [(name1[:-len("_s1")] + f"_s{s}", script, args1[:k + 1] + [str(s)] + args1[k + 2:], v) for s in (2, 3)]
    return sel, d1, runs


def final_groups():
    """(nhóm -> danh sách lần chạy) cho final / ablation, đọc cakg_final.toml. Mỗi lần chạy:
    (tên, script, tham số, None, (khóa mô hình trong toml, cfg mong đợi trừ seed))."""
    t = tomllib.loads(FINAL_TOML.read_text(encoding="utf-8"))
    ck, kg = t["cakg"]["cfg"], t["kgat"]["cfg"]
    fin = []
    for r in t["cakg"]["runs"]:
        if r["seed"] != 1:
            fin.append((Path(r["dir"]).name, "06_cakg_train.py", ["--lam1", repr(ck["lam1"]), "--seed", str(r["seed"])],
                        None, ("cakg", dict(ck))))
    for r in t["kgat"]["runs"]:
        if r["seed"] != 1:
            fin.append((Path(r["dir"]).name, "07_kgat_train.py", ["--lr", repr(kg["lr"]), "--seed", str(r["seed"])],
                        None, ("kgat", dict(kg))))
    abl = []
    for r in t["ablation"]:
        args = ["--lam1", repr(r["lam1"]), "--seed", str(r["seed"])] + (["--drop-suitable-for"] if r["drop_suitable_for"]
                                                                         else [])
        abl.append((Path(r["dir"]).name, "06_cakg_train.py", args, None,
                    ("cakg", {**ck, "lam1": r["lam1"], "drop_suitable_for": r["drop_suitable_for"]})))
    return t, {"final": fin, "ablation": abl}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", required=True, choices=sorted(GROUPS) + ["final", "ablation", "v2seeds"])
    ap.add_argument("--select-dir", help="nhóm v2seeds: thư mục select_<thời điểm> của 06v2_select.py")
    ap.add_argument("--label", required=True, help="nhãn của đợt dò, vd 20261014 (giữ nguyên khi chạy tiếp)")
    ap.add_argument("--allow-dirty", action="store_true", help="cho chạy khi file đã theo dõi trong git bị sửa")
    ap.add_argument("--smoke", action="store_true", help="(kiểm thử) mỗi lần chạy chỉ 1 epoch")
    a = ap.parse_args()
    is_final = a.group in ("final", "ablation")
    if is_final:
        toml_, fg = final_groups()
        pname, runs = None, fg[a.group]
        root = OUT_DIR / f"{'smoke_' if a.smoke else ''}final_{a.label}"
        if not a.smoke:
            rel = str(root.relative_to(C.ROOT)).replace(chr(92), "/")
            assert rel == toml_["chung"]["final_dir"], f"nhãn phải khớp final_dir của cakg_final.toml: {rel}"
    elif a.group == "v2seeds":
        sel_, d_s1, runs = v2seeds_runs(a.select_dir)
        pname = "variant"
        root = OUT_DIR / f"{'smoke_' if a.smoke else ''}val_sweep_{a.label}"
    else:
        pname, runs = GROUPS[a.group]
        root = OUT_DIR / f"{'smoke_' if a.smoke else ''}val_sweep_{a.label}"
    root.mkdir(parents=True, exist_ok=True)
    log = E.Log(root / f"sweep_{a.group}_{E.now_tag()}.log")
    git = E.git_state()
    log(f"{'Chạy cấu hình chốt' if is_final else 'Dò val'} | nhóm {a.group} | {root} | git {git} | {len(runs)} lần chạy"
        + (f" | cakg_final.toml sha256 {E.sha256(FINAL_TOML)}" if is_final else "") + (" | SMOKE: 1 epoch" if a.smoke else ""))
    if git["dirty"] and not a.allow_dirty:
        log("DỪNG: có file đã theo dõi trong git bị sửa mà chưa commit. Commit trước (hoặc --allow-dirty).")
        sys.exit(2)
    if E.DEVICE.type != "cuda":
        log("DỪNG: không thấy GPU (torch.cuda.is_available() = False).")
        sys.exit(2)

    t_all = time.time()
    for k, (name, script, args, *_) in enumerate(runs, 1):
        rd = root / name
        if (rd / "result.json").exists():
            log(f"[{k}/{len(runs)}] {name}: đã xong, bỏ qua")
            continue
        cmd = [sys.executable, "-W", "ignore", str(PIPE / script), *args, "--run-dir", str(rd)]
        if a.smoke:
            cmd += ["--max-epoch", "1", "--eval-every", "1"]
        log(f"[{k}/{len(runs)}] {name}: {'chạy tiếp' if (rd / 'last.pt').exists() else 'bắt đầu'} lúc "
            f"{time.strftime('%H:%M:%S')} | git {E.git_state()} | {' '.join(cmd[3:])}")
        t = time.time()
        try:
            rc = subprocess.run(cmd).returncode
        except KeyboardInterrupt:
            log(f"Bị ngắt ở {name} sau {(time.time() - t) / 60:.1f} phút. Gõ lại đúng lệnh để chạy tiếp.")
            sys.exit(130)
        if rc != 0:
            log(f"DỪNG: {name} lỗi (mã {rc}) sau {(time.time() - t) / 60:.1f} phút; xem log trong {rd}")
            sys.exit(rc)
        log(f"[{k}/{len(runs)}] {name}: xong sau {(time.time() - t) / 60:.1f} phút")

    log(f"\nXong cả {len(runs)} lần chạy ({(time.time() - t_all) / 60:.1f} phút ở lần gọi này).")
    log(f"{'lần chạy':<26} {'NDCG@20 val':>11} {'sau mặt nạ':>10} {'R@20 val':>9} {'epoch tốt':>9} {'đã chạy':>7} "
        f"{'s/epoch':>7} {'VRAM MiB':>8}  ghi chú")
    summary, shas = {}, {}
    for name, _, _, val, *_ in runs:
        r = json.loads((root / name / "result.json").read_text(encoding="utf-8"))
        c = json.loads((root / name / "config.json").read_text(encoding="utf-8"))
        shas[name] = (c.get("code_sha256"), c["inputs_sha256"])
        f = r["val"]["full"]
        fm = r.get("val_mask", {}).get("full", {})
        summary[name] = {"model": r["model"], "cfg": r["cfg"], pname: val, "val_ndcg@20": f["ndcg@20"],
                         "val_ndcg@20_mask": fm.get("ndcg@20"), "val_recall@20": f["recall@20"],
                         "best_epoch": r["best_epoch"], "epochs_run": r["epochs_run"],
                         "chua_chac_hoi_tu": r["chua_chac_hoi_tu"], "median_sec_per_epoch": r["median_sec_per_epoch"],
                         "peak_vram_allocated_mib": r.get("peak_vram_allocated_mib"),
                         "peak_vram_eval_allocated_mib": r.get("peak_vram_eval_allocated_mib"),
                         "git_start": c["git"], "git_at_finish": r["git_at_finish"]}
        s = summary[name]
        log(f"{name:<26} {f['ndcg@20']:>11.5f} {(fm.get('ndcg@20') or float('nan')):>10.5f} {f['recall@20']:>9.5f} "
            f"{r['best_epoch']:>9} {r['epochs_run']:>7} {r['median_sec_per_epoch']:>7.1f} "
            f"{(s['peak_vram_allocated_mib'] or 0):>8.0f}  "
            f"{'chưa chắc hội tụ' if r['chua_chac_hoi_tu'] else 'dừng sớm'}; git đầu {c['git']['commit'][:7]}"
            f"{' (dirty)' if c['git']['dirty'] else ''}")
    if is_final:
        t_ = tomllib.loads(FINAL_TOML.read_text(encoding="utf-8"))
        ok_all = True
        for name, _, _, _, (mk, want) in runs:
            r = json.loads((root / name / "result.json").read_text(encoding="utf-8"))
            c = json.loads((root / name / "config.json").read_text(encoding="utf-8"))
            s1 = json.loads((C.ROOT / next(x["dir"] for x in t_[mk]["runs"] if x["seed"] == 1) / "config.json")
                            .read_text(encoding="utf-8"))
            got = {k: v for k, v in r["cfg"].items() if k != "seed"}
            w = {k: (list(v) if isinstance(v, (list, tuple)) else v) for k, v in want.items()}
            ok_cfg = got == w or a.smoke
            ok_sha = (c.get("code_sha256") == s1.get("code_sha256") and c["inputs_sha256"] == s1["inputs_sha256"])
            ok_all &= ok_cfg and ok_sha
            log(f"  {name}: cfg = cfg chốt (trừ seed / phần ablation): {'CÓ' if ok_cfg else 'KHÔNG'}; sha256 code + đầu vào "
                f"= lần chạy seed 1 ({mk}): {'CÓ' if ok_sha else 'KHÔNG — xem config.json'}")
        out = root / f"summary_{a.group}_{E.now_tag()}.json"
        out.write_text(json.dumps({"git": git, "group": a.group, "cakg_final_toml_sha256": E.sha256(FINAL_TOML),
                                   "cfg_and_code_match_seed1": bool(ok_all), "runs": summary}, indent=2,
                                  ensure_ascii=False), encoding="utf-8")
        log(f"-> {out}")
        log.close()
        return
    if a.group == "v2seeds":
        c1 = json.loads((d_s1 / "config.json").read_text(encoding="utf-8"))
        ok_all = True
        for name, *_ in runs:
            c = json.loads((root / name / "config.json").read_text(encoding="utf-8"))
            ign = ("seed", "max_epoch", "eval_every")
            ok_cfg = ({k: v for k, v in c["cfg"].items() if k not in ign}
                      == {k: v for k, v in c1["cfg"].items() if k not in ign}
                      and (a.smoke or c["cfg"] == {**c1["cfg"], "seed": c["cfg"]["seed"]}))
            ok_sha = c.get("code_sha256") == c1.get("code_sha256") and c["inputs_sha256"] == c1["inputs_sha256"]
            ok_all &= ok_cfg and ok_sha
            log(f"  {name}: cfg = cfg seed 1 ({d_s1.name}) trừ seed: {'CÓ' if ok_cfg else 'KHÔNG'}; sha256 code + đầu vào "
                f"= seed 1: {'CÓ' if ok_sha else 'KHÔNG — xem config.json'}")
        out = root / f"summary_{a.group}_{E.now_tag()}.json"
        out.write_text(json.dumps({"git": git, "group": a.group, "select_dir": str(Path(a.select_dir)),
                                   "seed1_dir": str(d_s1.relative_to(C.ROOT)), "cfg_and_code_match_seed1": bool(ok_all),
                                   "runs": summary}, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"-> {out}")
        log("Bước tiếp: 06v2_dung2.py (kiểm DỪNG 2 trên trung bình 3 seed, kế hoạch 4.3).")
        log.close()
        return
    same = len({json.dumps(v, sort_keys=True) for v in shas.values()}) == 1
    log(f"Mọi lần chạy cùng sha256 code + đầu vào (config.json): {'CÓ' if same else 'KHÔNG — xem config.json'}")
    best = max(summary, key=lambda n: summary[n]["val_ndcg@20"])
    vals = sorted(x[3] for x in runs)
    edge = all(isinstance(v, float) for v in vals) and summary[best][pname] in (vals[0], vals[-1])
    log(f"Tốt nhất theo NDCG@20 val (trước mặt nạ): {best} ({pname} = {summary[best][pname]})"
        + (" — Ở BIÊN LƯỚI (ghi lại, không mở rộng lưới: kế hoạch mục 4.1)" if edge else "")
        + (" — CHỈ ĐỂ XEM: chọn biến thể v2 theo 06v2_select.py (điều kiện phụ + điều kiện DỪNG)"
           if a.group == "v2" else ""))
    out = root / f"summary_{a.group}_{E.now_tag()}.json"
    out.write_text(json.dumps({"git": git, "group": a.group, "best": best, "best_at_grid_edge": edge,
                               "same_code_and_inputs": same, "runs": summary}, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    log(f"-> {out}")
    log.close()


if __name__ == "__main__":
    main()
