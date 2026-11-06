"""
to_recbole_kg.py — xuất đồ thị tri thức nội dung 4 (ai/data/kg/kg_hetero.pt) sang file .kg / .link của RecBole,
để chạy KGIN (và KGAT bản RecBole) trên CÙNG đồ thị KGAT / R-GCN của nhóm dùng. Viết 06/11/2026.

Quy ước (như 05c_rgcn_train.load_homogeneous và 07_kgat_train):
  - lấy mọi loại cạnh của kg_hetero.pt TRỪ cạnh có đầu hoặc đuôi là user (user–item đã nằm trong file .inter);
  - chỉ lấy chiều XUÔI (bỏ quan hệ tên bắt đầu bằng "rev_"): RecBole tự thêm chiều ngược cho mô hình cần;
  - bỏ 134 cạnh has_spec → mount có cờ ngam_khong_chac = 1 (QĐ 5-4);
  - thực thể = "<loại nút>_<chỉ số>", ví dụ ống iid 23 -> "item_23", ngàm số 4 -> "mount_4";
  - .link: CHỈ các item có mặt trong .kg -> "item_<iid>". Ở chế độ benchmark RecBole 1.2.1 bỏ qua _data_filtering
    (nên KHÔNG xóa tương tác nào), nhưng _merge_item_and_entity đòi mọi thực thể trong .link phải có trong .kg (bản
    06/11 lan1 ghi cả 27.940 item -> KeyError 'mount_14'). Item ngoài .kg vẫn có mã thực thể (0..n_items-1) nhưng
    không có cạnh tri thức — giống code KGIN gốc.
Ví dụ: cạnh (item 23) -has_spec-> (mount 4) -> dòng "item_23<TAB>item-has_spec-mount<TAB>mount_4".

Cần torch + torch_geometric để đọc kg_hetero.pt -> chạy bằng ai/.venv:
  ai\\.venv\\Scripts\\python.exe ai/recbole/to_recbole_kg.py
Đầu ra: ai/data/recbole/camera_loo/camera_loo.kg, camera_loo.link, manifest_kg.json (không lên git).
"""
import hashlib
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
KG_PT = ROOT / "ai" / "data" / "kg" / "kg_hetero.pt"
OUT = ROOT / "ai" / "data" / "recbole" / "camera_loo"
N_UNSURE_EXPECTED = 134


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    data = torch.load(str(KG_PT), weights_only=False)
    n_items = data["item"].num_nodes
    counts, dropped, kg_items = {}, {}, set()
    p_kg = OUT / "camera_loo.kg"
    with open(p_kg, "w", encoding="utf-8", newline="\n") as f:
        f.write("head_id:token\trelation_id:token\ttail_id:token\n")
        for et in data.edge_types:
            s, rel, d = et
            if "user" in (s, d) or rel.startswith("rev_"):
                continue
            st = data[et]
            ei = st.edge_index
            keep = torch.ones(ei.size(1), dtype=torch.bool)
            if "ngam_khong_chac" in st:
                keep = st.ngam_khong_chac.view(-1) == 0
                dropped[f"{s}-{rel}-{d}"] = int((~keep).sum())
            name = f"{s}-{rel}-{d}"
            hs, ts = ei[0, keep].tolist(), ei[1, keep].tolist()
            for h, t in zip(hs, ts):
                f.write(f"{s}_{h}\t{name}\t{d}_{t}\n")
            counts[name] = len(hs)
            if s == "item":
                kg_items.update(hs)
            if d == "item":
                kg_items.update(ts)
    assert dropped == {"item-has_spec-mount": N_UNSURE_EXPECTED}, dropped
    p_link = OUT / "camera_loo.link"
    with open(p_link, "w", encoding="utf-8", newline="\n") as f:
        f.write("item_id:token\tentity_id:token\n")
        for i in sorted(kg_items):
            f.write(f"{i}\titem_{i}\n")
    man = {"kg_hetero_sha256": sha256(KG_PT), "edge_types_all": [list(e) for e in data.edge_types],
           "kept_forward_relations": counts, "n_triples": sum(counts.values()), "dropped_ngam_khong_chac": dropped,
           "n_items": n_items, "n_items_linked": len(kg_items),
           "outputs_sha256": {p_kg.name: sha256(p_kg), p_link.name: sha256(p_link)}}
    (OUT / "manifest_kg.json").write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(man, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
