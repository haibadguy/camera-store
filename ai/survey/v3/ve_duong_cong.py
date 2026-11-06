"""
ve_duong_cong.py — vẽ đường cong của MỘT lần chạy (train_05): loss mỗi epoch và NDCG@20 val mỗi lần chấm, đánh dấu
epoch tốt nhất và mốc trần cũ 300. Viết 06/11/2026 (docs/reviews/v3_eval_plan.md mục 4 "đường cong"). Chỉ đọc.

Đọc history từ result.json (lần chạy đã xong) hoặc từ last.pt (đang chạy / dở). Ghi vào thư mục lần chạy:
  curve_val_e<epoch>.png và curve_val_e<epoch>.csv (tên theo số epoch đã có -> không ghi đè ảnh cũ).
Chạy: ai\\.venv\\Scripts\\python.exe ai/survey/v3/ve_duong_cong.py <thư mục lần chạy> [...]
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def history(d):
    if (d / "result.json").exists():
        r = json.loads((d / "result.json").read_text(encoding="utf-8"))
        return r["history"], r["best_epoch"], ("dừng sớm" if r["stopped_early"] else "chạm trần"), "result.json"
    import torch
    ck = torch.load(d / "last.pt", map_location="cpu", weights_only=False)
    s = ck["state"]
    return s["history"], s["best_epoch"], "đang chạy / dở", "last.pt"


def main():
    for arg in sys.argv[1:]:
        d = Path(arg)
        h, best, status, src = history(d)
        ep = [x["epoch"] for x in h]
        ev = [(x["epoch"], x["val_ndcg@20"]) for x in h if "val_ndcg@20" in x]
        n = ep[-1]
        png, csv = d / f"curve_val_e{n}.png", d / f"curve_val_e{n}.csv"
        if png.exists():
            print(f"đã có, bỏ qua: {png}")
            continue
        with open(csv, "w", encoding="utf-8") as f:
            f.write("epoch,loss,val_ndcg@20,sec\n")
            for x in h:
                f.write(f"{x['epoch']},{x['loss']},{x.get('val_ndcg@20', '')},{x['sec']}\n")
        fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
        ax[0].plot(ep, [x["loss"] for x in h], lw=1)
        ax[0].set_xlabel("epoch")
        ax[0].set_ylabel("loss huấn luyện")
        ax[1].plot([e for e, _ in ev], [v for _, v in ev], marker=".", lw=1)
        bv = max(v for _, v in ev)
        ax[1].axvline(best, ls="--", c="g", lw=1, label=f"tốt nhất: epoch {best}, {bv:.5f}")
        if n > 300:
            ax[1].axvline(300, ls=":", c="gray", lw=1, label="trần cũ 300")
        ax[1].set_xlabel("epoch")
        ax[1].set_ylabel("NDCG@20 val (full ranking)")
        ax[1].legend(fontsize=8)
        fig.suptitle(f"{d.name} — {n} epoch, {status} (nguồn {src})", fontsize=10)
        fig.tight_layout()
        fig.savefig(png, dpi=110)
        plt.close(fig)
        print(f"-> {png}")


if __name__ == "__main__":
    main()
