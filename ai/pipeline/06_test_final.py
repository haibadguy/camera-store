"""
06_test_final.py -- Chấm một lần các mô hình nội dung 6–8 trên test (docs/reviews/cakg_eval_plan.md mục 3, 4.2 bước 6,
5, 12). Viết 15/10/2026 theo khuôn 05_test_final.py. Script này CHỈ chấm và lưu mảng từng người + bảng tổng hợp; các so
sánh đăng ký trước (bootstrap, mục 8) tính ở 06_test_compare.py từ mảng đã lưu, sau khi đã commit kết quả chấm.

Mô hình (checkpoint đọc từ ai/config/cakg_final.toml và ai/config/n5_final.toml, kiểm sha256):
  - CaKG-Rec × 3 seed: trước mặt nạ, sau mặt nạ (15) QĐ 4-9 (số chính), sau mặt nạ (16) ∃b (song song, mô tả);
  - LightGCN × 3 seed (checkpoint nội dung 5, không huấn luyện lại): cùng 3 nhánh; "LightGCN" = nhánh trước mặt nạ,
    "LightGCN + mặt nạ" = nhánh QĐ 4-9; hai nhánh lấy từ CÙNG một lần tính điểm (Nam yêu cầu 15/10);
  - KGAT × 3 seed: chỉ trước mặt nạ (kế hoạch mục 3);
  - 2 ablation, seed 1: CaKG-Rec λ1 = 0; CaKG-Rec bỏ suitable_for; cùng 3 nhánh.
  Popularity, MountAware, R-GCN không chấm lại: số và mảng test 09/10 (results/n5/test_final_20261009/).
Mỗi nhánh = eval_cakg.evaluate_with_masks: eval_05.evaluate (full ranking, CVR strict, kịch bản, sampled, loại sản phẩm)
+ CVR_relaxed R1 / R2 + Path Coverage + số người có item cần đoán bị chặn.

Kiểm trước khi chấm (DỪNG nếu sai): cây git sạch, toml và script đã commit (bắt buộc với --split test); mỗi lần chạy có
best.pt đúng sha256, cfg = cfg chốt trừ seed (và phần ablation), git sạch lúc đầu / cuối huấn luyện, best_epoch và NDCG@20
val khớp toml, sha256 code + đầu vào = lần chạy seed 1 cùng mô hình.
Với --split val: so số chấm lại với result.json lúc huấn luyện (trước mặt nạ: "val", sau mặt nạ QĐ 4-9: "val_mask").

Chạy (từ thư mục camera-store):
  thử trên val : ai\\.venv\\Scripts\\python.exe ai/pipeline/06_test_final.py --split val --out results/cakg/<nhãn mới>
  chạy test    : ai\\.venv\\Scripts\\python.exe ai/pipeline/06_test_final.py --split test --out results/cakg/<nhãn mới>
"""

import argparse
import importlib
import json
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

T05 = importlib.import_module("05_test_final")             # build_tables, ms, fmt (dùng lại, không sửa)
T06 = importlib.import_module("06_cakg_train")
T07 = importlib.import_module("07_kgat_train")
X08 = importlib.import_module("08_explain")
FINAL_TOML = C.ROOT / "ai" / "config" / "cakg_final.toml"
N5_TOML = C.ROOT / "ai" / "config" / "n5_final.toml"
N5_TEST = C.ROOT / "results" / "n5" / "test_final_20261009"
BR_ALL = EC.ALL_BRANCHES


def _rel(p):
    return str(Path(p).resolve().relative_to(C.ROOT)).replace("\\", "/")


# -- Kiểm cấu hình chốt và checkpoint --------------------------------------

