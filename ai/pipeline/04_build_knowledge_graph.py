"""
Script: 04_build_knowledge_graph.py — Nội dung 4: dựng đồ thị tri thức G = (V, E, R) (PyG HeteroData).

Thiết kế: docs/content4_design.md mục 2, 5, 6, 9 (khi mục 9 khác các mục trước thì theo mục 9).

Ví dụ (content4_design mục 1, sửa 09/10/2026): người dùng thật uid 47 (train có Nikon D4S iid 12369,
ống 200-400mm f/4 iid 3680, ống 70-200mm f/2.8 iid 13215; in từ ai/survey/content4/vidu_chuong4.py)
  uid 47 ──interacted_with──▶ D4S, 200-400mm, 70-200mm    (train.txt)
  D4S ──compatible_with──▶ 200-400mm, 70-200mm            (nội dung 3, compat_pairs.csv)
  D4S ──has_spec──▶ [ngàm nikon_f], [khổ ff]
  70-200mm ──has_spec──▶ [ngàm nikon_f], [khổ ff], [tiêu cự 36-70, 71-135, 136-300], [khẩu độ <=2.8]
  70-200mm ──suitable_for──▶ [chan_dung]                  (luật mục đích, usecase_rules.toml)
(Ví dụ cũ "Rebel T7i + EF 50mm f/1.8 STM" là ví dụ giả định: không người dùng nào trong train có cả hai.)

Nút: user | item (thân / ống / phụ kiện / khác) | mount | sensor_format | focal_range | aperture_class | usecase
Cạnh (chiều xuôi; ToUndirected(merge=False) thêm rev_* cho mọi quan hệ, kể cả item -> item):
  user  -interacted_with->  item            chỉ train.txt
  item  -compatible_with->  item            thân -> ống, mức compatible_with, ống không "không chắc" (QĐ 4-5)
  item  -crops_sensor->     item            thân -> ống, mức crops_sensor        (hai quan hệ này = M = 1)
  item  -requires_adapter-> item            thân -> ống, mức requires_adapter (ngàm chuyển chính hãng)
  item  -has_spec->         mount           thân / ống / phụ kiện có 1 ngàm; ngàm chuyển "A>B": 2 cạnh (QĐ 4-10)
                                            thuộc tính cạnh: src_phu_kien (1 = nguồn là phụ kiện),
                                            phia (0 = không phải ngàm chuyển, 1 = phía ống, 2 = phía thân),
                                            ngam_khong_chac (1 = cạnh của ống "không chắc" QĐ 3-4)
  item  -has_spec->         sensor_format   thân / ống có 1 ngàm và khung ff / apsc / khac
  item  -has_spec->         focal_range     ống đọc được tiêu cự + khẩu độ (lens_specs.read_title), tiêu cự thật (QĐ 4-1)
  item  -has_spec->         aperture_class  như trên, theo số f nhỏ nhất
  item  -suitable_for->     usecase         luật mục đích (usecase_labels.py đọc usecase_rules.toml)
Cặp mức "unknown" và cặp của ống "không chắc" không có cạnh tương thích.

Đầu ra (--out-dir, mặc định ai/data/kg):
  kg_hetero.pt, kg_edges_<quan hệ>.csv, kg_node_index.json, kg_stats.json,
  kg_validation_log_<--run-label>.txt  (log tên mới; đã có thì DỪNG, không ghi đè)
Kiểm tra mục 6A (1–7) chạy trong script; sai một điều kiện là DỪNG (mã thoát 2). Kiểm tra 8 (chạy 2 lần, so sha256)
làm ngoài script. Mục 6B (10 cạnh ngẫu nhiên mỗi quan hệ) in vào log.

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/pipeline/04_build_knowledge_graph.py --run-label 20261008_lan1
"""

import argparse
import csv
import json
import os
import random
import sys
import tomllib
from collections import Counter, defaultdict

import torch
from scipy.sparse import load_npz
from torch_geometric.data import HeteroData
from torch_geometric.transforms import ToUndirected

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lens_specs as ls  # noqa: E402
from usecase_labels import UsecaseRules  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── Đường dẫn đầu vào ─────────────────────────────────────────────────────────
USER_MAP = "ai/data/processed/user_map.json"
ITEM_MAP = "ai/data/processed/item_map.json"
TRAIN_TXT = "ai/data/processed/train.txt"
VAL_TXT = "ai/data/processed/val.txt"
TEST_TXT = "ai/data/processed/test.txt"
MOUNT_RULES = "ai/config/mount_rules.toml"
KG_IN_FILES = ["item_attributes.csv", "compat_pairs.csv", "compatibility_matrix.npz", "unknown_mask.npz",
               "body_index.json", "lens_index.json"]

OUT_FILES = ["kg_hetero.pt", "kg_node_index.json", "kg_stats.json"]   # + kg_edges_*.csv (EDGE_CSV)

