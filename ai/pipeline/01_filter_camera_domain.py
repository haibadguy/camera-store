"""
Script: 01_filter_camera_domain.py
Mục đích:
1. Trích xuất Domain Camera & Photo từ meta_Electronics.jsonl.gz.
2. Lọc các tương tác từ Electronics.jsonl.gz thuộc các sản phẩm Camera.
3. Thực hiện lọc k-core lặp (Iterative k-core filtering, k=5) để loại bỏ nhiễu và dữ liệu thưa.
4. Xuất file thống kê và dữ liệu chuẩn bị cho bước chia train/val/test.
"""

import gzip
import json
import os
import sys
import time
from collections import defaultdict
from tqdm import tqdm

# Đảm bảo in UTF-8 không bị lỗi mã hóa trên Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

RAW_META_PATH = "ai/data/raw/meta_Electronics.jsonl.gz"
RAW_REVIEWS_PATH = "ai/data/raw/Electronics.jsonl.gz"
OUTPUT_META_PATH = "ai/data/processed/camera_items_meta.jsonl"
OUTPUT_INTERACTIONS_PATH = "ai/data/processed/camera_interactions_k5.csv"
STATS_PATH = "ai/data/processed/filtering_stats.json"

K_CORE = 5

CAMERA_KEYWORDS = {
    "camera & photo", "digital camera", "digital cameras", "camera lenses",
    "camera lens", "mirrorless cameras", "dslr cameras", "dslr lenses",
    "mirrorless lenses", "slr lenses", "point & shoot digital cameras",
    "camera flashes", "tripods & monopods"
}

EXCLUDE_KEYWORDS = {
    "security & surveillance", "surveillance cameras", "baby monitor",
    "trail camera", "dash cam", "hunting cameras", "webcams", "inspection camera",
    "endoscope", "hidden cameras", "spy camera"
}

def is_camera_product(item):
    """Xác định sản phẩm có thuộc domain Máy ảnh/Ống kính hay không."""
    categories = item.get("categories", [])
    cat_str = " ".join(categories).lower() if categories else ""
    title = (item.get("title") or "").lower()
    main_cat = (item.get("main_category") or "").lower()
    
    # Kiểm tra loại trừ trước (camera an ninh, webcam, cam hành trình...)
    for kw in EXCLUDE_KEYWORDS:
        if kw in cat_str or kw in title:
            return False
            
    # Kiểm tra từ khóa hợp lệ
    for kw in CAMERA_KEYWORDS:
        if kw in cat_str or kw in title or kw in main_cat:
            return True
            
    return False

def step_1_filter_metadata():
    print("=" * 60)
    print("BƯỚC 1: LỌC DOMAIN CAMERA TỪ METADATA...")
    print("=" * 60)
    
    camera_items = {}
    total_meta = 0
    start_time = time.time()
    
    with gzip.open(RAW_META_PATH, "rt", encoding="utf-8") as f:
        for line in tqdm(f, desc="Scanning metadata"):
            total_meta += 1
            try:
                item = json.loads(line)
            except Exception:
                continue
                
            asin = item.get("parent_asin") or item.get("asin")
            if not asin:
                continue
                
            if is_camera_product(item):
                # Lưu thông tin tối giản
                camera_items[asin] = {
                    "parent_asin": asin,
                    "title": item.get("title", ""),
                    "brand": item.get("store") or (item.get("details") or {}).get("Brand", ""),
                    "categories": item.get("categories", []),
                    "average_rating": item.get("average_rating"),
                    "rating_number": item.get("rating_number"),
                    "price": item.get("price")
                }
                
    elapsed = time.time() - start_time
    print(f"\n-> Tổng số sản phẩm trong Electronics: {total_meta:,}")
    print(f"-> Số sản phẩm Camera & Lens trích xuất được: {len(camera_items):,} (mất {elapsed:.1f}s)")
    
    # Ghi ra file JSONL
    os.makedirs(os.path.dirname(OUTPUT_META_PATH), exist_ok=True)
    with open(OUTPUT_META_PATH, "w", encoding="utf-8") as f:
        for it in camera_items.values():
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
            
    return set(camera_items.keys()), total_meta, len(camera_items)

