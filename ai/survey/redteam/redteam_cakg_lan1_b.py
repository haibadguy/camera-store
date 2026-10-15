"""
redteam_cakg_lan1_b.py -- Red Team lần 1 nội dung 6–8, phần b: CHỈ ĐỌC mảng / bảng đã lưu (không nạp mô hình, không
tính lại điểm). Viết 15/10/2026, sau redteam_cakg_lan1.py.

  (b1) loại sản phẩm trong top-10 của NGƯỜI CÓ THÂN (bảng test chỉ báo trung bình mọi người dùng), và thân trong top-10
       có cùng ngàm với một thân của người đó không — val (finalcheck_val_20261015_nhap1) và test (test_final_20261015);
  (b2) Recall@10 người có thân, tách theo item cần đoán có biểu diễn phần cứng (có nút trong H) hay không — val và test;
  (b3) tách hiệu C1 / C2 (test, compare_test_*.json) thành phần người có thân / không có thân (số học trên bảng);
  (b4) thứ tự mô hình theo full ranking và theo sampled 1+99 ở K = 5, 10, 20 (kế hoạch mục 5; bảng md chỉ có K = 10).
Dùng mảng TEST ở (b1), (b2) để kiểm cơ chế tìm thấy trên val có lặp lại trên test (sau khi kết quả test đã commit).

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/redteam/redteam_cakg_lan1_b.py --label 20261015_lan1
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ai" / "pipeline"))
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

VALDIR = ROOT / "results" / "cakg" / "finalcheck_val_20261015_nhap1"
TESTDIR = ROOT / "results" / "cakg" / "test_final_20261015"
N5TEST = ROOT / "results" / "n5" / "test_final_20261009"
PRE, Q = "truoc_mat_na", "mat_na_qd49"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = E.Log(ROOT / "ai" / "data" / "survey" / "redteam" / f"run_redteam_cakg_b_{a.label}.log")
    log(f"redteam_cakg_lan1_b | git {E.git_state()} | script sha256 {E.sha256(Path(__file__))}")
    train = C.load_train()
    item_type = C.load_item_type()
    bodies = C.build_train_bodies(train, None, item_type)
    with open(C.DATA_DIR / "kg" / "item_attributes.csv", encoding="utf-8") as f:
        mount = {int(r["iid"]): r["mount"] for r in csv.DictReader(f)}
    H = CK.build_h()
    in_h = np.zeros(C.N_ITEMS, bool)
    in_h[list(H.item_loc)] = True

    for split, base in (("val", VALDIR), ("test", TESTDIR)):
        pos = C.load_pos(split)
        log(f"\n=== {split} ===")
        for nm in ("cakg_s1", "cakg_s2", "cakg_s3", "abl_lam1_0_s1", "abl_bo_suitable_for_s1", "lightgcn_s1",
                   "lightgcn_s2", "lightgcn_s3"):
            for br in (PRE, Q):
                users = np.load(base / nm / f"{split}_{br}_users.npy")
                top = np.load(base / nm / f"{split}_{br}_top20_full.npy")[:, :10]
                rank = np.load(base / nm / f"{split}_{br}_rank_full.npy")
                b = np.array([u in bodies for u in users.tolist()])
                t = item_type[top[b]]
                same = tot = 0
                for r in np.flatnonzero(b):
                    um = {mount[x] for x in bodies[int(users[r])]}
                    for i in top[r].tolist():
                        if item_type[i] == 0:
                            tot += 1
                            same += mount[i] in um
                ph = in_h[np.array([pos[int(u)] for u in users[b].tolist()])]
                hb = (rank[b] <= 10).astype(float)
                log(f"  {nm:<24} {br:<13} người có thân {int(b.sum()):,}: top-10 thân {(t == 0).sum(1).mean():.2f} ống "
                    f"{(t == 1).sum(1).mean():.2f} phụ kiện {(t == 2).sum(1).mean():.2f} khác {(t == 3).sum(1).mean():.2f}"
                    f" | thân cùng ngàm với thân của người đó {same}/{tot} = {same / max(tot, 1):.3f} | R@10 người có "
                    f"thân {hb.mean():.5f}; item cần đoán có nút trong H ({int(ph.sum())}) {hb[ph].mean():.5f}, không có "
                    f"({int((~ph).sum())}) {hb[~ph].mean():.5f}")
        pb = item_type[np.array([pos[u] for u in sorted(bodies)])]
        log(f"  item cần đoán của người có thân: thân {(pb == 0).sum()}, ống {(pb == 1).sum()}, phụ kiện "
            f"{(pb == 2).sum()}, khác {(pb == 3).sum()}")

    # (b3) tách hiệu C1 / C2 theo nhóm (số học trên bảng test đã commit)
    cmp_ = json.loads(sorted(TESTDIR.glob("compare_test_*.json"))[0].read_text(encoding="utf-8"))
    log("\n=== (b3) tách hiệu C1 / C2 (test) ===")
    c = {(r["id"], r["metric"], r["set"][:5]): r["diff"] for r in cmp_["comparisons"]}
    n_all, n_b = 67_661, 10_406
    for met in ("Recall@10", "NDCG@10"):
        d_all, d_b = c[("C2", met, "mọi n")], c[("C2", met, "người")]
        part_b = d_b * n_b / n_all
        log(f"  C2 {met}: hiệu mọi người {d_all:+.5f} = phần người có thân {part_b:+.5f} ({part_b / d_all:.0%}) + phần "
            f"người không có thân {d_all - part_b:+.5f}; hiệu riêng người không có thân "
            f"{(d_all - part_b) * n_all / (n_all - n_b):+.5f}")
        log(f"  C1 {met}: {c[('C1', met, 'mọi n')]:+.5f} (LightGCN + mặt nạ − LightGCN trên mọi người: "
            f"{c[('C1', met, 'mọi n')] - d_all:+.5f})")

    # (b4) thứ tự full / sampled
    log("\n=== (b4) thứ tự mô hình, test: full ranking (Recall@K) và sampled 1+99 (Hit@K) ===")
    T = json.loads(sorted(TESTDIR.glob("summary_test_*.json"))[0].read_text(encoding="utf-8"))["tables"]
    n5 = json.loads(sorted(N5TEST.glob("summary_test_*.json"))[0].read_text(encoding="utf-8"))["tables"]
    rows = {"CaKG-Rec (mặt nạ)": T["cakg|mat_na_qd49"], "LightGCN": T["lightgcn|truoc_mat_na"],
            "KGAT": T["kgat|truoc_mat_na"], "R-GCN": n5["R-GCN"], "Popularity": n5["Popularity"],
            "MountAware": n5["Popularity-MountAware"]}

    def v(x):
        return x["mean"] if isinstance(x, dict) else x
    for K in (5, 10, 20):
        for kind, sec, key in (("full", "full", f"recall@{K}"), ("sampled", "sampled_1_99", f"hit@{K}")):
            vals = sorted(((m, v(r[sec][key])) for m, r in rows.items()), key=lambda t: -t[1])
            log(f"  K={K:<2} {kind:<8} " + " > ".join(f"{m} {x:.4f}" for m, x in vals))
    log("\nXong.")
    log.close()


if __name__ == "__main__":
    main()
