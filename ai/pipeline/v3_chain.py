"""
v3_chain.py — chạy NỐI TIẾP các đợt v3 trên máy nhóm sau đợt s1, không cần người bấm (Nam 06/11/2026 khuya: "Đợt s1 cứ
chạy tiếp; khi nó xong thì chạy các đợt sau theo kế hoạch, không cần chờ tôi"). Quy tắc chọn lấy đúng từ
docs/reviews/v3_eval_plan.md mục 3, 4, 6, 6.2 (đăng ký trước, ghi 06/11 khuya TRƯỚC khi đợt s1 xong). KHÔNG chấm test.

Các bước:
  0. Chờ tiến trình đợt s1 (--wait-pid) kết thúc, rồi gọi lại v3_sweep --group s1 (đã xong hết thì chỉ in bảng tổng;
     bị ngắt thì chạy tiếp phần dở; lỗi thì DỪNG cả chuỗi).
  1. Chọn (seed 1, NDCG@20 full ranking val, trước mặt nạ) cho LightGCN λ2, KGAT lr, R-GCN lr trên lưới = các lần cũ đã
     dừng sớm (giữ) + đợt s1. CaKG-Rec v2 A: chỉ λ1 = 0,1 (HỎI 11), không chọn.
     Ví dụ: LightGCN 1e-5 / 1e-4 / 1e-3 / 3e-3 / 1e-2 có val 0,0377 / 0,0380 / 0,0405 / 0,0410 / 0,0399 -> chọn 3e-3
     (không ở biên). Nếu 1e-2 cao nhất (ở biên trên) -> đợt s1b thêm đúng 1 điểm 3e-2 (HỎI 3), chọn lại một lần; 3e-2 vẫn
     cao nhất -> chọn 3e-2 và ghi hạn chế "vẫn ở biên". Bằng nhau tuyệt đối: lấy giá trị đứng trước trong lưới.
  2. Ghi ai/config/v3_final.toml + results/v3/chain_<nhãn>/select_*.json, git commit RIÊNG file toml (kế hoạch mục 6:
     commit trước khi chạy seed 2–5). Không push.
  3. Đợt s25: seed 2–5 của cấu hình chốt (LightGCN, CaKG-Rec v2 A, KGAT, R-GCN). Lần cũ cùng cấu hình + seed: đã dừng sớm
     -> GIỮ, không chạy; chạm trần -> chạy tiếp từ last.pt nếu ĐẠT kiểm (v3_sweep tự kiểm), không thì chạy lại.
  4. Đợt abl: CaKG-Rec v2 A λ1 = 0 và λ1 = 0,1 bỏ suitable_for, seed 1–5 (mới).
  5. ItemKNN (RecBole, venv riêng, --group-eval, tất định nên không seed): k ∈ {50, 100, 200}.
Mỗi bước gọi v3_sweep (log, đường cong, bảng tổng như đợt s1). Trước mỗi lần gọi: cây git phải sạch (file đã theo dõi),
không sạch thì chờ (kiểm lại mỗi 10 phút) — để mọi lần chạy ghi đúng một commit.
Log: results/v3/chain_<nhãn>/chain_<thời điểm>.log (không ghi đè). Gọi lại đúng lệnh: bước đã xong được bỏ qua.

Lệnh:
  ai\\.venv\\Scripts\\python.exe ai/pipeline/v3_chain.py --label 20261106 --wait-pid 3380
  (--dry-run: chỉ in việc sẽ làm từ kết quả hiện có, không chạy, không ghi toml, không commit)
"""
import argparse
import json
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
RES = C.RESULTS_DIR
KIEM = "results/v3/kiem_last_pt_lan2.json"
RB_PY = Path(r"E:\DATN\venvs\recbole\Scripts\python.exe")
TOML = C.ROOT / "ai" / "config" / "v3_final.toml"

