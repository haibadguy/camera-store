"""
Script: 04_build_knowledge_graph.py
Mục đích: Xây dựng PyG HeteroData từ artifacts Mục 1–3.

Input:
  ai/data/processed/user_map.json
  ai/data/processed/item_map.json
  ai/data/processed/train.txt
  ai/data/kg/linked_products.csv
  ai/data/kg/compatibility_matrix.npz
  ai/data/kg/body_index.json
  ai/data/kg/lens_index.json
  ai/data/specs/camera_lens_specs.csv

Output:
  ai/data/kg/kg_hetero.pt            ← RGCN (Mục 5)
  ai/data/kg/kg_stats.json
  ai/data/kg/validation_log.txt
  ai/data/kg/user_item_train_edges.csv  ← LightGCN + Popularity
  ai/data/kg/compatible_item_edges.csv  ← Popularity-MountAware

Schema:
  Nodes : user | item (item_type one-hot[3]) | mount | usecase
  Edges : interacted_with | compatible_with | has_mount | suitable_for
          + 4 reverse via ToUndirected()

Chạy từ thư mục gốc camera-store:
  python ai/pipeline/04_build_knowledge_graph.py
"""

import json
import os
import sys

import pandas as pd
import torch
import torch.nn.functional as F
from scipy.sparse import load_npz
from torch_geometric.data import HeteroData
from torch_geometric.transforms import ToUndirected
from tqdm import tqdm

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── Paths ──────────────────────────────────────────────────────────────
USER_MAP   = "ai/data/processed/user_map.json"
ITEM_MAP   = "ai/data/processed/item_map.json"
TRAIN_TXT  = "ai/data/processed/train.txt"
LINKED_CSV = "ai/data/kg/linked_products.csv"
COMPAT_NPZ = "ai/data/kg/compatibility_matrix.npz"
BODY_IDX   = "ai/data/kg/body_index.json"
LENS_IDX   = "ai/data/kg/lens_index.json"
SPECS_CSV  = "ai/data/specs/camera_lens_specs.csv"

OUT_PT     = "ai/data/kg/kg_hetero.pt"
OUT_STATS  = "ai/data/kg/kg_stats.json"
OUT_LOG    = "ai/data/kg/validation_log.txt"
OUT_COMPAT = "ai/data/kg/compatible_item_edges.csv"
OUT_UI     = "ai/data/kg/user_item_train_edges.csv"

# Nếu unknown_mounts xuất hiện khi chạy, thêm vào đây đúng tên cột "mount"
MOUNT_INDEX = {
    "Sony E": 0,
    "Canon RF": 1,
    "Canon EF": 2,
    "Nikon Z": 3,
    "Nikon F": 4,
    "Fujifilm X": 5,
    "Micro Four Thirds": 6,
    "L-Mount": 7,
}

USECASE_INDEX = {
    "Portrait": 0,
    "Landscape": 1,
    "Sports": 2,
    "Wildlife": 3,
    "Vlog": 4,
    "Street": 5,
    "Travel": 6,
}

os.makedirs("ai/data/kg", exist_ok=True)
log_lines: list[str] = []


def log(msg: str) -> None:
    print(msg)
    log_lines.append(msg)


# ── BƯỚC 1: Load inputs ───────────────────────────────────────────────
log("=" * 60)
log("BƯỚC 1: LOAD INPUTS")
log("=" * 60)

user_map = json.load(open(USER_MAP, encoding="utf-8"))
item_map = json.load(open(ITEM_MAP, encoding="utf-8"))
body_idx = json.load(open(BODY_IDX, encoding="utf-8"))
lens_idx = json.load(open(LENS_IDX, encoding="utf-8"))

# Dùng len() — không dùng max(uid)+1
# (user có thể chỉ xuất hiện trong val/test, không có trong train)
N_USERS = len(user_map)
N_ITEMS = len(item_map)
log(f"→ N_USERS = {N_USERS:,}  |  N_ITEMS = {N_ITEMS:,}")

# Assert IDs liên tục — invariant do Mục 2 đảm bảo
assert set(item_map.values()) == set(range(N_ITEMS)), \
    "item_map IDs không liên tục 0..N_ITEMS-1"
assert set(user_map.values()) == set(range(N_USERS)), \
    "user_map IDs không liên tục 0..N_USERS-1"

# In 2 dòng đầu để xác nhận format {ASIN: index}
log(f"body_idx sample : {list(body_idx.items())[:2]}")
log(f"lens_idx  sample: {list(lens_idx.items())[:2]}")

