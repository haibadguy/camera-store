"""
to_recbole.py — chuyển ĐÚNG cách chia của nhóm (ai/data/processed/train.txt, val.txt, test.txt) sang file "atomic"
của RecBole, dạng benchmark (RecBole đọc sẵn 3 file đã chia, không tự chia lại). Viết 06/11/2026 cho việc kiểm
"RecBole có tái hiện được số LightGCN của nhóm không" (nhận xét cô 06/11, mục A3; docs/reviews/v3_eval_plan.md).

Ví dụ: train.txt có dòng "0 19283 3900" -> camera_loo.train.inter có 2 dòng "0<TAB>19283", "0<TAB>3900";
val.txt có "0 6293" -> camera_loo.valid.inter có "0<TAB>6293"; test tương tự.
Mã người dùng / sản phẩm giữ nguyên số nguyên của nhóm (user_map.json / item_map.json), RecBole coi là token.

Không đổi dữ liệu gốc, chỉ đọc. Chỉ dùng thư viện chuẩn (chạy được bằng venv nào cũng được).
Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/recbole/to_recbole.py
Đầu ra: ai/data/recbole/camera_loo/ (không lên git) + manifest.json (sha256 đầu vào / đầu ra, số dòng, kiểm tra).
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "ai" / "data" / "processed"
OUT = ROOT / "ai" / "data" / "recbole" / "camera_loo"
NAME = "camera_loo"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_split(p):
    """Mỗi dòng 'uid iid1 iid2 ...' -> list (uid, iid) theo đúng thứ tự trong file."""
    pairs = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            u = int(t[0])
            pairs += [(u, int(i)) for i in t[1:]]
    return pairs


def main():
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    n_users = len(json.loads((PROC / "user_map.json").read_text(encoding="utf-8")))
    n_items = len(json.loads((PROC / "item_map.json").read_text(encoding="utf-8")))
    splits = {"train": read_split(PROC / "train.txt"), "valid": read_split(PROC / "val.txt"),
              "test": read_split(PROC / "test.txt")}
    # Kiểm: mỗi người đúng 1 item val, 1 item test; không trùng cặp giữa các phần; mã trong khoảng.
    chk = {}
    for k in ("valid", "test"):
        us = [u for u, _ in splits[k]]
        chk[f"{k}_users"] = len(us)
        chk[f"{k}_one_item_per_user"] = len(us) == len(set(us)) == n_users
    tr = set(splits["train"])
    chk["train_pairs"] = len(splits["train"])
    chk["train_no_dup"] = len(tr) == len(splits["train"])
    chk["train_users"] = len({u for u, _ in splits["train"]})
    chk["val_test_overlap_train"] = sum((p in tr) for p in splits["valid"] + splits["test"])
    chk["val_eq_test_pairs"] = len(set(splits["valid"]) & set(splits["test"]))
    items_all = {i for s in splits.values() for _, i in s}
    items_train = {i for _, i in splits["train"]}
    chk["items_in_any_split"] = len(items_all)
    chk["items_in_train"] = len(items_train)
    chk["items_only_in_val_or_test"] = len(items_all - items_train)
    chk["ids_in_range"] = all(0 <= u < n_users and 0 <= i < n_items for s in splits.values() for u, i in s)
    chk["all_items_present"] = len(items_all) == n_items   # RecBole chỉ biết sản phẩm xuất hiện trong 3 file

    out_sha = {}
    for k, pairs in splits.items():
        p = OUT / f"{NAME}.{k}.inter"
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("user_id:token\titem_id:token\n")
            for u, i in pairs:
                f.write(f"{u}\t{i}\n")
        out_sha[p.name] = sha256(p)
    man = {"n_users": n_users, "n_items": n_items, "checks": chk,
           "inputs_sha256": {n: sha256(PROC / n) for n in ("train.txt", "val.txt", "test.txt", "user_map.json",
                                                            "item_map.json")},
           "outputs_sha256": out_sha}
    (OUT / "manifest.json").write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(man, indent=2, ensure_ascii=False))
    ok = (chk["valid_one_item_per_user"] and chk["test_one_item_per_user"] and chk["train_no_dup"]
          and chk["val_test_overlap_train"] == 0 and chk["ids_in_range"] and chk["all_items_present"])
    print("KIỂM:", "ĐẠT" if ok else "KHÔNG ĐẠT")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