SEED = 20261008
ITEM_TYPE_CODE = {"than": 0, "ong": 1, "phu_kien": 2, "khac": 3}      # giống common_05.load_item_type
COMPAT_RELS = ["compatible_with", "crops_sensor", "requires_adapter"]
# Khổ cảm biến (content4_design mục 2): khung ff / apsc giữ nguyên; khung "khac" tra theo ngàm (mount_detect.py:
# canon_ef "khac" = EOS-1D APS-H, leica_m "khac" = M8 APS-H, mft / four_thirds, nikon_1, fuji_g = GFX, pentax_q).
SENSOR_FORMATS = ["ff", "apsc", "aps_h", "four_thirds", "one_inch", "medium", "small"]
KHAC_BY_MOUNT = {"canon_ef": "aps_h", "leica_m": "aps_h", "mft": "four_thirds", "four_thirds": "four_thirds",
                 "nikon_1": "one_inch", "fuji_g": "medium", "pentax_q": "small"}
ITEM_X_NAMES = ["la_than", "la_ong", "la_phu_kien", "la_khac", "tieu_cu_min_mm", "tieu_cu_max_mm",
                "khau_do_min_f", "khau_do_max_f", "co_tieu_cu_khau_do"]
PHIA = {0: "khong_phai_ngam_chuyen", 1: "phia_ong", 2: "phia_than"}

log_lines: list[str] = []


def log(msg: str = "") -> None:
    print(msg)
    log_lines.append(msg)


def is_single(m: str) -> bool:
    return m not in ("khong_co", "khong_ro", "nhieu", "") and ">" not in m


