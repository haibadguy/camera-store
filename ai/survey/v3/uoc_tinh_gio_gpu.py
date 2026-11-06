"""
uoc_tinh_gio_gpu.py — số đo giây / epoch thật của các lần huấn luyện đã chạy (máy nhóm, GTX 1660 Ti) và ước tính giờ
GPU cho mục A1–A3 nhận xét cô 06/11 theo 3 phương án (docs/reviews/v3_eval_plan.md). Viết 06/11/2026. Chỉ đọc.

Phần ĐO (in nhãn [ĐO]): đọc result.json (history: sec mỗi epoch, sec_eval mỗi lần chấm) và log sweep ("xong sau X phút")
  -> giây huấn luyện / epoch (trung vị), giây / lần chấm val, phần cố định mỗi lần chạy = thời gian tường − Σsec − Σsec_eval.
  Thêm số đo thời gian của RecBole (results/recbole/probe_*/*/result.json, chạy --probe-epochs) nếu có.
Phần ƯỚC TÍNH (nhãn [ƯỚC TÍNH]): giờ một lần chạy = cố định + E·(giây/epoch) + ⌊E / chấm_mỗi⌋·(giây/lần chấm),
  E = số epoch: lần đã dừng sớm có số đo -> dùng lại (0 giờ); lần chạy tiếp từ last.pt -> chỉ phần 300 -> E;
  lần chưa có -> CẬN TRÊN E = 1.000 (không giả định dừng sớm).
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/v3/uoc_tinh_gio_gpu.py  (log: ai/data/survey/v3/run_uoc_tinh_gio_<nhãn>.log)
"""
import json
import re
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
R = ROOT / "results"
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Lần chạy thật (không chạy thử) và log sweep ghi thời gian tường
RUNS = {
    "LightGCN": ["n5/val_sweep_20261010/val_lightgcn_l2-1e-05_s1", "n5/val_sweep_20261010/val_lightgcn_l2-1e-04_s1",
                 "n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1", "n5/final_20261009/lightgcn_l2-1e-03_s2",
                 "n5/final_20261009/lightgcn_l2-1e-03_s3"],
    "R-GCN": ["n5/val_sweep_20261010/val_rgcn_lr-1e-02_s1", "n5/val_sweep_20261010/val_rgcn_lr-1e-03_s1",
              "n5/final_20261009/rgcn_lr-1e-03_s2", "n5/final_20261009/rgcn_lr-1e-03_s3"],
    "CaKG-Rec": ["cakg/val_sweep_20261014/val_cakg_lam1-1e-02_s1", "cakg/val_sweep_20261014/val_cakg_lam1-1e-01_s1",
                 "cakg/val_sweep_20261014/val_cakg_lam1-1e+00_s1", "cakg/final_20261015/cakg_lam1-1e-01_s2",
                 "cakg/final_20261015/cakg_lam1-1e-01_s3", "cakg/final_20261015/abl_cakg_lam1-0_s1",
                 "cakg/final_20261015/abl_cakg_lam1-1e-01_nosuit_s1",
                 "cakg/val_sweep_v2_20261016/val_v2_A_lens_gate_s1", "cakg/val_sweep_v2_20261016/val_v2_B_loo_hu_s1",
                 "cakg/val_sweep_v2_20261016/val_v2_C_body_hardneg_s1",
                 "cakg/val_sweep_v2seeds_20261016/val_v2_A_lens_gate_s2",
                 "cakg/val_sweep_v2seeds_20261016/val_v2_A_lens_gate_s3"],
    "KGAT": ["cakg/val_sweep_20261014/val_kgat_lr-1e-03_s1", "cakg/val_sweep_20261014/val_kgat_lr-1e-04_s1",
             "cakg/final_20261015/kgat_lr-1e-03_s2", "cakg/final_20261015/kgat_lr-1e-03_s3"],
}
SWEEP_LOGS = ["n5/val_sweep_20261010/sweep_20261009_022613.log", "cakg/val_sweep_20261014/sweep_cakg_20261014_223030.log",
              "cakg/val_sweep_20261014/sweep_kgat_20261015_041443.log",
              "cakg/final_20261015/sweep_final_20261015_084426.log",
              "cakg/final_20261015/sweep_ablation_20261015_135426.log",
              "cakg/val_sweep_v2_20261016/sweep_v2_20261016_074929.log",
              *[str(p.relative_to(R)).replace("\\", "/") for p in (R / "cakg/val_sweep_v2seeds_20261016").glob("*.log")]]
EVAL_EVERY = {"LightGCN": 10, "R-GCN": 5, "CaKG-Rec": 10, "KGAT": 10}


