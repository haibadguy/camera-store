"""Hàm dùng chung cho các script viết chương báo cáo (ai/survey/report/).

Mọi script trong thư mục này CHỈ ĐỌC dữ liệu / đầu ra đã có, không ghi gì vào ai/data/processed,
ai/data/kg, results/. Log ghi ra file TÊN MỚI; file log đã có thì DỪNG (không ghi đè).
"""
import hashlib
import os
import subprocess
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

REPORT_LOG_DIR = "ai/data/survey/report"


class Log:
    """In ra màn hình và giữ lại để ghi vào một file log tên mới."""

    def __init__(self, path):
        if os.path.exists(path):
            sys.exit(f"DỪNG: log {path} đã có, chọn nhãn lần chạy khác (không ghi đè log cũ).")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.path = path
        self.lines = []

    def __call__(self, msg=""):
        print(msg)
        self.lines.append(str(msg))

    def save(self):
        with open(self.path, "x", encoding="utf-8") as f:
            f.write("\n".join(self.lines) + "\n")
        print(f"-> log: {self.path}")


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def git_state():
    """(commit HEAD, cây có thay đổi chưa commit không) của repo hiện tại."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                                capture_output=True, text=True).stdout.strip())
    return head, dirty


def header(log, script_path):
    head, dirty = git_state()
    log(f"script: {script_path} (sha256 {sha256_file(script_path)})")
    log(f"git HEAD: {head}, có thay đổi chưa commit (không tính file mới): {dirty}")
