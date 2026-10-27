"""
list_runtime_files.py -- Liệt kê mọi file trong repo mà dịch vụ mô hình FastAPI đọc khi chạy, file nào không có trong
git, kích thước và sha256 (để gửi cho máy khác chạy demo). Viết 28/10/2026.

Cách làm: bật móc kiểm tra (sys.addaudithook, sự kiện "open") rồi chạy app.py trong tiến trình này bằng TestClient
(lifespan nạp RecommenderCore như run_service.py), gọi đủ 5 điểm cuối: /health, /recommend (409, 47, cả hai chế độ
exclude), /items, /users/{id}/bodies, /compat. Mọi file mở để đọc nằm trong repo được ghi lại; file nào
`git ls-files` không có là file phải lấy riêng.

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/service/list_runtime_files.py --label <nhãn>
Kết quả: results/demo/runtime_files_<nhãn>/ (thư mục mới): log, files.json.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OPENED = set()


def hook(event, args):
    if event == "open" and isinstance(args[0], (str, os.PathLike)):
        mode = args[1] if len(args) > 1 and isinstance(args[1], str) else "r"
        if "w" not in mode and "a" not in mode and "x" not in mode:
            OPENED.add(str(args[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb-dir", default="results/service/emb_s1_20261021")
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(HERE))
    import core            # noqa: E402,F401  (thêm ai/pipeline vào sys.path; chưa nạp dữ liệu)
    import eval_05 as E    # noqa: E402  (Log, sha256, git_state)
    import common_05 as C  # noqa: E402
    run_dir = C.RESULTS_DIR / "demo" / f"runtime_files_{a.label}"
    run_dir.mkdir(parents=True, exist_ok=False)
    log = E.Log(run_dir / f"list_runtime_files_{E.now_tag()}.log")
    log(f"list_runtime_files | emb {a.emb_dir} | git {E.git_state()} | script sha256 {E.sha256(__file__)} | "
        f"python {sys.version.split()[0]}")

    os.environ["CAMERA_EMB_DIR"] = str((ROOT / a.emb_dir).resolve())
    os.environ["CAMERA_DEVICE"] = "cpu"
    from fastapi.testclient import TestClient   # noqa: E402
    sys.addaudithook(hook)
    import app as A   # noqa: E402
    calls = [("/health", None), ("/recommend", {"user_id": 409, "k": 10}), ("/recommend", {"user_id": 47, "k": 10}),
             ("/recommend", {"user_id": 47, "k": 10, "exclude": "train_val"}), ("/items/13466", None),
             ("/users/47/bodies", None), ("/users/47/bodies", {"exclude": "train_val"}),
             ("/compat", {"body_id": 9022, "lens_id": 13448})]
    with TestClient(A.app) as cl:
        for path, params in calls:
            r = cl.get(path, params=params)
            log(f"  {path} {params or ''}: {r.status_code}")
            assert r.status_code == 200, (path, r.text[:300])

    tracked = set(subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines())
    rows = []
    for s in sorted(OPENED):
        p = Path(s)
        p = p if p.is_absolute() else (Path.cwd() / p)
        try:
            rel = p.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            continue                               # ngoài repo (thư viện Python, ...)
        if not p.is_file() or rel.startswith(("ai/.venv/", "ai/service/", "ai/pipeline/")) or rel.endswith(".py"):
            continue
        rows.append({"path": rel, "in_git": rel in tracked, "bytes": p.stat().st_size, "sha256": E.sha256(p)})
    for r in rows:
        log(f"  {'git    ' if r['in_git'] else 'NGOÀI GIT'} {r['bytes']:>12,} B  {r['sha256']}  {r['path']}")
    out = [r for r in rows if not r["in_git"]]
    log(f"{len(rows)} file dữ liệu được đọc, {len(out)} file không có trong git, tổng "
        f"{sum(r['bytes'] for r in out) / 2**20:.1f} MiB")
    (run_dir / "files.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    log.close()


if __name__ == "__main__":
    main()
