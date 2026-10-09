"""
05_test_final.py -- Chấm một lần 4 baseline nội dung 5 trên test (docs/reviews/n5_eval_plan.md mục 7.2 bước 5).
Viết 09/10/2026 (lỗi L12, L15 còn lại của kế hoạch mục 2: 3 seed, bảng tổng hợp, bootstrap).

Mô hình: Popularity, Popularity-MountAware (05a), LightGCN × 3 seed (05b), R-GCN × 3 seed (05c); checkpoint và cấu
hình đọc từ ai/config/n5_final.toml. Mỗi mô hình chấm bằng eval_05.evaluate, tức:
  - full ranking (số chính): ứng viên = mọi sản phẩm trừ train, chấm test thì bỏ thêm item val (QĐ 5-1);
    Recall / NDCG / Hit @5/10/20; quy tắc hòa π;
  - CVR@K (QĐ 4-9) từ top-K đó;
  - kịch bản "ống cho người đã có thân": chỉ ống (số chính), toàn catalog (số phụ), tách nhóm lắp được / không lắp được;
  - sampled 1+99 (số phụ).
Rồi tổng hợp: mô hình học báo trung bình ± độ lệch chuẩn mẫu (ddof = 1) qua 3 seed; bootstrap ghép cặp theo người
dùng (B = 2000, seed 20261009) cho 5 so sánh đăng ký trước S1–S5 (mục 8). Chỉ số từng người của mô hình học = trung
bình qua 3 seed; CVR của mô hình học = (tổng vi phạm 3 seed) / (tổng ống chấm được 3 seed).

Ví dụ bootstrap (S1, 3 người): Hit@10 của LightGCN theo seed = (1,1,0), (0,0,0), (1,1,1) -> từng người 2/3, 0, 1;
Popularity 0, 0, 1. Một lần lấy mẫu chọn người {1, 1, 3} -> LightGCN (2/3 + 2/3 + 1)/3 = 0,778, Popularity 1/3,
hiệu 0,444. Lặp 2000 lần trên CÙNG các mẫu người cho mọi mô hình; khoảng 95% = phân vị 2,5% – 97,5% của hiệu.

Kiểm trước khi chấm (DỪNG nếu sai): cây git sạch (bắt buộc với --split test); mỗi lần chạy trong toml có best.pt đúng
sha256, result.json, config.json trùng cấu hình chốt trừ seed, cùng commit huấn luyện, dirty = False, best_epoch khớp.

Chạy (từ thư mục camera-store):
  thử trên val : ai\\.venv\\Scripts\\python.exe ai/pipeline/05_test_final.py --split val --out results/n5/<nhãn mới>
  chạy test    : ai\\.venv\\Scripts\\python.exe ai/pipeline/05_test_final.py --split test --out results/n5/<nhãn mới>
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
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

P05A = importlib.import_module("05a_popularity")
P05B = importlib.import_module("05b_lightgcn_train")
P05C = importlib.import_module("05c_rgcn_train")

FINAL_TOML = C.ROOT / "ai" / "config" / "n5_final.toml"
SCN_GROUPS = ("lap_duoc", "khong_lap_duoc")          # hai nhóm đem so (khong_phan_duoc chỉ báo số người)
MODELS = ("Popularity", "Popularity-MountAware", "LightGCN", "R-GCN")
SHORT = {"Popularity": "pop", "Popularity-MountAware": "popma", "LightGCN": "lightgcn", "R-GCN": "rgcn"}


# -- Kiểm cấu hình chốt và checkpoint --------------------------------------

def check_runs(cfg, log):
    """Kiểm 6 lần chạy trong n5_final.toml. Trả về {mô hình: [(seed, thư mục)]}."""
    out = {}
    for key, name in (("lightgcn", "LightGCN"), ("rgcn", "R-GCN")):
        sec = cfg[key]
        seeds = [r["seed"] for r in sec["runs"]]
        assert seeds == cfg["chung"]["seeds"], f"{key}: seed {seeds}"
        out[name] = []
        for r in sec["runs"]:
            d = C.ROOT / r["dir"]
            assert (d / "result.json").exists(), f"thiếu {d / 'result.json'}"
            assert E.sha256(d / "best.pt") == r["best_pt_sha256"], f"sha256 best.pt khác: {d}"
            c = json.loads((d / "config.json").read_text(encoding="utf-8"))
            res = json.loads((d / "result.json").read_text(encoding="utf-8"))
            run_cfg = dict(c["cfg"])
            assert run_cfg.pop("seed") == r["seed"], f"seed khác: {d}"
            assert run_cfg == sec["cfg"], f"cấu hình khác cấu hình chốt: {d}\n {run_cfg}\n {sec['cfg']}"
            for g in (c["git"], res["git_at_finish"]):
                assert g == {"commit": cfg["chung"]["commit_huan_luyen"], "dirty": False}, f"git khác: {d} {g}"
            assert res["best_epoch"] == r["best_epoch"], f"best_epoch khác: {d}"
            assert res["chua_chac_hoi_tu"] == sec["chua_chac_hoi_tu"], f"cờ hội tụ khác: {d}"
            assert res["val"]["full"]["ndcg@20"] == r["val_ndcg20"], f"NDCG@20 val khác: {d}"
            log(f"  {name} seed {r['seed']}: {r['dir']} | best epoch {r['best_epoch']} / chạy {res['epochs_run']}"
                f" | NDCG@20 val {r['val_ndcg20']:.5f} | "
                f"{'CHƯA CHẮC HỘI TỤ' if res['chua_chac_hoi_tu'] else 'dừng sớm'} | best.pt sha256 khớp")
            out[name].append((r["seed"], d))
    return out


def load_model(name, run_dir, train, log):
    """Dựng mô hình đúng như lúc huấn luyện (05b / 05c) rồi nạp best.pt; trả về mô hình ở chế độ eval."""
    ck = torch.load(run_dir / "best.pt", map_location=E.DEVICE, weights_only=False)
    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))["cfg"]
    if name == "LightGCN":
        adj = P05B.build_norm_adj(train, C.N_USERS, C.N_ITEMS).to(E.DEVICE)
        m = P05B.LightGCN(C.N_USERS, C.N_ITEMS, cfg["dim"], cfg["n_layers"], adj, cfg["l2"])
    else:
        ei, et, names, n, offs = P05C.load_homogeneous(train, log)
        m = P05C.RGCN(n, cfg["dim"], len(names), cfg["num_bases"], ei.to(E.DEVICE), et.to(E.DEVICE), offs["user"],
                      offs["item"], cfg["edge_dropout"], cfg["l2_decoder"])
    m = m.to(E.DEVICE)
    m.load_state_dict(ck["model"], strict=True)
    m.eval()
    return m, int(ck["epoch"])


# -- Mảng từng người dùng đã lưu --------------------------------------------

def load_arrays(d, prefix=""):
    def ld(nm):
        return np.load(d / f"{prefix}{nm}.npy")
    a = {"users": ld("users"), "rank": ld("rank_full"), "scn_users": ld("scn_users"),
         "rank_lens": ld("rank_lens_only"), "rank_sampled": ld("rank_sampled")}
    for k in E.K_LIST:
        a[f"nl@{k}"] = ld(f"cvr_n_lenses_at{k}")
        a[f"nv@{k}"] = ld(f"cvr_n_viol_at{k}")
    return a


def hit(rank, k):
    return (rank <= k).astype(np.float64)


def ndcg(rank, k):
    return np.where(rank <= k, 1.0 / np.log2(rank + 1.0), 0.0)


# -- Bảng ------------------------------------------------------------------

def ms(vals):
    """Trung bình ± độ lệch chuẩn mẫu (ddof = 1); một giá trị thì sd = None."""
    v = np.asarray(vals, dtype=np.float64)
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)) if len(v) > 1 else None,
            "per_seed": [float(x) for x in v]}


def fmt(d, nd=4):
    if d is None:
        return "—"
    if isinstance(d, dict):
        if np.isnan(d["mean"]):
            return "nan"
        return f"{d['mean']:.{nd}f}" + (f" ± {d['sd']:.{nd}f}" if d["sd"] is not None else "")
    return "nan" if np.isnan(d) else f"{d:.{nd}f}"


def get(res_list, path):
    """res_list: các dict kết quả evaluate (1 cho Popularity, 3 cho mô hình học); path: ('full', 'recall@10')."""
    vals = []
    for r in res_list:
        x = r
        for p in path:
            x = x[p]
        vals.append(x)
    return ms(vals)


def build_tables(results):
    """results: {mô hình: [res của evaluate]} -> dict bảng tổng hợp (mean ± sd)."""
    T = {}
    for m, rl in results.items():
        t = {"n_seeds": len(rl)}
        t["full"] = {f"{x}@{k}": get(rl, ("full", f"{x}@{k}")) for k in E.K_LIST for x in ("recall", "ndcg", "hit")}
        t["cvr"] = {f"cvr@{k}": get(rl, ("cvr", f"cvr@{k}")) for k in E.K_LIST}
        for k in E.K_LIST:
            for x in ("cvr_n_users", "cvr_n_lenses", "cvr_n_violations"):
                t["cvr"][f"{x}@{k}"] = get(rl, ("cvr", f"{x}@{k}"))
        t["cvr"]["cvr_n_users_with_body"] = rl[0]["cvr"]["cvr_n_users_with_body"]
        t["top10_type_mix"] = {c: get(rl, ("top10_type_mix", c)) for c in rl[0]["top10_type_mix"]}
        t["n_users_tie_at_target"] = get(rl, ("n_users_tie_at_target",))
        t["sampled_1_99"] = {k: get(rl, ("sampled_1_99", k)) for k in rl[0]["sampled_1_99"]}
        t["scenario"] = {}
        for g, d in rl[0]["scenario"].items():
            s = {"n_users": d["n_users"], "n_with_adapter_pair": d["n_with_adapter_pair"]}
            if d["n_users"]:
                s["lens_only"] = {k: get(rl, ("scenario", g, "lens_only", k)) for k in d["lens_only"]}
                s["lens_only_cvr"] = {k: get(rl, ("scenario", g, "lens_only_cvr", k)) for k in d["lens_only_cvr"]}
                s["full_catalog"] = {k: get(rl, ("scenario", g, "full_catalog", k)) for k in d["full_catalog"]}
            t["scenario"][g] = s
        T[m] = t
    return T


def tables_md(T, split, boot):
    L = [f"# Nội dung 5 — kết quả {split} (05_test_final.py)", ""]
    L.append("Mô hình học: trung bình ± độ lệch chuẩn mẫu qua 3 seed. Popularity / MountAware: một giá trị.")
    L += ["", "## 1. Full ranking (số chính), mọi người dùng", "",
          "| Mô hình | Recall@10 | NDCG@10 | Recall@20 | NDCG@20 | CVR@10 | CVR@20 |", "|---|---|---|---|---|---|---|"]
    for m in MODELS:
        t = T[m]
        L.append(f"| {m} | " + " | ".join(fmt(t["full"][x]) for x in ("recall@10", "ndcg@10", "recall@20", "ndcg@20"))
                 + f" | {fmt(t['cvr']['cvr@10'])} | {fmt(t['cvr']['cvr@20'])} |")
    L += ["", "Đủ K (Recall@K = Hit@K từng người, script đã kiểm):", "",
          "| Mô hình | " + " | ".join(f"{x}@{k}" for k in E.K_LIST for x in ("Recall", "NDCG")) + " |",
          "|---|" + "---|" * 6]
    for m in MODELS:
        L.append(f"| {m} | " + " | ".join(fmt(T[m]["full"][f"{x}@{k}"]) for k in E.K_LIST
                                          for x in ("recall", "ndcg")) + " |")
    L += ["", "CVR@K chi tiết (người dùng được tính / ống chấm được / vi phạm; mô hình học: trung bình 3 seed):", "",
          "| Mô hình | K | CVR | người được tính | ống chấm được | vi phạm |", "|---|---|---|---|---|---|"]
    for m in MODELS:
        c = T[m]["cvr"]
        for k in E.K_LIST:
            L.append(f"| {m} | {k} | {fmt(c[f'cvr@{k}'])} | {c[f'cvr_n_users@{k}']['mean']:,.1f} | "
                     f"{c[f'cvr_n_lenses@{k}']['mean']:,.1f} | {c[f'cvr_n_violations@{k}']['mean']:,.1f} |")
    L.append(f"\nNgười có thân trong train: {T['Popularity']['cvr']['cvr_n_users_with_body']:,}.")
    L += ["", "Loại sản phẩm trung bình trong top-10 và số người có item cần đoán bị hòa điểm:", "",
          "| Mô hình | thân | ống | phụ kiện | khác | người bị hòa |", "|---|---|---|---|---|---|"]
    for m in MODELS:
        tm = T[m]["top10_type_mix"]
        L.append(f"| {m} | " + " | ".join(fmt(tm[c], 2) for c in ("than", "ong", "phu_kien", "khac"))
                 + f" | {fmt(T[m]['n_users_tie_at_target'], 1)} |")

    L += ["", "## 2. Kịch bản \"ống cho người đã có thân\"", ""]
    sc0 = T["Popularity"]["scenario"]
    L.append("Số người: " + ", ".join(f"{g} {sc0[g]['n_users']:,}" for g in sc0)
             + f" (không lắp được có cặp requires_adapter: {sc0['khong_lap_duoc']['n_with_adapter_pair']:,}).")
    for title, part in (("Chỉ ống (số chính)", "lens_only"), ("Toàn catalog (số phụ)", "full_catalog")):
        L += ["", f"### {title}", "", "| Nhóm | Mô hình | Recall@10 | NDCG@10 | Recall@20 | NDCG@20"
              + (" | CVR@10 | CVR@20 |" if part == "lens_only" else " |"),
              "|---|---|---|---|---|---" + ("|---|---|" if part == "lens_only" else "|")]
        for g in SCN_GROUPS:
            for m in MODELS:
                s = T[m]["scenario"][g]
                row = f"| {g} | {m} | " + " | ".join(fmt(s[part][x]) for x in
                                                     ("recall@10", "ndcg@10", "recall@20", "ndcg@20"))
                if part == "lens_only":
                    row += f" | {fmt(s['lens_only_cvr']['cvr@10'])} | {fmt(s['lens_only_cvr']['cvr@20'])}"
                L.append(row + " |")

    L += ["", "## 3. Sampled 1+99 (số phụ) đặt cạnh full ranking", "",
          "| Mô hình | Hit@10 sampled | NDCG@10 sampled | Hit@20 sampled | Recall@10 full | NDCG@10 full |",
          "|---|---|---|---|---|---|"]
    for m in MODELS:
        t = T[m]
        L.append(f"| {m} | {fmt(t['sampled_1_99']['hit@10'])} | {fmt(t['sampled_1_99']['ndcg@10'])} | "
                 f"{fmt(t['sampled_1_99']['hit@20'])} | {fmt(t['full']['recall@10'])} | {fmt(t['full']['ndcg@10'])} |")
    for lab, key in (("full ranking NDCG@10", ("full", "ndcg@10")), ("sampled NDCG@10", ("sampled_1_99", "ndcg@10")),
                     ("sampled Hit@10", ("sampled_1_99", "hit@10"))):
        order = sorted(MODELS, key=lambda m: -T[m][key[0]][key[1]]["mean"])
        L.append(f"\nThứ tự theo {lab}: " + " > ".join(order))

    L += ["", "## 4. Bootstrap ghép cặp theo người dùng (B = 2000, seed 20261009), khoảng 95% phân vị", "",
          "| So sánh | Chỉ số | Tập | Hiệu | Khoảng 95% | Khác 0? |", "|---|---|---|---|---|---|"]
    for row in boot["comparisons"]:
        lo, hi = row["ci"]
        L.append(f"| {row['id']} {row['name']} | {row['metric']} | {row['set']} | {row['diff']:+.5f} | "
                 f"[{lo:+.5f}, {hi:+.5f}] | {'có' if (lo > 0 or hi < 0) else 'không'} |")
    L += ["", "Ghi chú: CVR của mô hình học trong bảng 1 = trung bình ± độ lệch chuẩn của CVR từng seed; trong bootstrap "
          "= (tổng vi phạm 3 seed) / (tổng ống chấm được 3 seed) (kế hoạch mục 8), nên hai số có thể khác nhau. "
          "Chỉ số từng người của mô hình học trong bootstrap = trung bình qua 3 seed.",
          "", "Khoảng 95% của từng mô hình (mô tả):", "", "| Tập | Chỉ số | Mô hình | Giá trị | Khoảng 95% |",
          "|---|---|---|---|---|"]
    for row in boot["per_model"]:
        L.append(f"| {row['set']} | {row['metric']} | {row['model']} | {row['value']:.4f} | "
                 f"[{row['ci'][0]:.4f}, {row['ci'][1]:.4f}] |")
    return "\n".join(L) + "\n"


# -- Bootstrap -------------------------------------------------------------

def run_bootstrap(arrs, ev, log, B, seed):
    """arrs: {mô hình: [mảng từng người của mỗi seed]}. 5 so sánh đăng ký trước (mục 8) + khoảng từng mô hình."""
    users = arrs["Popularity"][0]["users"]
    for m in MODELS:
        for a in arrs[m]:
            assert np.array_equal(a["users"], users) and np.array_equal(a["scn_users"], arrs["Popularity"][0]["scn_users"])

    def avg(m, f):                          # chỉ số từng người, trung bình qua các seed
        return np.mean([f(a) for a in arrs[m]], axis=0)

    def tot(m, key):                        # cộng qua các seed (CVR của mô hình học)
        return np.sum([a[key] for a in arrs[m]], axis=0).astype(np.float64)

    comps, per_model = [], []
    t0 = time.time()

    # (a) mọi người dùng: Recall@10, NDCG@10 (đăng ký trước), @20 chỉ mô tả
    ser = {}
    for m in MODELS:
        for k in (10, 20):
            ser[f"{m}|recall@{k}"] = (avg(m, lambda a, k=k: hit(a["rank"], k)), None)
            ser[f"{m}|ndcg@{k}"] = (avg(m, lambda a, k=k: ndcg(a["rank"], k)), None)
    pairs = [("LightGCN|recall@10", "Popularity|recall@10"), ("LightGCN|ndcg@10", "Popularity|ndcg@10"),
             ("R-GCN|recall@10", "LightGCN|recall@10"), ("R-GCN|ndcg@10", "LightGCN|ndcg@10"),
             ("Popularity-MountAware|recall@10", "Popularity|recall@10")]
    bs = E.bootstrap_paired(ser, pairs=pairs, B=B, seed=seed)
    tag = {pairs[0]: "S1", pairs[1]: "S1", pairs[2]: "S2", pairs[3]: "S2", pairs[4]: "S3"}
    for a, b in pairs:
        v = bs[f"{a} - {b}"]
        comps.append({"id": tag[(a, b)], "name": f"{a.split('|')[0]} − {b.split('|')[0]}", "metric": a.split("|")[1],
                      "set": f"mọi người dùng ({len(users):,})", "diff": v[0], "ci": [v[1], v[2]]})
    for nm in ser:
        per_model.append({"set": "mọi người dùng", "model": nm.split("|")[0], "metric": nm.split("|")[1],
                          "value": bs[nm][0], "ci": [bs[nm][1], bs[nm][2]]})
    log(f"  bootstrap (a) mọi người dùng xong ({time.time() - t0:.0f}s)")

    # (b) người có thân: CVR@10 (S3, S4), @20 mô tả
    sel = np.array([u in ev.bodies for u in users.tolist()])
    ser = {}
    for m in MODELS:
        for k in (10, 20):
            ser[f"{m}|cvr@{k}"] = (tot(m, f"nv@{k}")[sel], tot(m, f"nl@{k}")[sel])
    pairs_b = [("Popularity-MountAware|cvr@10", "Popularity|cvr@10"), ("R-GCN|cvr@10", "LightGCN|cvr@10")]
    bs = E.bootstrap_paired(ser, pairs=pairs_b, B=B, seed=seed)
    for (a, b), sid in zip(pairs_b, ("S3", "S4")):
        v = bs[f"{a} - {b}"]
        comps.append({"id": sid, "name": f"{a.split('|')[0]} − {b.split('|')[0]}", "metric": "cvr@10",
                      "set": f"người có thân ({int(sel.sum()):,})", "diff": v[0], "ci": [v[1], v[2]]})
    for nm in ser:
        per_model.append({"set": "người có thân", "model": nm.split("|")[0], "metric": nm.split("|")[1],
                          "value": bs[nm][0], "ci": [bs[nm][1], bs[nm][2]]})
    log(f"  bootstrap (b) người có thân xong ({time.time() - t0:.0f}s)")

    # (c) kịch bản, chỉ ống, từng nhóm: Recall@10 (S5), NDCG@10 mô tả
    lab = {int(u): g for u, g in zip(ev.split.users.tolist(), ev.scn_lab.tolist())}
    scn_users = arrs["Popularity"][0]["scn_users"]
    glab = np.array([lab[int(u)] for u in scn_users])
    for g in SCN_GROUPS:
        gs = glab == g
        ser = {}
        for m in MODELS:
            ser[f"{m}|recall@10"] = (avg(m, lambda a: hit(a["rank_lens"], 10))[gs], None)
            ser[f"{m}|ndcg@10"] = (avg(m, lambda a: ndcg(a["rank_lens"], 10))[gs], None)
        pr = ("Popularity-MountAware|recall@10", "Popularity|recall@10")
        bs = E.bootstrap_paired(ser, pairs=[pr], B=B, seed=seed)
        v = bs[f"{pr[0]} - {pr[1]}"]
        comps.append({"id": "S5", "name": "Popularity-MountAware − Popularity", "metric": "recall@10 (chỉ ống)",
                      "set": f"kịch bản {g} ({int(gs.sum()):,})", "diff": v[0], "ci": [v[1], v[2]]})
        for nm in ser:
            per_model.append({"set": f"kịch bản {g}, chỉ ống", "model": nm.split("|")[0], "metric": nm.split("|")[1],
                              "value": bs[nm][0], "ci": [bs[nm][1], bs[nm][2]]})
    log(f"  bootstrap (c) kịch bản xong ({time.time() - t0:.0f}s)")
    return {"B": B, "seed": seed, "comparisons": comps, "per_model": per_model}


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
    # git_state bỏ qua file chưa theo dõi: kiểm riêng là toml và các script 05 đã được commit
    must_track = [FINAL_TOML, Path(__file__), Path(E.__file__), Path(C.__file__), Path(P05A.__file__),
                  Path(P05B.__file__), Path(P05C.__file__)]
    untracked = [str(p) for p in must_track if subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(p)], cwd=C.ROOT, capture_output=True).returncode != 0]
    git["untracked_required"] = untracked
    if (git["dirty"] or untracked) and (a.split == "test" or not a.allow_dirty):
        print(f"DỪNG: cây git chưa sạch hoặc file cần thiết chưa commit ({git}). Commit trước khi chạy"
              + (" test." if a.split == "test" else "."))
        sys.exit(2)
    if E.DEVICE.type != "cuda":
        print("DỪNG: không thấy GPU.")
        sys.exit(2)
    out.mkdir(parents=True)
    log = E.Log(out / f"run_{a.split}_{E.now_tag()}.log")
    t_all = time.time()
    cfg = tomllib.loads(FINAL_TOML.read_text(encoding="utf-8"))
    meta = {"split": a.split, "git": git, "n5_final_toml_sha256": E.sha256(FINAL_TOML),
            "script_sha256": E.sha256(Path(__file__)), "inputs_sha256": E.inputs_sha256(),
            "device": f"{E.DEVICE} ({torch.cuda.get_device_name(0)})", "torch": torch.__version__,
            "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    log(f"05_test_final | split {a.split} | git {git} | {meta['device']} | torch {meta['torch']}")
    log(f"n5_final.toml sha256 {meta['n5_final_toml_sha256']} | script sha256 {meta['script_sha256']}")
    if a.split == "val":
        log("CHẾ ĐỘ THỬ TRÊN VAL (không chấm test).")

    log("\nKiểm 6 lần chạy trong n5_final.toml:")
    runs = check_runs(cfg, log)

    ev = E.EvalContext(a.split)
    sp = ev.split
    log(f"\nTập {a.split}: {len(sp.users):,} người dùng; sản phẩm bị loại khỏi ứng viên trung bình "
        f"{len(sp.excl_col) / len(sp.users):.2f}/người ({'train + item val' if a.split == 'test' else 'train'}); "
        f"người có thân {len(ev.bodies):,}")
    log(f"kịch bản: " + ", ".join(f"{g} {int((ev.scn_lab == g).sum()):,}"
                                 for g in ("lap_duoc", "khong_lap_duoc", "khong_phan_duoc"))
        + f" | không lắp được có cặp requires_adapter {int(ev.scn_adp.sum()):,}")

    results, arrs, per_dirs = {m: [] for m in MODELS}, {m: [] for m in MODELS}, {}

    # Popularity, MountAware
    pop = P05A.build_pop_scores(ev.train)
    lens_cols, viol = E.certain_violation_mask(ev.bodies, ev.ctx)
    log(f"MountAware: {int(viol.any(1).sum()):,} người có ít nhất 1 ống bị lọc")
    for m, scorer in (("Popularity", P05A.global_scorer(pop)),
                      ("Popularity-MountAware", P05A.mountaware_scorer(pop, lens_cols, viol))):
        d = out / SHORT[m]
        d.mkdir()
        log(f"\n=== {m} ===")
        res = E.evaluate(scorer, ev, log=log, save_dir=d)
        if m == "Popularity-MountAware":
            bad = {k: res["cvr"][f"cvr_n_violations@{k}"] for k in E.K_LIST}
            bad_l = {f"{g}@{k}": v["lens_only_cvr"][f"cvr@{k}"] for g, v in res["scenario"].items() if v["n_users"]
                     for k in E.K_LIST}
            log(f"kiểm: vi phạm của MountAware (toàn catalog) = {bad}; CVR kịch bản chỉ ống = {bad_l}")
            assert all(v == 0 for v in bad.values()), "CVR của MountAware khác 0 -> lỗi code"
            assert all(v == 0 or np.isnan(v) for v in bad_l.values()), "CVR kịch bản của MountAware khác 0"
        (d / "result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
        results[m].append(res)
        arrs[m].append(load_arrays(d))
        per_dirs[m] = [str(d.relative_to(C.ROOT)).replace("\\", "/")]

    # LightGCN, R-GCN × 3 seed
    for m in ("LightGCN", "R-GCN"):
        per_dirs[m] = []
        for seed, rd in runs[m]:
            d = out / f"{SHORT[m]}_s{seed}"
            d.mkdir()
            log(f"\n=== {m} seed {seed} ({rd.relative_to(C.ROOT)}) ===")
            model, ep = load_model(m, rd, ev.train, log)
            log(f"  nạp best.pt: epoch {ep}")
            res = E.evaluate(model.score_fn(), ev, log=log, save_dir=d)
            res["checkpoint"] = {"dir": str(rd.relative_to(C.ROOT)).replace("\\", "/"), "epoch": ep}
            if a.split == "val":
                old = json.loads((rd / "result.json").read_text(encoding="utf-8"))["val"]["full"]
                diff = max(abs(res["full"][k] - old[k]) for k in old)
                log(f"  so với result.json lúc huấn luyện (val): lệch tuyệt đối lớn nhất {diff:.2e} "
                    f"(NDCG@20 {res['full']['ndcg@20']:.6f} / {old['ndcg@20']:.6f})")
                res["val_max_abs_diff_vs_training"] = diff
            (d / "result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
            results[m].append(res)
            arrs[m].append(load_arrays(d))
            per_dirs[m].append(str(d.relative_to(C.ROOT)).replace("\\", "/"))
            del model
            torch.cuda.empty_cache()

    log("\n=== Tổng hợp ===")
    T = build_tables(results)
    log("=== Bootstrap ghép cặp ===")
    boot = run_bootstrap(arrs, ev, log, B=cfg["chung"]["bootstrap_B"], seed=cfg["chung"]["bootstrap_seed"])
    for row in boot["comparisons"]:
        lo, hi = row["ci"]
        log(f"  {row['id']} {row['name']:<36} {row['metric']:<20} {row['set']:<32} hiệu {row['diff']:+.5f} "
            f"[{lo:+.5f}, {hi:+.5f}] {'KHÁC 0' if (lo > 0 or hi < 0) else 'chứa 0'}")

    meta["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    meta["minutes"] = round((time.time() - t_all) / 60, 1)
    summary = {"meta": meta, "runs": per_dirs, "tables": T, "bootstrap": boot}
    tag = E.now_tag()
    (out / f"summary_{a.split}_{tag}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                                                       encoding="utf-8")
    md = tables_md(T, a.split, boot)
    (out / f"summary_{a.split}_{tag}.md").write_text(md, encoding="utf-8")
    log("\n" + md)
    log(f"-> {out / f'summary_{a.split}_{tag}.json'} ({meta['minutes']} phút)")
    log.close()


if __name__ == "__main__":
    main()