def check_runs(fin, n5, log):
    """Trả về danh sách lần chạy cần chấm: (nhãn thư mục ra, loại mô hình, seed, thư mục, nhánh)."""
    jobs = []
    for key in ("cakg", "kgat"):
        sec = fin[key]
        assert [r["seed"] for r in sec["runs"]] == fin["chung"]["seeds"], f"{key}: seed"
        s1 = json.loads((C.ROOT / sec["runs"][0]["dir"] / "config.json").read_text(encoding="utf-8"))
        for r in sec["runs"]:
            want = dict(sec["cfg"])
            _check_one(key, r, want, s1, log)
            jobs.append((f"{key}_s{r['seed']}", key, r["seed"], C.ROOT / r["dir"],
                         BR_ALL if key == "cakg" else ("truoc_mat_na",)))
    s1 = json.loads((C.ROOT / fin["cakg"]["runs"][0]["dir"] / "config.json").read_text(encoding="utf-8"))
    for r in fin["ablation"]:
        want = {**fin["cakg"]["cfg"], "lam1": r["lam1"], "drop_suitable_for": r["drop_suitable_for"]}
        _check_one("cakg", r, want, s1, log, tag=f"ablation {r['ten']}")
        jobs.append((f"abl_{r['ten']}_s{r['seed']}", "cakg", r["seed"], C.ROOT / r["dir"], BR_ALL))
    for r in n5["lightgcn"]["runs"]:
        d = C.ROOT / r["dir"]
        assert E.sha256(d / "best.pt") == r["best_pt_sha256"], f"sha256 best.pt LightGCN khác: {d}"
        log(f"  LightGCN seed {r['seed']}: {r['dir']} | best.pt sha256 khớp n5_final.toml")
        jobs.append((f"lightgcn_s{r['seed']}", "lightgcn", r["seed"], d, BR_ALL))
    return jobs


def _check_one(key, r, want, s1, log, tag=None):
    d = C.ROOT / r["dir"]
    c = json.loads((d / "config.json").read_text(encoding="utf-8"))
    res = json.loads((d / "result.json").read_text(encoding="utf-8"))
    assert E.sha256(d / "best.pt") == r["best_pt_sha256"], f"sha256 best.pt khác: {d}"
    cfg = dict(c["cfg"])
    assert cfg.pop("seed") == r["seed"], f"seed khác: {d}"
    want = {k: (list(v) if isinstance(v, tuple) else v) for k, v in want.items()}
    assert cfg == want, f"cấu hình khác cấu hình chốt: {d}\n {cfg}\n {want}"
    assert not c["git"]["dirty"] and not res["git_at_finish"]["dirty"], f"huấn luyện trên cây không sạch: {d}"
    assert c["code_sha256"] == s1["code_sha256"] and c["inputs_sha256"] == s1["inputs_sha256"], \
        f"sha256 code / đầu vào khác lần chạy seed 1: {d}"
    assert res["best_epoch"] == r["best_epoch"] and res["val"]["full"]["ndcg@20"] == r["val_ndcg20"], f"khác toml: {d}"
    log(f"  {tag or key} seed {r['seed']}: {r['dir']} | commit {c['git']['commit'][:7]} | best epoch {r['best_epoch']} / "
        f"chạy {res['epochs_run']} | NDCG@20 val {r['val_ndcg20']:.5f} | "
        f"{'CHƯA CHẮC HỘI TỤ' if res['chua_chac_hoi_tu'] else 'dừng sớm'} | sha256 best.pt, cfg, code khớp")


def load_model(kind, d, train, log):
    if kind == "lightgcn":
        m, _, _ = EC.load_lightgcn(d, train)
        return m
    cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))["cfg"]
    if kind == "cakg":
        m = T06.build_cakg(cfg, train, log=lambda s: None)
    else:
        m = T07.build_kgat(cfg, train, log=lambda s: None)
    m.load_state_dict(torch.load(d / "best.pt", map_location=E.DEVICE, weights_only=False)["model"], strict=True)
    m.eval()
    return m


# -- Bảng ------------------------------------------------------------------

