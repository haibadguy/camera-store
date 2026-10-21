"""
count_history_bodies.py -- Chỉ đọc, chỉ đếm (21/10/2026). Từ 21/10 /recommend mặc định bỏ cả lịch sử (train + val + test),
nhưng thân máy dùng cho mặt nạ QĐ 4-9 và giải thích vẫn là thân TRONG TRAIN (common_05.build_train_bodies). Đếm số người
có item val / test là thân máy, và trong đó bao nhiêu người thân đó KHÔNG có trong train (tức mặt nạ / giải thích của
demo không biết họ có thân này). Ví dụ: train {thẻ nhớ}, val = Nikon D750 -> demo không gợi ý D750 nữa, nhưng người này
vẫn được coi là "không có thân": không ống nào bị chặn, không có câu giải thích.

Chạy: ai\\.venv\\Scripts\\python.exe ai/service/count_history_bodies.py --label <nhãn>
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = E.Log(C.RESULTS_DIR / "service" / "logs" / f"count_history_bodies_{a.label}_{E.now_tag()}.log")
    log(f"count_history_bodies | git {E.git_state()} | script sha256 {E.sha256(__file__)}")
    train, val, test = C.load_train(), C.load_pos("val"), C.load_pos("test")
    it = C.load_item_type()
    bodies = C.build_train_bodies(train, None, it)
    ctx = C.load_cvr_context()
    n_hist_body = n_new_body = n_no_train_body = n_new_in_m = 0
    for u in range(C.N_USERS):
        hb = {i for i in (val[u], test[u]) if it[i] == 0}
        if not hb:
            continue
        n_hist_body += 1
        new = hb - bodies.get(u, set())
        if new:
            n_new_body += 1
            n_no_train_body += u not in bodies
            n_new_in_m += any(b in ctx.bodies_in_m for b in new)
    log(f"người dùng: {C.N_USERS:,}; có thân trong train: {len(bodies):,}")
    log(f"người có item val hoặc test là thân máy: {n_hist_body:,}")
    log(f"  trong đó thân đó không có trong train: {n_new_body:,} (thân mới nằm trong M: {n_new_in_m:,}); "
        f"không có thân nào trong train: {n_no_train_body:,}")
    log.close()


if __name__ == "__main__":
    main()
