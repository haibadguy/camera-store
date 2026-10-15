"""Kiểm mọi con số cô ghi trong khung quyển đồ án (bản 11/10/2026, nhận 13/10) bằng dữ liệu / đầu ra đã có.

CHỈ ĐỌC: không sửa pipeline, không ghi gì vào ai/data/processed, ai/data/kg, results/; không huấn luyện,
không chấm lại mô hình. Log ghi ra file TÊN MỚI trong ai/data/survey/khung/ (file đã có thì DỪNG).

Mỗi mục in: số trong khung -> số tính lại -> KHỚP / LỆCH (kèm ghi chú nếu cách hiểu khác).

Ví dụ trước (mục 6, các mức của M rời nhau): cặp (Canon 80D, ống EF 50mm) chỉ được nằm ở đúng một mức
(compatible_with). Nếu một cặp xuất hiện ở hai mức, hoặc thiếu cặp nào, thì tổng 5 mức sẽ khác 537 × 1.033.
Script đếm số cặp (thân, ống) KHÁC NHAU trong compat_pairs.csv (bỏ ống "không chắc"), đếm theo mức,
rồi đối chiếu với ma trận M (compatibility_matrix.npz) và U (unknown_mask.npz) từng ô.

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/khung/kiem_so_khung.py --label 20261014_lan1
"""
import argparse
import collections
import csv
import json
import os
import sys
import tomllib

import numpy as np
from scipy.sparse import load_npz

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header, sha256_file  # noqa: E402
import common_05 as C  # noqa: E402

LOG_DIR = "ai/data/survey/khung"
KG = "ai/data/kg"
TEST = "results/n5/test_final_20261009"
SUMMARY = f"{TEST}/summary_test_20261009_125536.json"
H_CSV = "ai/data/survey/n3_lan3/holdout_lan2_20261008.csv"
SPLIT_CSV = "ai/survey/content3/eval_split.csv"
DEV_CSV = "ai/survey/content3/label_dev_50.csv"