def extra_tables(rl):
    """CVR_relaxed, Path Coverage, người bị chặn: trung bình ± độ lệch chuẩn qua các seed."""
    t = {"cvr_relaxed": {k: T05.ms([r["cvr_relaxed"][k] for r in rl]) for k in rl[0]["cvr_relaxed"]},
         "path_coverage": {k: T05.ms([r["path_coverage"][k] for r in rl]) for k in rl[0]["path_coverage"]}}
    if "n_target_blocked" in rl[0]:
        t["n_target_blocked"] = T05.ms([r["n_target_blocked"] for r in rl])
        t["n_target_blocked_by_scenario"] = {g: T05.ms([r["n_target_blocked_by_scenario"][g] for r in rl])
                                             for g in rl[0]["n_target_blocked_by_scenario"]}
    return t


ROWS = [("CaKG-Rec, trước mặt nạ", "cakg|truoc_mat_na"), ("CaKG-Rec, mặt nạ QĐ 4-9", "cakg|mat_na_qd49"),
        ("CaKG-Rec, mặt nạ ∃b", "cakg|mat_na_exists"), ("LightGCN", "lightgcn|truoc_mat_na"),
        ("LightGCN + mặt nạ QĐ 4-9", "lightgcn|mat_na_qd49"), ("LightGCN + mặt nạ ∃b", "lightgcn|mat_na_exists"),
        ("KGAT", "kgat|truoc_mat_na"),
        ("Ablation λ1 = 0, trước mặt nạ (s1)", "abl_lam1_0|truoc_mat_na"),
        ("Ablation λ1 = 0, mặt nạ QĐ 4-9 (s1)", "abl_lam1_0|mat_na_qd49"),
        ("Ablation bỏ suitable_for, trước mặt nạ (s1)", "abl_bo_suitable_for|truoc_mat_na"),
        ("Ablation bỏ suitable_for, mặt nạ QĐ 4-9 (s1)", "abl_bo_suitable_for|mat_na_qd49")]


def tables_md(T, X, n5T, split):
    f = T05.fmt
    L = [f"# Nội dung 6–8 — kết quả {split} (06_test_final.py)", "",
         "Mô hình học 3 seed: trung bình ± độ lệch chuẩn mẫu; ablation 1 seed. Popularity, R-GCN: số test nội dung 5 "
         "(09/10, không chấm lại). Mọi nhánh của một mô hình lấy từ cùng một lần tính điểm.", "",
         "## 1. Bảng chính", "",
         "| Mô hình | Recall@10 | NDCG@10 | NDCG@20 | CVR@10 | Chỉ ống R@10, lắp được | Chỉ ống R@10, không lắp được |",
         "|---|---|---|---|---|---|---|"]
    rows = [(lab, T.get(k)) for lab, k in ROWS if k in T]
    if n5T is not None:
        rows += [("R-GCN (nội dung 5)", n5T["R-GCN"]), ("Popularity (nội dung 5)", n5T["Popularity"])]
    for lab, t in rows:
        sc = t["scenario"]
        L.append(f"| {lab} | {f(t['full']['recall@10'])} | {f(t['full']['ndcg@10'])} | {f(t['full']['ndcg@20'])} | "
                 f"{f(t['cvr']['cvr@10'])} | {f(sc['lap_duoc']['lens_only']['recall@10'])} | "
                 f"{f(sc['khong_lap_duoc']['lens_only']['recall@10'])} |")
    L += ["", "## 2. CVR strict / relaxed R1 (relaxed chính) / R2 (phụ) @10, người có thân", "",
          "| Mô hình | strict | R1 | R2 | vi phạm | nới R1 | nới R2 | ống chấm được |", "|---|---|---|---|---|---|---|---|"]
    for lab, k in ROWS:
        if k in X:
            r = X[k]["cvr_relaxed"]
            L.append(f"| {lab} | {f(r['cvr_strict@10'])} | {f(r['cvr_relaxed_r1@10'])} | {f(r['cvr_relaxed_r2@10'])} | "
                     f"{f(r['n_violations@10'], 1)} | {f(r['n_relaxed_r1@10'], 1)} | {f(r['n_relaxed_r2@10'], 1)} | "
                     f"{f(r['n_lenses@10'], 1)} |")
    L += ["", "## 3. Mặt nạ: người có item cần đoán bị chặn (tổng; theo nhóm kịch bản)", "",
          "| Mô hình | tổng | lắp được | không lắp được | không phán được |", "|---|---|---|---|---|"]
    for lab, k in ROWS:
        if k in X and "n_target_blocked" in X[k]:
            b = X[k]["n_target_blocked_by_scenario"]
            L.append(f"| {lab} | {f(X[k]['n_target_blocked'], 1)} | {f(b['lap_duoc'], 1)} | {f(b['khong_lap_duoc'], 1)} | "
                     f"{f(b['khong_phan_duoc'], 1)} |")
    L += ["", "## 4. Path Coverage (người có thân)", "",
          "| Mô hình | PC@10 | PC_ngắn@10 | PC_mọi_sp@10 | PC@5 | PC_ngắn@5 |", "|---|---|---|---|---|---|"]
    for lab, k in ROWS:
        if k in X:
            p = X[k]["path_coverage"]
            L.append(f"| {lab} | {f(p['pc@10'])} | {f(p['pc_ngan@10'])} | {f(p['pc_moi_sp@10'])} | {f(p['pc@5'])} | "
                     f"{f(p['pc_ngan@5'])} |")
    L += ["", "## 5. Loại sản phẩm trong top-10; sampled 1+99 (số phụ)", "",
          "| Mô hình | thân | ống | phụ kiện | khác | Hit@10 sampled | NDCG@10 sampled |", "|---|---|---|---|---|---|---|"]
    for lab, k in ROWS:
        if k in T:
            tm, s = T[k]["top10_type_mix"], T[k]["sampled_1_99"]
            L.append(f"| {lab} | " + " | ".join(f(tm[c], 2) for c in ("than", "ong", "phu_kien", "khac"))
                     + f" | {f(s['hit@10'])} | {f(s['ndcg@10'])} |")
    return "\n".join(L) + "\n"


