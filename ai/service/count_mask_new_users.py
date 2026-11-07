"""
count_mask_new_users.py -- Kiểm câu ở chương 3 (mục 3.3.2): "2.062 người bị chặn nhiều ống hơn [ở chế độ demo
all_history], đều là người trước đó không có thân nào". Viết 02/11/2026 theo phản biện
E:\\DATN\\reviews\\redteam_ch123_lan2.md mục 2.3: log check_history_s1_20261028_lan3 chỉ ghi "trước 0 ống, nay > 0:
2,062", mà "0 ống" ở chế độ chỉ thân train còn gồm người có thân ngoài M (count_bodies_outside_m: 71 người).

Dùng đúng hai tập thân và hai mặt nạ của dịch vụ (core.RecommenderCore.views["train"] / ["history"], cùng hàm như
check_service.py giai đoạn history). Với mỗi người u:
  nt = số ống bị chặn khi chỉ tính thân train, nh = khi tính thân cả lịch sử (train + val + test).
Đếm nhóm nt == 0 và nh > 0, tách theo u có thân trong train hay không (có thì in ra từng người). Đếm thêm nhóm nh < nt
và người có thân mới mà vẫn bị chặn 0 ống.

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/service/count_mask_new_users.py --label <nhãn>
Kết quả: results/service/count_mask_new_users_<nhãn>/count_<giờ>.log (thư mục mới) và summary.json.
"""

import argparse
import json

import check_service as CS   # nạp common_05 (C), eval_05 (E), đường dẫn ai/pipeline

C, E = CS.C, CS.E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb-dir", default="results/service/emb_s1_20261021")
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    run_dir = C.RESULTS_DIR / "service" / f"count_mask_new_users_{a.label}"
    run_dir.mkdir(parents=True, exist_ok=False)
    log = E.Log(run_dir / f"count_{E.now_tag()}.log")
    log(f"count_mask_new_users | emb {a.emb_dir} | git {E.git_state()} | script sha256 {E.sha256(__file__)}")
    from core import RecommenderCore
    core = RecommenderCore(C.ROOT / a.emb_dir, device="cpu", log=log)
    vt, vh = core.views["train"], core.views["history"]

    new_with_train_bodies, new_without = [], 0
    less, has_bodies_new_zero = 0, []
    for u in range(C.N_USERS):
        nt, nh = int(vt.cmask[u].sum()), int(vh.cmask[u].sum())
        if nt == 0 and nh > 0:
            if u in vt.bodies:
                new_with_train_bodies.append({"u": u, "train_bodies": sorted(vt.bodies[u]),
                                              "history_bodies": sorted(vh.bodies[u]), "nh": nh})
            else:
                new_without += 1
        less += nh < nt
        if u not in vt.bodies and u in vh.bodies and nh == 0:
            has_bodies_new_zero.append({"u": u, "history_bodies": sorted(vh.bodies[u])})
    n_new = new_without + len(new_with_train_bodies)
    log(f"người có thân: train {len(vt.bodies):,}, cả lịch sử {len(vh.bodies):,} (thêm "
        f"{sum(u not in vt.bodies for u in vh.bodies):,})")
    log(f"trước 0 ống (chỉ thân train), nay > 0 (thân cả lịch sử): {n_new:,} người")
    log(f"  trong đó KHÔNG có thân nào trong train: {new_without:,}")
    log(f"  trong đó CÓ thân trong train: {len(new_with_train_bodies):,}")
    for r in new_with_train_bodies[:20]:
        log(f"    {json.dumps(r)}")
    log(f"số ống bị chặn giảm (nh < nt): {less:,} người")
    log(f"có thân mới (không có thân train, có thân ở val / test) mà vẫn bị chặn 0 ống: {len(has_bodies_new_zero)} người "
        f"{[r['u'] for r in has_bodies_new_zero[:20]]}")
    res = {"git": E.git_state(), "n_new": n_new, "n_new_without_train_bodies": new_without,
           "new_with_train_bodies": new_with_train_bodies, "n_less": less, "has_bodies_new_zero": has_bodies_new_zero}
    (run_dir / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
