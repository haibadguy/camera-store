"""
count_bodies_outside_m.py -- Chỉ đọc, chỉ đếm (28/10/2026). Mặt nạ QĐ 4-9 (eval_05.certain_violation_mask) bỏ qua người
có ít nhất một thân NGOÀI ma trận M (thân không có đúng 1 ngàm trong mount_rules): người đó không bị chặn ống nào. Hợp
đồng 1.3 mới chỉ ghi "người không có thân thì không có ống nào bị chặn". Script đếm, theo hai cách lấy thân của dịch vụ
(train: như lúc chấm; cả lịch sử train + val + test: all_history của demo):
  - số người có thân; số người có >= 1 thân ngoài M; kiểm lại bằng mặt nạ thật rằng những người đó bị chặn 0 ống;
  - số người mọi thân trong M mà vẫn bị chặn 0 ống (nếu có);
  - số ống trong catalog, số ống trong M (ống ngoài M không bao giờ bị chặn);
  - vài user_id ví dụ cho từng nhóm (để thử trên giao diện).
Ví dụ: người có Nikon D3100 (trong M) và một máy không rõ ngàm (ngoài M) -> 0 ống bị chặn, dù Nikon D3100 không lắp được
ống Canon EF.

Chạy: ai\\.venv\\Scripts\\python.exe ai/service/count_bodies_outside_m.py --label <nhãn>
Kết quả: results/demo/count_bodies_outside_m_<nhãn>/ (thư mục mới): log, summary.json.
"""

import argparse
import json
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
    run_dir = C.RESULTS_DIR / "demo" / f"count_bodies_outside_m_{a.label}"
    run_dir.mkdir(parents=True, exist_ok=False)
    log = E.Log(run_dir / f"count_bodies_outside_m_{E.now_tag()}.log")
    log(f"count_bodies_outside_m | git {E.git_state()} | script sha256 {E.sha256(__file__)}")
    train, val, test = C.load_train(), C.load_pos("val"), C.load_pos("test")
    it = C.load_item_type()
    ctx = C.load_cvr_context()
    history = {u: train[u] | {val[u], test[u]} for u in range(C.N_USERS)}     # như core.RecommenderCore.history
    n_lens_catalog = int((it == 1).sum())
    res = {"n_lenses_catalog": n_lens_catalog, "n_lenses_in_m": len(ctx.lenses_in_m),
           "n_bodies_in_m": len(ctx.bodies_in_m)}
    log(f"ống trong catalog {n_lens_catalog:,}, ống trong M {len(ctx.lenses_in_m):,} (ngoài M "
        f"{n_lens_catalog - len(ctx.lenses_in_m):,}, không bao giờ bị chặn); thân trong M {len(ctx.bodies_in_m):,}")
    for name, owned in (("train", train), ("all_history", history)):
        bodies = C.build_train_bodies(owned, None, it)       # cùng hàm dịch vụ dùng (core._view)
        _, cmask = E.certain_violation_mask(bodies, ctx)
        blocked = cmask.sum(axis=1)
        outside = sorted(u for u, bs in bodies.items() if any(b not in ctx.bodies_in_m for b in bs))
        inside_zero = sorted(u for u, bs in bodies.items() if u not in set(outside) and blocked[u] == 0)
        assert all(blocked[u] == 0 for u in outside), "người có thân ngoài M mà vẫn bị chặn ống"
        only_outside = [u for u in outside if all(b not in ctx.bodies_in_m for b in bodies[u])]
        row = {"n_users_with_bodies": len(bodies), "n_users_with_body_outside_m": len(outside),
               "n_of_them_all_bodies_outside_m": len(only_outside),
               "n_users_all_bodies_in_m_but_0_blocked": len(inside_zero),
               "examples_body_outside_m": outside[:10],
               "examples_mixed_in_and_outside_m": [u for u in outside if u not in set(only_outside)][:10]}
        res[name] = row
        log(f"[{name}] người có thân {len(bodies):,}; có >= 1 thân ngoài M {len(outside):,} (trong đó mọi thân đều "
            f"ngoài M {len(only_outside):,}); những người này bị chặn 0 ống (đã kiểm bằng mặt nạ thật); người mọi thân "
            f"trong M mà bị chặn 0 ống: {len(inside_zero):,}")
        log(f"  ví dụ có thân ngoài M: {row['examples_body_outside_m']}; vừa trong vừa ngoài M: "
            f"{row['examples_mixed_in_and_outside_m']}")
    (run_dir / "summary.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    log.close()


if __name__ == "__main__":
    main()
