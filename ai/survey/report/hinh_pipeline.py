"""Vẽ hình "pipeline tổng quát nội dung 2–5" cho báo cáo (chương 1).

CHỈ ĐỌC. Mọi số trên hình đọc từ file đầu ra, không gõ tay:
- nội dung 2: `ai/data/processed/filtering_stats.json`; số train / val / test đếm từ `train.txt`,
  `val.txt`, `test.txt`;
- nội dung 3: `ai/data/kg/mount_compat_stats.json`; số luật và số trang nguồn đếm trong
  `ai/config/mount_rules.toml`;
- nội dung 4: `ai/data/kg/kg_stats.json`;
- nội dung 5: số người của kịch bản trong `results/n5/test_final_20261009/summary_test_*.json`.
Kiểm chéo: train = k-core − 2 × số người; số cạnh `interacted_with` của đồ thị = train.

Bố cục theo 4 khối nối tiếp (giữ bố cục hình 1.1 của bản báo cáo trước, vẽ lại với số mới).

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/report/hinh_pipeline.py --out E:/DATN/baocao/hinh --label 20261009_lan1
"""
import argparse
import glob
import json
import os
import sys
import tomllib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_common import REPORT_LOG_DIR, Log, header, sha256_file  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

P = "ai/data/processed"
FILTER_STATS = f"{P}/filtering_stats.json"
MOUNT_STATS = "ai/data/kg/mount_compat_stats.json"
MOUNT_RULES = "ai/config/mount_rules.toml"
KG_STATS = "ai/data/kg/kg_stats.json"
SUMMARY_GLOB = "results/n5/test_final_20261009/summary_test_*.json"

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
BOX_FILL = "#e8f1fc"
BOX_EDGE = "#2a78d6"
FRAME_FILL = "#fcfcfb"


def vn(x):
    return f"{int(x):,}".replace(",", ".")