# Lưới (thấp -> cao), lần cũ seed 1 đã DỪNG SỚM (giữ), điểm thêm khi ở biên (HỎI 3; giá trị ghi ở kế hoạch mục 6.2)
GRID = {
    "lightgcn": {"script": "05b_lightgcn_train.py", "flag": "--l2", "key": "l2", "name": "lightgcn_l2-{v}",
                 "values": [1e-5, 1e-4, 1e-3, 3e-3, 1e-2], "ext": {"low": 3e-6, "high": 3e-2},
                 "old_s1": {1e-5: "n5/val_sweep_20261010/val_lightgcn_l2-1e-05_s1",
                            1e-4: "n5/val_sweep_20261010/val_lightgcn_l2-1e-04_s1"}},
    "kgat": {"script": "07_kgat_train.py", "flag": "--lr", "key": "lr", "name": "kgat_lr-{v}",
             "values": [1e-4, 1e-3, 3e-3], "ext": {"low": 3e-5, "high": 1e-2},
             "old_s1": {1e-3: "cakg/val_sweep_20261014/val_kgat_lr-1e-03_s1"}},
    "rgcn": {"script": "05c_rgcn_train.py", "flag": "--lr", "key": "lr", "name": "rgcn_lr-{v}",
             "values": [1e-4, 3e-4, 1e-3, 1e-2], "ext": {"low": 3e-5, "high": 3e-2},
             "old_s1": {1e-2: "n5/val_sweep_20261010/val_rgcn_lr-1e-02_s1",
                        1e-3: "n5/val_sweep_20261010/val_rgcn_lr-1e-03_s1"}},
}
CAKG = {"script": "06_cakg_train.py", "lam1": 0.1, "variant": "lens_gate",
        "old": {2: "cakg/val_sweep_v2seeds_20261016/val_v2_A_lens_gate_s2",
                3: "cakg/val_sweep_v2seeds_20261016/val_v2_A_lens_gate_s3"}}
# lần cũ seed 2, 3 (chỉ dùng nếu cấu hình chốt trùng)
OLD_SEEDS = {("lightgcn", 1e-3): {2: "n5/final_20261009/lightgcn_l2-1e-03_s2", 3: "n5/final_20261009/lightgcn_l2-1e-03_s3"},
             ("kgat", 1e-3): {2: "cakg/final_20261015/kgat_lr-1e-03_s2", 3: "cakg/final_20261015/kgat_lr-1e-03_s3"},
             ("rgcn", 1e-3): {2: "n5/final_20261009/rgcn_lr-1e-03_s2", 3: "n5/final_20261009/rgcn_lr-1e-03_s3"}}
ITEMKNN_K = [50, 100, 200]


def fmt(v):
    return f"{v:.0e}"