M         = load_npz(COMPAT_NPZ)
df_linked = pd.read_csv(LINKED_CSV)
df_specs  = pd.read_csv(SPECS_CSV)

log(f"→ linked_products: {len(df_linked)} rows  |  M: {M.shape}  nnz={M.nnz}")
log(f"→ df_linked columns: {list(df_linked.columns)}")
log(f"→ df_linked category: {df_linked['category'].value_counts().to_dict()}")

# ── BƯỚC 2: Map ASIN → iid ────────────────────────────────────────────
log("\n" + "=" * 60)
log("BƯỚC 2: ASIN → IID MAPPING")
log("=" * 60)

df_linked["iid"] = df_linked["parent_asin"].map(item_map)
before = len(df_linked)
df_linked = df_linked.dropna(subset=["iid"])
df_linked["iid"] = df_linked["iid"].astype(int)
after = len(df_linked)
log(f"→ linked sau join: {after}  (dropped {before - after})")

assert after == 257, (
    f"Số linked items sau join = {after}, expected 257. "
    "Kiểm tra item_map vs linked_products.csv."
)

# ── BƯỚC 3: item_type feature ─────────────────────────────────────────
log("\n" + "=" * 60)
log("BƯỚC 3: ITEM TYPE FEATURE  [body=0 | lens=1 | accessory=2]")
log("=" * 60)

ITEM_TYPE = torch.full((N_ITEMS,), 2, dtype=torch.long)  # mặc định = accessory
for _, row in df_linked.iterrows():
    cat = str(row["category"]).strip()
    if cat == "Body":
        ITEM_TYPE[int(row["iid"])] = 0
    elif cat == "Lens":
        ITEM_TYPE[int(row["iid"])] = 1

n_body = (ITEM_TYPE == 0).sum().item()
n_lens = (ITEM_TYPE == 1).sum().item()
n_acc  = (ITEM_TYPE == 2).sum().item()
log(f"→ body={n_body}  |  lens={n_lens}  |  accessory={n_acc}  |  total={n_body+n_lens+n_acc}")

# Xác nhận khớp kết quả Mục 3
assert n_body == 106, f"n_body={n_body} ≠ 106"
assert n_lens == 151, f"n_lens={n_lens} ≠ 151"

item_x = F.one_hot(ITEM_TYPE, num_classes=3).float()  # [N_ITEMS, 3]

# ── BƯỚC 4: User-Item edges ────────────────────────────────────────────
log("\n" + "=" * 60)
log("BƯỚC 4: USER-ITEM EDGES  (train.txt)")
log("=" * 60)

uid_list: list[int] = []
iid_list: list[int] = []

with open(TRAIN_TXT, encoding="utf-8") as f:
    for line in tqdm(f, desc="Parsing train.txt"):
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        uid = int(parts[0])
        for iid_str in parts[1:]:
            uid_list.append(uid)
            iid_list.append(int(iid_str))

user_item_ei = torch.tensor([uid_list, iid_list], dtype=torch.long)
log(f"→ user-item edges: {user_item_ei.shape[1]:,}")

pd.DataFrame({"uid": uid_list, "iid": iid_list}).to_csv(OUT_UI, index=False)
log(f"→ Saved: {OUT_UI}")

# ── BƯỚC 5: compatible_with edges ─────────────────────────────────────
log("\n" + "=" * 60)
log("BƯỚC 5: COMPATIBLE_WITH EDGES")
log("=" * 60)

body_idx2asin = {v: k for k, v in body_idx.items()}
lens_idx2asin = {v: k for k, v in lens_idx.items()}

cx = M.tocoo()
src_iids: list[int] = []
dst_iids: list[int] = []
src_asins: list[str] = []
dst_asins: list[str] = []
skipped = 0

for b_i, l_i in zip(cx.row, cx.col):
    b_asin = body_idx2asin.get(int(b_i))
    l_asin = lens_idx2asin.get(int(l_i))
    b_iid  = item_map.get(b_asin) if b_asin else None
    l_iid  = item_map.get(l_asin) if l_asin else None
    if b_iid is not None and l_iid is not None:
        src_iids.append(int(b_iid));  dst_iids.append(int(l_iid))
        src_asins.append(b_asin);     dst_asins.append(l_asin)
    else:
        skipped += 1

skip_rate = skipped / M.nnz if M.nnz > 0 else 0.0
log(f"→ compatible edges: {len(src_iids)}  |  skipped: {skipped} ({skip_rate:.2%})")

