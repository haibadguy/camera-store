"""In mọi bảng số của chương 2 quyển đồ án (dạng markdown, số theo kiểu Việt Nam) vào một log tên mới.

CHỈ ĐỌC. Không huấn luyện, không chấm lại mô hình, không mở mảng theo từng người. Mọi số lấy từ:
- dữ liệu: ai/data/processed/filtering_stats.json, train.txt / val.txt / test.txt, ai/data/kg/kg_stats.json,
  ai/data/kg/mount_compat_stats.json, ai/config/mount_rules.toml;
- độ chính xác phân loại / ngàm (lần đo 3) và tiêu cự / khẩu độ: log đã có
  ai/data/survey/n3_lan3/run_measure_holdout_20261008.log, ai/data/survey/n4_fa/run_fa_eval_holdout_20261008.log;
- dò trên val: results/n5/val_sweep_20261010/summary_*.json, results/cakg/val_sweep_20261014/summary_*.json,
  results/cakg/val_sweep_v2_20261016/select_*/select.json, results/cakg/val_sweep_v2seeds_20261016/dung2_*/dung2.json;
- test lần 1 (đã chấm, 3 seed): results/n5/test_final_20261009/summary_test_*.json,
  results/cakg/test_final_20261015/summary_test_*.json, compare_test_*.json, explain_s*/summary.json;
- phân tích sau test (chỉ đọc mảng đã lưu): ai/data/survey/redteam/run_redteam_cakg_b_20261015_lan1.log;
- giải thích hệ thống cuối: results/final_system/explain_test_20261016/summary.json, explanations.jsonl;
- thời gian / VRAM / độ trễ: result.json của các lần chạy, latency.json của CaKG-Rec.

Chạy (cwd bất kỳ):
  E:\\DATN\\camera-store\\ai\\.venv\\Scripts\\python.exe ai/survey/report_c2/bang_c2.py --root E:/DATN/camera-store --label 20261017_lan1
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2_common import Inputs, Log, header, vn_dec, vn_int, vn_pct  # noqa: E402

N5_SUMMARY = "results/n5/test_final_20261009/summary_test_*.json"
CAKG_SUMMARY = "results/cakg/test_final_20261015/summary_test_*.json"
CAKG_COMPARE = "results/cakg/test_final_20261015/compare_test_*.json"
RT_LOG_B = "ai/data/survey/redteam/run_redteam_cakg_b_20261015_lan1.log"
N3_LOG = "ai/data/survey/n3_lan3/run_measure_holdout_20261008.log"
N4_LOG = "ai/data/survey/n4_fa/run_fa_eval_holdout_20261008.log"
FINAL_EXPLAIN = "results/final_system/explain_test_20261016/summary.json"
FINAL_SENT = "results/final_system/explain_test_20261016/lightgcn_s1/explanations.jsonl"
CAKG_LAT = "results/cakg/val_sweep_20261014/val_cakg_lam1-1e-01_s1/latency_test_20261015/latency.json"


def one(inp, pattern):
    files = sorted(glob.glob(os.path.join(inp.root, pattern)))
    assert len(files) == 1, (pattern, files)
    return os.path.relpath(files[0], inp.root).replace("\\", "/")


def jload(inp, rel):
    with open(inp.path(rel), encoding="utf-8") as f:
        return json.load(f)


def ms(d, dec=4):
    """'mean ± sd' (sd bỏ khi chỉ có 1 seed)."""
    if d.get("sd") in (None, 0) and len(d.get("per_seed", [0])) <= 1:
        return vn_dec(d["mean"], dec)
    return f"{vn_dec(d['mean'], dec)} ± {vn_dec(d['sd'] or 0, dec)}"


def ci(lo, hi, dec):
    return f"[{vn_dec(lo, dec, True)}; {vn_dec(hi, dec, True)}]"


def table(log, title, head, rows):
    log("")
    log(f"### {title}")
    log("")
    log("| " + " | ".join(head) + " |")
    log("|" + "|".join("---" for _ in head) + "|")
    for r in rows:
        log("| " + " | ".join(str(x) for x in r) + " |")


def count_lines(path):
    n_lines, n_items = 0, 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.split()
            if p:
                n_lines += 1
                n_items += len(p) - 1
    return n_lines, n_items


# --------------------------------------------------------------------------- dữ liệu (2.2, 2.3)
def t_data(log, inp):
    fs = jload(inp, "ai/data/processed/filtering_stats.json")
    tr = count_lines(inp.path("ai/data/processed/train.txt"))
    va = count_lines(inp.path("ai/data/processed/val.txt"))
    te = count_lines(inp.path("ai/data/processed/test.txt"))
    rows = [
        ["Electronics, toàn bộ", "", vn_int(fs["raw_electronics_metadata"]) + " (có thông tin)",
         vn_int(fs["raw_electronics_reviews"])],
        ["Thuộc lĩnh vực máy ảnh", vn_int(fs["raw_camera_users"]),
         vn_int(fs["raw_camera_items_with_interaction"]) + " (có đánh giá)", vn_int(fs["raw_camera_interactions"])],
        ["Sau gộp tương tác lặp", vn_int(fs["raw_camera_users"]), vn_int(fs["raw_camera_items_with_interaction"]),
         vn_int(fs["dedup_interactions"])],
        [f"Sau k-core, k = {fs['k_core']}", vn_int(fs["filtered_users"]), vn_int(fs["filtered_items"]),
         vn_int(fs["filtered_interactions"])],
    ]
    table(log, "T-du-lieu. Quy mô dữ liệu qua từng bước", ["Bước", "Người dùng", "Sản phẩm", "Tương tác"], rows)
    log(f"gộp lặp bỏ {vn_int(fs['dedup_removed_total'])} dòng = {vn_int(fs['dedup_removed_exact_copy'])} bản sao + "
        f"{vn_int(fs['dedup_removed_re_review'])} đánh giá lại; độ thưa {vn_dec(100 * fs['sparsity'], 3)}%; "
        f"TB {vn_dec(fs['avg_interactions_per_user'], 2)} tương tác / người")
    log(f"train: {vn_int(tr[0])} người, {vn_int(tr[1])} tương tác; val: {vn_int(va[0])} người, {vn_int(va[1])}; "
        f"test: {vn_int(te[0])} người, {vn_int(te[1])}")
    log(f"kiểm: |train| = |k-core| − 2|U| ? {tr[1] == fs['filtered_interactions'] - 2 * fs['filtered_users']}")


def t_m(log, inp):
    st = jload(inp, "ai/data/kg/mount_compat_stats.json")
    it = st["item_type"]
    n = st["n_items"]
    table(log, "T-loai. Loại sản phẩm (27.940 sản phẩm sau k-core)", ["Loại", "Số sản phẩm", "Tỉ lệ"],
          [[k, vn_int(it[k]), vn_pct(it[k] / n, 2)] for k in ("phu_kien", "khac", "ong", "than")])
    lv = st["pairs_by_level"]
    rows = [["compatible_with", vn_int(lv["compatible_with"])], ["crops_sensor", vn_int(lv["crops_sensor"])],
            ["requires_adapter", vn_int(lv["requires_adapter"])], ["incompatible", vn_int(lv["incompatible"])],
            ["unknown", vn_int(lv["unknown"])]]
    table(log, "T-M. Ma trận M theo mức", ["Mức", "Số cặp"], rows)
    log(f"thân trong M {st['n_bodies_in_M']}, ống trong M {st['n_lenses_in_M']}, ống không chắc "
        f"{st['n_lenses_uncertain']}; tổng cặp {vn_int(st['pairs_total'])}; M=1 {vn_int(st['M_nnz'])} "
        f"({vn_pct(st['M_nnz'] / st['pairs_total'], 2)}), trong đó cờ chưa rõ cắt khung {vn_int(st['M_crop_unknown'])}; "
        f"U=1 {vn_int(st['unknown_nnz'])} ({vn_pct(st['unknown_nnz'] / st['pairs_total'], 2)})")
    assert st["M_nnz"] == lv["compatible_with"] + lv["crops_sensor"]
    assert st["pairs_total"] == st["n_bodies_in_M"] * st["n_lenses_in_M"]
    with open(inp.path("ai/config/mount_rules.toml"), encoding="utf-8") as f:
        n_rule = sum(1 for line in f if line.strip() == "[[rule]]")
    log(f"số luật trong mount_rules.toml: {n_rule}; số luật có cặp (kể cả mặc định): {len(st['pairs_by_rule'])}")


def t_acc(log, inp):
    """Đọc phần (1) của log lần đo 3 và phần holdout của log tiêu cự / khẩu độ (không tính lại)."""
    with open(inp.path(N3_LOG), encoding="utf-8") as f:
        txt = f.read()
    sec = txt.split("== (1) bộ đánh giá lan2")[1].split("== (2)")[0]
    pat = re.compile(r"^\s*(\S+)\s+(\d+)/(\d+) = ([\d.]+)%\s+\[([\d.]+)% – ([\d.]+)%\]", re.M)
    src, rows = None, []
    for line in sec.splitlines():
        m = re.match(r"^\s*\[([^\]]+)\]\s*$", line)
        if m:
            src = m.group(1)
            continue
        m = pat.match(line)
        if m:
            name, a, b, p, lo, hi = m.groups()
            rows.append([src, name, f"{a}/{b}", f"{p.replace('.', ',')}% [{lo.replace('.', ',')}–{hi.replace('.', ',')}]"])
    table(log, "T-acc. Lần đo 3, tập H733 (log run_measure_holdout, phần (1))", ["Nguồn", "Chỉ số", "Đúng / chấm", "Tỉ lệ [95%]"], rows)
    with open(inp.path(N4_LOG), encoding="utf-8") as f:
        lines = f.read().splitlines()
    log("tiêu cự / khẩu độ, holdout (dòng đầu tiên của mỗi chỉ số):")
    seen = set()
    for line in lines:
        m = re.match(r"^\s*(T\d|K\d)\s.*?(lensfun|wikidata)\s+(\d+/\d+ = [\d.]+% \[[\d.–]+\])", line)
        if m and (m.group(1), m.group(2)) not in seen:
            seen.add((m.group(1), m.group(2)))
            log("  " + line.strip())


def t_kg(log, inp):
    kg = jload(inp, "ai/data/kg/kg_stats.json")
    table(log, "T-nut. Nút của đồ thị", ["Loại nút", "Số nút"], [[k, vn_int(v)] for k, v in kg["nut"].items()])
    table(log, "T-canh. Cạnh xuôi", ["Quan hệ", "Số cạnh"], [[k, vn_int(v)] for k, v in kg["canh_xuoi"].items()])
    tong = sum(kg["canh_ke_ca_rev"].values())
    log(f"cạnh xuôi {vn_int(kg['canh_xuoi_tong'])}; kể cả cạnh ngược: {len(kg['canh_ke_ca_rev'])} loại, {vn_int(tong)} cạnh")


# --------------------------------------------------------------------------- dò trên val (2.5)
def t_val(log, inp):
    n5 = jload(inp, one(inp, "results/n5/val_sweep_20261010/summary_*.json"))
    rows = []
    for k, r in n5["runs"].items():
        rows.append([k, vn_dec(r["val_ndcg@20"], 5), r["best_epoch"], "có" if r["chua_chac_hoi_tu"] else "không"])
    for g in ("cakg", "kgat"):
        d = jload(inp, one(inp, f"results/cakg/val_sweep_20261014/summary_{g}_*.json"))
        for k, r in d["runs"].items():
            rows.append([k, vn_dec(r["val_ndcg@20"], 5), r["best_epoch"], "có" if r["chua_chac_hoi_tu"] else "không"])
    table(log, "T-do-val. Dò siêu tham số trên val, seed 1, NDCG@20 trước mặt nạ",
          ["Lần chạy", "NDCG@20 val", "epoch tốt nhất", "chạm 300 epoch (chưa chắc hội tụ)"], rows)


# --------------------------------------------------------------------------- test lần 1 (2.6)
def load_tests(inp):
    n5 = jload(inp, one(inp, N5_SUMMARY))["tables"]
    ck = jload(inp, one(inp, CAKG_SUMMARY))
    return n5, ck["tables"], ck["extra"]


def t_main(log, n5, ck, ex):
    rows_def = [
        ("Popularity", n5["Popularity"], None),
        ("Popularity-MountAware", n5["Popularity-MountAware"], "0 (do cách dựng)"),
        ("LightGCN", ck["lightgcn|truoc_mat_na"], None),
        ("LightGCN + mặt nạ (1.7)", ck["lightgcn|mat_na_qd49"], "0 (do cách dựng)"),
        ("R-GCN", n5["R-GCN"], None),
        ("KGAT", ck["kgat|truoc_mat_na"], None),
        ("CaKG-Rec, trước mặt nạ", ck["cakg|truoc_mat_na"], None),
        ("CaKG-Rec, mặt nạ (1.7)", ck["cakg|mat_na_qd49"], "0 (do cách dựng)"),
    ]
    rows = []
    for name, t, cvr0 in rows_def:
        f = t["full"]
        rows.append([name, ms(f["recall@10"]), ms(f["ndcg@10"]), ms(f["recall@20"]), ms(f["ndcg@20"]),
                     cvr0 if cvr0 else ms(t["cvr"]["cvr@10"])])
    table(log, "T-chinh. Test, xếp hạng toàn bộ, 67.661 người (TB ± ĐLC 3 seed)",
          ["Mô hình", "Recall@10", "NDCG@10", "Recall@20", "NDCG@20", "CVR@10"], rows)
    rows = []
    for name, t, _ in rows_def:
        sc = t["scenario"]
        rows.append([name, ms(sc["lap_duoc"]["lens_only"]["recall@10"]), ms(sc["khong_lap_duoc"]["lens_only"]["recall@10"])])
    n_ld = ck["cakg|mat_na_qd49"]["scenario"]["lap_duoc"]["n_users"]
    n_kld = ck["cakg|mat_na_qd49"]["scenario"]["khong_lap_duoc"]["n_users"]
    n_kpd = ck["cakg|mat_na_qd49"]["scenario"]["khong_phan_duoc"]["n_users"]
    table(log, f"T-kich-ban. Kịch bản ống cho người có thân, test, xếp hạng chỉ trong ống, Recall@10 "
               f"(lắp được {n_ld}, không lắp được {n_kld}, không phán được {n_kpd})",
          ["Mô hình", f"Lắp được ({n_ld})", f"Không lắp được ({n_kld})"], rows)
    log(f"người có thân trong train: {vn_int(ck['cakg|truoc_mat_na']['cvr']['cvr_n_users_with_body'])}")
    # top-10 trên mọi người (bảng của summary; để so với bảng người có thân)
    rows = []
    for name, t, _ in rows_def:
        mx = t["top10_type_mix"]
        rows.append([name] + [vn_dec(mx[k]["mean"], 2) for k in ("than", "ong", "phu_kien", "khac")])
    table(log, "T-top10-moi-nguoi. Loại sản phẩm trong top-10, TB trên mọi 67.661 người (test)",
          ["Mô hình", "thân", "ống", "phụ kiện", "khác"], rows)


def t_compare(log, inp):
    c = jload(inp, one(inp, CAKG_COMPARE))
    rows = []
    for r in c["comparisons"]:
        dec = 4 if ("ống" in r["metric"] or "CVR" in r["metric"] or "PC" in r["metric"]) else 5
        rows.append([r["id"], r["name"], r["metric"], r["set"], vn_dec(r["diff"], dec, True), ci(*r["ci"], dec),
                     "có" if r["khac_0"] else "không"])
    table(log, f"T-so-sanh. C1–C8, test, K = 10, bootstrap ghép cặp B = {c['B']}",
          ["#", "So sánh", "Chỉ số", "Tập", "Hiệu", "Khoảng 95%", "Khác 0"], rows)


def parse_rt_b(inp):
    """Bảng 'top-10 người có thân' của log phân tích sau test (đọc mảng đã lưu)."""
    with open(inp.path(RT_LOG_B), encoding="utf-8") as f:
        txt = f.read()
    out = {}
    pat = re.compile(r"^\s*(\S+)\s+(truoc_mat_na|mat_na_qd49)\s+người có thân [\d,]+: top-10 thân ([\d.]+) ống ([\d.]+) "
                     r"phụ kiện ([\d.]+) khác ([\d.]+) \| thân cùng ngàm .*= ([\d.]+) \| R@10 người có thân ([\d.]+); "
                     r"item cần đoán có nút trong H \((\d+)\) ([\d.]+), không có \((\d+)\) ([\d.]+)")
    for split in ("val", "test"):
        sec = txt.split(f"=== {split} ===")[1].split("===")[0]
        for line in sec.splitlines():
            m = pat.match(line)
            if not m:
                continue
            g = m.groups()
            out[(split, g[0], g[1])] = dict(than=float(g[2]), ong=float(g[3]), pk=float(g[4]), khac=float(g[5]),
                                            cung_ngam=float(g[6]), r10=float(g[7]), n_h=int(g[8]), r10_h=float(g[9]),
                                            n_noh=int(g[10]), r10_noh=float(g[11]))
        m = re.search(r"item cần đoán của người có thân: thân (\d+), ống (\d+), phụ kiện (\d+), khác (\d+)", sec)
        out[(split, "item_can_doan")] = [int(x) for x in m.groups()]
    return out


def rng(vals, d=2):
    lo, hi = min(vals), max(vals)
    return vn_dec(lo, d) if abs(hi - lo) < 10 ** -(d + 1) else f"{vn_dec(lo, d)}–{vn_dec(hi, d)}"


def t_top10_body(log, inp):
    rt = parse_rt_b(inp)
    groups = [("LightGCN (3 seed)", [f"lightgcn_s{s}" for s in (1, 2, 3)]),
              ("CaKG-Rec (3 seed)", [f"cakg_s{s}" for s in (1, 2, 3)]),
              ("CaKG-Rec λ1 = 0 (seed 1)", ["abl_lam1_0_s1"]),
              ("CaKG-Rec bỏ suitable_for (seed 1)", ["abl_bo_suitable_for_s1"])]
    for split in ("test", "val"):
        rows = []
        for name, keys in groups:
            a = [rt[(split, k, "truoc_mat_na")] for k in keys]
            b = [rt[(split, k, "mat_na_qd49")] for k in keys]
            rows.append([name, rng([x["than"] for x in a]), rng([x["ong"] for x in a]), rng([x["pk"] for x in a]),
                         rng([100 * x["cung_ngam"] for x in a], 1) + "%",
                         rng([x["r10"] for x in b], 4), rng([x["r10_h"] for x in b], 4), rng([x["r10_noh"] for x in b], 4)])
        n_h, n_noh = rt[(split, "cakg_s1", "mat_na_qd49")]["n_h"], rt[(split, "cakg_s1", "mat_na_qd49")]["n_noh"]
        table(log, f"T-top10-co-than-{split}. Người có thân (10.406), {split}: top-10 trước mặt nạ (thân / ống / phụ kiện, "
                   f"tỉ lệ thân cùng ngàm với thân đã có); Recall@10 sau mặt nạ (khoảng = min–max theo seed)",
              ["Mô hình", "thân", "ống", "phụ kiện", "thân cùng ngàm", "R@10 người có thân",
               f"item có nút trong H ({n_h})", f"item không có ({n_noh})"], rows)
        ic = rt[(split, "item_can_doan")]
        log(f"item cần đoán ({split}) của người có thân: thân {ic[0]}, ống {ic[1]}, phụ kiện {ic[2]}, khác {ic[3]} "
            f"(thân {vn_pct(ic[0] / sum(ic))}, phụ kiện {vn_pct(ic[2] / sum(ic))})")


def t_v2(log, inp):
    sel = jload(inp, one(inp, "results/cakg/val_sweep_v2_20261016/select_*/select.json"))
    rows = []
    for k, v in sel["variants"].items():
        a = v["lap_duoc_hieu_vs_LightGCN_mat_na_s1"]
        mx = v["co_che"]["top10_mix_body_users"]
        rows.append([k, vn_dec(v["ndcg@20_truoc_mat_na"], 5), vn_dec(v["ndcg@20_mat_na"], 5),
                     f"{vn_dec(a[0], 4, True)} {ci(a[1], a[2], 4)}", "đạt" if v["dieu_kien_phu_a"] else "không",
                     "đạt" if v["hon_LightGCN_mat_na_b"] else "không", vn_dec(mx["than"], 2)])
    table(log, f"T-v2-buoc1. Val, seed 1; ngưỡng (b) = {vn_dec(sel['nguong_b'], 5)} (max NDCG@20 val của LightGCN + mặt nạ 3 seed: "
               + ", ".join(vn_dec(x, 5) for x in sel["lightgcn_mask_ndcg20"].values()) + ")",
          ["Biến thể", "NDCG@20 trước mặt nạ", "NDCG@20 sau mặt nạ", "(a) R@10 chỉ ống, lắp được, − LightGCN + mặt nạ s1 [95%]",
           "(a)", "(b)", "thân / top-10 người có thân"], rows)
    d2 = jload(inp, one(inp, "results/cakg/val_sweep_v2seeds_20261016/dung2_*/dung2.json"))
    rows = []
    for s, v in d2["per_seed"].items():
        rows.append([f"lens_gate s{s}", vn_dec(v["ndcg@20_mat_na"], 5), vn_dec(v["lap_duoc_R@10_chi_ong_mat_na"], 4),
                     vn_dec(v["co_che"]["top10_mix_body_users"]["than"], 2)])
    for s, v in d2["lightgcn_mask_ndcg20"].items():
        rows.append([f"LightGCN + mặt nạ s{s}", vn_dec(v, 5), vn_dec(d2["lightgcn_mask_lap_duoc_R@10"][s], 4), ""])
    table(log, "T-v2-dung2. Val, 3 seed", ["Mô hình", "NDCG@20 sau mặt nạ", "R@10 chỉ ống, lắp được", "thân / top-10"], rows)
    log(f"TB 3 seed NDCG@20 val sau mặt nạ: v2 {vn_dec(d2['mean_ndcg20_mask']['v2'], 5)}, "
        f"LightGCN + mặt nạ {vn_dec(d2['mean_ndcg20_mask']['lightgcn_mask'], 5)}")
    for k, v in d2.items():
        if k not in ("per_seed", "lightgcn_mask_ndcg20", "lightgcn_mask_lap_duoc_R@10", "mean_ndcg20_mask", "runs", "git"):
            log(f"  dung2 {k}: {json.dumps(v, ensure_ascii=False)}")


def t_ablation(log, n5, ck, ex, inp):
    rt = parse_rt_b(inp)
    rows = []
    for name, key, rk, i in (("CaKG-Rec (seed 1)", "cakg", "cakg_s1", 0), ("λ1 = 0 (seed 1)", "abl_lam1_0", "abl_lam1_0_s1", 0),
                             ("bỏ suitable_for (seed 1)", "abl_bo_suitable_for", "abl_bo_suitable_for_s1", 0)):
        tr, mk = ck[f"{key}|truoc_mat_na"], ck[f"{key}|mat_na_qd49"]
        pc = ex[f"{key}|mat_na_qd49"]["path_coverage"]
        rows.append([name, vn_dec(mk["full"]["recall@10"]["per_seed"][i], 4), vn_dec(tr["cvr"]["cvr@10"]["per_seed"][i], 4),
                     vn_int(tr["cvr"]["cvr_n_lenses@10"]["per_seed"][i]),
                     vn_dec(mk["scenario"]["lap_duoc"]["lens_only"]["recall@10"]["per_seed"][i], 4),
                     vn_dec(pc["pc_ngan@10"]["per_seed"][i], 4), vn_dec(rt[("test", rk, "truoc_mat_na")]["than"], 2)])
    table(log, "T-ablation. Test, seed 1", ["Biến thể", "Recall@10 (mặt nạ)", "CVR@10 trước mặt nạ", "ống chấm được @10",
                                             "R@10 chỉ ống, lắp được", "PC_ngắn@10", "thân / top-10 người có thân"], rows)
    log("CaKG-Rec CVR@10 trước mặt nạ theo seed: " + ", ".join(vn_dec(x, 4) for x in ck["cakg|truoc_mat_na"]["cvr"]["cvr@10"]["per_seed"])
        + "; LightGCN: " + ", ".join(vn_dec(x, 4) for x in ck["lightgcn|truoc_mat_na"]["cvr"]["cvr@10"]["per_seed"]))


def t_mask(log, ck, ex):
    rows = []
    for name, key in (("LightGCN + mặt nạ (1.7)", "lightgcn|mat_na_qd49"), ("LightGCN + mặt nạ ∃b", "lightgcn|mat_na_exists"),
                      ("CaKG-Rec, mặt nạ (1.7)", "cakg|mat_na_qd49"), ("CaKG-Rec, mặt nạ ∃b", "cakg|mat_na_exists")):
        t, e = ck[key], ex[key]
        bl = e["n_target_blocked_by_scenario"]
        tot = e["n_target_blocked"]
        rows.append([name, ms(t["full"]["recall@10"]), ms(t["scenario"]["lap_duoc"]["lens_only"]["recall@10"]),
                     vn_int(tot["mean"] if isinstance(tot, dict) else tot)]
                    + [vn_int(bl[g]["mean"] if isinstance(bl[g], dict) else bl[g]) for g in ("lap_duoc", "khong_lap_duoc", "khong_phan_duoc")])
    table(log, "T-mat-na. Hai cách đặt mặt nạ, test (3 seed)",
          ["Mô hình", "Recall@10 mọi người", "R@10 chỉ ống, lắp được", "người mất item test", "trong đó lắp được",
           "không lắp được", "không phán được"], rows)


def t_sampled(log, n5, ck):
    models = [("Popularity", n5["Popularity"]), ("Popularity-MountAware", n5["Popularity-MountAware"]),
              ("LightGCN", ck["lightgcn|truoc_mat_na"]), ("R-GCN", n5["R-GCN"]), ("KGAT", ck["kgat|truoc_mat_na"]),
              ("CaKG-Rec (mặt nạ)", ck["cakg|mat_na_qd49"])]
    rows = []
    for name, t in models:
        rows.append([name] + [f"{vn_dec(t['full'][f'recall@{k}']['mean'], 4)} / {vn_dec(t['sampled_1_99'][f'hit@{k}']['mean'], 4)}"
                              for k in (5, 10, 20)])
    table(log, "T-sampled. Test: Recall@K xếp hạng toàn bộ / Hit@K lấy mẫu 1 + 99 (TB 3 seed)",
          ["Mô hình", "K = 5", "K = 10", "K = 20"], rows)
    for k in (5, 10, 20):
        for kind, key in (("full", f"recall@{k}"), ("sampled", f"hit@{k}")):
            src = "full" if kind == "full" else "sampled_1_99"
            order = sorted(models, key=lambda m: -m[1][src][key]["mean"])
            log(f"  thứ tự K={k} {kind}: " + " > ".join(m[0] for m in order))


def t_cvr(log, ck, ex):
    rows = []
    for name, key in (("LightGCN", "lightgcn|truoc_mat_na"), ("KGAT", "kgat|truoc_mat_na"), ("CaKG-Rec", "cakg|truoc_mat_na")):
        c = ex[key]["cvr_relaxed"]
        rows.append([name, ms(c["cvr_strict@10"]), ms(c["cvr_relaxed_r1@10"]), ms(c["cvr_relaxed_r2@10"]),
                     vn_int(c["n_violations@10"]["mean"]), vn_int(c["n_relaxed_r1@10"]["mean"]), vn_int(c["n_relaxed_r2@10"]["mean"]),
                     vn_int(c["n_lenses@10"]["mean"])])
    table(log, "T-cvr. CVR@10 trước mặt nạ, người có thân, test (TB 3 seed)",
          ["Mô hình", "strict", "R1", "R2", "vi phạm", "nới R1", "nới R2", "ống chấm được"], rows)


def t_explain(log, inp):
    fe = jload(inp, FINAL_EXPLAIN)
    rows = []
    for s, v in fe["seeds"].items():
        pc, f = v["path_coverage_recomputed"], v["faithfulness"]
        c = f["c9_lg"]
        rows.append([f"LightGCN + mặt nạ s{s}", vn_int(v["n_explanations"]), v["n_fact_errors"], vn_dec(pc["pc@10"], 4),
                     vn_dec(pc["pc_ngan@10"], 4), vn_dec(pc["pc_moi_sp@10"], 4), vn_dec(f["fs_pn"], 4),
                     f"{vn_dec(f['fs_pn_mot_than'], 3)} ({vn_int(f['n_pairs_mot_than'])})",
                     f"{vn_dec(f['fs_pn_tu_hai_than'], 3)} ({vn_int(f['n_pairs_tu_hai_than'])})",
                     f"{vn_dec(c['expl - ctrl'][0], 4, True)} {ci(c['expl - ctrl'][1], c['expl - ctrl'][2], 4)} ({f['n_pairs_with_ctrl_body']})",
                     f"{vn_dec(c['dS_expl - dS_ctrl'][0], 3, True)} {ci(c['dS_expl - dS_ctrl'][1], c['dS_expl - dS_ctrl'][2], 3)}"])
        log(f"  s{s}: pc_matches_saved {v['pc_matches_saved']}, cặp bị loại vì không còn trong top-10 khi chấm lại "
            f"{f['n_excluded_base_not_in_top10']}, b* hòa {v['n_bstar_tie_broken']}, ΔS TB {vn_dec(f['dS_mean'], 3)}")
    for s in (1, 2, 3):
        v = jload(inp, f"results/cakg/test_final_20261015/explain_s{s}/summary.json")
        pc, f = v["path_coverage_after_mask_qd49"], v["faithfulness"]
        c = f["bootstrap_ctrl_body"]
        rows.append([f"CaKG-Rec s{s}", vn_int(v["n_explanations"]), v["n_fact_errors"], vn_dec(pc["pc@10"], 4),
                     vn_dec(pc["pc_ngan@10"], 4), vn_dec(pc["pc_moi_sp@10"], 4), vn_dec(f["fs_pn"], 4), "", "",
                     f"{vn_dec(c['expl - ctrl'][0], 4, True)} {ci(c['expl - ctrl'][1], c['expl - ctrl'][2], 4)} ({f['n_pairs_with_ctrl_body']})",
                     f"{vn_dec(c['dS_expl - dS_ctrl'][0], 3, True)} {ci(c['dS_expl - dS_ctrl'][1], c['dS_expl - dS_ctrl'][2], 3)}"])
        lab = f["bootstrap_ctrl_label"]
        log(f"  CaKG s{s}: đối chứng nhãn {f['n_pairs_with_ctrl_label']} cặp, FS giải thích {vn_dec(lab['expl'][0], 4)} "
            f"đối chứng {vn_dec(lab['ctrl'][0], 4)}; không có đối chứng nhãn {f['n_pairs_no_ctrl_label']}; ΔS TB {vn_dec(f['dS_mean'], 3)}")
    table(log, "T-giai-thich. Giải thích, test, top-10 sau mặt nạ, người có thân; Faithfulness 2.000 cặp / seed",
          ["Mô hình", "số câu", "lỗi sự kiện", "PC@10", "PC_ngắn@10", "PC_mọi_sp@10", "FS_PN@10",
           "FS_PN nhóm 1 thân (cặp)", "FS_PN nhóm ≥ 2 thân (cặp)", "C9 / C9-LG: giải thích − đối chứng [95%] (cặp)",
           "ΔS giải thích − đối chứng [95%]"], rows)
    # câu ví dụ (theo thứ tự file, cố định)
    ex_full = ex_two = ex_crop = None
    with open(inp.path(FINAL_SENT), encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if ex_full is None and d["c_star"]:
                ex_full = d
            if ex_two is None and d["c_star"] and len(d["cand_bodies"]) >= 2:
                ex_two = d
            if ex_crop is None and d["rho"] == "crops_sensor":
                ex_crop = d
            if ex_full and ex_two and ex_crop:
                break
    for tag, d in (("đủ 3 bước", ex_full), ("≥ 2 thân", ex_two), ("crops_sensor", ex_crop)):
        log(f"  câu ví dụ ({tag}), seed 1: u {d['u']}, l {d['l']}, b* {d['b_star']}, e_score {d['e_score']}: {d['sentence']}")


def t_cost(log, inp):
    fe = jload(inp, FINAL_EXPLAIN)["latency"]
    la = jload(inp, CAKG_LAT)
    rows = []
    for name, d in (("LightGCN + mặt nạ + giải thích (seed 1)", fe), ("CaKG-Rec + mặt nạ + giải thích (seed 1)", la)):
        rows.append([name, vn_dec(d["precompute_ms_gpu"], 1), " / ".join(vn_dec(d["cuda"][k], 2) for k in ("p50", "p95", "p99")),
                     " / ".join(vn_dec(d["cpu"][k], 2) for k in ("p50", "p95", "p99")),
                     vn_dec(d["cuda"]["peak_vram_allocated_mib"], 0)])
    table(log, f"T-do-tre. Một yêu cầu ở tầng mô hình, {fe['n_users']} người, {fe['warmup']} lần khởi động, {fe['machine']['gpu']}",
          ["Hệ thống", "tính sẵn biểu diễn (ms, GPU)", "GPU p50 / p95 / p99 (ms)", "CPU p50 / p95 / p99 (ms)", "đỉnh VRAM suy luận (MiB)"], rows)
    log(f"  máy: {fe['machine']}; CaKG: {la['machine']}")
    # huấn luyện
    runs = {"LightGCN": ["results/n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1", "results/n5/final_20261009/lightgcn_l2-1e-03_s2",
                         "results/n5/final_20261009/lightgcn_l2-1e-03_s3"],
            "R-GCN": ["results/n5/val_sweep_20261010/val_rgcn_lr-1e-03_s1", "results/n5/final_20261009/rgcn_lr-1e-03_s2",
                      "results/n5/final_20261009/rgcn_lr-1e-03_s3"],
            "KGAT": ["results/cakg/val_sweep_20261014/val_kgat_lr-1e-03_s1", "results/cakg/final_20261015/kgat_lr-1e-03_s2",
                     "results/cakg/final_20261015/kgat_lr-1e-03_s3"],
            "CaKG-Rec": ["results/cakg/val_sweep_20261014/val_cakg_lam1-1e-01_s1", "results/cakg/final_20261015/cakg_lam1-1e-01_s2",
                         "results/cakg/final_20261015/cakg_lam1-1e-01_s3"]}
    rows = []
    for name, dirs in runs.items():
        rs = [jload(inp, f"{d}/result.json") for d in dirs]
        sec = [r["median_sec_per_epoch"] for r in rs]
        ep = [r["epochs_run"] for r in rs]
        vr = [r.get("peak_vram_allocated_mib") for r in rs]
        hours = [s * e / 3600 for s, e in zip(sec, ep)]
        rows.append([name, rng(sec, 1), rng(ep, 0), rng(hours, 1),
                     rng([v for v in vr if v], 0) if any(vr) else "không ghi"])
    table(log, "T-huan-luyen. Huấn luyện, 3 seed (khoảng min–max)",
          ["Mô hình", "giây / epoch (trung vị)", "số epoch đã chạy", "giờ ≈ giây/epoch × epoch", "đỉnh VRAM huấn luyện (MiB)"], rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    log = Log(root, f"run_bang_c2_{args.label}.log")
    header(log, __file__, root)
    inp = Inputs(root, log)
    log("\n## 2.2–2.3. Dữ liệu, M, đồ thị")
    t_data(log, inp)
    t_m(log, inp)
    t_acc(log, inp)
    t_kg(log, inp)
    log("\n## 2.5. Dò trên val")
    t_val(log, inp)
    log("\n## 2.6. Test lần 1 và phân tích")
    n5, ck, ex = load_tests(inp)
    t_main(log, n5, ck, ex)
    t_compare(log, inp)
    t_top10_body(log, inp)
    t_v2(log, inp)
    t_ablation(log, n5, ck, ex, inp)
    t_mask(log, ck, ex)
    t_sampled(log, n5, ck)
    t_cvr(log, ck, ex)
    t_explain(log, inp)
    t_cost(log, inp)
    log.save()


if __name__ == "__main__":
    main()
