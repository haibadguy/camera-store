"""
run_service.py -- Chạy dịch vụ mô hình FastAPI (uvicorn). Viết 21/10/2026.

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/service/run_service.py --emb-dir results/service/emb_s1_20261021 --port 8001
Mỗi lần chạy ghi một log tên mới: results/service/logs/serve_<ngày giờ>.log (hoặc --log-file).
"""

import argparse
import copy
import os
import sys
import time
from pathlib import Path

import uvicorn

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb-dir", default="results/service/emb_s1_20261021")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--log-file", default=None)
    ap.add_argument("--access-log", action="store_true", help="ghi từng yêu cầu (tắt mặc định để không làm chậm)")
    a = ap.parse_args()
    log_file = Path(a.log_file) if a.log_file else ROOT / "results" / "service" / "logs" / \
        f"serve_{time.strftime('%Y%m%d_%H%M%S')}.log"
    assert not log_file.exists(), f"log đã có, không ghi đè: {log_file}"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    os.environ["CAMERA_EMB_DIR"] = str((ROOT / a.emb_dir).resolve() if not Path(a.emb_dir).is_absolute() else a.emb_dir)
    os.environ["CAMERA_DEVICE"] = a.device
    sys.path.insert(0, str(HERE))
    cfg = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)        # thêm một file log cạnh màn hình
    cfg["formatters"]["file"] = {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}
    cfg["handlers"]["file"] = {"class": "logging.FileHandler", "filename": str(log_file), "encoding": "utf-8",
                               "formatter": "file"}
    cfg["loggers"]["uvicorn"]["handlers"].append("file")
    cfg["loggers"]["uvicorn.access"]["handlers"].append("file")
    with open(log_file, "x", encoding="utf-8") as f:
        f.write(f"run_service | emb {os.environ['CAMERA_EMB_DIR']} | thiết bị {a.device} | {a.host}:{a.port}\n")
    uvicorn.run("app:app", host=a.host, port=a.port, access_log=a.access_log, log_level="info", workers=1,
                log_config=cfg)


if __name__ == "__main__":
    main()
