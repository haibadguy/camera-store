"""Đếm dữ liệu cho thiết kế CaKG-Rec (docs/cakg_design.md, docs/reviews/cakg_eval_plan.md).

CHỈ ĐỌC: không huấn luyện, không chấm lại mô hình, không ghi gì vào ai/data/processed, ai/data/kg, results/.
Chỉ dùng đầu ra VAL đã lưu của LightGCN seed 1 (results/n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1), không đọc
mảng test, để các định nghĩa mới (CVR_relaxed, Path Coverage) được chọn mà không nhìn thêm số test.
Log ghi ra file TÊN MỚI trong ai/data/survey/cakg/ (file đã có thì DỪNG).

(1) Đồ thị con phần cứng H: nút, cạnh theo quan hệ (tách theo cờ cạnh), hai phương án H_loi (thân, ống, ngàm, khổ,
    mục đích) và H_pk (thêm phụ kiện có cạnh ngàm). Bao nhiêu sản phẩm / item val / tương tác train có nút trong H.
(2) Người dùng: có thân trong train; có ống trong H mà không có thân.
(3) L_comp: cặp dương M = 1, cặp âm M = 0 ∧ U = 0, cặp U bỏ; phân bố theo thân; thân không có cặp dương nào;
    loại cặp âm (requires_adapter, cùng chuỗi ngàm, khác ngàm).
(4) Mặt nạ trên VAL: QĐ 4-9 và biến thể ∃b của khung; người kịch bản val mất item val.
(5) CVR_relaxed trên top-10 VAL của LightGCN s1: ống bị tính vi phạm mà lắp được qua ngàm chuyển người đó có
    (R1: ngàm chuyển a>b; R2: thêm phụ kiện 1 ngàm có chữ "adapter" khi cặp là requires_adapter). Ca uid 2465.
(6) Trần thô của Path Coverage trên top-10 VAL của LightGCN s1: ống chấm được có đường
    u -> b -(compatible_with | crops_sensor)-> l -(suitable_for)-> c, hoặc chỉ u -> b -> l.

Ví dụ trước (cách đếm (5)): người có EOS M (canon_efm) và "Canon EF to EOS M" (canon_ef>canon_efm); top-10 có ống
EF 50mm -> strict: vi phạm (M = 0, requires_adapter); R1: không vi phạm (ngàm ống = canon_ef = phía ống của ngàm
chuyển, phía thân = canon_efm = ngàm thân).

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/cakg/dem_cakg.py --label 20261014_lan1
"""
import argparse
import collections
import csv
import json
import os
import sys

import numpy as np
from scipy.sparse import load_npz

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header, sha256_file  # noqa: E402
import common_05 as C  # noqa: E402

LOG_DIR = "ai/data/survey/cakg"
KG = "ai/data/kg"
VAL_RUN = "results/n5/val_sweep_20261010/val_lightgcn_l2-1e-03_s1"


def rows(name):
    return list(csv.DictReader(open(f"{KG}/{name}", encoding="utf-8")))


def dist(xs):
    xs = np.asarray(sorted(xs))
    if len(xs) == 0:
        return "rỗng"
    return (f"n {len(xs):,}, min {xs[0]}, trung vị {np.median(xs):g}, TB {xs.mean():.1f}, max {xs[-1]}")


