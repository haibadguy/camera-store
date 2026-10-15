"""
06_test_compare.py -- So sánh đăng ký trước C1–C8 (docs/reviews/cakg_eval_plan.md mục 7, 8), K = 10, từ mảng từng người
đã lưu bởi 06_test_final.py (KHÔNG tính lại điểm). C9 (Faithfulness) tính ở 08_explain.py. Viết 15/10/2026.

Bootstrap ghép cặp theo người dùng: B = 2000, seed 20261009 (cakg_final.toml), khoảng 95% phân vị; mọi chuỗi trong một
nhóm dùng CHUNG các mẫu người. Chỉ số từng người của mô hình học = trung bình 3 seed của người đó (C4, C8: seed 1 vs seed 1);
CVR = tổng vi phạm / tổng ống chấm được cộng qua các seed; kịch bản bootstrap riêng trong từng nhóm.

Ví dụ (C1, 3 người, 1 seed cho gọn): Recall@10 CaKG-Rec (mặt nạ) = (1, 0, 1), LightGCN = (1, 0, 0) -> hiệu 1/3. Một mẫu
{3, 3, 1}: CaKG 1, LightGCN 1/3, hiệu 2/3. Lặp 2.000 lần, khoảng 95% = phân vị 2,5% – 97,5% của các hiệu.

  C1  CaKG-Rec (mặt nạ) − LightGCN                         Recall@10, NDCG@10      mọi người dùng
  C2  CaKG-Rec (mặt nạ) − LightGCN + mặt nạ                Recall@10, NDCG@10      người có thân; mọi người dùng
  C3  CaKG-Rec (trước) − LightGCN (trước)                  CVR_strict@10           người có thân
  C4  CaKG-Rec s1 − λ1 = 0 s1 (cả hai trước mặt nạ)        CVR_strict@10; Recall@10  người có thân; mọi người dùng
  C5  CaKG-Rec (mặt nạ) − R-GCN                            Recall@10, NDCG@10      mọi người dùng
  C6  chỉ ống: CaKG-Rec (mặt nạ) − LightGCN + mặt nạ;      Recall@10               nhóm lắp được; không lắp được
           CaKG-Rec (mặt nạ) − LightGCN
  C7  KGAT − LightGCN                                      Recall@10, NDCG@10      mọi người dùng
  C8  CaKG-Rec s1 − bỏ suitable_for s1 (mặt nạ)            Recall@10; PC_ngắn@10   mọi người dùng; người có thân
"Mặt nạ" = mặt nạ chính (15) QĐ 4-9 (mục 8: mọi so sánh dùng mặt nạ chính và CVR_strict).

Chạy: ai\\.venv\\Scripts\\python.exe ai/pipeline/06_test_compare.py --dir results/cakg/<thư mục của 06_test_final>
"""

import argparse
import json
import sys
import tomllib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

FINAL_TOML = C.ROOT / "ai" / "config" / "cakg_final.toml"
N5_TOML = C.ROOT / "ai" / "config" / "n5_final.toml"
N5_TEST = C.ROOT / "results" / "n5" / "test_final_20261009"
Q, PRE = "mat_na_qd49", "truoc_mat_na"


def hit(r, k=10):
    return (r <= k).astype(np.float64)


