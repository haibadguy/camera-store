"""Chương 5: các chỗ [CẦN SỐ] / [CẦN KIỂM] đọc được từ đầu ra đã lưu của lần chạy test (chỉ đọc; không huấn luyện,
không chấm lại mô hình, không ghi gì vào results/).

(1) Tỉ lệ ống KHÔNG chấm được trong top-K của từng mô hình (hạn chế 13), tách lý do; kiểm số ống chấm được trùng
    mảng cvr_n_lenses_at10 đã lưu. Người được xét: người có thân trong train (10.406).
(2) Ngàm chuyển trong train (hạn chế 12): số người có thân và có ngàm chuyển; trong các ống bị tính vi phạm ở top-10,
    bao nhiêu ống lắp được qua ngàm chuyển dạng "a>b" mà chính người đó có (a = ngàm ống, b = ngàm một thân của họ).
(3) Thông tin Amazon của "Canon EOS M Mount Adapter" (iid 7524) trong metadata đầy đủ.
(4) 10.406 − 10.335 = 71 người có thân mà không có ống nào bị bộ lọc MountAware loại: vì sao.

Ví dụ trước (chỉ cách đếm): người có thân EOS M (canon_efm) và phụ kiện "Canon EF to EOS M" (canon_ef>canon_efm); top-10
có ống EF 50mm -> CVR tính vi phạm (M = 0, requires_adapter), nhưng ống này lắp được qua ngàm chuyển người đó đã có
-> đếm vào (2).

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/report/c5_checks.py --label 20261009_lan1
"""
import argparse
import collections
import csv
import json
import os
import sys

import numpy as np

from report_common import REPORT_LOG_DIR, Log, header, sha256_file

sys.path.insert(0, "ai/pipeline")
import common_05 as C  # noqa: E402

TEST = "results/n5/test_final_20261009"
MODELS = ["pop", "popma", "lightgcn_s1", "lightgcn_s2", "lightgcn_s3", "rgcn_s1", "rgcn_s2", "rgcn_s3"]


