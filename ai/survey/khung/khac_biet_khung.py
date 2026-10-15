"""Những chỗ khung quyển đồ án (bản 11/10/2026) khác code / quyết định hiện tại, đếm trên dữ liệu thật.

CHỈ ĐỌC: không sửa pipeline, không ghi gì vào ai/data/processed, ai/data/kg, results/; không huấn luyện.
Log ghi ra file TÊN MỚI trong ai/data/survey/khung/ (file đã có thì DỪNG).

(a) Mặt nạ cứng. Ví dụ trước: người dùng có Canon 80D (EF-S) và Sony a6000 (E); ống cần đoán là Sony E 50mm.
    - Khung: chặn ống l nếu TỒN TẠI một thân b của người dùng với M[b,l] = 0 và U[b,l] = 0.
      (80D, Sony E) = 0 và không "không biết" -> ống bị chặn, dù lắp vừa a6000.
    - QĐ 4-9 (code hiện tại, judge_lens is True): chỉ chặn khi MỌI thân đều M = 0 và không cặp nào "không biết".
      (a6000, Sony E) = 1 -> không chặn.
    Đếm trên mọi người có thân trong train (10.406) × 1.033 ống của M: số cặp (người, ống) bị chặn theo hai cách;
    trên kịch bản test (1.060): số người có item test bị chặn theo hai cách; top-10 của LightGCN seed 1.
    Thân ngoài M (không xác định được ngàm) không có hàng trong M: cả hai cách đều bỏ qua thân đó khi tìm b.
(b) Quan hệ "owns" trong đường giải thích: có trong đồ thị không, hiện ứng với cạnh nào; độ phủ thô của đường
    u -> b -(compatible_with)-> l -(suitable_for)-> c trên nhóm "lắp được" của kịch bản test.
(c) Kênh phần cứng (Body – Mount – Lens – Sensor Format): bao nhiêu sản phẩm có cạnh ở kênh này, bao nhiêu không;
    item test thuộc nhóm nào.
(d) Quét repo tìm những gì khung cần (KGAT, CVR_relaxed, Hit@5, Path Coverage, Faithfulness, độ trễ, VRAM, ...).

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/khung/khac_biet_khung.py --label 20261014_lan1
"""
import argparse
import collections
import csv
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, "ai/survey/report")
sys.path.insert(0, "ai/pipeline")
from report_common import Log, header, sha256_file  # noqa: E402
import common_05 as C  # noqa: E402

LOG_DIR = "ai/data/survey/khung"
KG = "ai/data/kg"
TEST = "results/n5/test_final_20261009"


def load_npy(d, name):
    res = json.load(open(f"{TEST}/{d}/result.json", encoding="utf-8"))
    fn = f"{TEST}/{d}/{name}.npy"
    assert sha256_file(fn) == res["arrays_sha256"][f"{name}.npy"], fn
    return np.load(fn)