def ndcg(r, k=10):
    return np.where(r <= k, 1.0 / np.log2(r + 1.0), 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()
    out = Path(a.dir).resolve()
    summ = sorted(out.glob("summary_*.json"))
    assert len(summ) == 1, summ
    S = json.loads(summ[0].read_text(encoding="utf-8"))
    split = S["meta"]["split"]
    log = E.Log(out / f"compare_{split}_{E.now_tag()}.log")
    fin = tomllib.loads(FINAL_TOML.read_text(encoding="utf-8"))
    B, seed = fin["chung"]["bootstrap_B"], fin["chung"]["bootstrap_seed"]
    log(f"06_test_compare | {out} | split {split} | git {E.git_state()} | summary {summ[0].name} sha256 "
        f"{E.sha256(summ[0])} | B {B}, seed {seed}")

    def load(name, br, nm):
        return np.load(out / name / f"{split}_{br}_{nm}.npy")

    def runs(group, br):
        return [Path(d).name for d in S["runs"][f"{group}|{br}"]]

    # mảng R-GCN của nội dung 5 (không chấm lại), kiểm sha256 với result.json đã lưu
    n5 = tomllib.loads(N5_TOML.read_text(encoding="utf-8"))
    rg = []
    for r in n5["rgcn"]["runs"]:
        if split == "test":
            d, pre = N5_TEST / f"rgcn_s{r['seed']}", ""
            shas = json.loads((d / "result.json").read_text(encoding="utf-8"))["arrays_sha256"]
        else:
            d, pre = C.ROOT / r["dir"], "val_"
            shas = json.loads((d / "result.json").read_text(encoding="utf-8"))["val"]["arrays_sha256"]
        a_ = {}
        for nm in ("users", "rank_full", "scn_users", "rank_lens_only"):
            fn = d / f"{pre}{nm}.npy"
            assert E.sha256(fn) == shas[fn.name], f"sha256 khác: {fn}"
            a_[nm] = np.load(fn)
        rg.append(a_)
    log(f"R-GCN: mảng {split} nội dung 5 của 3 seed, sha256 khớp result.json")

    ev = E.EvalContext(split)
    users = ev.split.users
    body = np.array([u in ev.bodies for u in users.tolist()])
    lab = {int(u): g for u, g in zip(users.tolist(), ev.scn_lab.tolist())}

    def series(group, br, f):
        """Chỉ số từng người, trung bình qua các seed của nhóm."""
        vals = []
        for nm in runs(group, br):
            assert np.array_equal(load(nm, br, "users"), users)
            vals.append(f(load(nm, br, "rank_full")))
        return np.mean(vals, axis=0)

    def cvr(group, br):
        nv = sum(load(nm, br, "cvr_n_viol_at10").astype(np.float64) for nm in runs(group, br))
        nl = sum(load(nm, br, "cvr_n_lenses_at10").astype(np.float64) for nm in runs(group, br))
        return nv, nl

    def lens_only(group, br, g):
        vals, su = [], None
        for nm in runs(group, br):
            su_ = load(nm, br, "scn_users")
            su = su_ if su is None else su
            assert np.array_equal(su, su_)
            vals.append(hit(load(nm, br, "rank_lens_only")))
        gs = np.array([lab[int(u)] == g for u in su])
        return np.mean(vals, axis=0)[gs], su

    comps, per_model = [], []

    def add(cid, name, metric, set_name, bs, a_, b_):
        v = bs[f"{a_} - {b_}"]
        comps.append({"id": cid, "name": name, "metric": metric, "set": set_name, "diff": v[0], "ci": [v[1], v[2]],
                      "khac_0": bool(v[1] > 0 or v[2] < 0), "a": bs[a_], "b": bs[b_]})
        log(f"  {cid:<3} {name:<46} {metric:<14} {set_name:<30} hiệu {v[0]:+.5f} [{v[1]:+.5f}, {v[2]:+.5f}] "
            f"{'KHÁC 0' if (v[1] > 0 or v[2] < 0) else 'chứa 0'} | {bs[a_][0]:.5f} vs {bs[b_][0]:.5f}")

    rg_rank = np.mean([hit(x["rank_full"]) for x in rg], axis=0), np.mean([ndcg(x["rank_full"]) for x in rg], axis=0)
    assert all(np.array_equal(x["users"], users) for x in rg)
    n_all, n_b = f"mọi người dùng ({len(users):,})", f"người có thân ({int(body.sum()):,})"

    # Mọi người dùng: C1, C2 (mọi người), C5, C7, C4 (Recall), C8 (Recall)
    ser = {"cakg_q|r": (series("cakg", Q, hit), None), "cakg_q|n": (series("cakg", Q, ndcg), None),
           "lgcn|r": (series("lightgcn", PRE, hit), None), "lgcn|n": (series("lightgcn", PRE, ndcg), None),
           "lgcn_q|r": (series("lightgcn", Q, hit), None), "lgcn_q|n": (series("lightgcn", Q, ndcg), None),
           "rgcn|r": (rg_rank[0], None), "rgcn|n": (rg_rank[1], None),
           "kgat|r": (series("kgat", PRE, hit), None), "kgat|n": (series("kgat", PRE, ndcg), None)}
    s1 = runs("cakg", PRE)[0]
    assert s1.endswith("_s1")
    ser["cakg1_pre|r"] = (hit(load(s1, PRE, "rank_full")), None)
    ser["abl0_pre|r"] = (series("abl_lam1_0", PRE, hit), None)
    ser["cakg1_q|r"] = (hit(load(s1, Q, "rank_full")), None)
    ser["ablns_q|r"] = (series("abl_bo_suitable_for", Q, hit), None)
    log("\nMọi người dùng:")
    bs = E.bootstrap_paired(ser, pairs=[("cakg_q|r", "lgcn|r"), ("cakg_q|n", "lgcn|n"), ("cakg_q|r", "lgcn_q|r"),
                                        ("cakg_q|n", "lgcn_q|n"), ("cakg_q|r", "rgcn|r"), ("cakg_q|n", "rgcn|n"),
                                        ("kgat|r", "lgcn|r"), ("kgat|n", "lgcn|n"), ("cakg1_pre|r", "abl0_pre|r"),
                                        ("cakg1_q|r", "ablns_q|r")], B=B, seed=seed)
    add("C1", "CaKG-Rec (mặt nạ) − LightGCN", "Recall@10", n_all, bs, "cakg_q|r", "lgcn|r")
    add("C1", "CaKG-Rec (mặt nạ) − LightGCN", "NDCG@10", n_all, bs, "cakg_q|n", "lgcn|n")
    add("C2", "CaKG-Rec (mặt nạ) − LightGCN + mặt nạ", "Recall@10", n_all, bs, "cakg_q|r", "lgcn_q|r")
    add("C2", "CaKG-Rec (mặt nạ) − LightGCN + mặt nạ", "NDCG@10", n_all, bs, "cakg_q|n", "lgcn_q|n")
    add("C4", "CaKG-Rec s1 − λ1 = 0 s1 (trước mặt nạ)", "Recall@10", n_all, bs, "cakg1_pre|r", "abl0_pre|r")
    add("C5", "CaKG-Rec (mặt nạ) − R-GCN", "Recall@10", n_all, bs, "cakg_q|r", "rgcn|r")
    add("C5", "CaKG-Rec (mặt nạ) − R-GCN", "NDCG@10", n_all, bs, "cakg_q|n", "rgcn|n")
    add("C7", "KGAT − LightGCN", "Recall@10", n_all, bs, "kgat|r", "lgcn|r")
    add("C7", "KGAT − LightGCN", "NDCG@10", n_all, bs, "kgat|n", "lgcn|n")
    add("C8", "CaKG-Rec s1 − bỏ suitable_for s1 (mặt nạ)", "Recall@10", n_all, bs, "cakg1_q|r", "ablns_q|r")
    for k, v in bs.items():
        if " - " not in k:
            per_model.append({"set": "mọi người dùng", "series": k, "value": v[0], "ci": [v[1], v[2]]})

    # Người có thân: C2, C3, C4 (CVR), C8 (PC_ngắn)
    log("\nNgười có thân:")
    pc = {}
    for key, (grp, br, nm) in {"cakg1": ("cakg", Q, s1), "ablns": ("abl_bo_suitable_for", Q, None)}.items():
        nm = nm or runs(grp, br)[0]
        c = load(nm, br, "pc_counts_at10").astype(np.float64)
        pc[key] = (c[:, 3][body], c[:, 1][body])
    cq, cl = cvr("cakg", PRE), cvr("lightgcn", PRE)
    c1 = (load(s1, PRE, "cvr_n_viol_at10").astype(np.float64), load(s1, PRE, "cvr_n_lenses_at10").astype(np.float64))
    a0 = cvr("abl_lam1_0", PRE)
    ser = {"cakg_q|r": (ser["cakg_q|r"][0][body], None), "cakg_q|n": (ser["cakg_q|n"][0][body], None),
           "lgcn_q|r": (ser["lgcn_q|r"][0][body], None), "lgcn_q|n": (ser["lgcn_q|n"][0][body], None),
           "cakg_pre|cvr": (cq[0][body], cq[1][body]), "lgcn_pre|cvr": (cl[0][body], cl[1][body]),
           "cakg1_pre|cvr": (c1[0][body], c1[1][body]), "abl0_pre|cvr": (a0[0][body], a0[1][body]),
           "cakg1_q|pc_ngan": pc["cakg1"], "ablns_q|pc_ngan": pc["ablns"]}
    bs = E.bootstrap_paired(ser, pairs=[("cakg_q|r", "lgcn_q|r"), ("cakg_q|n", "lgcn_q|n"),
                                        ("cakg_pre|cvr", "lgcn_pre|cvr"), ("cakg1_pre|cvr", "abl0_pre|cvr"),
                                        ("cakg1_q|pc_ngan", "ablns_q|pc_ngan")], B=B, seed=seed)
    add("C2", "CaKG-Rec (mặt nạ) − LightGCN + mặt nạ", "Recall@10", n_b, bs, "cakg_q|r", "lgcn_q|r")
    add("C2", "CaKG-Rec (mặt nạ) − LightGCN + mặt nạ", "NDCG@10", n_b, bs, "cakg_q|n", "lgcn_q|n")
    add("C3", "CaKG-Rec (trước) − LightGCN (trước)", "CVR_strict@10", n_b, bs, "cakg_pre|cvr", "lgcn_pre|cvr")
    add("C4", "CaKG-Rec s1 − λ1 = 0 s1 (trước mặt nạ)", "CVR_strict@10", n_b, bs, "cakg1_pre|cvr", "abl0_pre|cvr")
    add("C8", "CaKG-Rec s1 − bỏ suitable_for s1 (mặt nạ)", "PC_ngắn@10", n_b, bs, "cakg1_q|pc_ngan", "ablns_q|pc_ngan")
    for k, v in bs.items():
        if " - " not in k:
            per_model.append({"set": "người có thân", "series": k, "value": v[0], "ci": [v[1], v[2]]})

    # C6: kịch bản chỉ ống, từng nhóm
    for g in ("lap_duoc", "khong_lap_duoc"):
        cq_, su = lens_only("cakg", Q, g)
        lq_, su2 = lens_only("lightgcn", Q, g)
        lp_, su3 = lens_only("lightgcn", PRE, g)
        assert np.array_equal(su, su2) and np.array_equal(su, su3)
        log(f"\nKịch bản {g}, chỉ ống:")
        bs = E.bootstrap_paired({"cakg_q": (cq_, None), "lgcn_q": (lq_, None), "lgcn": (lp_, None)},
                                pairs=[("cakg_q", "lgcn_q"), ("cakg_q", "lgcn")], B=B, seed=seed)
        nset = f"kịch bản {g} ({len(cq_):,})"
        add("C6", "CaKG-Rec (mặt nạ) − LightGCN + mặt nạ", "Recall@10 chỉ ống", nset, bs, "cakg_q", "lgcn_q")
        add("C6", "CaKG-Rec (mặt nạ) − LightGCN", "Recall@10 chỉ ống", nset, bs, "cakg_q", "lgcn")
        for k, v in bs.items():
            if " - " not in k:
                per_model.append({"set": nset, "series": k, "value": v[0], "ci": [v[1], v[2]]})

    order = {"C1": 1, "C2": 2, "C3": 3, "C4": 4, "C5": 5, "C6": 6, "C7": 7, "C8": 8}
    comps.sort(key=lambda r: order[r["id"]])
    L = [f"# So sánh đăng ký trước C1–C8 ({split}), K = 10, bootstrap ghép cặp B = {B}, seed {seed}", "",
         "| # | So sánh | Chỉ số | Tập | A | B | Hiệu A − B | Khoảng 95% | Khác 0? |", "|---|---|---|---|---|---|---|---|---|"]
    for r in comps:
        L.append(f"| {r['id']} | {r['name']} | {r['metric']} | {r['set']} | {r['a'][0]:.5f} | {r['b'][0]:.5f} | "
                 f"{r['diff']:+.5f} | [{r['ci'][0]:+.5f}, {r['ci'][1]:+.5f}] | {'có' if r['khac_0'] else 'không'} |")
    L.append(f"\nSố khoảng tin cậy: {len(comps)} (C9 ở 08_explain.py).")
    tag = E.now_tag()
    res = {"split": split, "summary_file": summ[0].name, "summary_sha256": E.sha256(summ[0]), "B": B, "seed": seed,
           "git": E.git_state(), "comparisons": comps, "per_model": per_model}
    (out / f"compare_{split}_{tag}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / f"compare_{split}_{tag}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    log("\n" + "\n".join(L))
    log(f"-> {out / f'compare_{split}_{tag}.json'}")
    log.close()


if __name__ == "__main__":
    main()
