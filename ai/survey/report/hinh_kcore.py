"""Vẽ hình "quá trình hội tụ của k-core" cho báo cáo (chương 2).

CHỈ ĐỌC: số từng vòng lấy từ log của script 01 (`ai/data/processed/run01_fix.log`, các dòng
"Vòng n: … tương tác | … users | … items"), số đầu vào (vòng 0) lấy từ `filtering_stats.json`
(dedup_interactions, raw_camera_users, raw_camera_items_with_interaction). Không gõ tay số nào.
Kiểm: vòng cuối trùng filtered_* trong `filtering_stats.json`; số vòng = 14.

Ba đại lượng có thang rất khác nhau nên vẽ thành 3 ô nhỏ (không dùng hai trục y). Vẽ vòng 1–14 trên
thang thường để thấy hiệu ứng dây chuyền; giá trị đầu vào (trước vòng 1) ghi ở tiêu đề mỗi ô.

Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/report/hinh_kcore.py --out E:/DATN/baocao/hinh --label 20261009_lan1
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_common import REPORT_LOG_DIR, Log, header, sha256_file  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

RUN01_LOG = "ai/data/processed/run01_fix.log"
STATS = "ai/data/processed/filtering_stats.json"

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
SERIES = "#2a78d6"
GRID = "#e4e3df"


def vn_int(x):
    """67661 -> '67.661' (dấu chấm hàng nghìn)."""
    return f"{int(round(x)):,}".replace(",", ".")


def read_rounds():
    pat = re.compile(r"Vòng (\d+): ([\d,]+) tương tác \| ([\d,]+) users \| ([\d,]+) items")
    rounds = []
    with open(RUN01_LOG, encoding="utf-8") as f:
        for line in f:
            m = pat.search(line)
            if m:
                n, e, u, i = (int(g.replace(",", "")) for g in m.groups())
                rounds.append((n, e, u, i))
    return rounds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="thư mục ghi hình (ngoài repo)")
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_hinh_kcore_{args.label}.log"))
    header(log, __file__)

    st = json.load(open(STATS, encoding="utf-8"))
    rounds = read_rounds()
    log(f"đọc {RUN01_LOG} (sha256 {sha256_file(RUN01_LOG)}): {len(rounds)} vòng")
    log(f"đọc {STATS} (sha256 {sha256_file(STATS)})")
    assert [r[0] for r in rounds] == list(range(1, len(rounds) + 1)), "số vòng không liên tục"
    assert len(rounds) == 14, f"mong đợi 14 vòng, có {len(rounds)}"
    last = rounds[-1]
    assert (last[1], last[2], last[3]) == (st["filtered_interactions"], st["filtered_users"],
                                           st["filtered_items"]), "vòng cuối khác filtering_stats.json"
    assert rounds[-1][1:] == rounds[-2][1:], "hai vòng cuối phải giống nhau (hội tụ)"

    x = [0] + [r[0] for r in rounds]
    series = [
        ("Tương tác", [st["dedup_interactions"]] + [r[1] for r in rounds]),
        ("Người dùng", [st["raw_camera_users"]] + [r[2] for r in rounds]),
        ("Sản phẩm", [st["raw_camera_items_with_interaction"]] + [r[3] for r in rounds]),
    ]
    for name, ys in series:
        log(f"  {name}: " + ", ".join(vn_int(v) for v in ys))

    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 10,
                         "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2})
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.6), dpi=300)
    for ax, (name, ys) in zip(axes, series):
        xr, yr = x[1:], ys[1:]
        ax.plot(xr, yr, color=SERIES, linewidth=1.6, marker="o", markersize=3.2, zorder=3)
        ax.set_title(f"{name}\n(đầu vào: {vn_int(ys[0])})", color=INK, fontsize=10, pad=6)
        ax.set_xlabel("Vòng lặp", fontsize=9)
        ax.set_xticks([1, 2, 4, 6, 8, 10, 12, 14])
        ax.grid(axis="y", color=GRID, linewidth=0.6, zorder=0)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: vn_int(v)))
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="both", labelsize=8)
        # nhãn trực tiếp: giá trị vòng 1 và giá trị cuối
        ax.annotate(vn_int(yr[0]), (xr[0], yr[0]), xytext=(5, -2), textcoords="offset points",
                    fontsize=8, color=INK2, va="top")
        ax.annotate(vn_int(yr[-1]), (xr[-1], yr[-1]), xytext=(0, 6), textcoords="offset points",
                    fontsize=8, color=INK, ha="right", va="bottom")
        span = max(yr) - min(yr)
        ax.set_ylim(min(yr) - 0.08 * span, max(yr) + 0.08 * span)
    fig.tight_layout(w_pad=1.0)

    os.makedirs(args.out, exist_ok=True)
    out = os.path.join(args.out, "hinh_2_1_kcore.png")
    if os.path.exists(out):
        sys.exit(f"DỪNG: {out} đã có (không ghi đè).")
    fig.savefig(out, dpi=300, facecolor="white")
    log(f"ghi hình: {out} (sha256 {sha256_file(out)})")
    log.save()


if __name__ == "__main__":
    main()