def measure():
    wall = {}
    for lg in SWEEP_LOGS:
        for line in (R / lg).read_text(encoding="utf-8").splitlines():
            m = re.match(r"\[\d+/\d+\] (\S+): xong sau ([\d.]+) phút", line)
            if m:
                wall[m.group(1)] = float(m.group(2)) * 60
    out = {}
    for model, runs in RUNS.items():
        sec_ep, sec_ev, fixed, rows = [], [], [], []
        for r in runs:
            d = json.loads((R / r / "result.json").read_text(encoding="utf-8"))
            h = d["history"]
            s = [x["sec"] for x in h]
            e = [x["sec_eval"] for x in h if x.get("sec_eval") is not None]
            sec_ep += s
            sec_ev += e
            name = Path(r).name
            w = wall.get(name)
            if w is not None:
                fixed.append(w - sum(s) - sum(e))
            rows.append((name, d["epochs_run"], d["best_epoch"], d["stopped_early"], round(st.median(s), 2),
                         round(st.median(e), 2), None if w is None else round(w / 60, 1)))
        out[model] = {"sec_per_epoch_median": round(st.median(sec_ep), 2), "sec_per_epoch_min": min(sec_ep),
                      "sec_per_epoch_max": max(sec_ep), "sec_per_eval_median": round(st.median(sec_ev), 2),
                      "fixed_sec_median": round(st.median(fixed), 1) if fixed else None, "n_epochs": len(sec_ep),
                      "runs": rows}
    return out