# -- Chính -----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["val", "test"], required=True)
    ap.add_argument("--out", required=True, help="thư mục kết quả mới (đã có thì DỪNG)")
    ap.add_argument("--allow-dirty", action="store_true", help="(chỉ với --split val) cho chạy khi cây git chưa sạch")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    assert not out.exists(), f"thư mục đã có, không ghi đè: {out}"
    git = E.git_state()
    must_track = [FINAL_TOML, N5_TOML, Path(__file__), Path(E.__file__), Path(C.__file__), Path(EC.__file__),
                  Path(T05.__file__), Path(T06.__file__), Path(T07.__file__), Path(X08.__file__)]
    untracked = [str(p) for p in must_track if subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(p)], cwd=C.ROOT, capture_output=True).returncode != 0]
    git["untracked_required"] = untracked
    if (git["dirty"] or untracked) and (a.split == "test" or not a.allow_dirty):
        print(f"DỪNG: cây git chưa sạch hoặc file cần thiết chưa commit ({git}).")
        sys.exit(2)
    if E.DEVICE.type != "cuda":
        print("DỪNG: không thấy GPU.")
        sys.exit(2)
    out.mkdir(parents=True)
    log = E.Log(out / f"run_{a.split}_{E.now_tag()}.log")
    t_all = time.time()
    fin = tomllib.loads(FINAL_TOML.read_text(encoding="utf-8"))
    n5 = tomllib.loads(N5_TOML.read_text(encoding="utf-8"))
    meta = {"split": a.split, "git": git, "cakg_final_toml_sha256": E.sha256(FINAL_TOML),
            "n5_final_toml_sha256": E.sha256(N5_TOML), "script_sha256": E.sha256(Path(__file__)),
            "eval_cakg_sha256": E.sha256(Path(EC.__file__)), "inputs_sha256": E.inputs_sha256(),
            "device": f"{E.DEVICE} ({torch.cuda.get_device_name(0)})", "torch": torch.__version__,
            "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    log(f"06_test_final | split {a.split} | git {git} | {meta['device']} | torch {meta['torch']}")
    log(f"cakg_final.toml sha256 {meta['cakg_final_toml_sha256']} | script sha256 {meta['script_sha256']}")
    if a.split == "val":
        log("CHẾ ĐỘ THỬ TRÊN VAL (không chấm test).")
    log("\nKiểm các lần chạy:")
    jobs = check_runs(fin, n5, log)

    ev = E.EvalContext(a.split)
    sp = ev.split
    masks = EC.masks_on_device(ev)
    rc = EC.relaxed_context(ev.train, ev.bodies)
    pctx = EC.PathContext(ev.train, ev.item_type)
    log(f"\nTập {a.split}: {len(sp.users):,} người dùng; người có thân {len(ev.bodies):,}; kịch bản: "
        + ", ".join(f"{g} {int((ev.scn_lab == g).sum()):,}" for g in ("lap_duoc", "khong_lap_duoc", "khong_phan_duoc")))

    results, extras, dirs, checks = {}, {}, {}, {}
    for name, kind, seed, rd, branches in jobs:
        d = out / name
        log(f"\n=== {name} ({_rel(rd)}) ===")
        model = load_model(kind, rd, ev.train, log)
        res = EC.evaluate_with_masks(model.score_fn(), ev, rc, pctx, log=log, save_dir=d, tag=f"{name} ",
                                     branches=branches, masks=masks)
        group = name.rsplit("_s", 1)[0] if name.startswith("abl_") else kind
        for br, r in res.items():
            r["checkpoint"] = {"dir": _rel(rd), "seed": seed}
            results.setdefault(f"{group}|{br}", []).append(r)
            dirs.setdefault(f"{group}|{br}", []).append(_rel(d))
        if a.split == "val":
            old = json.loads((rd / "result.json").read_text(encoding="utf-8"))
            pairs = [("truoc_mat_na", old["val"]["full"])]
            if "val_mask" in old and "mat_na_qd49" in res:
                pairs.append(("mat_na_qd49", old["val_mask"]["full"]))
            for br, o in pairs:
                diff = max(abs(res[br]["full"][k] - o[k]) for k in o)
                checks[f"{name}|{br}"] = diff
                log(f"  so với result.json lúc huấn luyện ({br}): lệch tuyệt đối lớn nhất {diff:.2e} "
                    f"(NDCG@20 {res[br]['full']['ndcg@20']:.6f} / {o['ndcg@20']:.6f})")
        if kind == "lightgcn" and a.split == "test":
            old_rank = np.load(N5_TEST / f"lightgcn_s{seed}" / "rank_full.npy")
            new_rank = np.load(d / "test_truoc_mat_na_rank_full.npy")
            checks[f"{name}|so_voi_0910"] = int((old_rank != new_rank).sum())
            log(f"  LightGCN trước mặt nạ so với mảng test 09/10: {int((old_rank != new_rank).sum()):,} người có hạng khác "
                f"(GPU không tất định)")
        (d / "result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
        del model
        torch.cuda.empty_cache()

    log("\n=== Tổng hợp ===")
    T = T05.build_tables(results)
    X = {k: extra_tables(v) for k, v in results.items()}
    n5T = None
    if a.split == "test":
        n5s = sorted(N5_TEST.glob("summary_test_*.json"))
        assert len(n5s) == 1
        n5T = json.loads(n5s[0].read_text(encoding="utf-8"))["tables"]
        meta["n5_summary"] = {"file": _rel(n5s[0]), "sha256": E.sha256(n5s[0])}
    meta["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    meta["minutes"] = round((time.time() - t_all) / 60, 1)
    tag = E.now_tag()
    (out / f"summary_{a.split}_{tag}.json").write_text(json.dumps(
        {"meta": meta, "runs": dirs, "tables": T, "extra": X, "checks": checks}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    md = tables_md(T, X, n5T, a.split)
    (out / f"summary_{a.split}_{tag}.md").write_text(md, encoding="utf-8")
    log("\n" + md)
    log(f"-> {out / f'summary_{a.split}_{tag}.json'} ({meta['minutes']} phút)")
    log.close()


if __name__ == "__main__":
    main()
