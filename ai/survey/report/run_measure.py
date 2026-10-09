"""Chạy một lệnh (vd một script pipeline), đo thời gian thật và RAM đỉnh, ghi toàn bộ output vào log tên mới.

RAM đỉnh = PeakWorkingSetSize lớn nhất trong các tiến trình của cây lệnh (Windows). Lý do đo cả cây:
python.exe của venv trên Windows là trình chuyển tiếp, tự mở trình thông dịch thật làm tiến trình con.
Mỗi tiến trình con được giữ handle ngay khi thấy (quét mỗi 0,2 s), nên đọc được số đỉnh cả sau khi nó kết thúc.
Tiến trình sống ngắn hơn 0,2 s có thể bị sót (không ảnh hưởng các script dài).

Script này không đọc / ghi dữ liệu; chỉ ghi file log. Log đã có thì DỪNG.

Chạy (ví dụ):
  ai\\.venv\\Scripts\\python.exe ai/survey/report/run_measure.py --log <log mới> --cwd <thư mục> -- \\
      E:/DATN/camera-store/ai/.venv/Scripts/python.exe E:/DATN/camera-store/ai/pipeline/02_split_time_aware.py
"""
import argparse
import ctypes
import datetime
import os
import subprocess
import sys
import threading
import time
from ctypes import wintypes

import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


class PMC(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
kernel32.OpenProcess.restype = wintypes.HANDLE
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010


def peak_of(handle):
    c = PMC()
    c.cb = ctypes.sizeof(PMC)
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(c), c.cb):
        return None
    return c.PeakWorkingSetSize, c.PeakPagefileUsage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--cwd", default=".")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if os.path.exists(a.log):
        sys.exit(f"DỪNG: log {a.log} đã có (không ghi đè).")
    os.makedirs(os.path.dirname(os.path.abspath(a.log)), exist_ok=True)

    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    out = open(a.log, "x", encoding="utf-8")

    def w(s):
        out.write(s)
        out.flush()
        sys.stdout.write(s)

    w(f"[MEASURE] bắt đầu {datetime.datetime.now().isoformat(timespec='seconds')}\n")
    w(f"[MEASURE] cwd: {os.path.abspath(a.cwd)}\n[MEASURE] lệnh: {cmd}\n")
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=a.cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    handles = {}  # pid -> (tên, handle)
    stop = threading.Event()

    def watch():
        root = psutil.Process(p.pid)
        while not stop.is_set():
            try:
                procs = [root] + root.children(recursive=True)
            except psutil.NoSuchProcess:
                procs = []
            for pr in procs:
                if pr.pid not in handles:
                    h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pr.pid)
                    if h:
                        try:
                            name = pr.name()
                        except psutil.Error:
                            name = "?"
                        handles[pr.pid] = (name, h)
            time.sleep(0.2)

    th = threading.Thread(target=watch, daemon=True)
    th.start()
    for raw in iter(p.stdout.readline, b""):
        w(raw.decode("utf-8", errors="replace"))
    rc = p.wait()
    stop.set()
    th.join()
    dt = time.time() - t0
    w(f"\n[MEASURE] mã thoát: {rc}\n[MEASURE] thời gian thật: {dt:.1f} giây\n")
    best = 0
    for pid, (name, h) in sorted(handles.items()):
        r = peak_of(h)
        if r:
            w(f"[MEASURE] pid {pid} ({name}): Peak working set {r[0] / 2**30:.2f} GiB, "
              f"peak private (pagefile) {r[1] / 2**30:.2f} GiB\n")
            best = max(best, r[0])
        kernel32.CloseHandle(h)
    w(f"[MEASURE] RAM đỉnh (Peak working set lớn nhất trong cây tiến trình): {best / 2**30:.2f} GiB\n")
    out.close()
    sys.exit(rc)


if __name__ == "__main__":
    main()
