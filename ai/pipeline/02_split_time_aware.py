"""
Script: 02_split_time_aware.py
Mục đích:
1. Đọc tương tác dense sau lọc k-core (camera_interactions_k5.csv).
2. Mã hóa user_id và item_asin thành chỉ số nguyên (0-indexed integer IDs).
3. Chia tập theo chuẩn Time-aware Leave-One-Out:
   - Train: Toàn bộ tương tác trước thời điểm kế cuối.
   - Val: Tương tác kế cuối của mỗi user.
   - Test: Tương tác cuối cùng của mỗi user.
4. Sinh tập 99 negative items ngẫu nhiên cho tập Val và Test phục vụ đánh giá ranking.
"""

import json
import os
import random
import sys
import time
import pandas as pd
from tqdm import tqdm

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

INPUT_CSV = "ai/data/processed/camera_interactions_k5.csv"
USER_MAP_PATH = "ai/data/processed/user_map.json"
ITEM_MAP_PATH = "ai/data/processed/item_map.json"
TRAIN_PATH = "ai/data/processed/train.txt"
VAL_PATH = "ai/data/processed/val.txt"
TEST_PATH = "ai/data/processed/test.txt"
VAL_NEGS_PATH = "ai/data/processed/val_negatives.json"
TEST_NEGS_PATH = "ai/data/processed/test_negatives.json"

NUM_NEGATIVES = 99
RANDOM_SEED = 42

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Lỗi: Không tìm thấy file {INPUT_CSV}. Hãy chạy 01_filter_camera_domain.py trước!")
        return

    print("=" * 60)
    print("BẮT ĐẦU CHIA TẬP TIME-AWARE LEAVE-ONE-OUT...")
    print("=" * 60)
    
    random.seed(RANDOM_SEED)
    df = pd.read_csv(INPUT_CSV)
    
    # 1. Tạo ánh xạ ID sang số nguyên
    unique_users = sorted(df["user_id"].unique())
    unique_items = sorted(df["parent_asin"].unique())
    
    user_to_id = {u: idx for idx, u in enumerate(unique_users)}
    item_to_id = {i: idx for idx, i in enumerate(unique_items)}
    
    with open(USER_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(user_to_id, f, indent=2)
    with open(ITEM_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(item_to_id, f, indent=2)
        
    print(f"-> Đã mã hóa {len(user_to_id):,} Users và {len(item_to_id):,} Items.")
    
    df["uid"] = df["user_id"].map(user_to_id)
    df["iid"] = df["parent_asin"].map(item_to_id)
    
    # 2. Gom nhóm theo User và sắp xếp theo Timestamp
    user_histories = {}
    for uid, group in tqdm(df.groupby("uid"), desc="Processing users"):
        # Sắp xếp theo timestamp tăng dần
        sorted_items = group.sort_values(by="timestamp")["iid"].tolist()
        user_histories[uid] = sorted_items
        
    all_item_set = set(range(len(unique_items)))
    
    train_lines = []
    val_lines = []
    test_lines = []
    val_negs = {}
    test_negs = {}
    
    for uid, items in tqdm(user_histories.items(), desc="Splitting sequences"):
        # Với k-core >= 5, mỗi user chắc chắn có >= 5 items
        train_items = items[:-2]
        val_item = items[-2]
        test_item = items[-1]
        
        # Format chuẩn: uid item1 item2 item3 ...
        train_lines.append(f"{uid} " + " ".join(map(str, train_items)) + "\n")
        val_lines.append(f"{uid} {val_item}\n")
        test_lines.append(f"{uid} {test_item}\n")
        
        # Sample 99 negatives cho Val và Test
        seen_items = set(items)
        available_negs = list(all_item_set - seen_items)
        
        if len(available_negs) >= NUM_NEGATIVES:
            sampled_val_negs = random.sample(available_negs, NUM_NEGATIVES)
            sampled_test_negs = random.sample(available_negs, NUM_NEGATIVES)
        else:
            sampled_val_negs = available_negs
            sampled_test_negs = available_negs
            
        val_negs[str(uid)] = sampled_val_negs
        test_negs[str(uid)] = sampled_test_negs
        
    # Ghi ra các file txt
    with open(TRAIN_PATH, "w", encoding="utf-8") as f:
        f.writelines(train_lines)
    with open(VAL_PATH, "w", encoding="utf-8") as f:
        f.writelines(val_lines)
    with open(TEST_PATH, "w", encoding="utf-8") as f:
        f.writelines(test_lines)
        
    with open(VAL_NEGS_PATH, "w", encoding="utf-8") as f:
        json.dump(val_negs, f)
    with open(TEST_NEGS_PATH, "w", encoding="utf-8") as f:
        json.dump(test_negs, f)
        
    print(f"\n-> Đã xuất tập Train: {TRAIN_PATH} ({len(train_lines):,} users)")
    print(f"-> Đã xuất tập Val:   {VAL_PATH} ({len(val_lines):,} users)")
    print(f"-> Đã xuất tập Test:  {TEST_PATH} ({len(test_lines):,} users)")
    print(f"-> Đã xuất tập Negatives: {VAL_NEGS_PATH} & {TEST_NEGS_PATH}")
    print("HOÀN THÀNH PHÂN CHIA DỮ LIỆU CHUẨN LEAVE-ONE-OUT!")

if __name__ == "__main__":
    main()