def load(d, name):
    res = json.load(open(f"{TEST}/{d}/result.json", encoding="utf-8"))
    fn = f"{TEST}/{d}/{name}.npy"
    assert sha256_file(fn) == res["arrays_sha256"][f"{name}.npy"], fn
    return np.load(fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_c5_checks_{a.label}.log"))
    header(log, __file__)
    attrs = {int(r["iid"]): r for r in csv.DictReader(open("ai/data/kg/item_attributes.csv", encoding="utf-8"))}
    train = C.load_train()
    itype = C.load_item_type()
    ctx = C.load_cvr_context()
    tb = C.build_train_bodies(train, None, itype)
    log(f"người có thân trong train: {len(tb):,}; mọi mảng .npy đọc vào đều kiểm sha256 với result.json")

    def why(l, bodies):
        r = attrs[l]
        if l not in ctx.lenses_in_m:
            if r["uncertain"] == "True":
                return "ngoài M: ống 'không chắc'"
            return f"ngoài M: ngàm {r['mount'] if r['mount'] in ('khong_ro', 'nhieu', 'khong_co') else 'khác'}"
        if any((b, l) in ctx.unknown for b in bodies):
            return "trong M: có cặp 'không biết'"
        return "trong M: có thân ngoài M"

    # ── (1) ──
    log("\n(1) ống trong top-K full ranking, người có thân (tổng trên mọi người; mô hình học: từng seed)")
    for K in (10, 20):
        log(f"  K = {K}")
        for m in MODELS:
            users = load(m, "users")
            top = load(m, "top20_full")
            n_l = n_g = n_v = 0
            reasons = collections.Counter()
            for u, row in zip(users, top):
                bodies = tb.get(int(u))
                if not bodies:
                    continue
                for l in row[:K]:
                    l = int(l)
                    if itype[l] != 1:
                        continue
                    n_l += 1
                    j = C.judge_lens(l, bodies, ctx)
                    if j is None:
                        reasons[why(l, bodies)] += 1
                    else:
                        n_g += 1
                        n_v += j
            chk = ""
            if K == 10:
                saved = int(load(m, "cvr_n_lenses_at10").sum())
                chk = f"; ống chấm được trùng mảng đã lưu: {saved == n_g} ({saved:,})"
            log(f"    {m:12s} ống {n_l:6,}, chấm được {n_g:6,}, vi phạm {n_v:6,}, KHÔNG chấm được {n_l - n_g:6,} "
                f"({(n_l - n_g) / n_l * 100 if n_l else 0:.1f}%){chk}")
            log(f"                 lý do: {dict(reasons.most_common())}")
    log("  kịch bản 'chỉ ống' (1.060 người), top-10:")
    for m in MODELS:
        su = load(m, "scn_users")
        top = load(m, "top20_lens_only")
        n_l = n_g = 0
        reasons = collections.Counter()
        for u, row in zip(su, top):
            bodies = tb[int(u)]
            for l in row[:10]:
                l = int(l)
                n_l += 1
                j = C.judge_lens(l, bodies, ctx)
                if j is None:
                    reasons[why(l, bodies)] += 1
                else:
                    n_g += 1
        log(f"    {m:12s} ống {n_l:6,}, KHÔNG chấm được {n_l - n_g:6,} ({(n_l - n_g) / n_l * 100:.1f}%); "
            f"lý do {dict(reasons.most_common())}")

    # ── (2) ──
    log("\n(2) ngàm chuyển trong train của người có thân")
    adapters = {i: r["mount"] for i, r in attrs.items() if r["item_type"] == "phu_kien" and ">" in r["mount"]}
    named = {i for i, r in attrs.items() if r["item_type"] == "phu_kien" and ">" not in r["mount"]
             and r["mount"] not in ("khong_co", "khong_ro", "nhieu") and "adapter" in r["title"].lower()}
    u_ab = {u: {adapters[i] for i in train[u] if i in adapters} for u in tb}
    u_ab = {u: v for u, v in u_ab.items() if v}
    u_named = {u for u in tb if any(i in named for i in train[u])}
    log(f"  phụ kiện ngàm chuyển dạng a>b (toàn dữ liệu): {len(adapters)}; phụ kiện 1 ngàm có chữ 'adapter': {len(named)}")
    log(f"  người có thân và có ngàm chuyển a>b trong train: {len(u_ab):,}; có phụ kiện 1 ngàm chữ 'adapter': "
        f"{len(u_named):,}; hợp: {len(set(u_ab) | u_named):,}")
    body_mounts = {u: {attrs[b]["mount"] for b in bs} for u, bs in tb.items()}
    usable = {u: {ab.split(">")[0] for ab in v if ab.split(">")[1] in body_mounts[u]} for u, v in u_ab.items()}
    usable = {u: v for u, v in usable.items() if v}
    log(f"  … trong đó phía thân của ngàm chuyển trùng ngàm một thân của họ: {len(usable):,}")
    for m in ["pop", "lightgcn_s1", "lightgcn_s2", "lightgcn_s3", "rgcn_s1", "rgcn_s2", "rgcn_s3"]:
        users = load(m, "users")
        top = load(m, "top20_full")
        n_v = n_fix = 0
        for u, row in zip(users, top):
            u = int(u)
            if u not in tb:
                continue
            for l in row[:10]:
                l = int(l)
                if itype[l] == 1 and C.judge_lens(l, tb[u], ctx) is True:
                    n_v += 1
                    n_fix += attrs[l]["mount"] in usable.get(u, set())
        log(f"    {m:12s} ống vi phạm ở top-10: {n_v:,}; lắp được qua ngàm chuyển a>b người đó đã có: {n_fix:,}")

    # ── (3) ──
    log("\n(3) iid 7524 trong metadata đầy đủ")
    r = attrs[7524]
    for line in open("ai/data/survey/meta_full_k5.jsonl", encoding="utf-8"):
        d = json.loads(line)
        if d["parent_asin"] == r["parent_asin"]:
            log(f"  {r['parent_asin']} | item_attributes: {r['item_type']}/{r['mount']} evidence={r['evidence']!r}")
            log(f"  title: {d['title']}")
            log(f"  store: {d.get('store')!r}; categories: {d.get('categories')}")
            log(f"  details: {json.dumps(d.get('details'), ensure_ascii=False)[:600]}")
            log(f"  features: {json.dumps(d.get('features'), ensure_ascii=False)[:600]}")
            log(f"  description: {json.dumps(d.get('description'), ensure_ascii=False)[:600]}")
            break

    # ── (4) ──
    log("\n(4) người có thân mà không có ống nào trong M bị phán 'vi phạm'")
    lenses = sorted(ctx.lenses_in_m)
    none = [u for u, bs in tb.items() if not any(C.judge_lens(l, bs, ctx) is True for l in lenses)]
    cat = collections.Counter()
    for u in none:
        bs = tb[u]
        out_m = [b for b in bs if b not in ctx.bodies_in_m]
        film = [b for b in bs if attrs[b]["may_phim"] == "True"]
        cat[("có thân ngoài M" if out_m else "mọi thân trong M") + (", có thân phim" if film else "")] += 1
    log(f"  số người: {len(none):,}; phân loại: {dict(cat)}")
    for u in none[:3]:
        log(f"    vd uid {u}: {[(b, attrs[b]['mount'], attrs[b]['title'][:40]) for b in sorted(tb[u])]}")
    log.save()


if __name__ == "__main__":
    main()