def measure_recbole():
    out = {}
    for p in sorted((R / "recbole").glob("probe_*/*/result.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        out[f"{d['model']} ({p.parent.parent.name}/{p.parent.name})"] = {
            "sec_per_epoch_median": d.get("median_sec_per_epoch"), "sec_per_epoch": d.get("sec_per_epoch"),
            "sec_one_valid_eval_recbole": d.get("sec_one_valid_eval"), "peak_vram_mib": d.get("peak_vram_mib")}
    for p in sorted((R / "recbole").glob("repro_*/*/result.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        ev = [c["sec_eval"] for c in d.get("curve", [])]
        out[f"{d['model']} ({p.parent.parent.name}/{p.parent.name})"] = {
            "sec_per_epoch_median": d.get("median_sec_per_epoch"), "epochs_run": d.get("epochs_run"),
            "sec_per_eval_median_recbole": st.median(ev) if ev else None, "sec_fit_total": d.get("sec_fit_total")}
    return out


def run_hours(m, model, e_from, e_to):
    """Giờ của một lần chạy từ epoch e_from đến e_to (chạy tiếp: e_from = 300, không tính lại phần cố định nạp dữ
    liệu? -> VẪN tính: chạy tiếp cũng nạp dữ liệu và chấm đầy đủ ở cuối)."""
    a = m[model]
    n_ev = e_to // EVAL_EVERY[model] - e_from // EVAL_EVERY[model]
    return (a["fixed_sec_median"] + (e_to - e_from) * a["sec_per_epoch_median"] + n_ev * a["sec_per_eval_median"]) / 3600


def obs(model, key=None):
    """Số đo của các lần chạy cũ: [(tên, epochs_run, best_epoch, stopped_early)]; key lọc theo chuỗi trong tên."""
    out = []
    for r in RUNS[model]:
        if key and key not in r:
            continue
        d = json.loads((R / r / "result.json").read_text(encoding="utf-8"))
        out.append((Path(r).name, d["epochs_run"], d["best_epoch"], d["stopped_early"]))
    return out


PAT = 50   # dừng khi 5 lần chấm (mỗi 10 epoch) không tăng -> sớm nhất ở epoch tốt nhất + 50


def scenarios(m):
    """Mỗi việc: (khối, mô tả, số lần, mô hình lấy giây/epoch, epoch bắt đầu, epoch cuối CẬN TRÊN, epoch cuối CẬN DƯỚI).
    Cận dưới theo số đo: lần chạy tiếp -> epoch tốt nhất cũ + 50; seed mới của cấu hình cũ -> min(epoch tốt nhất các
    seed cũ) + 50; điểm lưới mới -> min(số epoch đã chạy của mọi lần cũ cùng mô hình); baseline mới -> = cận trên
    (chưa có số)."""
    E = 1000
    lg13 = obs("LightGCN", "1e-03")
    lg_min_run = min(o[1] for o in obs("LightGCN"))
    ck_grid = obs("CaKG-Rec", "val_cakg_lam1")
    ck_abl = obs("CaKG-Rec", "abl_")
    rg_min_run = min(o[1] for o in obs("R-GCN"))
    kg4 = obs("KGAT", "1e-04")
    kg_min_run = min(o[1] for o in obs("KGAT"))

    def lo_cont(rows):
        return [min(E, o[2] + PAT) for o in rows]

    def core(grid_pts_lgcn, grid_pts_rgcn, grid_pts_kgat, regrid_cakg, cont, nb_cfg):
        J = []
        c0 = 300 if cont else 0
        J.append(("LightGCN", f"λ2 thêm {grid_pts_lgcn} điểm trên biên (seed 1)", grid_pts_lgcn, "LightGCN", 0, E,
                  lg_min_run))
        for o in lg13:
            J.append(("LightGCN", f"λ2 = 1e-3 {o[0]} (đã chạm 300, tốt nhất {o[2]})", 1, "LightGCN", c0, E,
                      min(E, o[2] + PAT)))
        J.append(("LightGCN", "cấu hình chốt seed 4, 5", 2, "LightGCN", 0, E, min(o[2] for o in lg13) + PAT))
        if not cont:
            J.append(("LightGCN", "λ2 1e-5, 1e-4 (đã dừng sớm ở 180, chạy lại)", 2, "LightGCN", 0, 180, 180))
        cak = ck_grid if regrid_cakg else obs("CaKG-Rec", "val_cakg_lam1-1e-01")
        for o in cak + obs("CaKG-Rec", "final_20261015/cakg_lam1") + ck_abl:
            J.append(("CaKG-Rec", f"{o[0]} (đã chạm 300, tốt nhất {o[2]})", 1, "CaKG-Rec", c0, E, min(E, o[2] + PAT)))
        ck_lo = min(o[2] for o in ck_grid + ck_abl + obs("CaKG-Rec", "final_20261015/cakg_lam1")) + PAT
        J.append(("CaKG-Rec", "cấu hình chốt seed 4, 5", 2, "CaKG-Rec", 0, E, ck_lo))
        J.append(("CaKG-Rec", "2 ablation × seed 2–5", 8, "CaKG-Rec", 0, E, ck_lo))
        J.append(("R-GCN", f"lr thêm {grid_pts_rgcn} điểm dưới biên (seed 1)", grid_pts_rgcn, "R-GCN", 0, E,
                  rg_min_run))
        J.append(("R-GCN", "cấu hình chốt seed 4, 5", 2, "R-GCN", 0, E, rg_min_run))
        if not cont:
            for o in obs("R-GCN"):
                J.append(("R-GCN", f"{o[0]} (đã dừng sớm ở {o[1]}, chạy lại)", 1, "R-GCN", 0, o[1], o[1]))
        J.append(("KGAT", f"lr thêm {grid_pts_kgat} điểm trên biên (seed 1)", grid_pts_kgat, "KGAT", 0, E, kg_min_run))
        for o in kg4:
            J.append(("KGAT", f"lr = 1e-4 {o[0]} (đã chạm 300, tốt nhất {o[2]})", 1, "KGAT", c0, E, min(E, o[2] + PAT)))
        J.append(("KGAT", "cấu hình chốt seed 4, 5", 2, "KGAT", 0, E, kg_min_run))
        if not cont:
            for o in obs("KGAT", "1e-03"):
                J.append(("KGAT", f"{o[0]} (đã dừng sớm ở {o[1]}, chạy lại)", 1, "KGAT", 0, o[1], o[1]))
        for name, n_cfg in nb_cfg.items():
            J.append((name, f"dò {n_cfg} cấu hình (seed 1) + seed 2–5 (chưa có số: cận dưới = cận trên)", n_cfg + 4,
                      name, 0, E, E))
        return J

    full_bl = {"BPR-MF": 3, "UltraGCN": 3, "SimGCL": 3, "KGIN": 3}
    min_bl = {"BPR-MF": 2, "UltraGCN": 2, "SimGCL": 2, "KGIN": 2}
    return {
        "PA1 đủ, chạy lại từ đầu": core(2, 2, 1, True, False, full_bl),
        "PA2 đủ, chạy tiếp last.pt + giữ lần đã dừng sớm": core(2, 2, 1, True, True, full_bl),
        "PA3 tối thiểu (1 điểm / biên, không dò lại λ1, baseline mới 2 cấu hình)": core(1, 1, 1, False, True, min_bl),
    }


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "lan1"
    logp = ROOT / "ai" / "data" / "survey" / "v3" / f"run_uoc_tinh_gio_{tag}.log"
    logp.parent.mkdir(parents=True, exist_ok=True)
    assert not logp.exists(), f"log đã có, không ghi đè: {logp}"
    lines = []

    def log(s=""):
        print(s)
        lines.append(s)
    m = measure()
    log("[ĐO] Máy nhóm GTX 1660 Ti. Giây huấn luyện / epoch (trung vị, min–max), giây / lần chấm val, phần cố định / lần chạy")
    for k, v in m.items():
        log(f"  {k}: {v['sec_per_epoch_median']} s/epoch ({v['sec_per_epoch_min']}–{v['sec_per_epoch_max']}, "
            f"{v['n_epochs']} epoch), chấm val {v['sec_per_eval_median']} s/lần mỗi {EVAL_EVERY[k]} epoch, "
            f"cố định {v['fixed_sec_median']} s")
        for row in v["runs"]:
            log(f"      {row[0]}: chạy {row[1]} epoch, tốt nhất {row[2]}, dừng sớm {row[3]}, {row[4]} s/epoch, "
                f"chấm {row[5]} s, tường {row[6]} phút")
    rb = measure_recbole()
    log("[ĐO] RecBole 1.2.1 (venv riêng, cùng GPU):")
    for k, v in rb.items():
        log(f"  {k}: {json.dumps({kk: vv for kk, vv in v.items() if kk != 'sec_per_epoch'}, ensure_ascii=False)}")

    # giây / epoch cho baseline mới: ưu tiên số đo RecBole (probe); thiếu thì ước tính, ghi nguồn
    def rb_sec(model):
        c = [v["sec_per_epoch_median"] for k, v in rb.items() if k.startswith(model + " (probe")]
        return c[-1] if c else None
    nb = {}
    lg = m["LightGCN"]
    for name, rbname in [("BPR-MF", "BPR"), ("SimGCL", "SimGCL"), ("KGIN", "KGIN")]:
        s = rb_sec(rbname)
        nb[name] = (s, "[ĐO] RecBole probe") if s else (lg["sec_per_epoch_median"], "[ƯỚC TÍNH] = LightGCN (chưa đo)")
    nb["UltraGCN"] = (lg["sec_per_epoch_median"], "[ƯỚC TÍNH] = LightGCN (không có cài đặt trong RecBole / "
                                                  "RecBole-GNN, chưa đo)")
    for name, (s, src) in nb.items():
        m[name] = {"sec_per_epoch_median": s, "sec_per_eval_median": lg["sec_per_eval_median"],
                   "fixed_sec_median": lg["fixed_sec_median"]}
        EVAL_EVERY[name] = 10
        log(f"  baseline mới {name}: {s} s/epoch {src}; chấm val giả định = bộ chấm nhóm "
            f"{lg['sec_per_eval_median']} s/lần (RecBole tự chấm chậm hơn nhiều, xem trên)")

    log("\n[ƯỚC TÍNH] Giờ GPU máy nhóm, [cận dưới; cận trên]. Cận trên: mọi lần chạy chưa có số đo "
        "chạy đủ 1.000 epoch. Cận dưới: dừng sớm ở mức sớm nhất mà số đo cũ cho phép (xem docstring scenarios). "
        "ItemKNN không cần GPU (không tính).")
    summary = {}
    for name, jobs in scenarios(m).items():
        log(f"\n== {name}")
        hi_t, lo_t, by = 0.0, 0.0, {}
        for blk, desc, n, mdl, e0, e1, e1lo in jobs:
            hi = n * run_hours(m, mdl, e0, e1)
            lo = n * run_hours(m, mdl, e0, max(e0, e1lo))
            hi_t += hi
            lo_t += lo
            b = by.setdefault(blk, [0.0, 0.0])
            b[0] += lo
            b[1] += hi
            log(f"  {blk:9s} | {desc:58s} | {n:2d} × epoch {e0}→[{e1lo}; {e1}] | {lo:5.1f}–{hi:5.1f} giờ")
        log("  theo khối (cận dưới–cận trên): " + ", ".join(f"{k} {v[0]:.1f}–{v[1]:.1f}" for k, v in by.items()))
        log(f"  TỔNG: {lo_t:.1f}–{hi_t:.1f} giờ GPU (máy nhóm)")
        summary[name] = {"lo_h": round(lo_t, 1), "hi_h": round(hi_t, 1),
                         "by_block_h": {k: [round(v[0], 1), round(v[1], 1)] for k, v in by.items()}}
    log("\n[ƯỚC TÍNH] Phát sinh nếu cấu hình chốt KHÁC cấu hình cũ (các seed / ablation cũ phải chạy lại từ epoch 0):")
    for mdl, n, why in [("LightGCN", 2, "chốt λ2 ≠ 1e-3: seed 2, 3 chạy thêm 0→300"),
                        ("CaKG-Rec", 4, "chốt λ1 ≠ 0,1: seed 2, 3 + 2 ablation seed 1 chạy thêm 0→300")]:
        log(f"  {mdl}: +{n * run_hours(m, mdl, 0, 300):.1f} giờ ({why})")
    log(f"  KGAT: +{2 * run_hours(m, 'KGAT', 0, 1000):.1f} giờ cận trên (chốt lr ≠ 1e-3: seed 2, 3 chạy mới)")
    log("\n" + json.dumps(summary, ensure_ascii=False, indent=1))
    logp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nLog: {logp}")


if __name__ == "__main__":
    main()
