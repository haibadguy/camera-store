"""Chương 4, mục Nguồn: in phiên bản PyG đã cài trong ai/.venv và docstring của ToUndirected (tham số merge).

Chạy từ thư mục gốc camera-store:
  ai\\.venv\\Scripts\\python.exe ai/survey/report/c4_pyg_doc.py --label 20261009_lan1
"""
import argparse
import inspect
import os

import torch_geometric
from torch_geometric.transforms import ToUndirected

from report_common import REPORT_LOG_DIR, Log, header, sha256_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    log = Log(os.path.join(REPORT_LOG_DIR, f"run_c4_pyg_doc_{a.label}.log"))
    header(log, __file__)
    src = inspect.getsourcefile(ToUndirected)
    log(f"torch_geometric {torch_geometric.__version__}; file {src} (sha256 {sha256_file(src)})")
    log(f"chữ ký: ToUndirected{inspect.signature(ToUndirected.__init__)}")
    log("docstring:")
    log(ToUndirected.__doc__)
    log.save()


if __name__ == "__main__":
    main()