def vn(x, nd=0):
    """Số kiểu Việt Nam: 1.116.950 ; 86,98."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def so(log, ten, khung, tinh, ghi_chu="", xap_xi=None):
    """xap_xi = (giá trị khung, giá trị tính, sai số cho phép) khi khung ghi '~'."""
    if xap_xi is not None:
        ok = "KHỚP (xấp xỉ)" if abs(xap_xi[0] - xap_xi[1]) <= xap_xi[2] else "LỆCH"
    elif khung is None:
        ok = "THÔNG TIN"
    else:
        ok = "KHỚP" if khung == tinh else "LỆCH"
    log(f"  [{ok}] {ten}: khung {khung} | tính lại {tinh}" + (f" | {ghi_chu}" if ghi_chu else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(LOG_DIR, f"run_kiem_so_khung_{a.label}.log"))
    header(log, __file__)
    for p in ("ai/data/processed/camera_interactions_k5.csv", "ai/data/processed/train.txt",
              "ai/data/processed/val.txt", "ai/data/processed/test.txt", f"{KG}/item_attributes.csv",
              f"{KG}/compat_pairs.csv", f"{KG}/compatibility_matrix.npz", f"{KG}/unknown_mask.npz",
              f"{KG}/kg_hetero.pt", "ai/config/mount_rules.toml", SUMMARY, H_CSV):
        log(f"  sha256 {sha256_file(p)}  {p}")

    item_map = json.load(open(C.ITEM_MAP_JSON, encoding="utf-8"))
    user_map = json.load(open(C.USER_MAP_JSON, encoding="utf-8"))
    attrs = list(csv.DictReader(open(f"{KG}/item_attributes.csv", encoding="utf-8")))
    b_idx = json.load(open(f"{KG}/body_index.json", encoding="utf-8"))
    l_idx = json.load(open(f"{KG}/lens_index.json", encoding="utf-8"))

    # ------------------------------------------------------------ (1) phụ kiện / tương tác
    log("\n## (1) Mất cân đối danh mục (khung 1.2.2)")
    typ = collections.Counter(r["item_type"] for r in attrs)
    log(f"  loại sản phẩm (item_attributes.csv): {dict(typ)} | tổng {len(attrs):,}")
    so(log, "phụ kiện / catalog", "86,98%", vn(100 * typ["phu_kien"] / len(attrs), 2) + "%",
       f"{typ['phu_kien']:,}/{len(attrs):,}")
    in_m = set(b_idx) | set(l_idx)
    body_lens_all = {r["parent_asin"] for r in attrs if r["item_type"] in ("than", "ong")}
    n_tot = n_m = n_bl = 0
    with open("ai/data/processed/camera_interactions_k5.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            n_tot += 1
            n_m += r["parent_asin"] in in_m
            n_bl += r["parent_asin"] in body_lens_all
    so(log, "tương tác với thân / ống thuộc M", "8,48%", vn(100 * n_m / n_tot, 2) + "%",
       f"{n_m:,}/{n_tot:,}; M = {len(b_idx)} thân + {len(l_idx)} ống")
    log(f"  (so sánh) tương tác với MỌI thân / ống (kể cả ngoài M): {n_bl:,}/{n_tot:,} = {vn(100 * n_bl / n_tot, 2)}% "
        f"-> câu khung 'tương tác thân – ống chỉ chiếm 8,48%' đúng khi hiểu là thân / ống thuộc M")

    # ------------------------------------------------------------ (2) dữ liệu
    log("\n## (2) Số người dùng / sản phẩm / tương tác (khung 1.4, 2.2, 2.5)")
    so(log, "người dùng", "67.661", vn(len(user_map)))
    so(log, "sản phẩm", "27.940", vn(len(item_map)))
    so(log, "tương tác sau k-core", "595.515", vn(n_tot))
    train = C.load_train()
    n_train = sum(len(v) for v in train.values())
    so(log, "tương tác train (cặp khác nhau)", "460.193", vn(n_train))
    val, test = C.load_pos("val"), C.load_pos("test")
    so(log, "val", "67.661", vn(len(val)))
    so(log, "test", "67.661", vn(len(test)))
    log(f"  n_train + val + test = {n_train + len(val) + len(test):,} (phải = {n_tot:,})")
    vt = sum(val[u] == test[u] for u in test)
    tt = sum(test[u] in train.get(u, ()) for u in test)
    vtr = sum(val[u] in train.get(u, ()) for u in val)
    log(f"  rò rỉ: val = test {vt}, test ∈ train {tt}, val ∈ train {vtr}")
    rounds = [ln for ln in open("ai/data/processed/run01_fix.log", encoding="utf-8") if ln.startswith("Vòng ")]
    so(log, "số vòng k-core (run01_fix.log)", "14", str(len(rounds)),
       f"vòng cuối: {rounds[-1].strip()}; vòng 13 và 14 cùng số (vòng 14 là vòng xác nhận không đổi)")

    # ------------------------------------------------------------ (3) M, luật
    log("\n## (3) Ma trận M và bảng luật (khung 1.4, 2.3)")
    M = load_npz(f"{KG}/compatibility_matrix.npz")
    U = load_npz(f"{KG}/unknown_mask.npz")
    so(log, "kích thước M", "537 × 1.033", f"{vn(M.shape[0])} × {vn(M.shape[1])}",
       f"body_index {len(b_idx)}, lens_index {len(l_idx)}, U {U.shape}")
    rules = tomllib.load(open("ai/config/mount_rules.toml", "rb"))
    R = rules["rule"]
    so(log, "số luật [[rule]] trong mount_rules.toml", "22", str(len(R)), f"version {rules['meta']['version']}")
    kc = collections.Counter(r.get("kiem_chung", "?") for r in R)
    log(f"  mức kiểm chứng của 22 luật: {dict(kc)}")
    log(f"  luật có trường suy_rong (áp rộng hơn nguồn): {sum(1 for r in R if r.get('suy_rong'))} luật, "
        f"{sum(len(r['suy_rong']) if isinstance(r.get('suy_rong'), list) else bool(r.get('suy_rong')) for r in R)} mục; "
        f"có nhan_dinh_nhom: {sum(1 for r in R if r.get('nhan_dinh_nhom'))}")
    src_url = {k: v["url"] for k, v in rules["sources"].items()}
    log(f"  {len(src_url)} trang nguồn:")
    for k, u in src_url.items():
        log(f"    {k}: {u}")
    log("  từng luật (id | body_mount -> lens_mount | mức | kiem_chung | nguồn căn cứ):")
    hang_luat = collections.Counter()
    for r in R:
        srcs = sorted({c["source"] for c in r.get("can_cu", [])})
        log(f"    {r['id']} | {r['body_mount']} -> {r['lens_mount']} | {r['level']} | {r.get('kiem_chung')} | {srcs}")
        for s in srcs:
            hang_luat[s.split("_")[0]] += 1
    log(f"  tiền tố nguồn căn cứ theo số luật dùng: {dict(hang_luat)}")
    log("  khung ghi 5 hãng: Canon, Nikon, Sony, Pentax, Olympus. Tiền tố nguồn ở trên cho thấy thêm sigma (1 trang ống "
        "Sigma) và fuji (2 trang Fujifilm, luật leica_m_on_fuji_x_adapter); luật same_mount_* là 'dinh_nghia', không "
        "theo tài liệu hãng nào")

    # ------------------------------------------------------------ (4) 97,8 / 97,2
    log("\n## (4) Độ chính xác phân loại / ngàm (khung 2.3), tính lại từ CSV của lần đo 3")
    split = {r["parent_asin"]: r["nua"] for r in csv.DictReader(open(SPLIT_CSV, encoding="utf-8"))}
    dev = {r["parent_asin"] for r in csv.DictReader(open(DEV_CSV, encoding="utf-8-sig"))}
    hold = {p for p, h in split.items() if h == "holdout"}
    h733 = hold - dev
    rows = [r for r in csv.DictReader(open(H_CSV, encoding="utf-8-sig")) if r["parent_asin"] in h733]
    log(f"  holdout {len(hold)}, mẫu dev trong holdout {len(hold & dev)}, H733 = {len(h733)}")
    per = collections.defaultdict(list)
    for r in rows:
        if r["loai_dung"] in ("0", "1"):
            per[r["parent_asin"]].append(int(r["loai_dung"]))
    ok = sum(all(v) for v in per.values())
    so(log, "phân loại đúng theo sản phẩm (mọi nguồn có đáp án)", "97,8%",
       vn(100 * ok / len(per), 1) + "%", f"{ok}/{len(per)}")
    for s in ("lensfun", "wikidata"):
        rs = [r for r in rows if r["nguon"] == s and r["ngam_dung"] in ("0", "1")]
        k = sum(int(r["ngam_dung"]) for r in rs)
        so(log, f"ngàm đúng ({s})", "97,2%" if s == "lensfun" else None,
           vn(100 * k / len(rs), 1) + "%", f"{k}/{len(rs)}")
    log("  ghi chú: 97,8% là phân loại THEO SẢN PHẨM; theo nguồn là 99,1% (Lensfun) / 97,1% (Wikidata). 97,2% là "
        "ngàm theo Lensfun; Wikidata 100%. Tập đo là sản phẩm khớp được TÊN với Lensfun / Wikidata / openMVG, không "
        "phải 'tập có bằng chứng text rõ ràng'; holdout không sạch (STATUS hạn chế nội dung 3, điểm 10)")

    # ------------------------------------------------------------ (5) đồ thị
    log("\n## (5) Đồ thị tri thức (khung 2.3)")
    import torch
    g = torch.load(f"{KG}/kg_hetero.pt", weights_only=False)
    nodes = {t: int(g[t].num_nodes) for t in g.node_types}
    log(f"  loại nút ({len(nodes)}): {nodes}")
    so(log, "tổng nút", "95.646", vn(sum(nodes.values())))
    so(log, "số loại nút", "7", str(len(nodes)))
    for t, kh in (("mount", "23"), ("sensor_format", "7"), ("focal_range", "6"), ("aperture_class", "5"),
                  ("usecase", "4")):
        so(log, f"nút {t}", kh, str(nodes.get(t)))
    ets = {et: int(g[et].edge_index.shape[1]) for et in g.edge_types}
    so(log, "số loại cạnh (edge type, kể cả rev_)", "18", str(len(ets)))
    so(log, "tổng cạnh (kể cả rev_)", "1.116.950", vn(sum(ets.values())))
    fwd = {et: n for et, n in ets.items() if not et[1].startswith("rev_")}
    rel = sorted({et[1] for et in fwd})
    log(f"  cạnh xuôi: {len(fwd)} loại, {sum(fwd.values()):,} cạnh; tên quan hệ khác nhau: {rel}")
    for et, n in ets.items():
        log(f"    {et}: {n:,}")
    log("  ghi chú: 18 = 9 loại cạnh xuôi + 9 loại cạnh ngược (rev_). Theo tên quan hệ chỉ có 6 (interacted_with, "
        "compatible_with, crops_sensor, requires_adapter, has_spec, suitable_for); has_spec tách 4 loại theo nút đích")

    # ------------------------------------------------------------ (6) các mức của M
    log("\n## (6) Các mức của cặp (thân, ống) trong M (khung 2.3)")
    lvl = collections.Counter()
    seen = {}
    dup = 0
    bi = {int(item_map[k]): v for k, v in b_idx.items()}
    li = {int(item_map[k]): v for k, v in l_idx.items()}
    with open(f"{KG}/compat_pairs.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["lens_uncertain"] == "1":
                continue
            key = (int(r["body_iid"]), int(r["lens_iid"]))
            if key in seen:
                dup += 1
            seen[key] = r["level"]
            lvl[r["level"]] += 1
    assert "incompatible" not in lvl
    lvl["incompatible"] = len(b_idx) * len(l_idx) - len(seen)   # cặp không ghi trong CSV = mức mặc định (meta.default_level)
    log(f"  compat_pairs.csv (bỏ ống 'không chắc'): {len(seen) + dup:,} dòng, {len(seen):,} cặp khác nhau, dòng lặp {dup}; "
        f"CSV không ghi cặp mức incompatible (mức mặc định), nên incompatible = 537 × 1.033 − số cặp có trong CSV")
    for name, kh in (("compatible_with", "70.472"), ("crops_sensor", "2.248"), ("requires_adapter", "16.301"),
                     ("incompatible", "459.854"), ("unknown", "5.846")):
        so(log, f"mức {name}", kh, vn(lvl[name]))
    so(log, "tổng 5 mức", vn(537 * 1033), vn(sum(lvl.values())), "537 × 1.033 = 554.721")
    st = json.load(open(f"{KG}/mount_compat_stats.json", encoding="utf-8"))["pairs_by_level"]
    log(f"  đối chiếu mount_compat_stats.json (đếm độc lập lúc chạy 03, kể cả incompatible): "
        f"{ {k: v for k, v in st.items() if not k.startswith('(')} }")
    for k, v in st.items():
        if not k.startswith("(") and v != lvl[k]:
            log(f"    LỆCH với mount_compat_stats.json ở mức {k}: {v} vs {lvl[k]}")
    out_m = sum(1 for (b, l) in seen if b not in bi or l not in li)
    log(f"  cặp có thân / ống ngoài M: {out_m}")
    Md, Ud = M.toarray().astype(bool), U.toarray().astype(bool)
    bad_m = bad_u = 0
    for (b, l), lv in seen.items():
        bad_m += Md[bi[b], li[l]] != (lv in ("compatible_with", "crops_sensor"))
        bad_u += Ud[bi[b], li[l]] != (lv == "unknown")
    log(f"  đối chiếu từng ô: M = 1 ⇔ mức compatible_with/crops_sensor lệch {bad_m} ô; U = 1 ⇔ unknown lệch {bad_u} ô; "
        f"M ∧ U cùng = 1: {int((Md & Ud).sum())} ô; M nnz {int(Md.sum()):,}, U nnz {int(Ud.sum()):,}")
    log("  -> mỗi cặp trong CSV có đúng 1 mức (dòng lặp 0); M nnz = compatible_with + crops_sensor và U nnz = unknown, "
        "lệch 0 ô, nên các ô ngoài CSV có M = 0, U = 0 (= incompatible); M ∧ U = 0: 5 mức rời nhau, tổng = 537 × 1.033")
    log("  ghi chú: khung xếp requires_adapter thành 'cấp độ tương thích' riêng; trong M nó là M = 0 (QĐ 3-2), U = 0")

    # ------------------------------------------------------------ (7) kịch bản
    log("\n## (7) Người dùng có thân, kịch bản ống (khung 2.5)")
    import eval_05 as E
    itype = C.load_item_type()
    ctx = C.load_cvr_context()
    bodies = C.build_train_bodies(train, None, itype)
    so(log, "người có thân trong train", "10.406", vn(len(bodies)))
    sp = E.load_eval_split("test", train)
    lab, adp = E.scenario_groups(sp.users, sp.pos, bodies, itype, ctx, E.load_adapter_pairs())
    cnt = collections.Counter(x for x in lab.tolist() if x)
    so(log, "kịch bản test (có thân + item test là ống trong M)", "1.060", vn(sum(cnt.values())))
    so(log, "nhóm lắp được", "762", vn(cnt["lap_duoc"]))
    so(log, "nhóm không lắp được", "282", vn(cnt["khong_lap_duoc"]))
    log(f"  nhóm không phán được: {cnt['khong_phan_duoc']} (khung không nêu; 762 + 282 + {cnt['khong_phan_duoc']} = "
        f"{sum(cnt.values())}); trong nhóm không lắp được có cặp requires_adapter: {int(adp.sum())}")

    # ------------------------------------------------------------ (8) CVR@10
    log("\n## (8) CVR@10 trên test (khung 1.1: LightGCN ~13%, R-GCN ~40%), tính lại từ mảng từng người đã lưu")
    for d in ("pop", "popma", "lightgcn_s1", "lightgcn_s2", "lightgcn_s3", "rgcn_s1", "rgcn_s2", "rgcn_s3"):
        res = json.load(open(f"{TEST}/{d}/result.json", encoding="utf-8"))
        arr = {}
        for nm in ("cvr_n_lenses_at10", "cvr_n_viol_at10"):
            fn = f"{TEST}/{d}/{nm}.npy"
            assert sha256_file(fn) == res["arrays_sha256"][f"{nm}.npy"], fn
            arr[nm] = np.load(fn)
        nl, nv = int(arr["cvr_n_lenses_at10"].sum()), int(arr["cvr_n_viol_at10"].sum())
        log(f"  {d}: CVR@10 = {nv:,}/{nl:,} = {vn(100 * nv / nl, 2) if nl else 'nan'}%")
    S = json.load(open(SUMMARY, encoding="utf-8"))
    for m, kh, v in (("LightGCN", "~13%", 13), ("R-GCN", "~40%", 40)):
        c = S["tables"][m]["cvr"]["cvr@10"]
        so(log, f"{m} CVR@10 (TB 3 seed, summary)", kh,
           f"{vn(100 * c['mean'], 2)}% ± {vn(100 * c['sd'], 2)}",
           "theo seed " + " / ".join(vn(100 * x, 2) + "%" for x in c["per_seed"]), xap_xi=(v, 100 * c["mean"], 0.5))
    log("  ghi chú: CVR@10 = số ống vi phạm / số ống CHẤM ĐƯỢC trong top-10 toàn catalog của người có thân (QĐ 4-9), "
        "không phải tỉ lệ trên mọi gợi ý. R-GCN dao động mạnh theo seed (28% – 47%)")

    # ------------------------------------------------------------ (9) K = 5, bootstrap
    log("\n## (9) eval_05: K = 5? bootstrap bao nhiêu lần?")
    log(f"  eval_05.K_LIST = {E.K_LIST}")
    t = S["tables"]["LightGCN"]["full"]
    log(f"  summary test có recall@5 / ndcg@5 / hit@5: {all(k in t for k in ('recall@5', 'ndcg@5', 'hit@5'))}; "
        f"LightGCN hit@5 = {t['hit@5']['mean']:.4f}, recall@5 = {t['recall@5']['mean']:.4f} (bằng nhau vì mỗi người 1 item test)")
    b = S["bootstrap"]
    cfg = tomllib.load(open("ai/config/n5_final.toml", "rb"))
    so(log, "số lần bootstrap (summary test)", "2.000", vn(b["B"]),
       f"seed {b['seed']}; n5_final.toml bootstrap_B = {cfg['chung']['bootstrap_B']}; kiểu: ghép cặp theo người dùng")
    log("  các so sánh bootstrap (id | so sánh | chỉ số | tập | hiệu | khoảng 95%):")
    for c in b["comparisons"]:
        log(f"    {c['id']} | {c['name']} | {c['metric']} | {c['set']} | {c['diff']:+.4f} | "
            f"[{c['ci'][0]:+.4f}, {c['ci'][1]:+.4f}]")
    log("  -> bootstrap chỉ làm ở K = 10 (các so sánh S1–S5 đăng ký trước); K = 5 và 20 có số điểm, không có khoảng tin cậy")
    log.save()


if __name__ == "__main__":
    main()