def read_pairs(path):
    """train/val/test.txt: 'uid iid1 iid2 ...' -> list[(uid, iid)] theo thứ tự file."""
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.split()
            if len(p) >= 2:
                u = int(p[0])
                out.extend((u, int(x)) for x in p[1:])
    return out


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def g(x):
    return "" if x is None else f"{x:g}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-label", required=True, help="nhãn lần chạy, dùng trong tên log (vd 20261008_lan1)")
    ap.add_argument("--kg-in", default="ai/data/kg", help="thư mục đầu ra nội dung 3")
    ap.add_argument("--out-dir", default="ai/data/kg")
    ap.add_argument("--overwrite", action="store_true", help="cho phép ghi đè kg_hetero.pt / kg_edges_*.csv ... đã có")
    ap.add_argument("--expect-m-nnz", type=int, default=72720, help="số cặp M = 1 (kiểm tra 3)")
    ap.add_argument("--expect-train", type=int, default=460193, help="số tương tác train (kiểm tra 2)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    out_log = os.path.join(args.out_dir, f"kg_validation_log_{args.run_label}.txt")
    if os.path.exists(out_log):
        sys.exit(f"DỪNG: {out_log} đã có. Log không ghi đè, chọn --run-label khác.")
    edge_csv = {}  # tên quan hệ -> tên file, điền ở dưới

    def P(name):
        return os.path.join(args.out_dir, name)

    def K(name):
        return os.path.join(args.kg_in, name)

    # ═══ BƯỚC 1: đọc đầu vào ══════════════════════════════════════════════════
    log("=" * 70)
    log("NỘI DUNG 4 — ĐỒ THỊ TRI THỨC")
    log("=" * 70)
    user_map = json.load(open(USER_MAP, encoding="utf-8"))
    item_map = json.load(open(ITEM_MAP, encoding="utf-8"))
    N_USERS, N_ITEMS = len(user_map), len(item_map)
    assert set(user_map.values()) == set(range(N_USERS)), "user_map: id không liên tục"
    assert set(item_map.values()) == set(range(N_ITEMS)), "item_map: id không liên tục"
    log(f"-> người dùng {N_USERS:,} | sản phẩm {N_ITEMS:,}")

    attrs = list(csv.DictReader(open(K("item_attributes.csv"), encoding="utf-8")))
    assert len(attrs) == N_ITEMS, "item_attributes.csv: số dòng khác item_map"
    A = [None] * N_ITEMS
    for a in attrs:
        i = int(a["iid"])
        assert item_map[a["parent_asin"]] == i, f"iid lệch item_map: {a['parent_asin']}"
        A[i] = a
    itype = [a["item_type"] for a in A]
    log(f"-> loại sản phẩm (item_attributes.csv): {dict(Counter(itype))}")

    body_idx = json.load(open(K("body_index.json"), encoding="utf-8"))
    lens_idx = json.load(open(K("lens_index.json"), encoding="utf-8"))
    M = load_npz(K("compatibility_matrix.npz")).tocoo()
    U = load_npz(K("unknown_mask.npz")).tocoo()
    log(f"-> M {M.shape[0]} x {M.shape[1]}, nnz {M.nnz:,} | unknown_mask nnz {U.nnz:,}")
    b_iid = {j: item_map[s] for s, j in body_idx.items()}
    l_iid = {j: item_map[s] for s, j in lens_idx.items()}
    M_pairs = {(b_iid[int(r)], l_iid[int(c)]) for r, c in zip(M.row, M.col)}
    U_pairs = {(b_iid[int(r)], l_iid[int(c)]) for r, c in zip(U.row, U.col)}

    cp = list(csv.DictReader(open(K("compat_pairs.csv"), encoding="utf-8")))
    log(f"-> compat_pairs.csv: {len(cp):,} dòng (mọi cặp khác incompatible, kể cả ống 'không chắc')")

    ucr = UsecaseRules()
    log(f"-> luật mục đích: usecase_rules.toml v{ucr.version}, nhãn {ucr.labels}; bộ đọc lens_specs {ls.READER_VERSION}")
    mrules_cfg = tomllib.load(open(MOUNT_RULES, "rb"))
    log(f"-> luật ngàm: mount_rules.toml v{mrules_cfg['meta']['version']}")

    # ═══ BƯỚC 2: nút item và vector đặc trưng ════════════════════════════════
    specs = [ls.read_title(a["title"]) if a["item_type"] == "ong" else None for a in A]
    x_rows = []
    for i in range(N_ITEMS):
        oh = [0.0] * 4
        oh[ITEM_TYPE_CODE[itype[i]]] = 1.0
        s = specs[i]
        if s:
            f1, f2, a1, a2 = s
            x_rows.append(oh + [f1, f2 if f2 is not None else f1, a1, a2 if a2 is not None else a1, 1.0])
        else:
            x_rows.append(oh + [0.0, 0.0, 0.0, 0.0, 0.0])
    item_x = torch.tensor(x_rows, dtype=torch.float32)
    item_type_t = torch.tensor([ITEM_TYPE_CODE[t] for t in itype], dtype=torch.long)

    # ═══ BƯỚC 3: interacted_with (chỉ train) ═════════════════════════════════
    train_pairs = read_pairs(TRAIN_TXT)
    ui = sorted(set(train_pairs))
    log(f"\n[interacted_with] train.txt: {len(train_pairs):,} dòng cặp, {len(ui):,} cặp khác nhau")

    # ═══ BƯỚC 4: cạnh thân -> ống (compat_pairs.csv, bỏ ống 'không chắc' và mức unknown) ═══
    compat = {r: [] for r in COMPAT_RELS}          # rel -> list[(b, l, rule_id, crop_unknown)]
    skipped = Counter()
    for r in cp:
        lev = r["level"]
        if r["lens_uncertain"] == "1":
            skipped[f"ống không chắc, mức {lev}"] += 1
            continue
        if lev == "unknown":
            skipped["mức unknown"] += 1
            continue
        compat[lev].append((int(r["body_iid"]), int(r["lens_iid"]), r["rule_id"], int(r["crop_unknown"])))
    for rel in COMPAT_RELS:
        compat[rel].sort()
        log(f"[{rel}] {len(compat[rel]):,} cạnh")
    log(f"   không thành cạnh: {dict(sorted(skipped.items()))}")

    # ═══ BƯỚC 5: has_spec -> mount (QĐ 4-7, 4-10) ═══════════════════════════
    mount_names = set()
    for a in A:
        m = a["mount"]
        if is_single(m):
            mount_names.add(m)
        elif ">" in m:
            mount_names.update(m.split(">"))
    mount_names = sorted(mount_names)
    mount_id = {m: k for k, m in enumerate(mount_names)}
    hs_mount = []                                     # (iid, mount, src_phu_kien, phia)
    for i, a in enumerate(A):
        m, t = a["mount"], a["item_type"]
        if is_single(m):
            if t in ("than", "ong"):
                hs_mount.append((i, m, 0, 0))
            elif t == "phu_kien":
                hs_mount.append((i, m, 1, 0))
            else:
                raise SystemExit(f"DỪNG: sản phẩm loại {t} có ngàm {m} (iid {i}), thiết kế không có trường hợp này")
        elif ">" in m:
            assert t == "phu_kien", f"ngàm chuyển không phải phụ kiện: iid {i}"
            lens_side, body_side = m.split(">")       # "A>B": ống ngàm A lắp lên thân ngàm B
            hs_mount.append((i, lens_side, 1, 1))
            hs_mount.append((i, body_side, 1, 2))
    hs_mount.sort(key=lambda e: (e[0], mount_id[e[1]]))
    # Cờ "ngàm không chắc" (Nam chốt 08/10 khuya): cạnh của ống "không chắc" (QĐ 3-4), để mô hình không coi đường
    # thân -> ngàm <- ống này là "lắp được"
    unc_lens = {i for i, a in enumerate(A) if a["uncertain"] == "True"}
    log(f"\n[has_spec -> mount] {len(mount_names)} nút ngàm; {len(hs_mount):,} cạnh: "
        f"{dict(Counter((itype[i], PHIA[p]) for i, _, _, p in hs_mount))}; "
        f"có cờ ngam_khong_chac: {sum(1 for e in hs_mount if e[0] in unc_lens)}")

    # ═══ BƯỚC 6: has_spec -> sensor_format ═══════════════════════════════════
    hs_sensor = []                                    # (iid, sensor_format)
    for i, a in enumerate(A):
        if a["item_type"] not in ("than", "ong") or not is_single(a["mount"]):
            continue
        k = a["khung"]
        if k in ("ff", "apsc"):
            hs_sensor.append((i, k))
        elif k == "khac":
            if a["mount"] not in KHAC_BY_MOUNT:
                raise SystemExit(f"DỪNG: khung 'khac' với ngàm {a['mount']} chưa có khổ (iid {i})")
            hs_sensor.append((i, KHAC_BY_MOUNT[a["mount"]]))
    log(f"[has_spec -> sensor_format] {len(hs_sensor):,} cạnh: {dict(Counter(s for _, s in hs_sensor))}")

    # ═══ BƯỚC 7: has_spec -> focal_range / aperture_class (QĐ 4-1, tiêu cự thật) ═══
    focal_names = [b for b, _, _ in ls.FOCAL_BINS]
    aper_names = [b for b, _ in ls.APER_BINS]
    hs_focal, hs_aper = [], []
    for i, s in enumerate(specs):
        if s:
            f1, f2, a1, _ = s
            hs_focal.extend((i, b) for b in ls.focal_nodes(f1, f2))
            hs_aper.append((i, ls.aperture_node(a1)))
    n_lens = itype.count("ong")
    n_read = sum(1 for s in specs if s)
    log(f"[has_spec -> focal_range] ống {n_lens:,}, đọc được tiêu cự + khẩu độ {n_read:,}; {len(hs_focal):,} cạnh: "
        f"{ {b: c for b, c in sorted(Counter(b for _, b in hs_focal).items(), key=lambda x: focal_names.index(x[0]))} }")
    log(f"[has_spec -> aperture_class] {len(hs_aper):,} cạnh: "
        f"{ {b: c for b, c in sorted(Counter(b for _, b in hs_aper).items(), key=lambda x: aper_names.index(x[0]))} }")

    # ═══ BƯỚC 8: suitable_for ════════════════════════════════════════════════
    uc_names = list(ucr.labels)
    suit = []
    for i, a in enumerate(A):
        if a["item_type"] == "ong":
            for lab in sorted(ucr.label_lens(a["title"], a["mount"], a["khung"]), key=uc_names.index):
                suit.append((i, lab))
    n_no_label = sum(1 for i, s in enumerate(specs) if s and not any(e[0] == i for e in suit))
    log(f"[suitable_for] {len(suit):,} cạnh: {dict(Counter(l for _, l in suit))}; ống đọc được mà không nhãn: {n_no_label}")

    # ═══ BƯỚC 9: HeteroData ══════════════════════════════════════════════════
    def ei(pairs):
        if not pairs:
            return torch.zeros((2, 0), dtype=torch.long)
        return torch.tensor(pairs, dtype=torch.long).t().contiguous()

    data = HeteroData()
    data["user"].num_nodes = N_USERS
    data["item"].x = item_x
    data["item"].item_type = item_type_t
    small = {"mount": mount_names, "sensor_format": SENSOR_FORMATS, "focal_range": focal_names,
             "aperture_class": aper_names, "usecase": uc_names}
    for nt, names in small.items():
        data[nt].x = torch.eye(len(names))
    sid = {nt: {n: k for k, n in enumerate(names)} for nt, names in small.items()}

    data["user", "interacted_with", "item"].edge_index = ei(ui)
    for rel in COMPAT_RELS:
        data["item", rel, "item"].edge_index = ei([(b, l) for b, l, _, _ in compat[rel]])
    data["item", "compatible_with", "item"].crop_unknown = torch.tensor(
        [c for _, _, _, c in compat["compatible_with"]], dtype=torch.int8)
    st = data["item", "has_spec", "mount"]
    st.edge_index = ei([(i, mount_id[m]) for i, m, _, _ in hs_mount])
    st.src_phu_kien = torch.tensor([s for _, _, s, _ in hs_mount], dtype=torch.int8)
    st.phia = torch.tensor([p for _, _, _, p in hs_mount], dtype=torch.int8)
    st.ngam_khong_chac = torch.tensor([int(i in unc_lens) for i, _, _, _ in hs_mount], dtype=torch.int8)
    data["item", "has_spec", "sensor_format"].edge_index = ei([(i, sid["sensor_format"][s]) for i, s in hs_sensor])
    data["item", "has_spec", "focal_range"].edge_index = ei([(i, sid["focal_range"][b]) for i, b in hs_focal])
    data["item", "has_spec", "aperture_class"].edge_index = ei([(i, sid["aperture_class"][b]) for i, b in hs_aper])
    data["item", "suitable_for", "usecase"].edge_index = ei([(i, sid["usecase"][l]) for i, l in suit])
    fwd_types = list(data.edge_types)
    data = ToUndirected(merge=False)(data)
    log(f"\nHeteroData: {len(data.node_types)} loại nút, {len(fwd_types)} loại cạnh xuôi, "
        f"{len(data.edge_types)} loại cạnh kể cả rev_*")

    # ═══ BƯỚC 10: kiểm tra 6A (1–6) ══════════════════════════════════════════
    log("\n" + "=" * 70)
    log("KIỂM TRA TOÀN VẸN (content4_design mục 6A)")
    log("=" * 70)
    fails = []

    def chk(no, cond, msg):
        log(f"  [{no}] {'ĐẠT' if cond else 'SAI'}: {msg}")
        if not cond:
            fails.append(f"[{no}] {msg}")

    # (1) chỉ số nút trong khoảng; không cạnh lặp trong cùng quan hệ
    for et in data.edge_types:
        e = data[et].edge_index
        ns, nd = data[et[0]].num_nodes, data[et[2]].num_nodes
        in_range = e.numel() == 0 or (int(e.min()) >= 0 and int(e[0].max()) < ns and int(e[1].max()) < nd)
        n_uniq = len(set(zip(e[0].tolist(), e[1].tolist())))
        chk(1, in_range and n_uniq == e.shape[1],
            f"{et}: {e.shape[1]:,} cạnh, chỉ số trong [0,{ns}) x [0,{nd}), không lặp ({n_uniq:,} cặp khác nhau)")
    for rel in COMPAT_RELS:
        bad = [(b, l) for b, l, _, _ in compat[rel] if itype[b] != "than" or itype[l] != "ong"]
        chk(1, not bad, f"{rel}: đầu là thân, cuối là ống (sai: {len(bad)})")

    # (2) interacted_with = đúng tập cặp train; giao val / test = 0
    val_pairs, test_pairs = set(read_pairs(VAL_TXT)), set(read_pairs(TEST_TXT))
    e_ui = set(zip(*[t.tolist() for t in data["user", "interacted_with", "item"].edge_index]))
    chk(2, e_ui == set(train_pairs) and len(e_ui) == len(train_pairs) == args.expect_train,
        f"interacted_with = tập cặp train.txt: {len(e_ui):,} cạnh, train {len(train_pairs):,} dòng cặp, "
        f"kỳ vọng {args.expect_train:,}")
    chk(2, len(e_ui & val_pairs) == 0 and len(e_ui & test_pairs) == 0,
        f"giao với val = {len(e_ui & val_pairs)}, với test = {len(e_ui & test_pairs)} (val {len(val_pairs):,}, "
        f"test {len(test_pairs):,} cặp)")

    # (3) cạnh thân–ống khớp M, compat_pairs, unknown_mask
    E = {rel: {(b, l) for b, l, _, _ in compat[rel]} for rel in COMPAT_RELS}
    m1 = E["compatible_with"] | E["crops_sensor"]
    chk(3, len(E["compatible_with"]) + len(E["crops_sensor"]) == M.nnz == args.expect_m_nnz and m1 == M_pairs,
        f"compatible_with {len(E['compatible_with']):,} + crops_sensor {len(E['crops_sensor']):,} = "
        f"{len(E['compatible_with']) + len(E['crops_sensor']):,}; nnz(M) = {M.nnz:,}; kỳ vọng {args.expect_m_nnz:,}; "
        f"trùng từng cặp với M: {m1 == M_pairs}")
    cp_ra = {(int(r["body_iid"]), int(r["lens_iid"])) for r in cp
             if r["level"] == "requires_adapter" and r["lens_uncertain"] == "0"}
    chk(3, E["requires_adapter"] == cp_ra,
        f"requires_adapter {len(E['requires_adapter']):,} cạnh = các dòng requires_adapter (ống chắc chắn) "
        f"của compat_pairs.csv ({len(cp_ra):,})")
    ov = [(a, b, len(E[a] & E[b])) for a in COMPAT_RELS for b in COMPAT_RELS if a < b]
    chk(3, all(n == 0 for _, _, n in ov), f"ba quan hệ thân–ống không trùng cặp: {ov}")
    allc = E["compatible_with"] | E["crops_sensor"] | E["requires_adapter"]
    chk(3, not (allc & U_pairs), f"không cặp nào thuộc unknown_mask (giao = {len(allc & U_pairs)}, "
        f"unknown_mask {len(U_pairs):,} cặp)")
    chk(3, not any(l in unc_lens for _, l in allc),
        f"không cạnh nào tới ống 'không chắc' (QĐ 4-5; {len(unc_lens)} ống)")

    # (4) mức của cạnh đúng luật mount_rules.toml (tra ngàm hai đầu)
    rules_by_id = {r["id"]: r for r in mrules_cfg["rule"]}

    def mount_ok(rule, bm, lm):
        pb = rule["body_mount"]
        pl = rule["lens_mount"]
        okb = pb == "*" or (bm in pb if isinstance(pb, list) else pb == bm)
        if pl == "=":
            return okb and lm == bm
        return okb and (pl == "*" or (lm in pl if isinstance(pl, list) else pl == lm))

    for rel in COMPAT_RELS:
        bad, same_mount, pairs = [], 0, Counter()
        for b, l, rid, _ in compat[rel]:
            bm, lm = A[b]["mount"], A[l]["mount"]
            rule = rules_by_id.get(rid)
            any_rule = any(r["level"] == rel and mount_ok(r, bm, lm) for r in mrules_cfg["rule"])
            if rule is None or rule["level"] != rel or not mount_ok(rule, bm, lm) or not any_rule:
                bad.append((b, l, rid, bm, lm))
            same_mount += bm == lm
            pairs[(bm, lm)] += 1
        chk(4, not bad, f"{rel}: luật của từng cạnh có đúng mức và khớp ngàm hai đầu (sai {len(bad)}); "
            f"cùng ngàm {same_mount:,}/{len(compat[rel]):,}; cặp ngàm (thân, ống): {dict(sorted(pairs.items()))}")
        for x in bad[:5]:
            log(f"      sai: {x}")

    # (5) mỗi thân / ống có 1 ngàm: đúng 1 cạnh has_spec -> mount, trùng cột mount; phụ kiện / ngàm chuyển có cờ
    by_item = defaultdict(list)
    for i, m, s, p in hs_mount:
        by_item[i].append((m, s, p))
    bad5 = []
    for i, a in enumerate(A):
        m, t, got = a["mount"], a["item_type"], sorted(by_item.get(i, []))
        if is_single(m):
            want = [(m, 1 if t == "phu_kien" else 0, 0)]
        elif ">" in m:
            ls_, bs_ = m.split(">")
            want = sorted([(ls_, 1, 1), (bs_, 1, 2)])
        else:
            want = []
        if got != want:
            bad5.append((i, t, m, got))
    n_tl = sum(1 for a in A if a["item_type"] in ("than", "ong") and is_single(a["mount"]))
    n_acc = sum(1 for a in A if a["item_type"] == "phu_kien" and is_single(a["mount"]))
    n_ad = sum(1 for a in A if ">" in a["mount"])
    chk(5, not bad5, f"thân + ống có 1 ngàm {n_tl:,} -> đúng 1 cạnh, trùng cột mount, src_phu_kien = 0; phụ kiện có "
        f"1 ngàm {n_acc:,} -> 1 cạnh, src_phu_kien = 1; ngàm chuyển {n_ad:,} -> 2 cạnh (phia_ong, phia_than), "
        f"src_phu_kien = 1; sản phẩm khác 0 cạnh (sai {len(bad5)})")
    for x in bad5[:5]:
        log(f"      sai: {x}")
    flag_e = {i for i, _, _, _ in hs_mount if i in unc_lens}
    n_flag = sum(1 for i, _, _, _ in hs_mount if i in unc_lens)
    chk(5, flag_e == unc_lens and n_flag == len(unc_lens) and all(itype[i] == "ong" for i in unc_lens)
        and int(st.ngam_khong_chac.sum()) == n_flag,
        f"cờ ngam_khong_chac: {n_flag} cạnh = {len(unc_lens)} ống 'không chắc' (mỗi ống 1 cạnh), các cạnh khác cờ 0")
    chk(5, len(hs_mount) == n_tl + n_acc + 2 * n_ad, f"tổng cạnh has_spec -> mount {len(hs_mount):,} = "
        f"{n_tl:,} + {n_acc:,} + 2 x {n_ad:,}")

    # (6) thân máy phim không có cạnh thân–ống
    film = {i for i, a in enumerate(A) if a["item_type"] == "than" and a["may_phim"] == "True"}
    film_e = sum(1 for b, _ in allc if b in film)
    chk(6, film_e == 0, f"{len(film)} thân máy phim, số cạnh compatible_with / crops_sensor / requires_adapter: {film_e}")

    if fails:
        log("\nDỪNG: kiểm tra sai, không ghi đầu ra:")
        for f_ in fails:
            log(f"  - {f_}")
        open(out_log, "w", encoding="utf-8").write("\n".join(log_lines) + "\n")
        sys.exit(2)

    # ═══ BƯỚC 11: ghi đầu ra ═════════════════════════════════════════════════
    titles = [a["title"] for a in A]
    asin = [a["parent_asin"] for a in A]
    edge_csv["interacted_with"] = ("kg_edges_interacted_with.csv", ["uid", "iid"], [list(p) for p in ui])
    for rel in COMPAT_RELS:
        edge_csv[rel] = (f"kg_edges_{rel}.csv",
                         ["body_iid", "body_asin", "body_mount", "lens_iid", "lens_asin", "lens_mount", "rule_id",
                          "crop_unknown"],
                         [[b, asin[b], A[b]["mount"], l, asin[l], A[l]["mount"], rid, cu] for b, l, rid, cu in compat[rel]])
    edge_csv["has_spec_mount"] = ("kg_edges_has_spec_mount.csv",
                                  ["iid", "parent_asin", "item_type", "mount", "src_phu_kien", "phia", "ngam_khong_chac",
                                   "title"],
                                  [[i, asin[i], itype[i], m, s, PHIA[p], int(i in unc_lens), titles[i]]
                                   for i, m, s, p in hs_mount])
    edge_csv["has_spec_sensor_format"] = ("kg_edges_has_spec_sensor_format.csv",
                                          ["iid", "parent_asin", "item_type", "mount", "khung", "sensor_format", "title"],
                                          [[i, asin[i], itype[i], A[i]["mount"], A[i]["khung"], s, titles[i]]
                                           for i, s in hs_sensor])
    edge_csv["has_spec_focal_range"] = ("kg_edges_has_spec_focal_range.csv",
                                        ["iid", "parent_asin", "f1", "f2", "focal_range", "title"],
                                        [[i, asin[i], g(specs[i][0]), g(specs[i][1]), b, titles[i]] for i, b in hs_focal])
    edge_csv["has_spec_aperture_class"] = ("kg_edges_has_spec_aperture_class.csv",
                                           ["iid", "parent_asin", "a1", "a2", "aperture_class", "title"],
                                           [[i, asin[i], g(specs[i][2]), g(specs[i][3]), b, titles[i]]
                                            for i, b in hs_aper])
    edge_csv["suitable_for"] = ("kg_edges_suitable_for.csv", ["iid", "parent_asin", "usecase", "title"],
                                [[i, asin[i], l, titles[i]] for i, l in suit])
    out_names = OUT_FILES + [v[0] for v in edge_csv.values()]
    existing = [n for n in out_names if os.path.exists(P(n))]
    if existing and not args.overwrite:
        log(f"\nDỪNG: {existing} đã có trong thư mục đầu ra. Thêm --overwrite nếu chắc chắn muốn ghi đè.")
        open(out_log, "w", encoding="utf-8").write("\n".join(log_lines) + "\n")
        sys.exit(2)

    torch.save(data, P("kg_hetero.pt"))
    for name, header, rows in edge_csv.values():
        write_csv(P(name), header, rows)
    node_index = {
        "ghi_chu": "chỉ số nút -> tên. user: chỉ số là giá trị trong ai/data/processed/user_map.json (không chép mã "
                   "người dùng). item: [parent_asin, item_type, title], chỉ số = iid của item_map.json.",
        "item_x": ITEM_X_NAMES,
        "has_spec_mount_phia": PHIA,
        "item_type_code": ITEM_TYPE_CODE,
        "user": {"so_nut": N_USERS},
        "item": [[asin[i], itype[i], titles[i]] for i in range(N_ITEMS)],
        **small,
    }
    json.dump(node_index, open(P("kg_node_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    fwd_counts = {"interacted_with": len(ui), **{r: len(compat[r]) for r in COMPAT_RELS},
                  "has_spec_mount": len(hs_mount), "has_spec_sensor_format": len(hs_sensor),
                  "has_spec_focal_range": len(hs_focal), "has_spec_aperture_class": len(hs_aper),
                  "suitable_for": len(suit)}
    stats = {
        "nut": {"user": N_USERS, "item": N_ITEMS, **{k: len(v) for k, v in small.items()},
                "tong": N_USERS + N_ITEMS + sum(len(v) for v in small.values())},
        "item_theo_loai": dict(Counter(itype)),
        "canh_xuoi": fwd_counts,
        "canh_xuoi_tong": sum(fwd_counts.values()),
        "canh_ke_ca_rev": {"__".join(et): int(data[et].edge_index.shape[1]) for et in data.edge_types},
        "has_spec_mount_theo_nguon": {f"{t}/{PHIA[p]}": c for (t, p), c in
                                      sorted(Counter((itype[i], p) for i, _, _, p in hs_mount).items())},
        "has_spec_sensor_format_theo_khung": dict(Counter(s for _, s in hs_sensor)),
        "has_spec_focal_range_theo_khoang": {b: sum(1 for _, x in hs_focal if x == b) for b in focal_names},
        "has_spec_aperture_class_theo_khoang": {b: sum(1 for _, x in hs_aper if x == b) for b in aper_names},
        "suitable_for_theo_nhan": {l: sum(1 for _, x in suit if x == l) for l in uc_names},
        "ong": {"tong": n_lens, "doc_duoc_tieu_cu_khau_do": n_read, "khong_chac_QD4": len(unc_lens),
                "doc_duoc_ma_khong_nhan_muc_dich": n_no_label},
        "has_spec_mount_ngam_khong_chac": n_flag,
        "compatible_with_crop_unknown": int(sum(c for _, _, _, c in compat["compatible_with"])),
        "M_nnz": int(M.nnz), "unknown_nnz": int(U.nnz), "than_may_phim": len(film),
        "phien_ban": {"lens_specs": ls.READER_VERSION, "usecase_rules": ucr.version,
                      "mount_rules": mrules_cfg["meta"]["version"]},
    }
    json.dump(stats, open(P("kg_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"\nĐã ghi: {', '.join(out_names)}")

    # ═══ BƯỚC 12: kiểm tra 7 — đọc lại .pt, chạy 1 lớp RGCNConv trên GPU ══════
    from torch_geometric.nn import RGCNConv
    d2 = torch.load(P("kg_hetero.pt"), weights_only=False)
    same = (set(d2.edge_types) == set(data.edge_types)
            and all(torch.equal(d2[et].edge_index, data[et].edge_index) for et in data.edge_types)
            and torch.equal(d2["item"].x, data["item"].x))
    h = d2.to_homogeneous(node_attrs=[], edge_attrs=[])
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(SEED)
    conv = RGCNConv(16, 16, num_relations=len(d2.edge_types)).to(dev)
    x0 = torch.randn(h.num_nodes, 16, device=dev)
    with torch.no_grad():
        out = conv(x0, h.edge_index.to(dev), h.edge_type.to(dev))
    ok7 = same and dev.type == "cuda" and tuple(out.shape) == (h.num_nodes, 16) and bool(torch.isfinite(out).all())
    chk(7, ok7, f"torch.load đọc lại khớp từng tensor: {same}; đồ thị đồng nhất {h.num_nodes:,} nút, "
        f"{h.edge_index.shape[1]:,} cạnh, {len(d2.edge_types)} quan hệ; RGCNConv trên {dev.type} "
        f"({torch.cuda.get_device_name(0) if dev.type == 'cuda' else '-'}) ra {tuple(out.shape)}, hữu hạn")
    if fails:
        log("\nDỪNG: kiểm tra 7 sai (đầu ra đã ghi, không dùng được).")
        open(out_log, "w", encoding="utf-8").write("\n".join(log_lines) + "\n")
        sys.exit(2)
    log("\n=> Kiểm tra 6A (1–7): ĐẠT cả. Kiểm tra 8 (chạy 2 lần, so sha256) làm ngoài script.")

    # ═══ BƯỚC 13: 6B — 10 cạnh ngẫu nhiên mỗi quan hệ ══════════════════════
    log("\n" + "=" * 70)
    log(f"ĐỌC BẰNG MẮT (mục 6B): 10 cạnh mỗi quan hệ, random.Random({SEED}).sample trên danh sách cạnh đã sắp")
    log("=" * 70)

    def T(i, n=70):
        return f"[{itype[i]} {i}] {titles[i][:n]}"

    samples = {
        "interacted_with": [f"user {u} -> {T(i)}" for u, i in ui],
        **{rel: [f"{T(b, 55)} ({A[b]['mount']}/{A[b]['khung']}) -> {T(l, 55)} ({A[l]['mount']}/{A[l]['khung']}) "
                 f"| {rid}{' | crop_unknown' if cu else ''}" for b, l, rid, cu in compat[rel]] for rel in COMPAT_RELS},
        "has_spec_mount": [f"{T(i)} -> {m} | src_phu_kien={s} | {PHIA[p]}{' | ngam_khong_chac' if i in unc_lens else ''}"
                           for i, m, s, p in hs_mount],
        "has_spec_sensor_format": [f"{T(i)} -> {s} (khung {A[i]['khung']}, ngàm {A[i]['mount']})" for i, s in hs_sensor],
        "has_spec_focal_range": [f"{T(i)} -> {b} (đọc {g(specs[i][0])}{'-' + g(specs[i][1]) if specs[i][1] else ''}mm)"
                                 for i, b in hs_focal],
        "has_spec_aperture_class": [f"{T(i)} -> {b} (đọc f/{g(specs[i][2])}{'-' + g(specs[i][3]) if specs[i][3] else ''})"
                                    for i, b in hs_aper],
        "suitable_for": [f"{T(i)} -> {l} (khung {A[i]['khung'] or '-'})" for i, l in suit],
    }
    for rel, rows in samples.items():
        log(f"-- {rel} ({len(rows):,})")
        for r in random.Random(SEED).sample(rows, min(10, len(rows))):
            log(f"   {r}")
    flagged = [r for r in samples["has_spec_mount"] if r.endswith("ngam_khong_chac")]
    log(f"-- has_spec_mount, chỉ cạnh có cờ ngam_khong_chac ({len(flagged):,})")
    for r in random.Random(SEED).sample(flagged, min(10, len(flagged))):
        log(f"   {r}")

    open(out_log, "w", encoding="utf-8").write("\n".join(log_lines) + "\n")
    print(f"\nLog: {out_log}")


if __name__ == "__main__":
    main()