def step_2_filter_interactions(camera_asins):
    print("\n" + "=" * 60)
    print("BƯỚC 2: TRÍCH XUẤT TƯƠNG TÁC THUỘC DOMAIN CAMERA...")
    print("=" * 60)
    
    interactions = []
    total_reviews = 0
    start_time = time.time()
    
    with gzip.open(RAW_REVIEWS_PATH, "rt", encoding="utf-8") as f:
        for line in tqdm(f, desc="Scanning reviews"):
            total_reviews += 1
            try:
                rev = json.loads(line)
            except Exception:
                continue
                
            asin = rev.get("parent_asin") or rev.get("asin")
            user_id = rev.get("user_id")
            rating = rev.get("rating")
            timestamp = rev.get("timestamp")
            
            if asin in camera_asins and user_id and timestamp:
                interactions.append({
                    "user_id": user_id,
                    "parent_asin": asin,
                    "rating": float(rating) if rating is not None else 5.0,
                    "timestamp": int(timestamp)
                })
                
    elapsed = time.time() - start_time
    print(f"\n-> Tổng số reviews trong Electronics: {total_reviews:,}")
    print(f"-> Số tương tác Camera thu được: {len(interactions):,} (mất {elapsed:.1f}s)")
    
    return interactions, total_reviews

def step_3_iterative_k_core(interactions, k=5):
    print("\n" + "=" * 60)
    print(f"BƯỚC 3: THỰC HIỆN THUẬT TOÁN LỌC K-CORE LẶP (k = {k})...")
    print("=" * 60)
    
    current_data = interactions
    iteration = 0
    
    while True:
        iteration += 1
        user_counts = defaultdict(int)
        item_counts = defaultdict(int)
        
        for record in current_data:
            user_counts[record["user_id"]] += 1
            item_counts[record["parent_asin"]] += 1
            
        filtered_data = [
            r for r in current_data
            if user_counts[r["user_id"]] >= k and item_counts[r["parent_asin"]] >= k
        ]
        
        num_users = len({r["user_id"] for r in filtered_data})
        num_items = len({r["parent_asin"] for r in filtered_data})
        num_interactions = len(filtered_data)
        
        print(f"Vòng {iteration}: {num_interactions:,} tương tác | {num_users:,} users | {num_items:,} items")
        
        if len(filtered_data) == len(current_data):
            print(f"-> Đạt trạng thái hội tụ hoàn toàn sau {iteration} vòng lặp!")
            break
            
        current_data = filtered_data
        
    return current_data

def main():
    start_all = time.time()
    
    # 1. Lọc Metadata
    camera_asins, total_meta, total_camera_items = step_1_filter_metadata()
    
    # 2. Lọc Reviews
    camera_interactions, total_reviews = step_2_filter_interactions(camera_asins)
    
    # 3. Lọc k-core
    dense_interactions = step_3_iterative_k_core(camera_interactions, k=K_CORE)
    
    # 4. Tính toán thống kê
    n_users = len({r["user_id"] for r in dense_interactions})
    n_items = len({r["parent_asin"] for r in dense_interactions})
    n_inter = len(dense_interactions)
    sparsity = 1.0 - (n_inter / (n_users * n_items)) if (n_users * n_items) > 0 else 0.0
    
    print("\n" + "=" * 60)
    print("KẾT QUẢ CUỐI CÙNG SAU K-CORE:")
    print("=" * 60)
    print(f"• Số Users:        {n_users:,}")
    print(f"• Số Items:        {n_items:,}")
    print(f"• Số Tương tác:    {n_inter:,}")
    print(f"• Độ thưa Sparsity: {sparsity * 100:.3f}%")
    print(f"• TB tương tác/User: {n_inter / n_users:.2f}")
    
    # Ghi file tương tác dense
    import pandas as pd
    df = pd.DataFrame(dense_interactions)
    df.to_csv(OUTPUT_INTERACTIONS_PATH, index=False)
    print(f"\n-> Đã lưu dữ liệu tương tác sạch vào: {OUTPUT_INTERACTIONS_PATH}")
    
    # Cập nhật metadata chỉ giữ lại các item còn tồn tại sau k-core
    surviving_items = set(df["parent_asin"].unique())
    surviving_meta = []
    with open(OUTPUT_META_PATH, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if item["parent_asin"] in surviving_items:
                surviving_meta.append(item)
                
    with open(OUTPUT_META_PATH, "w", encoding="utf-8") as f:
        for it in surviving_meta:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
            
    print(f"-> Đã đồng bộ lại metadata sản phẩm (còn {len(surviving_meta):,} items) vào: {OUTPUT_META_PATH}")
    
    # Lưu thống kê vào JSON
    stats = {
        "raw_electronics_reviews": total_reviews,
        "raw_electronics_metadata": total_meta,
        "raw_camera_items": total_camera_items,
        "raw_camera_interactions": len(camera_interactions),
        "k_core": K_CORE,
        "filtered_users": n_users,
        "filtered_items": n_items,
        "filtered_interactions": n_inter,
        "sparsity": sparsity,
        "avg_interactions_per_user": n_inter / n_users if n_users > 0 else 0
    }
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)
        
    print(f"-> Đã lưu báo cáo thống kê vào: {STATS_PATH}")
    print(f"\nHOÀN THÀNH TOÀN BỘ TRONG {time.time() - start_all:.1f} GIÂY!")

if __name__ == "__main__":
    main()