def count_split():
    n_train = 0
    with open(f"{P}/train.txt", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if parts:
                n_train += len(parts) - 1
    n_val = sum(1 for line in open(f"{P}/val.txt", encoding="utf-8") if line.strip())
    n_test = sum(1 for line in open(f"{P}/test.txt", encoding="utf-8") if line.strip())
    return n_train, n_val, n_test


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_hinh_pipeline_{args.label}.log"))
    header(log, __file__)

    summary = sorted(glob.glob(SUMMARY_GLOB))
    assert len(summary) == 1, f"mong đợi 1 file summary, có {summary}"
    summary = summary[0]
    for path in (FILTER_STATS, MOUNT_STATS, MOUNT_RULES, KG_STATS, summary,
                 f"{P}/train.txt", f"{P}/val.txt", f"{P}/test.txt"):
        log(f"đọc {path} (sha256 {sha256_file(path)})")

    fs = json.load(open(FILTER_STATS, encoding="utf-8"))
    ms = json.load(open(MOUNT_STATS, encoding="utf-8"))
    rules = tomllib.load(open(MOUNT_RULES, "rb"))
    kg = json.load(open(KG_STATS, encoding="utf-8"))
    sm = json.load(open(summary, encoding="utf-8"))
    n_train, n_val, n_test = count_split()

    # kiểm chéo
    assert n_train == fs["filtered_interactions"] - 2 * fs["filtered_users"], "train ≠ k-core − 2 × người"
    assert n_val == n_test == fs["filtered_users"]
    assert kg["canh_xuoi"]["interacted_with"] == n_train, "cạnh interacted_with ≠ train"
    assert kg["nut"]["item"] == ms["n_items"] == fs["filtered_items"]

    it = ms["item_type"]
    ce = kg["canh_xuoi"]
    n_compat = ce["compatible_with"] + ce["crops_sensor"] + ce["requires_adapter"]
    n_attr = (ce["has_spec_mount"] + ce["has_spec_sensor_format"] + ce["has_spec_focal_range"]
              + ce["has_spec_aperture_class"] + ce["suitable_for"])
    n_node_types = len([k for k in kg["nut"] if k != "tong"])
    n_edge_types = len(kg["canh_ke_ca_rev"])
    scen = sm["tables"]["Popularity"]["scenario"]
    n_scen = sum(scen[g]["n_users"] for g in scen)

    blocks = [
        ("Nội dung 2. Thu thập và làm sạch dữ liệu", [
            f"Amazon Reviews 2023\nElectronics\n{vn(fs['raw_electronics_reviews'])} đánh giá\n"
            f"{vn(fs['raw_electronics_metadata'])} sản phẩm",
            f"Lọc lĩnh vực\nmáy ảnh\n{vn(fs['raw_camera_items'])} sản phẩm\n"
            f"{vn(fs['raw_camera_interactions'])} tương tác",
            f"Gộp tương tác lặp\n(mỗi cặp người–\nsản phẩm 1 lần)\n{vn(fs['dedup_interactions'])} tương tác",
            f"k-core, k = {fs['k_core']}\n{vn(fs['filtered_users'])} người\n"
            f"{vn(fs['filtered_items'])} sản phẩm\n{vn(fs['filtered_interactions'])} tương tác",
            f"Chia theo thời gian\ntrain {vn(n_train)}\nval {vn(n_val)}\ntest {vn(n_test)}",
        ]),
        ("Nội dung 3. Phân loại, ngàm và ma trận tương thích M", [
            f"Phân loại sản phẩm\nthân {vn(it['than'])}\nống {vn(it['ong'])}\n"
            f"phụ kiện {vn(it['phu_kien'])}\nkhác {vn(it['khac'])}",
            "Ngàm và khổ\nđọc từ tiêu đề,\ndòng máy",
            f"Xếp mức tương thích\n{len(rules['rule'])} luật,\n{len(rules['sources'])} trang nguồn của hãng",
            f"Ma trận M\n{vn(ms['n_bodies_in_M'])} thân × {vn(ms['n_lenses_in_M'])} ống\n"
            f"lắp được: {vn(ms['M_nnz'])}\nkhông biết: {vn(ms['unknown_nnz'])}",
        ]),
        ("Nội dung 4. Đồ thị tri thức", [
            f"Cạnh hành vi\nngười → sản phẩm\n{vn(ce['interacted_with'])}\n(chỉ tập train)",
            f"Cạnh tương thích\nthân → ống\n{vn(n_compat)}\n(3 mức)",
            f"Cạnh thuộc tính\nvà mục đích\n{vn(n_attr)}",
            f"Đồ thị dị thể\n{vn(kg['nut']['tong'])} nút, {n_node_types} loại\n"
            f"{vn(kg['canh_xuoi_tong'])} cạnh xuôi\n{n_edge_types} loại cạnh (kể cả ngược)",
        ]),
        ("Nội dung 5. Mô hình đối chứng và đo lường", [
            "4 mô hình\nPopularity\nPopularity-MountAware\nLightGCN\nR-GCN",
            f"Xếp hạng toàn bộ\nsản phẩm\n{vn(n_test)} người dùng\n(tập test)",
            "Chỉ số\nRecall@K, NDCG@K\nCVR@K",
            f"Kịch bản\nống cho người\nđã có thân\n{vn(n_scen)} người",
        ]),
    ]
    links = ["sản phẩm đã lọc, train / val / test", "M, mặt nạ không biết, ngàm, khổ",
             "đồ thị G (cho R-GCN), M (cho CVR)"]
    for title, boxes in blocks:
        log(f"[{title}]")
        for b in boxes:
            log("   " + b.replace("\n", " | "))

    plt.rcParams.update({"font.family": "Times New Roman"})
    W, H = 6.6, 7.86
    fig = plt.figure(figsize=(W, H), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    margin, frame_h, gap = 0.08, 1.62, 0.42
    box_h = 1.08
    top = H - 0.06
    for bi, (title, boxes) in enumerate(blocks):
        y1 = top - bi * (frame_h + gap)
        y0 = y1 - frame_h
        ax.add_patch(FancyBboxPatch((margin, y0), W - 2 * margin, frame_h,
                                    boxstyle="round,pad=0,rounding_size=0.08",
                                    fc=FRAME_FILL, ec=MUTED, lw=0.8))
        ax.text(margin + 0.12, y1 - 0.2, title, fontsize=10.5, fontweight="bold", color=INK,
                va="center", ha="left")
        n = len(boxes)
        inner_l, inner_r = margin + 0.12, W - margin - 0.12
        arrow_w = 0.16
        bw = (inner_r - inner_l - arrow_w * (n - 1)) / n
        by = y0 + 0.1
        for k, text in enumerate(boxes):
            bx = inner_l + k * (bw + arrow_w)
            ax.add_patch(FancyBboxPatch((bx, by), bw, box_h,
                                        boxstyle="round,pad=0,rounding_size=0.05",
                                        fc=BOX_FILL, ec=BOX_EDGE, lw=0.7))
            ax.text(bx + bw / 2, by + box_h / 2, text, fontsize=7.6, color=INK,
                    ha="center", va="center", linespacing=1.25)
            if k < n - 1:
                ax.add_patch(FancyArrowPatch((bx + bw + 0.02, by + box_h / 2),
                                             (bx + bw + arrow_w - 0.02, by + box_h / 2),
                                             arrowstyle="-|>", mutation_scale=7, color=INK2, lw=0.8))
        if bi < len(blocks) - 1:
            xa = W / 2
            ax.add_patch(FancyArrowPatch((xa, y0 - 0.03), (xa, y0 - gap + 0.03),
                                         arrowstyle="-|>", mutation_scale=10, color=INK2, lw=1.1))
            ax.text(xa + 0.1, y0 - gap / 2, links[bi], fontsize=8, color=INK2, ha="left", va="center",
                    style="italic")

    os.makedirs(args.out, exist_ok=True)
    out = os.path.join(args.out, "hinh_1_1_pipeline.png")
    if os.path.exists(out):
        sys.exit(f"DỪNG: {out} đã có (không ghi đè).")
    fig.savefig(out, dpi=300, facecolor="white")
    log(f"ghi hình: {out} (sha256 {sha256_file(out)})")
    log.save()


if __name__ == "__main__":
    main()
