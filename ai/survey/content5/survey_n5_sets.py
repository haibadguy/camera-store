"""Khảo sát cho kế hoạch đánh giá nội dung 5 (docs/reviews/n5_eval_plan.md). Chỉ đếm, không huấn luyện, không chấm mô hình.

Đếm:
  A. loại sản phẩm của item val / test;
  B. người dùng có thân trong train (tập tính CVR), người dùng không có thân;
  C. kịch bản "gợi ý ống cho người đã có thân": người dùng có thân trong train, item (val / test) là ống trong M;
     tách theo common_05.judge_lens: False = có thân M = 1 ("lắp được"), True = mọi thân M = 0 ("không lắp được"),
     None = không phán được; trong nhóm "không lắp được" đếm thêm số ca có cặp requires_adapter;
  D. ảnh hưởng của bộ lọc MountAware lên item test: bộ lọc cũ (05a: loại mọi ống ngoài tập M = 1 của người dùng,
     kể cả người dùng không có thân) và bộ lọc mới (chỉ loại ống judge_lens = True, Nam chốt 08/10 khuya);
  E. tập 99 âm mẫu của 02: có trùng train / val / test không.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/content5/survey_n5_sets.py <đường dẫn log mới>
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "ai/pipeline")
sys.stdout.reconfigure(encoding="utf-8")
import common_05 as C  # noqa: E402

log_lines: list[str] = []


def log(msg: str = "") -> None:
    print(msg)
    log_lines.append(msg)


def pct(a, b):
    return f"{a:,}/{b:,} = {100 * a / b:.2f}%" if b else f"{a}/0"


def main(out_log: Path) -> None:
    assert not out_log.exists(), f"log đã có, không ghi đè: {out_log}"
    TYPE = {0: "than", 1: "ong", 2: "phu_kien", 3: "khac"}
    train = C.load_train()
    pos = {s: C.load_pos(s) for s in ("val", "test")}
    item_type = C.load_item_type()
    b2l = C.load_body_to_lenses()
    ctx = C.load_cvr_context(b2l)
    bodies = C.build_train_bodies(train, b2l, item_type)

    adapter = set()
    with open(C.DATA_DIR / "kg" / "kg_edges_requires_adapter.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            adapter.add((int(r["body_iid"]), int(r["lens_iid"])))

    n_u = len(train)
    log(f"N_USERS {C.N_USERS:,} | N_ITEMS {C.N_ITEMS:,} | user có train {n_u:,} | "
        f"cặp train {sum(len(v) for v in train.values()):,}")
    log(f"ống trong M {len(ctx.lenses_in_m):,} | thân trong M {len(ctx.bodies_in_m):,} | "
        f"cặp M = 1 {len(ctx.m1):,} | cặp 'không biết' {len(ctx.unknown):,} | cặp requires_adapter {len(adapter):,}")
    log(f"loại sản phẩm toàn catalog: { {TYPE[k]: int(v) for k, v in sorted(Counter(item_type.tolist()).items())} }")

    log("\n=== A. Loại sản phẩm của item val / test ===")
    for s in ("val", "test"):
        c = Counter(TYPE[int(item_type[i])] for i in pos[s].values())
        in_m = sum(1 for i in pos[s].values() if i in ctx.lenses_in_m)
        log(f"{s}: {dict(sorted(c.items()))} | ống trong M {in_m:,}")

    log("\n=== B. Người dùng có thân trong train (tập tính CVR) ===")
    n_body_in_m = sum(1 for bs in bodies.values() if bs & ctx.bodies_in_m)
    log(f"có ≥ 1 thân: {pct(len(bodies), n_u)} | có ≥ 1 thân trong M: {pct(n_body_in_m, n_u)}")
    log(f"không có thân nào: {pct(n_u - len(bodies), n_u)}")
    log(f"phân bố số thân / người dùng: {dict(sorted(Counter(len(b) for b in bodies.values()).items()))}")

    log("\n=== C. Kịch bản 'gợi ý ống cho người đã có thân' ===")
    for s in ("val", "test"):
        grp = Counter()
        adapt = 0
        lens_out_m = 0
        for u, bs in bodies.items():
            it = pos[s][u]
            if item_type[it] != 1:
                continue
            if it not in ctx.lenses_in_m:
                lens_out_m += 1
                continue
            v = C.judge_lens(it, bs, ctx)
            grp[v] += 1
            if v is True and any((b, it) in adapter for b in bs):
                adapt += 1
        tot = sum(grp.values())
        log(f"{s}: người dùng có thân + item {s} là ống trong M: {tot:,}")
        log(f"  lắp được (có thân M = 1, judge_lens False): {pct(grp[False], tot)}")
        log(f"  không lắp được (mọi thân M = 0, judge_lens True): {pct(grp[True], tot)}"
            f" | trong đó có cặp requires_adapter: {adapt:,}")
        log(f"  không phán được (judge_lens None): {pct(grp[None], tot)}")
        log(f"  (ngoài kịch bản) người có thân + item {s} là ống ngoài M (không ngàm / 'không chắc'): {lens_out_m:,}")

    log("\n=== D. Bộ lọc MountAware và item test (chỉ đếm, không xếp hạng) ===")
    old_removed = Counter()
    new_removed = 0
    for u in train:
        it = pos["test"][u]
        if item_type[it] != 1:
            continue
        bs = bodies.get(u, set())
        valid = set().union(*(b2l.get(b, set()) for b in bs)) if bs else set()
        if it not in valid:
            old_removed["có thân" if bs else "không có thân"] += 1
        if bs and C.judge_lens(it, bs, ctx) is True:
            new_removed += 1
    n_test_lens = sum(1 for i in pos["test"].values() if item_type[i] == 1)
    log(f"item test là ống: {n_test_lens:,}")
    log(f"bộ lọc cũ (05a) loại mất item test: {sum(old_removed.values()):,} "
        f"(người dùng có thân {old_removed['có thân']:,}, không có thân {old_removed['không có thân']:,})")
    log(f"bộ lọc mới (chỉ loại judge_lens = True) loại mất item test: {new_removed:,}")

    log("\n=== E. Âm mẫu 1+99 của script 02 ===")
    for s in ("val", "test"):
        neg = C.load_negatives(s)
        n_len = Counter(len(v) for v in neg.values())
        bad_train = sum(1 for u, v in neg.items() if set(v) & train.get(u, set()))
        bad_pos = sum(1 for u, v in neg.items() if pos["val"][u] in v or pos["test"][u] in v)
        log(f"{s}: số người dùng {len(neg):,} | độ dài {dict(n_len)} | trùng train {bad_train} | trùng val/test {bad_pos}")
        tc = Counter(TYPE[int(item_type[i])] for v in neg.values() for i in v)
        tot = sum(tc.values())
        log(f"  loại của âm mẫu: " + ", ".join(f"{k} {100 * c / tot:.2f}%" for k, c in sorted(tc.items())))

    out_log.parent.mkdir(parents=True, exist_ok=True)
    out_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"\n-> {out_log}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