assert len(src_iids) + skipped == M.nnz, \
    f"edge + skipped = {len(src_iids)+skipped} ≠ nnz(M) = {M.nnz}"
assert skipped == 0, (
    f"{skipped} ASIN trong compatibility_matrix không có trong item_map. "
    "Kiểm tra body_index.json / lens_index.json."
)

compat_ei = torch.tensor([src_iids, dst_iids], dtype=torch.long)

pd.DataFrame({
    "src_iid": src_iids, "dst_iid": dst_iids,
    "src_asin": src_asins, "dst_asin": dst_asins,
}).to_csv(OUT_COMPAT, index=False)
log(f"→ Saved: {OUT_COMPAT}")

# ── BƯỚC 6: has_mount edges ───────────────────────────────────────────
log("\n" + "=" * 60)
log("BƯỚC 6: HAS_MOUNT EDGES")
log("=" * 60)

mount_src: list[int] = []
mount_dst: list[int] = []
unknown_mounts: set[str] = set()

for _, row in df_linked.iterrows():
    m_name = str(row["mount"]).strip()
    m_idx  = MOUNT_INDEX.get(m_name)
    if m_idx is not None:
        mount_src.append(int(row["iid"]))
        mount_dst.append(m_idx)
    else:
        unknown_mounts.add(m_name)

if unknown_mounts:
    log(f"[ERROR] Mount không nhận diện: {unknown_mounts}")
    log("  Cập nhật MOUNT_INDEX ở đầu script rồi chạy lại.")
    raise ValueError(f"Unknown mount values: {unknown_mounts}")

log(f"→ has_mount edges: {len(mount_src)}")
mount_ei = torch.tensor([mount_src, mount_dst], dtype=torch.long)

# ── BƯỚC 7: suitable_for edges ────────────────────────────────────────
log("\n" + "=" * 60)
log("BƯỚC 7: SUITABLE_FOR EDGES")
log("=" * 60)

df_merged = df_linked.merge(
    df_specs[["spec_id", "suitable_usecase"]],
    on="spec_id",
    how="left",
)

uc_src: list[int] = []
uc_dst: list[int] = []
unknown_uc: set[str] = set()

for _, row in df_merged.iterrows():
    if pd.isna(row.get("suitable_usecase")):
        continue
    for uc in str(row["suitable_usecase"]).split("|"):
        uc = uc.strip()
        if uc in USECASE_INDEX:
            uc_src.append(int(row["iid"]))
            uc_dst.append(USECASE_INDEX[uc])
        else:
            unknown_uc.add(uc)

if unknown_uc:
    log(f"[WARN] Usecase labels không map được: {unknown_uc}")
log(f"→ suitable_for edges: {len(uc_src)}")

# Guard: tránh crash khi edge list rỗng
if len(uc_src) == 0:
    log("[WARN] suitable_for rỗng — kiểm tra join cột spec_id")
    usecase_ei = torch.zeros((2, 0), dtype=torch.long)
else:
    usecase_ei = torch.tensor([uc_src, uc_dst], dtype=torch.long)

# ── BƯỚC 8: Assemble HeteroData ───────────────────────────────────────
log("\n" + "=" * 60)
log("BƯỚC 8: ASSEMBLE HETERODATA")
log("=" * 60)

data = HeteroData()

data["user"].num_nodes = N_USERS
data["item"].x         = item_x        # [N_ITEMS, 3]  one-hot item_type
data["mount"].x        = torch.eye(8)  # [8, 8]
data["usecase"].x      = torch.eye(7)  # [7, 7]

data["user",  "interacted_with", "item"].edge_index    = user_item_ei
data["item",  "compatible_with", "item"].edge_index    = compat_ei
data["item",  "has_mount",       "mount"].edge_index   = mount_ei
data["item",  "suitable_for",    "usecase"].edge_index = usecase_ei

# Tạo tất cả inverse edges tự động
data = ToUndirected()(data)

log("\nEdge types sau ToUndirected():")
for et in data.edge_types:
    n = data[et].edge_index.shape[1]
    log(f"  {et}: {n:,}")

log(f"\n{data}")

# ── BƯỚC 9: Validation ────────────────────────────────────────────────
log("\n" + "=" * 60)
log("BƯỚC 9: VALIDATION CHECKS")
log("=" * 60)

errors: list[str] = []


def chk(cond: bool, msg: str) -> None:
    status = "✅ PASS" if cond else "❌ FAIL"
    log(f"  {status}: {msg}")
    if not cond:
        errors.append(msg)


