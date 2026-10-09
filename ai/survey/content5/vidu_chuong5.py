"""
Lấy ví dụ cho chương 5 của báo cáo. Chỉ ĐỌC đầu ra đã có của lần chạy test (results/n5/test_final_20261009/,
05_test_final.py ở commit 476f730): không huấn luyện, không chấm lại mô hình, không ghi gì vào results/ hay ai/data/kg/.

In ra:
  (0) kiểm sha256 các mảng .npy đọc vào so với result.json của lần chạy test;
  (1) chọn một người dùng thật (quy tắc chọn cố định, in số ứng viên): thuộc kịch bản "ống cho người đã có thân",
      nhóm lắp được; LightGCN seed 1 trúng item test trong top-10 full ranking; top-10 đó có ít nhất một ống vi phạm
      và một ống không vi phạm. Lấy uid nhỏ nhất;
  (2) train / val / test của người đó (loại, ngàm, khung, tiêu đề);
  (3) top-10 full ranking của LightGCN seed 1, Popularity, Popularity-MountAware: loại sản phẩm, phán CVR từng ống
      (common_05.judge_lens) và trạng thái từng cặp (thân, ống): M = 1 / "không biết" / M = 0 (+ requires_adapter);
  (4) top-10 chỉ ống (kịch bản) của ba mô hình;
  (5) tính tay Recall@10, NDCG@10, CVR@10 của người đó, so với mảng đã lưu; hạng sampled 1+99.

Ví dụ trước: nếu người dùng u có thân D3200 (nikon_f) và top-10 có ống Canon EF -> cặp (D3200, EF) M = 0, không
"không biết" -> ống vi phạm; ống Nikon DX -> (D3200, DX) M = 1 -> không vi phạm; phụ kiện -> không chấm.
CVR@10 của riêng u = số vi phạm / số ống chấm được trong top-10 của u.

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/content5/vidu_chuong5.py --log ai/data/survey/n5/run_c5_vidu_chuong5_<nhãn>.log
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ai" / "pipeline"))
import common_05 as C  # noqa: E402
import eval_05 as E    # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

TEST_DIR = ROOT / "results" / "n5" / "test_final_20261009"
MODELS = {"LightGCN s1": "lightgcn_s1", "Popularity": "pop", "Popularity-MountAware": "popma", "R-GCN s1": "rgcn_s1"}
NAMES = ["users", "rank_full", "top20_full", "rank_sampled", "scn_users", "rank_lens_only", "top20_lens_only",
         "cvr_n_lenses_at10", "cvr_n_viol_at10"]


def load_model_arrays(d, log):
    res = json.loads((d / "result.json").read_text(encoding="utf-8"))
    out = {}
    for nm in NAMES:
        fn = d / f"{nm}.npy"
        ok = E.sha256(fn) == res["arrays_sha256"][fn.name]
        assert ok, f"sha256 khác result.json: {fn}"
        out[nm] = np.load(fn)
    log(f"  {d.name}: {len(NAMES)} mảng, sha256 trùng result.json: có")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    log = E.Log(a.log)
    log(f"vidu_chuong5 | git {E.git_state()} | đọc {TEST_DIR.relative_to(ROOT)}")

    log("\n(0) Kiểm mảng đọc vào:")
    arr = {m: load_model_arrays(TEST_DIR / d, log) for m, d in MODELS.items()}

    ev = E.EvalContext("test")
    users = ev.split.users
    for m in MODELS:
        assert np.array_equal(arr[m]["users"], users), m
    attrs = {int(r["iid"]): r for r in csv.DictReader(open(C.ITEM_ATTR_CSV, encoding="utf-8"))}
    val = C.load_pos("val")
    test = C.load_pos("test")
    m1, unk, adapter = ev.ctx.m1, ev.ctx.unknown, ev.adapter

    def desc(i):
        r = attrs[i]
        t = r["title"][:90]
        return f"iid {i:>5} | {r['item_type']:<8} | {r['mount']}/{r['khung'] or '-'}" \
               f"{' phim' if r['may_phim'] == 'True' else ''}{' KHONG_CHAC' if r['uncertain'] == 'True' else ''} | {t}"

    def verdict(i, bs):
        if ev.item_type[i] != 1:
            return "không chấm (không phải ống)"
        v = C.judge_lens(int(i), bs, ev.ctx)
        if i not in ev.ctx.lenses_in_m:
            return "không chấm được (ống ngoài M)"
        pairs = []
        for b in sorted(bs):
            if (b, i) in m1:
                s = "M=1"
            elif (b, i) in unk:
                s = "không biết"
            elif b not in ev.ctx.bodies_in_m:
                s = "thân ngoài M"
            else:
                s = "M=0" + (" (requires_adapter)" if (b, i) in adapter else "")
            pairs.append(f"({b},{i}) {s}")
        lab = {False: "KHÔNG VI PHẠM", True: "VI PHẠM", None: "không chấm được"}[v]
        return f"{lab} | " + "; ".join(pairs)

    # (1) chọn người dùng
    lg = arr["LightGCN s1"]
    lab = ev.scn_lab
    cand = np.flatnonzero((lab == "lap_duoc") & (lg["rank_full"] <= 10))
    log(f"\n(1) Chọn người dùng: nhóm lắp được {int((lab == 'lap_duoc').sum()):,} người; trong đó LightGCN s1 trúng "
        f"top-10 full ranking: {len(cand):,}")
    chosen, n_a = None, 0
    for r in cand.tolist():
        u = int(users[r])
        bs = ev.bodies[u]
        vs = [C.judge_lens(int(i), bs, ev.ctx) for i in lg["top20_full"][r, :10] if ev.item_type[i] == 1]
        if True in vs and False in vs:
            n_a += 1
            if chosen is None:
                chosen = r
    log(f"  ... và top-10 có ≥ 1 ống vi phạm và ≥ 1 ống không vi phạm: {n_a:,} người; chọn uid nhỏ nhất")
    assert chosen is not None, "không có người dùng nào thỏa quy tắc chọn"
    r = chosen
    u = int(users[r])
    bs = ev.bodies[u]

    # (2) dữ liệu của người đó
    log(f"\n(2) uid {u} (chỉ số trong user_map.json); nhóm kịch bản: {lab[r]}")
    tr = sorted(ev.train[u])
    log(f"  train ({len(tr)} sản phẩm):")
    for i in tr:
        log(f"    {desc(i)}")
    log(f"  val : {desc(val[u])}")
    log(f"  test: {desc(test[u])}")
    log(f"  thân trong train: {sorted(bs)} | ống test trong M: {test[u] in ev.ctx.lenses_in_m}")
    log(f"  phán ống test với thân của người này: {verdict(test[u], bs)}")
    n_excl = int(ev.split.excl_ptr[r + 1] - ev.split.excl_ptr[r])
    log(f"  số sản phẩm bị loại khỏi ứng viên (train + item val): {n_excl}; ứng viên còn {C.N_ITEMS - n_excl:,}")

    # (3) top-10 full ranking
    for m in ("LightGCN s1", "Popularity", "Popularity-MountAware", "R-GCN s1"):
        A = arr[m]
        top = A["top20_full"][r, :10]
        log(f"\n(3) {m}: top-10 full ranking (hạng item test = {int(A['rank_full'][r])})")
        for k, i in enumerate(top.tolist(), 1):
            mark = "  <== ITEM TEST" if i == test[u] else ""
            log(f"  {k:>2}. {desc(i)}{mark}")
            log(f"      CVR: {verdict(i, bs)}")
        nl, nv = int(A["cvr_n_lenses_at10"][r]), int(A["cvr_n_viol_at10"][r])
        vs = [C.judge_lens(int(i), bs, ev.ctx) for i in top if ev.item_type[i] == 1]
        vs = [x for x in vs if x is not None]
        assert (len(vs), sum(vs)) == (nl, nv), "CVR tính lại khác mảng đã lưu"
        rk = int(A["rank_full"][r])
        rec = float(test[u] in top.tolist())
        nd = 1 / math.log2(rk + 1) if rk <= 10 else 0.0
        log(f"  -> Recall@10 = Hit@10 = {rec:.0f}; NDCG@10 = 1/log2({rk}+1) = {nd:.4f}" if rk <= 10 else
            f"  -> Recall@10 = Hit@10 = 0; NDCG@10 = 0 (hạng {rk} > 10)")
        log(f"  -> CVR@10 của riêng người này: {nv}/{nl} ống chấm được"
            + (f" = {nv / nl:.4f}" if nl else " (không có ống chấm được: bỏ khỏi CVR)")
            + " | khớp mảng đã lưu: có")
        log(f"  -> hạng sampled 1+99: {int(A['rank_sampled'][r])}")

    # (4) top-10 chỉ ống (kịch bản)
    sr = int(np.flatnonzero(arr["LightGCN s1"]["scn_users"] == u)[0])
    for m in ("LightGCN s1", "Popularity", "Popularity-MountAware"):
        A = arr[m]
        assert int(A["scn_users"][sr]) == u
        top = A["top20_lens_only"][sr, :10]
        log(f"\n(4) {m}: top-10 CHỈ ỐNG (kịch bản; hạng item test = {int(A['rank_lens_only'][sr])})")
        for k, i in enumerate(top.tolist(), 1):
            mark = "  <== ITEM TEST" if i == test[u] else ""
            log(f"  {k:>2}. {desc(i)}{mark}")
            log(f"      CVR: {verdict(i, bs)}")

    log("\nXong (không ghi file nào ngoài log này).")
    log.close()


if __name__ == "__main__":
    main()