def rows(name):
    with open(f"{KG}/{name}", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(LOG_DIR, f"run_khac_biet_khung_{a.label}.log"))
    header(log, __file__)
    for p in ("ai/data/processed/train.txt", "ai/data/processed/test.txt", f"{KG}/item_attributes.csv",
              f"{KG}/compat_pairs.csv", f"{KG}/unknown_mask.npz", f"{KG}/kg_hetero.pt"):
        log(f"  sha256 {sha256_file(p)}  {p}")

    import eval_05 as E
    attrs = {int(r["iid"]): r for r in csv.DictReader(open(f"{KG}/item_attributes.csv", encoding="utf-8"))}
    train = C.load_train()
    itype = C.load_item_type()
    ctx = C.load_cvr_context()
    bodies = C.build_train_bodies(train, None, itype)
    sp = E.load_eval_split("test", train)
    lab, _ = E.scenario_groups(sp.users, sp.pos, bodies, itype, ctx, E.load_adapter_pairs())
    level = {}
    for r in rows("compat_pairs.csv"):
        level[(int(r["body_iid"]), int(r["lens_iid"]))] = r["level"] + ("(ống không chắc)" if r["lens_uncertain"] == "1" else "")

    def lv(b, l):
        if b not in ctx.bodies_in_m:
            return "thân ngoài M"
        return level.get((b, l), "incompatible")

    def t(i):
        r = attrs[i]
        return f"iid {i} [{r['item_type']}, {r['mount']}, khung {r['khung'] or '-'}, phim {r['may_phim']}] {r['title'][:90]}"

    # ================================================================ (a)
    log("\n## (a) Mặt nạ cứng: khung (∃ thân M = 0 ∧ U = 0) so với QĐ 4-9 (mọi thân M = 0, không cặp nào 'không biết')")
    lens, qd_mask = E.certain_violation_mask(bodies, ctx)          # [N_USERS, 1033], đúng mặt nạ MountAware hiện tại
    col = {int(l): j for j, l in enumerate(lens)}
    m1 = collections.defaultdict(lambda: np.zeros(len(lens), bool))
    unk = collections.defaultdict(lambda: np.zeros(len(lens), bool))
    for (b, l) in ctx.m1:
        m1[b][col[l]] = True
    for (b, l) in ctx.unknown:
        unk[b][col[l]] = True
    kh_mask = np.zeros_like(qd_mask)
    n_multi_mount = n_out_m = 0
    for u, bs in bodies.items():
        bm = [b for b in bs if b in ctx.bodies_in_m]
        n_out_m += len(bm) < len(bs)
        n_multi_mount += len({attrs[b]["mount"] for b in bm}) >= 2
        for b in bm:
            kh_mask[u] |= ~(m1[b] | unk[b])
    assert not (qd_mask & ~kh_mask).any(), "QĐ 4-9 chặn mà khung không chặn: không thể xảy ra"
    users_b = np.array(sorted(bodies))
    q_u, k_u = qd_mask[users_b].sum(1), kh_mask[users_b].sum(1)
    log(f"  người có thân trong train: {len(users_b):,}; có thân ngoài M: {n_out_m:,}; có thân thuộc ≥ 2 ngàm khác nhau: "
        f"{n_multi_mount:,}")
    log(f"  cặp (người, ống trong M) bị chặn: QĐ 4-9 {int(q_u.sum()):,} | khung {int(k_u.sum()):,} | "
        f"chỉ khung chặn {int((k_u - q_u).sum()):,} (trên {len(users_b) * len(lens):,} cặp)")
    log(f"  số người có tập ống bị chặn khác nhau giữa hai cách: {int((k_u != q_u).sum()):,}")
    log(f"  người có ≥ 1 ống bị chặn: QĐ 4-9 {int((q_u > 0).sum()):,} | khung {int((k_u > 0).sum()):,}")

    # kịch bản test
    sc = [(r, int(u), int(it)) for r, (u, it) in enumerate(zip(sp.users.tolist(), sp.pos.tolist())) if lab[r]]
    cross = collections.Counter()
    ex = []
    for r, u, it in sc:
        cross[(lab[r], "n")] += 1
        cross[(lab[r], "qd")] += bool(qd_mask[u, col[it]])
        cross[(lab[r], "kh")] += bool(kh_mask[u, col[it]])
        if lab[r] == "lap_duoc" and kh_mask[u, col[it]]:
            ex.append((u, it))
    log(f"  kịch bản test ({len(sc):,} người, item test là ống trong M), item test bị chặn hay không:")
    for g in ("lap_duoc", "khong_lap_duoc", "khong_phan_duoc"):
        log(f"    nhóm {g} ({cross[(g, 'n')]}): QĐ 4-9 chặn {cross[(g, 'qd')]} | khung chặn {cross[(g, 'kh')]}")
    n_qd = sum(cross[(g, "qd")] for g in ("lap_duoc", "khong_lap_duoc", "khong_phan_duoc"))
    n_kh = sum(cross[(g, "kh")] for g in ("lap_duoc", "khong_lap_duoc", "khong_phan_duoc"))
    log(f"    tổng người bị chặn mất item test: QĐ 4-9 {n_qd} | khung {n_kh} -> khung chặn thêm {n_kh - n_qd} người "
        f"(Recall@K của họ = 0 với mọi mô hình có mặt nạ khung)")
    log(f"  ví dụ người dùng thật ở nhóm 'lắp được' bị khung chặn mất item test ({len(ex)} người; in 3 người đầu):")
    for u, it in ex[:3]:
        log(f"    uid {u}: item test {t(it)}")
        for b in sorted(bodies[u]):
            log(f"       thân {t(b)} -> mức với item test: {lv(b, it)}")
    # top-10 LightGCN seed 1
    top = load_npy("lightgcn_s1", "top20_full")
    users = load_npy("lightgcn_s1", "users")
    n_q = n_k = n_l = 0
    for r, u in enumerate(users.tolist()):
        if u not in bodies:
            continue
        for i in top[r, :10].tolist():
            if i in col:
                n_l += 1
                n_q += bool(qd_mask[u, col[i]])
                n_k += bool(kh_mask[u, col[i]])
    log(f"  top-10 toàn catalog LightGCN seed 1, người có thân: {n_l:,} ống trong M; QĐ 4-9 chặn {n_q:,}, khung chặn "
        f"{n_k:,} (khung chặn thêm {n_k - n_q:,} ống)")

    # ================================================================ (b)
    log("\n## (b) Quan hệ 'owns' trong đường giải thích")
    import torch
    g = torch.load(f"{KG}/kg_hetero.pt", weights_only=False)
    rels = sorted({et[1] for et in g.edge_types})
    log(f"  tên quan hệ trong kg_hetero.pt: {rels}")
    log(f"  có quan hệ tên 'owns': {'owns' in rels}")
    n_ub = sum(len(bs) for bs in bodies.values())
    log(f"  gần nhất: cạnh ('user','interacted_with','item') tới sản phẩm loại thân: {n_ub:,} cạnh, {len(bodies):,} người "
        f"(cạnh = người dùng có viết đánh giá sản phẩm đó trong train, QĐ 3-5; không phải xác nhận đang sở hữu)")
    spec_src = {et[0] for et in g.edge_types if et[2] == "usecase"}
    log(f"  nút có cạnh tới usecase: {sorted(spec_src)} (đường 1.2.1 'l -> spec -> c' không có: nút thông số không nối "
        f"tới usecase; suitable_for đi thẳng item -> usecase)")
    comp = {(int(r["body_iid"]), int(r["lens_iid"])) for r in rows("kg_edges_compatible_with.csv")}
    crop = {(int(r["body_iid"]), int(r["lens_iid"])) for r in rows("kg_edges_crops_sensor.csv")}
    suit = collections.defaultdict(set)
    for r in rows("kg_edges_suitable_for.csv"):
        suit[int(r["iid"])].add(r["usecase"])
    cnt = collections.Counter()
    for r, u, it in sc:
        if lab[r] != "lap_duoc":
            continue
        has_comp = any((b, it) in comp for b in bodies[u])
        has_crop = any((b, it) in crop for b in bodies[u])
        cnt["comp" if has_comp else ("crop" if has_crop else "khac")] += 1
        cnt["comp+suit"] += has_comp and bool(suit[it])
    n_lap = sum(1 for r, u, it in sc if lab[r] == "lap_duoc")
    log(f"  nhóm 'lắp được' ({n_lap}): có thân nối item test bằng compatible_with {cnt['comp']}, chỉ bằng crops_sensor "
        f"{cnt['crop']}; có đủ đường u -> b -compatible_with-> l -suitable_for-> c: {cnt['comp+suit']}")
    log(f"  ống trong M có nhãn suitable_for: {sum(1 for l in lens.tolist() if suit[l])}/{len(lens)}")

    # ================================================================ (c)
    log("\n## (c) Kênh phần cứng (Body – Mount – Lens – Sensor Format)")
    hw = set()
    for name in ("kg_edges_compatible_with.csv", "kg_edges_crops_sensor.csv", "kg_edges_requires_adapter.csv"):
        for r in rows(name):
            hw.add(int(r["body_iid"]))
            hw.add(int(r["lens_iid"]))
    spec_m = {int(r["iid"]) for r in rows("kg_edges_has_spec_mount.csv")}
    spec_s = {int(r["iid"]) for r in rows("kg_edges_has_spec_sensor_format.csv")}
    other = set()
    for name in ("kg_edges_has_spec_focal_range.csv", "kg_edges_has_spec_aperture_class.csv", "kg_edges_suitable_for.csv"):
        other |= {int(r["iid"]) for r in rows(name)}
    any_kg = hw | spec_m | spec_s | other
    TN = {0: "than", 1: "ong", 2: "phu_kien", 3: "khac"}

    def grp(i):
        ty = TN[int(itype[i])]
        if ty in ("than", "ong") and (i in hw or i in spec_m or i in spec_s):
            return f"{ty}: có cạnh phần cứng"
        if ty == "phu_kien" and i in spec_m:
            return "phu_kien: chỉ có has_spec -> mount (phụ kiện / ngàm chuyển)"
        if i in any_kg:
            return f"{ty}: có cạnh tri thức khác"
        return f"{ty}: không có cạnh tri thức"
    by = collections.Counter(grp(i) for i in range(C.N_ITEMS))
    log(f"  sản phẩm có ít nhất 1 cạnh tri thức (mọi loại): {len(any_kg):,}/{C.N_ITEMS:,}")
    log(f"  thân / ống có cạnh compatible_with / crops_sensor / requires_adapter / has_spec(mount, sensor_format): "
        f"{sum(v for k, v in by.items() if k.endswith('có cạnh phần cứng')):,}")
    for k, v in sorted(by.items()):
        log(f"    {k}: {v:,}")
    tg = collections.Counter(grp(int(i)) for i in sp.pos.tolist())
    log(f"  item test ({len(sp.pos):,} người) theo nhóm:")
    for k, v in sorted(tg.items()):
        log(f"    {k}: {v:,} ({100 * v / len(sp.pos):.2f}%)")
    trg = collections.Counter()
    for u, its in train.items():
        for i in its:
            trg[grp(i)] += 1
    n_tr = sum(trg.values())
    log(f"  tương tác train ({n_tr:,}) theo nhóm:")
    for k, v in sorted(trg.items()):
        log(f"    {k}: {v:,} ({100 * v / n_tr:.2f}%)")

    # ================================================================ (d)
    log("\n## (d) Quét repo: những gì khung cần (đếm file có từ khoá; bỏ .venv, data, node_modules, results)")
    kw = {
        "KGAT": r"\bKGAT\b", "KGIN": r"\bKGIN\b", "RGAT / GATConv": r"RGAT|GATConv|HGTConv",
        "CVR_relaxed / relaxed": r"relaxed", "Path Coverage": r"[Pp]ath[ _][Cc]overage|path_coverage",
        "Faithfulness": r"[Ff]aithful", "độ trễ suy luận / latency": r"latency|độ trễ",
        "VRAM đỉnh (max_memory_allocated)": r"max_memory_allocated", "contrastive / InfoNCE / L_comp": r"contrastive|InfoNCE|L_comp",
        "Adaptive Channel Fusion / dual channel": r"[Ff]usion|dual[_ -]?channel", "CaKG": r"CaKG",
        "metapath": r"[Mm]etapath", "UltraGCN / NGCF": r"UltraGCN|NGCF",
    }
    hits = {k: [] for k in kw}
    skip = {".venv", "data", "node_modules", "results", ".git", "__pycache__", "target"}
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in skip]
        for fn in files:
            if not fn.endswith((".py", ".toml", ".md", ".java", ".js", ".jsx", ".ts", ".tsx")):
                continue
            p = os.path.join(root, fn)
            if os.path.normpath(p).startswith(os.path.normpath("ai/survey/khung")):
                continue                                                      # bỏ chính các script này
            try:
                s = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for k, rx in kw.items():
                if re.search(rx, s):
                    hits[k].append(p.replace("\\", "/"))
    for k, ps in hits.items():
        log(f"  {k}: {len(ps)} file" + (f" -> {ps[:6]}" if ps else ""))
    S = json.load(open(f"{TEST}/summary_test_20261009_125536.json", encoding="utf-8"))
    log(f"  Hit@5 trong số test: {'hit@5' in S['tables']['LightGCN']['full']}")
    rj = json.load(open("results/n5/final_20261009/lightgcn_l2-1e-03_s2/result.json", encoding="utf-8"))
    log(f"  thời gian / epoch có ghi trong result.json huấn luyện (median_sec_per_epoch): {'median_sec_per_epoch' in rj} "
        f"(LightGCN s2: {rj['median_sec_per_epoch']:.1f} s)")
    log("  VRAM đỉnh khi huấn luyện thật: result.json không có khoá bộ nhớ GPU: "
        f"{[k for k in rj if 'mem' in k.lower() or 'gpu' in k.lower()]}")
    log.save()


if __name__ == "__main__":
    main()
