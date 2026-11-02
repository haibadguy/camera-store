"""
check_run_demo.py -- Chạy run_demo.ps1 đúng như người dùng chạy (một lệnh), ghi log để làm bằng chứng cho câu "bật cả ba
thành phần bằng một lệnh" ở chương 3. Viết 02/11/2026 theo phản biện E:\\DATN\\reviews\\redteam_ch123_lan2.md mục 1.3
(bản cuối của run_demo.ps1 chưa có log chạy nào trên cây sạch) và mục 1.2 (lỗi "404 (Not Found)" là tài nguyên gì).

Script không sửa run_demo.ps1 và không thay nó bật dịch vụ. Các bước:
  1. Ghi trạng thái git (commit, cây có sửa chưa commit không), sha256 của run_demo.ps1 và jar Spring, RAM trống; kiểm
     ba cổng mặc định (8001, 8080, 5173) đang trống.
  2. Chạy `powershell -NoProfile -ExecutionPolicy Bypass -File run_demo.ps1` (lệnh trong đầu file run_demo.ps1, thêm
     -NoProfile để hồ sơ PowerShell của máy không chen vào), đọc từng dòng nó in, ghi kèm thời điểm. Đợi dòng "Demo đang
     chạy" (run_demo.ps1 đã chờ cả ba lên).
  3. Trong lúc chạy: ghi tiến trình nghe ở ba cổng và cây tiến trình con của PowerShell; gọi /api/health,
     /api/recommend?user_id=409&k=10, /api/users/409/bodies qua Spring và trang chủ Vite; mở trang bằng Edge
     (tools/demo_e2e/find_http_errors.mjs) để ghi mọi phản hồi HTTP >= 400 kèm địa chỉ.
  4. Gửi Enter vào cửa sổ run_demo.ps1 (như người dùng nhấn Enter để tắt). Đợi PowerShell thoát, rồi kiểm "tắt sạch":
     mọi tiến trình con đã ghi ở bước 3 không còn, ba cổng không còn tiến trình nghe.
  5. Bật riêng một Vite ở chế độ dữ liệu mẫu (cổng 5174, như pha mock của check_demo.py) và chạy lại
     find_http_errors.mjs, rồi tắt: pha này không gọi API nên lỗi HTTP nào cũng là tài nguyên của trang.
  6. Chép thư mục log run_demo.ps1 tự ghi (results/demo/run_demo_logs/<giờ>/, bị .gitignore) vào thư mục kết quả.

Chạy (từ thư mục camera-store; cần mọi thứ run_demo.ps1 cần, và npm install trong tools/demo_e2e/):
  ai\\.venv\\Scripts\\python.exe ai/service/check_run_demo.py --label <nhãn>
Kết quả: results/demo/check_run_demo_<nhãn>/ (thư mục mới): check_run_demo_<giờ>.log, run_demo_stdout_<giờ>.log,
browser_http_errors_{api,mock}_<giờ>.log, http_errors_{api,mock}.json, run_demo_logs/, summary.json.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import threading
import time

import httpx
import psutil

import check_demo as CD   # start_vite, kill, free_gb; nạp check_backend (JAR), check_service, common_05, eval_05

CB, C, E = CD.CB, CD.C, CD.E
RUN_DEMO = C.ROOT / "run_demo.ps1"
PORTS = {"FastAPI": 8001, "Spring Boot": 8080, "Vite": 5173}   # mặc định của run_demo.ps1
MOCK_PORT = 5174
# PowerShell 5.1 in ra ống (pipe) theo bảng mã OEM của Windows, chữ tiếng Việt có dấu thành "?" (lần chạy
# 20261102_lan1 không nhận ra dòng "Demo đang chạy" vì vậy). Chỉ khớp phần không dấu của các dòng run_demo.ps1 in.
READY_RE = re.compile(r"^Demo .*http://127\.0\.0\.1:5173")
SERVICE_RE = re.compile(r"^\s*(FastAPI|Spring Boot|Vite) .* (\d+[.,]\d+) s$")


def listeners(port):
    """Tiến trình đang nghe ở cổng TCP này trên máy (pid, tên)."""
    out = []
    for c in psutil.net_connections(kind="tcp"):
        if c.status == psutil.CONN_LISTEN and c.laddr and c.laddr.port == port and c.pid:
            try:
                out.append({"pid": c.pid, "name": psutil.Process(c.pid).name()})
            except psutil.NoSuchProcess:
                pass
    return out


def proc_info(p):
    try:
        return {"pid": p.pid, "name": p.name(), "create_time": p.create_time(),
                "rss_mib": round(p.memory_info().rss / 2**20, 1)}
    except psutil.NoSuchProcess:
        return None


def still_alive(info):
    """Đúng tiến trình đó (cùng pid và cùng thời điểm tạo) còn chạy không."""
    try:
        return psutil.Process(info["pid"]).create_time() == info["create_time"]
    except psutil.NoSuchProcess:
        return False


def run_probe(web, name, run_dir, tag, log):
    node = shutil.which("node")
    out_json = run_dir / f"http_errors_{name}.json"
    cmd = [node, str(CD.E2E_DIR / "find_http_errors.mjs"), "--web", web, "--out", str(out_json)]
    log(f"trình duyệt ({name}): node {' '.join(cmd[1:])}")
    r = subprocess.run(cmd, cwd=C.ROOT, capture_output=True, text=True, encoding="utf-8", timeout=120)
    with open(run_dir / f"browser_http_errors_{name}_{tag}.log", "x", encoding="utf-8") as f:
        f.write(r.stdout + r.stderr)
    for line in r.stdout.splitlines():
        log("  | " + line)
    if r.returncode != 0:
        log(r.stderr[-3000:])
        return None
    return json.loads(out_json.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--wait-ready", type=int, default=600, help="giây tối đa chờ run_demo.ps1 báo 'Demo đang chạy'")
    a = ap.parse_args()
    run_dir = C.RESULTS_DIR / "demo" / f"check_run_demo_{a.label}"
    run_dir.mkdir(parents=True, exist_ok=False)
    tag = E.now_tag()
    log = E.Log(run_dir / f"check_run_demo_{tag}.log")
    res = {"git": E.git_state(), "run_demo_sha256": E.sha256(RUN_DEMO), "script_sha256": E.sha256(__file__),
           "find_http_errors_sha256": E.sha256(CD.E2E_DIR / "find_http_errors.mjs"),
           "jar_sha256": E.sha256(CB.JAR) if CB.JAR.exists() else None, "ram_free_gb_start": CD.free_gb()}
    log(f"check_run_demo | git {res['git']} | run_demo.ps1 sha256 {res['run_demo_sha256']} | script sha256 "
        f"{res['script_sha256']} | find_http_errors.mjs sha256 {res['find_http_errors_sha256']} | jar sha256 "
        f"{res['jar_sha256']} | RAM trống {res['ram_free_gb_start']} GB")

    # -- 1. Cổng phải trống trước khi chạy -----------------------------------------------------------------------
    for name, port in PORTS.items():
        busy = listeners(port)
        log(f"trước khi chạy, cổng {port} ({name}): {busy or 'trống'}")
        if busy:
            sys.exit(f"DỪNG: cổng {port} đang bận")

    # -- 2. Chạy run_demo.ps1 ------------------------------------------------------------------------------------
    old_dirs = set((C.RESULTS_DIR / "demo" / "run_demo_logs").glob("*"))
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RUN_DEMO)]
    log(f"lệnh: {' '.join(cmd)} (cwd {C.ROOT})")
    lines, ready = [], threading.Event()
    out_f = open(run_dir / f"run_demo_stdout_{tag}.log", "x", encoding="utf-8")
    t0 = time.perf_counter()
    ps = subprocess.Popen(cmd, cwd=C.ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def reader():
        for raw in iter(ps.stdout.readline, b""):
            s = raw.decode("utf-8", errors="replace").rstrip()
            dt = time.perf_counter() - t0
            lines.append((dt, s))
            out_f.write(f"[{dt:7.1f}s] {s}\n")
            out_f.flush()
            log(f"  run_demo [{dt:6.1f}s] {s}")
            if READY_RE.search(s):
                ready.set()
        out_f.close()

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    while not ready.is_set() and ps.poll() is None and time.perf_counter() - t0 < a.wait_ready:
        time.sleep(0.5)
    res["ready"] = ready.is_set()
    res["ready_after_s"] = round(time.perf_counter() - t0, 1) if ready.is_set() else None
    if not ready.is_set():
        log(f"KHÔNG thấy dòng 'Demo ... http://127.0.0.1:5173' (PowerShell {'đã thoát, mã ' + str(ps.returncode) if ps.poll() is not None else 'vẫn chạy'})")
        if ps.poll() is None:
            CD.kill(ps)
        th.join(10)
        res["ok"] = False
        (run_dir / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(1)
    log(f"run_demo.ps1 báo sẵn sàng sau {res['ready_after_s']} s kể từ lúc gõ lệnh (gồm cả bước kiểm máy, sha256)")
    res["service_ready_s"] = {m[1]: float(m[2].replace(",", ".")) for m in (SERVICE_RE.search(s) for _, s in lines) if m}
    log(f"thời gian sẵn sàng run_demo.ps1 tự đo cho từng dịch vụ (s): {res['service_ready_s']}")

    # -- 3. Trong lúc chạy ---------------------------------------------------------------------------------------
    tree = [i for i in (proc_info(p) for p in psutil.Process(ps.pid).children(recursive=True)) if i]
    res["process_tree"] = tree
    log(f"cây tiến trình con của PowerShell (pid {ps.pid}): {len(tree)} tiến trình")
    for i in tree:
        log(f"  pid {i['pid']} {i['name']} RSS {i['rss_mib']} MiB")
    res["listeners_running"] = {}
    for name, port in PORTS.items():
        res["listeners_running"][name] = listeners(port)
        log(f"cổng {port} ({name}) đang nghe: {res['listeners_running'][name]}")

    checks = {}
    with httpx.Client(timeout=10) as cl:
        h = cl.get("http://127.0.0.1:8080/api/health")
        hj = h.json()
        log(f"GET /api/health qua Spring: HTTP {h.status_code} | status {hj.get('status')}, model {hj.get('model')}, "
            f"seed {hj.get('seed')}, n_users {hj.get('n_users')}, n_items {hj.get('n_items')}, "
            f"contract {hj.get('contract_version')}, nạp dữ liệu (startup_s) {hj.get('startup_s')} s")
        checks["health_200"] = h.status_code == 200
        r = cl.get("http://127.0.0.1:8080/api/recommend", params={"user_id": 409, "k": 10})
        rj = r.json()
        n_items, mask = len(rj.get("items", [])), rj.get("mask") or {}
        log(f"GET /api/recommend?user_id=409&k=10 qua Spring: HTTP {r.status_code} | {n_items} mục | ống bị chặn "
            f"{mask.get('n_lenses_blocked')} | X-Process-Time-Ms {r.headers.get('X-Process-Time-Ms')}")
        checks["recommend_409_200_10_items"] = r.status_code == 200 and n_items == 10
        b = cl.get("http://127.0.0.1:8080/api/users/409/bodies")
        log(f"GET /api/users/409/bodies qua Spring: HTTP {b.status_code} | {len(b.json().get('bodies', []))} thân")
        checks["bodies_409_200"] = b.status_code == 200
        v = cl.get("http://127.0.0.1:5173/")
        log(f"GET trang chủ Vite: HTTP {v.status_code}, {len(v.content)} byte")
        checks["vite_200"] = v.status_code == 200
    res["http_errors_api"] = run_probe("http://127.0.0.1:5173", "api", run_dir, tag, log)
    checks["browser_list_shown_api"] = bool(res["http_errors_api"] and res["http_errors_api"].get("list_shown"))

    # -- 4. Nhấn Enter để tắt, kiểm tắt sạch ---------------------------------------------------------------------
    log("gửi Enter vào run_demo.ps1 (tắt cả ba)")
    t_stop = time.perf_counter()
    ps.stdin.write(b"\r\n")
    ps.stdin.flush()
    ps.stdin.close()
    try:
        ps.wait(120)
    except subprocess.TimeoutExpired:
        log("PowerShell không thoát sau 120 s")
    th.join(10)
    res["powershell_exit_code"] = ps.poll()
    res["stop_s"] = round(time.perf_counter() - t_stop, 1)
    log(f"PowerShell thoát, mã {res['powershell_exit_code']}, sau {res['stop_s']} s kể từ khi gửi Enter")
    time.sleep(2)   # để Windows đóng hẳn cổng
    alive = [i for i in tree if still_alive(i)]
    after = {name: listeners(port) for name, port in PORTS.items()}
    res["alive_after_stop"], res["listeners_after_stop"] = alive, after
    for name, port in PORTS.items():
        log(f"sau khi tắt, cổng {port} ({name}): {after[name] or 'trống'}")
    log(f"tiến trình con còn sống sau khi tắt: {alive or 'không có'}")
    checks["clean_shutdown"] = res["powershell_exit_code"] == 0 and not alive and not any(after.values())

    # -- 5. Vite chế độ dữ liệu mẫu --------------------------------------------------------------------------------
    mp, mf, mweb = CD.start_vite(MOCK_PORT, "http://127.0.0.1:8080/api", run_dir / f"vite_mock_{tag}.log", log,
                                 source="mock")
    try:
        res["http_errors_mock"] = run_probe(mweb, "mock", run_dir, tag, log)
    finally:
        CD.kill(mp)
        mf.close()
    checks["browser_list_shown_mock"] = bool(res["http_errors_mock"] and res["http_errors_mock"].get("list_shown"))

    # -- 6. Chép log run_demo.ps1 tự ghi ---------------------------------------------------------------------------
    new_dirs = sorted(set((C.RESULTS_DIR / "demo" / "run_demo_logs").glob("*")) - old_dirs)
    res["run_demo_log_dirs"] = [d.name for d in new_dirs]
    for d in new_dirs:
        shutil.copytree(d, run_dir / "run_demo_logs" / d.name)
    log(f"đã chép log của run_demo.ps1: {res['run_demo_log_dirs']}")

    res["checks"] = checks
    res["ok"] = all(checks.values())
    res["ram_free_gb_end"] = CD.free_gb()
    for k, ok in checks.items():
        log(f"  {'ĐẠT' if ok else 'KHÔNG ĐẠT'}: {k}")
    log(f"KẾT QUẢ: {sum(checks.values())}/{len(checks)} mục đạt | RAM trống lúc kết thúc {res['ram_free_gb_end']} GB")
    (run_dir / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