def load_val(name):
    res = json.load(open(f"{VAL_RUN}/result.json", encoding="utf-8"))
    fn = f"{VAL_RUN}/val_{name}.npy"
    want = res["val"]["arrays_sha256"].get(f"val_{name}.npy") if "arrays_sha256" in res.get("val", {}) else None
    got = sha256_file(fn)
    return np.load(fn), got, want


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(LOG_DIR, f"run_dem_cakg_{a.label}.log"))
    header(log, __file__)
    for f in ["item_attributes.csv", "kg_edges_compatible_with.csv", "kg_edges_crops_sensor.csv",
              "kg_edges_requires_adapter.csv", "kg_edges_has_spec_mount.csv", "kg_edges_has_spec_sensor_format.csv",
              "kg_edges_suitable_for.csv", "unknown_mask.npz", "body_index.json", "lens_index.json"]:
        log(f"  sha256 {f}: {sha256_file(f'{KG}/{f}')[:16]}…")

    attrs = {int(r["iid"]): r for r in rows("item_attributes.csv")}
    itype = C.load_item_type()
    train = C.load_train()
    val = C.load_pos("val")
    n_train = sum(len(v) for v in train.values())

    comp = rows("kg_edges_compatible_with.csv")
    crops = rows("kg_edges_crops_sensor.csv")
    radp = rows("kg_edges_requires_adapter.csv")
    hsm = rows("kg_edges_has_spec_mount.csv")
    hss = rows("kg_edges_has_spec_sensor_format.csv")
    suit = rows("kg_edges_suitable_for.csv")

    # ── (1) đồ thị con phần cứng ──
    log("\n(1) Đồ thị con phần cứng H (cạnh xuôi; mỗi quan hệ có thêm cạnh ngược cùng số)")
    rel = collections.Counter()
    rel["compatible_with (crop_unknown=0)"] = sum(r["crop_unknown"] == "0" for r in comp)
    rel["compatible_with (crop_unknown=1)"] = sum(r["crop_unknown"] == "1" for r in comp)
    rel["crops_sensor"] = len(crops)
    rel["requires_adapter"] = len(radp)
    for r in hsm:
        if r["ngam_khong_chac"] == "1":
            rel["has_spec→mount: ống 'không chắc' (BỎ)"] += 1
        elif r["src_phu_kien"] == "0":
            rel["has_spec→mount: thân / ống"] += 1
        elif r["phia"] == "khong_phai_ngam_chuyen":
            rel["has_spec→mount: phụ kiện 1 ngàm (chỉ H_pk)"] += 1
        else:
            rel[f"has_spec→mount: ngàm chuyển {r['phia']} (chỉ H_pk)"] += 1
    hss_by_type = collections.Counter(attrs[int(r["iid"])]["item_type"] for r in hss)
    rel["has_spec→sensor_format"] = len(hss)
    rel["suitable_for"] = len(suit)
    for k, v in rel.items():
        log(f"  {k:52s} {v:7,}")
    log(f"  has_spec→sensor_format theo loại sản phẩm: {dict(hss_by_type)}")

    core_items = set()
    for r in comp + crops + radp:
        core_items |= {int(r["body_iid"]), int(r["lens_iid"])}
    for r in hsm:
        if r["src_phu_kien"] == "0" and r["ngam_khong_chac"] == "0":
            core_items.add(int(r["iid"]))
    for r in hss:
        core_items.add(int(r["iid"]))
    suit_items = {int(r["iid"]) for r in suit}
    log(f"  sản phẩm có cạnh suitable_for: {len(suit_items):,}; trong đó không có cạnh ngàm / khổ / tương thích: "
        f"{len(suit_items - core_items):,}")
    core_items_all = core_items | suit_items
    acc_items = {int(r["iid"]) for r in hsm if r["src_phu_kien"] == "1"}
    unsure = {int(r["iid"]) for r in hsm if r["ngam_khong_chac"] == "1"}
    unsure_other = unsure & core_items_all
    for name, items in [("H_loi (thân + ống, kể cả ống chỉ có suitable_for)", core_items_all),
                        ("H_pk (H_loi + phụ kiện có cạnh ngàm)", core_items_all | acc_items)]:
        ty = collections.Counter(attrs[i]["item_type"] for i in items)
        n_val = sum(1 for u, i in val.items() if i in items)
        n_tr = sum(1 for u, its in train.items() for i in its if i in items)
        log(f"  {name}: {len(items):,} nút item {dict(ty)} | item val {n_val:,}/{len(val):,} "
            f"({n_val / len(val) * 100:.2f}%) | tương tác train {n_tr:,}/{n_train:,} ({n_tr / n_train * 100:.2f}%)")
    log(f"  134 ống 'không chắc': còn nút trong H_loi qua cạnh khổ / suitable_for: {len(unsure_other):,}; "
        f"không có nút: {len(unsure - core_items_all):,}")
    n_nodes_loi = len(core_items_all) + 23 + 7 + 4
    log(f"  số nút H_loi = item {len(core_items_all):,} + ngàm 23 + khổ 7 + mục đích 4 = {n_nodes_loi:,} "
        f"(ngàm / khổ không có cạnh vẫn tính)")

    # ── (2) người dùng ──
    log("\n(2) Người dùng")
    bodies = C.build_train_bodies(train, None, itype)
    lens_h = {u for u, its in train.items() if u not in bodies and any(itype[i] == 1 and i in core_items_all
                                                                         for i in its)}
    any_h = {u for u, its in train.items() if any(i in core_items_all for i in its)}
    log(f"  có thân trong train: {len(bodies):,}; không có thân nhưng có ống trong H_loi: {len(lens_h):,}; "
        f"có ít nhất 1 sản phẩm trong H_loi: {len(any_h):,} / {len(train):,}")
    nb = collections.Counter(len(v) for v in bodies.values())
    log(f"  số thân mỗi người (người có thân): {dict(sorted(nb.items()))}")

    # ── (3) L_comp ──
    log("\n(3) Cặp cho L_comp (537 thân × 1.033 ống của M)")
    b_idx = json.load(open(f"{KG}/body_index.json", encoding="utf-8"))
    l_idx = json.load(open(f"{KG}/lens_index.json", encoding="utf-8"))
    item_map = json.load(open(C.ITEM_MAP_JSON, encoding="utf-8"))
    b_iid = {j: item_map[s] for s, j in b_idx.items()}
    l_iid = {j: item_map[s] for s, j in l_idx.items()}
    nB, nL = len(b_iid), len(l_iid)
    M = np.zeros((nB, nL), bool)
    biid2r = {v: k for k, v in b_iid.items()}
    liid2c = {v: k for k, v in l_iid.items()}
    for r in comp + crops:
        M[biid2r[int(r["body_iid"])], liid2c[int(r["lens_iid"])]] = True
    U = load_npz(f"{KG}/unknown_mask.npz").toarray().astype(bool)
    assert U.shape == (nB, nL) and not (M & U).any()
    RA = np.zeros((nB, nL), bool)
    for r in radp:
        RA[biid2r[int(r["body_iid"])], liid2c[int(r["lens_iid"])]] = True
    neg = ~M & ~U
    log(f"  M = 1 (dương): {M.sum():,}; U = 1 (bỏ): {U.sum():,}; M = 0 ∧ U = 0 (âm): {neg.sum():,} "
        f"(requires_adapter {RA.sum():,} + incompatible {(neg & ~RA).sum():,}); tổng {M.size:,}")
    pos_b = M.sum(1)
    neg_b = neg.sum(1)
    log(f"  cặp dương mỗi thân: {dist(pos_b)}")
    log(f"  thân không có cặp dương nào: {(pos_b == 0).sum()} (máy phim {sum(attrs[b_iid[r]]['may_phim'] == 'True' for r in range(nB) if pos_b[r] == 0)})")
    log(f"  cặp âm mỗi thân (thân có cặp dương): {dist(neg_b[pos_b > 0])}")
    log(f"  cặp dương mỗi ống: {dist(M.sum(0))}; ống không có cặp dương: {(M.sum(0) == 0).sum()}")
    bm = np.array([attrs[b_iid[r]]["mount"] for r in range(nB)])
    lm = np.array([attrs[l_iid[c]]["mount"] for c in range(nL)])
    same = bm[:, None] == lm[None, :]
    log(f"  cặp âm cùng chuỗi ngàm (vd ống APS-C trên thân không nhận): {(neg & same).sum():,}; "
        f"requires_adapter {RA.sum():,}; khác ngàm, không ngàm chuyển {(neg & ~same & ~RA).sum():,}")
    top_pos = collections.Counter()
    for r in range(nB):
        top_pos[bm[r]] += int(pos_b[r])
    log(f"  cặp dương theo ngàm thân (5 ngàm nhiều nhất): {top_pos.most_common(5)}")

    # ── (4) mặt nạ trên val ──
    log("\n(4) Mặt nạ trên VAL (người có thân; ống trong M)")
    ctx = C.load_cvr_context()
    users_b = [u for u in sorted(bodies)]
    lost_q = lost_e = 0
    grp = collections.Counter()
    pairs_q = pairs_e = 0
    for u in users_b:
        bs = [b for b in bodies[u] if b in biid2r]
        rws = [biid2r[b] for b in bs]
        allin = len(bs) == len(bodies[u])
        if rws:
            ok = (M[rws] | U[rws]).any(0)
            q = ~ok if allin else np.zeros(nL, bool)
            e = (neg[rws]).any(0)
        else:
            q = e = np.zeros(nL, bool)
        pairs_q += int(q.sum())
        pairs_e += int(e.sum())
        it = val.get(u)
        if it is None or itype[it] != 1 or it not in liid2c:
            continue
        v = C.judge_lens(it, bodies[u], ctx)
        g = {False: "lap_duoc", True: "khong_lap_duoc", None: "khong_phan_duoc"}[v]
        grp[g] += 1
        c = liid2c[it]
        assert bool(q[c]) == (v is True)
        grp[f"{g}: bị chặn QĐ 4-9"] += int(q[c])
        grp[f"{g}: bị chặn ∃b"] += int(e[c])
    log(f"  cặp (người, ống) bị chặn: QĐ 4-9 {pairs_q:,}; ∃b {pairs_e:,}")
    for k in ["lap_duoc", "khong_lap_duoc", "khong_phan_duoc"]:
        log(f"  kịch bản val, {k}: {grp[k]:,} người; item val bị chặn QĐ 4-9 {grp[k + ': bị chặn QĐ 4-9']:,}, "
            f"∃b {grp[k + ': bị chặn ∃b']:,}")

    # ── (5) CVR_relaxed trên top-10 val ──
    log(f"\n(5) CVR_relaxed trên top-10 VAL (full ranking) của {VAL_RUN}")
    top, s_got, s_want = load_val("top20_full")
    users, u_got, u_want = load_val("users")
    log(f"  sha256 top20_full {s_got[:16]}… (result.json: {str(s_want)[:16]}…), users {u_got[:16]}… "
        f"(result.json: {str(u_want)[:16]}…)")
    if s_want is not None:
        assert s_got == s_want and u_got == u_want
    ab = {i: r["mount"] for i, r in attrs.items() if r["item_type"] == "phu_kien" and ">" in r["mount"]}
    named = {i: r["mount"] for i, r in attrs.items() if r["item_type"] == "phu_kien" and ">" not in r["mount"]
             and r["mount"] not in ("khong_co", "khong_ro", "nhieu", "") and "adapter" in r["title"].lower()}
    ra_set = {(int(r["body_iid"]), int(r["lens_iid"])) for r in radp}
    u_ab = {u: {ab[i] for i in train[u] if i in ab} for u in bodies}
    u_nm = {u: {named[i] for i in train[u] if i in named} for u in bodies}
    log(f"  phụ kiện ngàm chuyển a>b: {len(ab)}; phụ kiện 1 ngàm có chữ 'adapter': {len(named)}")
    log(f"  người có thân và có a>b: {sum(1 for v in u_ab.values() if v):,}; có phụ kiện 1 ngàm 'adapter': "
        f"{sum(1 for v in u_nm.values() if v):,}")
    n_l = n_v = n_r1 = n_r2 = 0
    users_fix = set()
    for u, row in zip(users.tolist(), top):
        if u not in bodies:
            continue
        bms = {attrs[b]["mount"] for b in bodies[u]}
        for l in row[:10].tolist():
            if itype[l] != 1:
                continue
            v = C.judge_lens(l, bodies[u], ctx)
            if v is None:
                continue
            n_l += 1
            if not v:
                continue
            n_v += 1
            lmnt = attrs[l]["mount"]
            r1 = any(x.split(">")[0] == lmnt and x.split(">")[1] in bms for x in u_ab[u])
            r2 = r1 or any((b, l) in ra_set and attrs[b]["mount"] in u_nm[u] for b in bodies[u])
            n_r1 += r1
            n_r2 += r2
            if r2:
                users_fix.add(u)
    log(f"  ống chấm được {n_l:,}; vi phạm strict {n_v:,} -> CVR_strict@10 = {n_v / n_l:.4f}")
    log(f"  R1 (a>b): lắp được qua ngàm chuyển {n_r1:,} -> CVR_relaxed_R1@10 = {(n_v - n_r1) / n_l:.4f}")
    log(f"  R2 (R1 + phụ kiện 1 ngàm 'adapter', cặp requires_adapter): {n_r2:,} -> CVR_relaxed_R2@10 = "
        f"{(n_v - n_r2) / n_l:.4f}; số người được nới: {len(users_fix):,}")
    u = 2465
    log(f"  uid 2465: thân {[(b, attrs[b]['mount'], attrs[b]['title'][:40]) for b in sorted(bodies.get(u, []))]}")
    log(f"    phụ kiện ngàm trong train: {[(i, attrs[i]['mount'], attrs[i]['title'][:40]) for i in sorted(train[u]) if i in ab or i in named]}")
    if u in set(users.tolist()):
        r = users.tolist().index(u)
        out = []
        for l in top[r, :10].tolist():
            if itype[l] == 1:
                v = C.judge_lens(l, bodies[u], ctx)
                fix = v and any((b, l) in ra_set and attrs[b]["mount"] in u_nm[u] for b in bodies[u])
                out.append((l, attrs[l]["mount"], {True: "vi phạm", False: "lắp được", None: "không chấm"}[v],
                            "R2 nới" if fix else ""))
        log(f"    ống trong top-10 val: {out}")

    # ── (6) trần thô Path Coverage ──
    log("\n(6) Trần thô Path Coverage trên top-10 VAL của LightGCN s1 (ống chấm được, người có thân)")
    m1 = collections.defaultdict(set)
    for r in comp + crops:
        m1[int(r["lens_iid"])].add(int(r["body_iid"]))
    m1_crop = {(int(r["body_iid"]), int(r["lens_iid"])) for r in crops}
    n_ok = n_full = n_crop_only = n_lap = 0
    for u, row in zip(users.tolist(), top):
        if u not in bodies:
            continue
        for l in row[:10].tolist():
            if itype[l] != 1 or C.judge_lens(l, bodies[u], ctx) is None:
                continue
            n_ok += 1
            bs = m1[l] & bodies[u]
            if not bs:
                continue
            n_lap += 1
            if all((b, l) in m1_crop for b in bs):
                n_crop_only += 1
            if l in suit_items:
                n_full += 1
    log(f"  ống chấm được {n_ok:,}; có đường u -> b -> l (M = 1, tức không vi phạm) {n_lap:,} "
        f"({n_lap / n_ok * 100:.1f}%), trong đó chỉ qua crops_sensor {n_crop_only:,}; "
        f"có đủ u -> b -> l -> c {n_full:,} ({n_full / n_ok * 100:.1f}% ống chấm được, "
        f"{n_full / max(n_lap, 1) * 100:.1f}% ống lắp được)")
    log(f"  ống trong M có suitable_for: {len(suit_items & set(liid2c)):,} / {nL:,}")
    log.save()


if __name__ == "__main__":
    main()
