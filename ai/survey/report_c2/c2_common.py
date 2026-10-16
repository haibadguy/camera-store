"""Hàm dùng chung cho các script viết chương 2 của quyển đồ án (ai/survey/report_c2/).

CHỈ ĐỌC. Mọi script trong thư mục này chỉ đọc đầu ra đã có (ai/data/, results/), không huấn luyện,
không chấm lại mô hình, không ghi gì vào ai/data/processed, ai/data/kg, results/.

Dữ liệu và kết quả nằm ở thư mục gốc dữ liệu `--root` (mặc định thư mục repo chứa script). Script có
thể đặt ở một worktree khác với thư mục dữ liệu, nên log ghi trạng thái git của CẢ HAI nơi và sha256
của mọi file đầu vào. Log ghi ra file TÊN MỚI trong <root>/ai/data/survey/report_c2/; log đã có thì DỪNG.
"""
import hashlib
import os
import subprocess
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
LOG_SUBDIR = os.path.join("ai", "data", "survey", "report_c2")


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def git_state(repo):
    """(nhánh, commit HEAD, có thay đổi chưa commit không) của repo `repo`."""
    def run(*a):
        return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True).stdout.strip()
    return (run("rev-parse", "--abbrev-ref", "HEAD"), run("rev-parse", "HEAD"),
            bool(run("status", "--porcelain", "--untracked-files=no")))


class Log:
    """In ra màn hình và giữ lại để ghi vào một file log tên mới."""

    def __init__(self, root, name):
        path = os.path.join(root, LOG_SUBDIR, name)
        if os.path.exists(path):
            sys.exit(f"DỪNG: log {path} đã có, chọn nhãn lần chạy khác (không ghi đè log cũ).")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self.lines = []

    def __call__(self, msg=""):
        print(msg)
        self.lines.append(str(msg))

    def save(self):
        with open(self.path, "x", encoding="utf-8") as f:
            f.write("\n".join(self.lines) + "\n")
        print(f"-> log: {self.path}")


def header(log, script_path, root):
    log(f"script: {os.path.abspath(script_path)} (sha256 {sha256_file(script_path)})")
    b, c, d = git_state(SCRIPT_REPO)
    log(f"git của script: {SCRIPT_REPO} nhánh {b} HEAD {c}, có thay đổi chưa commit: {d}")
    b, c, d = git_state(root)
    log(f"git của thư mục dữ liệu: {root} nhánh {b} HEAD {c}, có thay đổi chưa commit: {d}")


class Inputs:
    """Đọc file đầu vào theo đường dẫn tương đối với root, ghi sha256 vào log một lần."""

    def __init__(self, root, log):
        self.root, self.log, self.seen = root, log, set()

    def path(self, rel):
        p = os.path.join(self.root, rel)
        if rel not in self.seen:
            self.log(f"  đầu vào {rel} (sha256 {sha256_file(p)})")
            self.seen.add(rel)
        return p


def vn_int(x):
    return f"{int(round(x)):,}".replace(",", ".")


def vn_dec(x, d=4, sign=False):
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s.replace("-", "−").replace(".", ",")


def vn_pct(x, d=1):
    return f"{100 * x:.{d}f}".replace(".", ",") + "%"