def git_dirty():
    return bool(subprocess.run(["git", "-C", str(C.ROOT), "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True).stdout.strip())


def pid_alive(pid):
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
    return str(pid) in out


def read_result(d):
    p = RES / d / "result.json" if not Path(d).is_absolute() else Path(d) / "result.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def choose(values, scores):
    """values theo thứ tự lưới; scores: value -> NDCG@20. Bằng nhau: lấy giá trị đứng trước. Trả (best, 'low'|'high'|None)."""
    best = max(values, key=lambda v: (scores[v], -values.index(v)))
    edge = "low" if best == values[0] else ("high" if best == values[-1] else None)
    return best, edge


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="nhãn đợt s1 (vd 20261106); các đợt sau dùng cùng nhãn")
    ap.add_argument("--wait-pid", type=int, default=None, help="PID tiến trình đợt s1 đang chạy")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cdir = RES / "v3" / f"chain_{a.label}"
    cdir.mkdir(parents=True, exist_ok=True)
    log = E.Log(cdir / f"chain_{'dry_' if a.dry_run else ''}{E.now_tag()}.log")
    log(f"v3_chain | nhãn {a.label} | git {E.git_state()} | {'DRY-RUN' if a.dry_run else 'chạy thật'}")

    def sweep(group, runs_file=None, py=None):
        if a.dry_run:
            log(f"  (dry-run) sẽ gọi v3_sweep --group {group}" + (f" --runs-json {runs_file}" if runs_file else ""))
            return
        while git_dirty():
            log(f"  cây git có file đã theo dõi bị sửa -> chờ 10 phút rồi kiểm lại ({time.strftime('%H:%M')})")
            time.sleep(600)
        cmd = [sys.executable, "-W", "ignore", str(PIPE / "v3_sweep.py"), "--group", group, "--label", a.label,
               "--kiem", KIEM] + (["--runs-json", runs_file] if runs_file else [])
        log(f"  gọi: {' '.join(cmd[3:])} lúc {time.strftime('%Y-%m-%d %H:%M:%S')}")
        rc = subprocess.run(cmd).returncode
        log(f"  v3_sweep {group} kết thúc mã {rc} lúc {time.strftime('%Y-%m-%d %H:%M:%S')}")
        if rc != 0:
            log(f"DỪNG CHUỖI: đợt {group} lỗi (mã {rc}); xem results/v3/{group}_{a.label}/sweep_*.log")
            sys.exit(rc)

    def write_runs(group, runs):
        f = cdir / f"runs_{group}.json"
        if f.exists():
            old = json.loads(f.read_text(encoding="utf-8"))
            assert old == [list(r) for r in runs], f"{f} đã có và khác danh sách mới -> không ghi đè, kiểm tay"
        elif not a.dry_run:
            f.write_text(json.dumps([list(r) for r in runs], indent=1, ensure_ascii=False), encoding="utf-8")
        for r in runs:
            log(f"    {r[0]:<34} {r[1]} {' '.join(r[2])}" + (f"  (chạy tiếp từ {r[3]})" if r[3] else ""))
        try:
            return str(f.relative_to(C.ROOT)).replace("\\", "/")
        except ValueError:
            return str(f)

    # ---------- 0. đợt s1 ----------
    if a.wait_pid and not a.dry_run:
        log(f"Chờ tiến trình đợt s1 (PID {a.wait_pid}) kết thúc ...")
        while pid_alive(a.wait_pid):
            time.sleep(300)
        log(f"PID {a.wait_pid} đã kết thúc lúc {time.strftime('%Y-%m-%d %H:%M:%S')}")
    sweep("s1")
    s1 = RES / "v3" / f"s1_{a.label}"

    # ---------- 1. chọn + s1b ----------
    def seed1_dir(m, v):
        g = GRID[m]
        if v in g["old_s1"]:
            return g["old_s1"][v]
        name = g["name"].format(v=fmt(v)) + "_s1"
        for grp in ("s1", "s1b"):
            d = RES / "v3" / f"{grp}_{a.label}" / name
            if (d / "result.json").exists():
                return str(d.relative_to(RES)).replace("\\", "/")
        return None

    def scores_of(m, values):
        out = {}
        for v in values:
            d = seed1_dir(m, v)
            r = read_result(d) if d else None
            if r is None:
                log(f"DỪNG CHUỖI: thiếu result.json seed 1 của {m} {fmt(v)} ({d})")
                sys.exit(3)
            out[v] = r["val"]["full"]["ndcg@20"]
        return out

    sel = {}
    ext_runs = []
    for m, g in GRID.items():
        sc = scores_of(m, g["values"])
        best, edge = choose(g["values"], sc)
        sel[m] = {"values": list(g["values"]), "scores": {fmt(v): sc[v] for v in g["values"]}, "best_round1": best,
                  "edge_round1": edge}
        log(f"[chọn vòng 1] {m}: " + ", ".join(f"{fmt(v)}={sc[v]:.5f}" for v in g["values"])
            + f" -> {fmt(best)}" + (f" Ở BIÊN {'DƯỚI' if edge == 'low' else 'TRÊN'}" if edge else " (không ở biên)"))
        if edge:
            v = g["ext"][edge]
            ext_runs.append((g["name"].format(v=fmt(v)) + "_s1", g["script"], [g["flag"], fmt(v), "--seed", "1"], None))
            sel[m]["ext_value"] = v
    if ext_runs:
        log("Đợt s1b (thêm đúng 1 điểm ở biên, HỎI 3):")
        sweep("s1b", write_runs("s1b", ext_runs))
        if a.dry_run and not all((RES / "v3" / f"s1b_{a.label}" / r[0] / "result.json").exists() for r in ext_runs):
            log("  (dry-run) dừng ở đây vì s1b chưa có kết quả")
            return
    final = {}
    for m, g in GRID.items():
        vals = list(g["values"])
        if "ext_value" in sel[m]:
            v = sel[m]["ext_value"]
            vals = [v] + vals if v < vals[0] else vals + [v]
        sc = scores_of(m, vals)
        best, edge = choose(vals, sc)
        still = "ext_value" in sel[m] and edge is not None
        sel[m].update(values_final=vals, scores_final={fmt(v): sc[v] for v in vals}, best=best,
                      still_at_edge_after_extension=still, seed1_dir=seed1_dir(m, best))
        final[m] = best
        log(f"[chọn cuối] {m}: {g['key']} = {fmt(best)} (NDCG@20 val seed 1 {sc[best]:.5f})"
            + (" — VẪN Ở BIÊN sau khi thêm 1 điểm -> ghi hạn chế, không mở thêm (HỎI 3)" if still else ""))
    sel["cakg_v2A"] = {"lam1": CAKG["lam1"], "variant": CAKG["variant"], "ghi_chu": "không dò lại λ1 cho v2 A (HỎI 11)",
                       "seed1_dir": f"v3/s1_{a.label}/cakg_v2A_lam1-1e-01_s1"}

    # ---------- 2. toml + commit ----------
    toml = ["# v3_final.toml — SINH TỰ ĐỘNG bởi ai/pipeline/v3_chain.py theo quy tắc đăng ký trước",
            "# (docs/reviews/v3_eval_plan.md mục 3, 6, 6.2). Chọn trên val seed 1 (NDCG@20 full, trước mặt nạ). KHÔNG chấm test.",
            f"# nhãn đợt: {a.label}; lúc ghi: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for m, g in GRID.items():
        s = sel[m]
        toml += [f"[{m}]", f"{g['key']} = {final[m]!r}", f"seed1_dir = \"results/{s['seed1_dir']}\"",
                 "grid = { " + ", ".join(f"\"{k}\" = {v!r}" for k, v in s["scores_final"].items()) + " }",
                 f"still_at_edge_after_extension = {str(s['still_at_edge_after_extension']).lower()}", ""]
    toml += ["[cakg_v2A]", "lam1 = 0.1", "variant = \"lens_gate\"", f"seed1_dir = \"results/{sel['cakg_v2A']['seed1_dir']}\"",
             "note = \"không dò lại λ1 cho v2 A (HỎI 11, Nam 06/11)\"", ""]
    toml_text = "\n".join(toml)
    (cdir / f"select_{'dry_' if a.dry_run else ''}{E.now_tag()}.json").write_text(
        json.dumps({k: {kk: (fmt(vv) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in sel.items()},
                   indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    if a.dry_run:
        log("  (dry-run) toml sẽ ghi:\n" + toml_text)
    elif TOML.exists():
        old = TOML.read_text(encoding="utf-8")
        same = [ln for ln in old.splitlines() if not ln.startswith("#")] == [ln for ln in toml_text.splitlines()
                                                                               if not ln.startswith("#")]
        if not same:
            log(f"DỪNG CHUỖI: {TOML} đã có và KHÁC lựa chọn mới -> không ghi đè, kiểm tay")
            sys.exit(4)
        log(f"{TOML.name} đã có, trùng lựa chọn -> giữ")
    else:
        TOML.write_text(toml_text, encoding="utf-8")
        while git_dirty():
            log("  cây git bẩn trước khi commit toml -> chờ 10 phút")
            time.sleep(600)
        subprocess.run(["git", "-C", str(C.ROOT), "add", str(TOML)], check=True)
        msg = ("v3: chốt cấu hình sau đợt s1 (v3_chain.py, tự động): "
               + ", ".join(f"{m} {GRID[m]['key']}={fmt(final[m])}" for m in GRID) + "; CaKG-Rec v2 A λ1=0,1")
        r = subprocess.run(["git", "-C", str(C.ROOT), "commit", "-m", msg, "--", str(TOML)], capture_output=True, text=True)
        log(f"git commit toml: mã {r.returncode} {r.stdout.strip()[:200]} {r.stderr.strip()[:200]}")
        if r.returncode != 0:
            log("DỪNG CHUỖI: không commit được v3_final.toml")
            sys.exit(5)

    # ---------- 3. s25 ----------
    runs, kept = [], []
    for m, g in GRID.items():
        v = final[m]
        for seed in (2, 3, 4, 5):
            name = g["name"].format(v=fmt(v)) + f"_s{seed}"
            src = OLD_SEEDS.get((m, v), {}).get(seed)
            if src:
                r = read_result(src)
                if r and r["stopped_early"]:
                    kept.append((name, src, r["val"]["full"]["ndcg@20"], r["epochs_run"]))
                    continue
            runs.append((name, g["script"], [g["flag"], fmt(v), "--seed", str(seed)], src))
    for seed in (2, 3, 4, 5):
        runs.append((f"cakg_v2A_lam1-1e-01_s{seed}", CAKG["script"],
                     ["--lam1", "0.1", "--seed", str(seed), "--variant", "lens_gate"], CAKG["old"].get(seed)))
    for name, src, nd, ep in kept:
        log(f"  GIỮ lần cũ đã dừng sớm: {name} <- results/{src} (NDCG@20 val {nd:.5f}, dừng ở epoch {ep})")
    if not a.dry_run:
        (cdir / "kept_s25.json").write_text(json.dumps(kept, indent=1, ensure_ascii=False), encoding="utf-8")
    log(f"Đợt s25 ({len(runs)} lần chạy):")
    sweep("s25", write_runs("s25", runs))

    # ---------- 4. abl ----------
    abl = []
    for seed in (1, 2, 3, 4, 5):
        abl.append((f"abl_v2A_lam1-0_s{seed}", CAKG["script"],
                    ["--lam1", "0", "--seed", str(seed), "--variant", "lens_gate"], None))
        abl.append((f"abl_v2A_lam1-1e-01_nosuit_s{seed}", CAKG["script"],
                    ["--lam1", "0.1", "--seed", str(seed), "--variant", "lens_gate", "--drop-suitable-for"], None))
    log(f"Đợt abl ({len(abl)} lần chạy):")
    sweep("abl", write_runs("abl", abl))

    # ---------- 5. ItemKNN ----------
    kdir = RES / "v3" / f"itemknn_{a.label}"
    for k in ITEMKNN_K:
        rd = kdir / f"itemknn_k{k}"
        if (rd / "result.json").exists():
            log(f"ItemKNN k = {k}: đã xong, bỏ qua")
            continue
        cmd = [str(RB_PY), "-W", "ignore", str(C.ROOT / "ai" / "recbole" / "run_recbole.py"), "--model", "ItemKNN",
               "--seed", "1", "--epochs", "1", "--group-eval", "--set", f"k={k}", "--set", "shrink=0.0",
               "--run-dir", str(rd)]
        if a.dry_run:
            log(f"  (dry-run) sẽ chạy ItemKNN k = {k}: {' '.join(cmd[3:])}")
            continue
        while git_dirty():
            log("  cây git bẩn -> chờ 10 phút")
            time.sleep(600)
        kdir.mkdir(parents=True, exist_ok=True)
        lp = kdir / f"stdout_k{k}_{E.now_tag()}.txt"
        log(f"ItemKNN k = {k}: bắt đầu {time.strftime('%Y-%m-%d %H:%M:%S')} | git {E.git_state()}")
        with open(lp, "w", encoding="utf-8") as f:
            rc = subprocess.run(cmd, cwd=C.ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
        r = read_result(rd)
        log(f"ItemKNN k = {k}: mã {rc}" + (f", NDCG@20 val {r['val']['full']['ndcg@20']:.5f}" if r else ", KHÔNG có result.json"))
    log(f"Xong chuỗi v3 lúc {time.strftime('%Y-%m-%d %H:%M:%S')}. Chưa chấm test (kế hoạch mục 2: chấm một lần ở cuối, "
        f"khi đủ cả baseline Kaggle).")
    log.close()


if __name__ == "__main__":
    main()
