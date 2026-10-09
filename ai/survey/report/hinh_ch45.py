"""Vẽ 3 hình cho chương 4–5 của báo cáo.

CHỈ ĐỌC. Mọi số trên hình đọc từ file kết quả, không gõ tay:
- Hình 4.1 (lược đồ đồ thị tri thức): `ai/data/kg/kg_stats.json`;
- Hình 5.1 (Recall@10, CVR@10 của 4 mô hình, tập test, trung bình ± độ lệch chuẩn qua 3 seed) và
  Hình 5.2 (Hit@20 sampled 1+99 so với Recall@20 xếp hạng toàn bộ):
  `results/n5/test_final_20261009/summary_test_*.json`.
Hai đại lượng có thang khác nhau nên vẽ thành hai ô riêng, không dùng hai trục y.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/report/hinh_ch45.py --out E:/DATN/baocao/hinh --label 20261010_lan1
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_common import REPORT_LOG_DIR, Log, header, sha256_file  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

KG_STATS = "ai/data/kg/kg_stats.json"
SUMMARY_GLOB = "results/n5/test_final_20261009/summary_test_*.json"
MODELS = ["Popularity", "Popularity-MountAware", "LightGCN", "R-GCN"]
LABELS = ["Popularity", "Popularity-\nMountAware", "LightGCN", "R-GCN"]

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e4e3df"
SERIES = "#2a78d6"
BOX_FILL, BOX_EDGE, FRAME_FILL = "#e8f1fc", "#2a78d6", "#fcfcfb"


def vn_int(x):
    return f"{int(x):,}".replace(",", ".")


def vn_dec(x, d=4):
    return f"{x:.{d}f}".replace(".", ",")


def box(ax, x, y, w, h, text, fs=8, fill=BOX_FILL, edge=BOX_EDGE, bold_first=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05",
                                fc=fill, ec=edge, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, fontsize=fs, color=INK, ha="center", va="center",
            linespacing=1.25)


def arrow(ax, p0, p1, lw=0.9):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=8, color=INK2, lw=lw))


def fig_kg(kg, out):
    n, ce = kg["nut"], kg["canh_xuoi"]
    it = kg["item_theo_loai"]
    W, H = 6.6, 4.5
    fig = plt.figure(figsize=(W, H), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    # user
    box(ax, 0.08, 1.95, 0.95, 0.75, f"user\n{vn_int(n['user'])} nút")
    # khung item
    cx0, cx1, cy0, cy1 = 1.75, 4.2, 0.15, 4.35
    ax.add_patch(FancyBboxPatch((cx0, cy0), cx1 - cx0, cy1 - cy0, boxstyle="round,pad=0,rounding_size=0.08",
                                fc=FRAME_FILL, ec=MUTED, lw=0.8))
    ax.text(cx0 + 0.1, cy1 - 0.17, f"item: {vn_int(n['item'])} nút", fontsize=8.5, fontweight="bold",
            color=INK, ha="left", va="center")
    bx0, bw = 1.95, 2.05
    box(ax, bx0, 3.25, bw, 0.6, f"thân máy: {vn_int(it['than'])}")
    box(ax, bx0, 1.55, bw, 0.6, f"ống kính: {vn_int(it['ong'])}")
    box(ax, bx0, 0.35, bw, 0.75, f"phụ kiện: {vn_int(it['phu_kien'])}\nmáy ảnh khác: {vn_int(it['khac'])}")
    arrow(ax, (bx0 + 0.3, 3.25), (bx0 + 0.3, 2.15))
    ax.text(bx0 + 0.42, 2.7,
            f"compatible_with: {vn_int(ce['compatible_with'])}\n"
            f"crops_sensor: {vn_int(ce['crops_sensor'])}\n"
            f"requires_adapter: {vn_int(ce['requires_adapter'])}",
            fontsize=7.4, color=INK2, ha="left", va="center", linespacing=1.3)
    # user -> item
    arrow(ax, (1.03, 2.32), (cx0, 2.32))
    ax.text((1.03 + cx0) / 2, 2.45, "interacted_with", fontsize=7, color=INK2, ha="center", va="bottom")
    ax.text((1.03 + cx0) / 2, 2.2, vn_int(ce["interacted_with"]), fontsize=7, color=INK2, ha="center",
            va="top")
    # nút thuộc tính
    attrs = [
        ("mount", n["mount"], "has_spec", ce["has_spec_mount"]),
        ("sensor_format", n["sensor_format"], "has_spec", ce["has_spec_sensor_format"]),
        ("focal_range", n["focal_range"], "has_spec", ce["has_spec_focal_range"]),
        ("aperture_class", n["aperture_class"], "has_spec", ce["has_spec_aperture_class"]),
        ("usecase", n["usecase"], "suitable_for", ce["suitable_for"]),
    ]
    ax0, aw, ah = 5.15, 1.35, 0.55
    ys = [3.7, 2.9, 2.1, 1.3, 0.5]
    for (name, cnt, rel, ecnt), yc in zip(attrs, ys):
        box(ax, ax0, yc - ah / 2, aw, ah, f"{name}\n{vn_int(cnt)} nút", fs=7.6)
        arrow(ax, (cx1, yc), (ax0, yc))
        ax.text((cx1 + ax0) / 2, yc + 0.04, f"{rel}\n{vn_int(ecnt)}", fontsize=6.8, color=INK2,
                ha="center", va="bottom", linespacing=1.15)
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)


def bars(ax, vals, sds, title, fmt_labels):
    xs = range(len(vals))
    ax.bar(xs, vals, color=SERIES, width=0.6, zorder=3)
    for x, v, s in zip(xs, vals, sds):
        if s:
            ax.errorbar(x, v, yerr=s, color=INK, capsize=3, lw=0.9, zorder=4)
    tops = [v + (s or 0) for v, s in zip(vals, sds)]
    top = max(tops) if max(tops) > 0 else 1
    for x, t, lab in zip(xs, tops, fmt_labels):
        ax.text(x, t + top * 0.03, lab, ha="center", va="bottom", fontsize=7.6, color=INK)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(LABELS, fontsize=7.6)
    ax.set_title(title, fontsize=10, color=INK, pad=6)
    ax.set_ylim(0, top * 1.22)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: vn_dec(v, 2)))
    ax.tick_params(axis="y", labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def get(t, path):
    cur = t
    for k in path:
        cur = cur[k]
    return cur["mean"], cur.get("sd")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_hinh_ch45_{args.label}.log"))
    header(log, __file__)
    summary = sorted(glob.glob(SUMMARY_GLOB))
    assert len(summary) == 1, summary
    summary = summary[0]
    for p in (KG_STATS, summary):
        log(f"đọc {p} (sha256 {sha256_file(p)})")
    kg = json.load(open(KG_STATS, encoding="utf-8"))
    sm = json.load(open(summary, encoding="utf-8"))["tables"]
    assert sum(kg["canh_xuoi"].values()) == kg["canh_xuoi_tong"]

    os.makedirs(args.out, exist_ok=True)
    outs = {k: os.path.join(args.out, f) for k, f in (("kg", "hinh_4_1_kg.png"),
                                                       ("rc", "hinh_5_1_recall_cvr.png"),
                                                       ("sf", "hinh_5_2_sampled_full.png"))}
    for o in outs.values():
        if os.path.exists(o):
            sys.exit(f"DỪNG: {o} đã có (không ghi đè).")

    plt.rcParams.update({"font.family": "Times New Roman", "axes.edgecolor": MUTED,
                         "xtick.color": INK2, "ytick.color": INK2})
    fig_kg(kg, outs["kg"])
    log(f"Hình 4.1: nút {kg['nut']}; cạnh xuôi {kg['canh_xuoi']}")

    r10 = [get(sm[m], ("full", "recall@10")) for m in MODELS]
    c10 = [get(sm[m], ("cvr", "cvr@10")) for m in MODELS]
    h20 = [get(sm[m], ("sampled_1_99", "hit@20")) for m in MODELS]
    r20 = [get(sm[m], ("full", "recall@20")) for m in MODELS]
    for name, arr in (("Recall@10 full", r10), ("CVR@10", c10), ("Hit@20 sampled", h20), ("Recall@20 full", r20)):
        log(f"{name}: " + "; ".join(f"{m} {vn_dec(v)}" + (f" ± {vn_dec(s)}" if s else "")
                                     for m, (v, s) in zip(MODELS, arr)))

    def labels(arr, zero_note=None):
        out = []
        for (v, s) in arr:
            out.append(zero_note if (zero_note and v == 0) else vn_dec(v))
        return out

    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.9), dpi=300)
    bars(axes[0], [v for v, _ in r10], [s for _, s in r10], "Recall@10 (xếp hạng toàn bộ)", labels(r10))
    bars(axes[1], [v for v, _ in c10], [s for _, s in c10], "CVR@10 (người đã có thân máy)",
         labels(c10, "0 (do cách dựng)"))
    fig.tight_layout(w_pad=1.5)
    fig.savefig(outs["rc"], dpi=300, facecolor="white")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.9), dpi=300)
    bars(axes[0], [v for v, _ in h20], [s for _, s in h20], "Hit@20, lấy mẫu 1 + 99", labels(h20))
    bars(axes[1], [v for v, _ in r20], [s for _, s in r20], "Recall@20, xếp hạng toàn bộ", labels(r20))
    fig.tight_layout(w_pad=1.5)
    fig.savefig(outs["sf"], dpi=300, facecolor="white")
    plt.close(fig)

    for o in outs.values():
        log(f"ghi hình: {o} (sha256 {sha256_file(o)})")
    log.save()


if __name__ == "__main__":
    main()
