"""
make_demo_zip.py -- Đóng gói các file dữ liệu FastAPI đọc mà không có trong git thành một zip để gửi máy khác chạy demo.
Viết 05/11/2026 (Quyền chạy run_demo.ps1 trên máy khác: FastAPI thoát vì demo_data.zip 28/10 thiếu user_map.json).

Danh sách file KHÔNG ghi tay: đọc files.json do list_runtime_files.py ghi (mục "in_git": false), kiểm lại sha256 từng file
trên đĩa trùng files.json, rồi ghi zip (đường dẫn trong zip tính từ thư mục camera-store) kèm sha256.txt (dạng
`sha256sum`: "<sha256>  <đường dẫn>"); cạnh zip ghi thêm <tên>_sha256.txt (sha256 của chính zip + cùng danh sách).
Không ghi đè zip đã có.

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/service/make_demo_zip.py --files results/demo/runtime_files_20261105_lan1/files.json \\
      --out E:\\DATN\\demo_data_v2.zip
Sau đó kiểm: giải nén vào bản clone mới rồi chạy run_demo.ps1 (run_demo.ps1 tự kiểm sha256 cả danh sách).
"""

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", required=True, help="files.json của list_runtime_files.py")
    ap.add_argument("--out", required=True, help="đường dẫn zip (phải chưa có)")
    a = ap.parse_args()
    out = Path(a.out)
    side = out.with_name(out.stem + "_sha256.txt")
    for p in (out, side):
        if p.exists():
            sys.exit(f"DỪNG: {p} đã có, không ghi đè")
    rows = [r for r in json.loads(Path(a.files).read_text(encoding="utf-8")) if not r["in_git"]]
    lines = []
    for r in rows:
        got = sha256(ROOT / r["path"])
        if got != r["sha256"]:
            sys.exit(f"DỪNG: sha256 {r['path']} = {got}, files.json ghi {r['sha256']}")
        lines.append(f"{got}  {r['path']}")
    with zipfile.ZipFile(out, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for r in rows:
            z.write(ROOT / r["path"], r["path"])
        z.writestr("sha256.txt", "\n".join(lines) + "\n")
    # sha256 của chính zip, ghi cạnh zip (để người nhận kiểm zip trước khi giải nén)
    zsha = sha256(out)
    with open(side, "x", encoding="utf-8", newline="\n") as f:
        f.write(f"{zsha}  {out.name}\n" + "\n".join(lines) + "\n")
    print(f"{out}: {len(rows)} file ({sum(r['bytes'] for r in rows):,} B chưa nén), zip {out.stat().st_size:,} B, "
          f"sha256 zip {zsha}; ghi {side}")
    for s in lines:
        print("  " + s)


if __name__ == "__main__":
    main()