chk(max(uid_list) < N_USERS,
    f"uid max ({max(uid_list)}) < N_USERS ({N_USERS})")
chk(max(iid_list) < N_ITEMS,
    f"iid max (user-item) ({max(iid_list)}) < N_ITEMS ({N_ITEMS})")
chk(compat_ei.numel() == 0 or compat_ei.max().item() < N_ITEMS,
    "compat iid in range")
chk(mount_ei[1].max().item() < 8,
    "mount idx in [0, 7]")
chk(n_body == 106,
    f"item_type body == 106 (got {n_body})")
chk(n_lens == 151,
    f"item_type lens == 151 (got {n_lens})")
chk(len(mount_src) == after,
    f"has_mount edges ({len(mount_src)}) == linked items ({after})")
chk(compat_ei.shape[1] == M.nnz,
    f"compatible edges ({compat_ei.shape[1]}) == nnz(M) ({M.nnz})")
if usecase_ei.shape[1] > 0:
    chk(usecase_ei[1].max().item() < 7,
        "usecase idx in [0, 6]")

if errors:
    raise RuntimeError(
        "Validation FAILED:\n" + "\n".join(f"  • {e}" for e in errors)
    )
log("\n✅ Tất cả validation PASSED")

# Sanity check 10 compatible pairs
log("\n10 compatible pairs sanity check:")
df_info = (
    df_linked.drop_duplicates(subset=["parent_asin"])
    .set_index("parent_asin")
)
for i in range(min(10, len(src_iids))):
    b_a = src_asins[i];  l_a = dst_asins[i]
    b_n = df_info.loc[b_a, "canonical_model"] if b_a in df_info.index else "?"
    l_n = df_info.loc[l_a, "canonical_model"] if l_a in df_info.index else "?"
    b_m = df_info.loc[b_a, "mount"]           if b_a in df_info.index else "?"
    log(f"  [{b_m}]  {b_n}  →  {l_n}")

# ── BƯỚC 10: Save artifacts ───────────────────────────────────────────
log("\n" + "=" * 60)
log("BƯỚC 10: SAVE ARTIFACTS")
log("=" * 60)

torch.save(data, OUT_PT)
log(f"✅ {OUT_PT}")

# Đếm users có body đã linked trong train
linked_body_iids = set(
    df_linked[df_linked["category"] == "Body"]["iid"].tolist()
)
users_with_body: set[int] = set()
with open(TRAIN_TXT, encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        uid = int(parts[0])
        for iid_str in parts[1:]:
            if int(iid_str) in linked_body_iids:
                users_with_body.add(uid)
                break

stats = {
    "node_counts": {
        "user": N_USERS, "item": N_ITEMS, "mount": 8, "usecase": 7,
    },
    "edge_counts_forward": {
        "interacted_with": int(user_item_ei.shape[1]),
        "compatible_with":  int(compat_ei.shape[1]),
        "has_mount":        int(mount_ei.shape[1]),
        "suitable_for":     int(usecase_ei.shape[1]),
    },
    "item_type_counts": {
        "body": n_body, "lens": n_lens, "accessory": n_acc,
    },
    "coverage": {
        "items_with_kg_edges": int(after),
        "items_without_kg_edges": N_ITEMS - int(after),
        "pct_items_without_kg_edges": round(
            (N_ITEMS - int(after)) / N_ITEMS * 100, 2
        ),
        "users_with_linked_body_in_train": len(users_with_body),
    },
    "compat_skipped": skipped,
    "compat_skip_rate_pct": round(skip_rate * 100, 2),
    "unknown_mounts": sorted(unknown_mounts),
    "unknown_usecase_labels": sorted(unknown_uc),
    "notes": {
        "train_interactions": int(user_item_ei.shape[1]),
        "full_kcore_interactions": 622997,
        "val_interactions": 70424,
        "test_interactions": 70424,
        "requires_adapter": "Out of scope — native mount compatibility only",
        "learnable_embeddings": "Defined in model (Mục 5), not stored in data.pt",
    },
}

with open(OUT_STATS, "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)
log(f"✅ {OUT_STATS}")

with open(OUT_LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))
log(f"✅ {OUT_LOG}")

log("\n" + "=" * 60)
log("=== HOÀN TẤT MỤC 4 ===")
log("=" * 60)
log(f"  {OUT_PT:<45} → RGCN (Mục 5)")
log(f"  {OUT_UI:<45} → LightGCN + Popularity (Mục 5)")
log(f"  {OUT_COMPAT:<45} → Popularity-MountAware (Mục 5)")
