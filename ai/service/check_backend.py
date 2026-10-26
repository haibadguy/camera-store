"""
check_backend.py -- Kiểm thật backend Spring Boot nối với dịch vụ mô hình (nội dung 10). Viết 26/10/2026.

Chuỗi demo React -> Spring Boot -> FastAPI, ở đây "React" là script này. Các bước:
  0. Đóng gói Spring (mvn -o -q -DskipTests package) -> backend/target/camera-store-backend-0.1.0.jar (ghi sha256).
  1. Bật FastAPI seed 1 (run_service.py như check_service.py) và Spring (java -jar, model-service.base-url trỏ tới
     FastAPI vừa bật); mỗi tiến trình ghi log tên mới trong thư mục kết quả.
  2. So với dữ liệu giả của frontend (frontend/src/mock/, phản hồi thật của FastAPI seed 1 lưu 26/10, export_mock.py):
     /api/recommend?user_id=<u>&k=10 (u = 409, 47), /api/users/<u>/bodies, /api/items/<id> cho mọi file items/*.json
     phải TRÙNG NỘI DUNG (so hai object JSON sau khi đọc: cùng trường, cùng giá trị; thứ tự khóa không tính).
     Đồng thời so phản hồi qua Spring với phản hồi gọi thẳng FastAPI cùng tham số.
  3. Cùng nội dung với gọi thẳng FastAPI: /api/health, /api/compat (4 cặp), và 3 lỗi (404 USER_NOT_FOUND, 422
     INVALID_PARAM, 400 NOT_A_BODY): cùng mã HTTP, cùng thân lỗi.
  4. CORS: GET có Origin http://localhost:5173 -> có Access-Control-Allow-Origin đúng; Origin lạ -> 403.
  5. Độ trễ thêm của Spring: 200 yêu cầu /recommend?k=10 (người 0..199) qua Spring và gọi thẳng FastAPI, xen kẽ,
     sau 20 yêu cầu khởi động; p50 / p95 / max phía khách. Chỉ là số tham khảo trên máy của Nam.
  6. Tắt FastAPI: /api/recommend và /api/health qua Spring phải trả 503 MODEL_SERVICE_UNAVAILABLE.

Chạy (từ thư mục camera-store; cần JDK 21+ và Maven có trong PATH):
  ai\\.venv\\Scripts\\python.exe ai/service/check_backend.py --label <nhãn>
Kết quả: results/backend/check_backend_<nhãn>/ (thư mục mới): log, log FastAPI, log Spring, summary.json.
"""

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_service as CS   # noqa: E402  (start_server, tree; nạp common_05 / eval_05)

C, E = CS.C, CS.E
BACKEND = C.ROOT / "backend"
JAR = BACKEND / "target" / "camera-store-backend-0.1.0.jar"
MOCK = C.ROOT / "frontend" / "src" / "mock"
VITE = "http://localhost:5173"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def build(log):
    mvn = shutil.which("mvn")
    assert mvn, "không thấy mvn trong PATH"
    t = time.perf_counter()
    r = subprocess.run([mvn, "-o", "-q", "-DskipTests", "package"], cwd=BACKEND, capture_output=True, text=True)
    if r.returncode != 0:
        log(r.stdout[-3000:] + r.stderr[-3000:])
        sys.exit(f"DỪNG: mvn package lỗi (mã {r.returncode})")
    log(f"đóng gói Spring: {time.perf_counter() - t:.1f}s, {JAR.relative_to(C.ROOT)} sha256 {E.sha256(JAR)}")


def start_spring(port, fastapi_base, log_file, log):
    java = shutil.which("java")
    v = subprocess.run([java, "-version"], capture_output=True, text=True).stderr.splitlines()[0]
    cmd = [java, "-jar", str(JAR), f"--server.port={port}", f"--model-service.base-url={fastapi_base}"]
    log(f"bật Spring: {v} | {' '.join(cmd[1:])}")
    f = open(log_file, "x", encoding="utf-8")
    p = subprocess.Popen(cmd, cwd=BACKEND, stdout=f, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    t = time.perf_counter()
    while time.perf_counter() - t < 120:
        if p.poll() is not None:
            sys.exit(f"DỪNG: Spring thoát (mã {p.returncode}), xem {log_file}")
        try:
            r = httpx.get(base + "/api/health", timeout=2)
            if r.status_code == 200:
                log(f"Spring sẵn sàng sau {time.perf_counter() - t:.1f}s, /api/health = {r.json()}")
                return p, f, base
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    for x in reversed(CS.tree(p)):
        x.kill()
    sys.exit("DỪNG: Spring không lên sau 120 s")


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q / 100 * (len(xs) - 1))))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb-dir", default="results/service/emb_s1_20261021")
    ap.add_argument("--label", required=True)
    ap.add_argument("--fastapi-port", type=int, default=8051)
    ap.add_argument("--spring-port", type=int, default=8091)
    ap.add_argument("--users", type=int, nargs="+", default=[409, 47])
    a = ap.parse_args()
    run_dir = C.RESULTS_DIR / "backend" / f"check_backend_{a.label}"
    run_dir.mkdir(parents=True, exist_ok=False)
    tag = E.now_tag()
    log = E.Log(run_dir / f"check_backend_{tag}.log")
    meta = json.loads((C.ROOT / a.emb_dir / "meta.json").read_text(encoding="utf-8"))
    log(f"check_backend | emb {a.emb_dir} (seed {meta['seed']}) | git {E.git_state()} | script sha256 "
        f"{E.sha256(__file__)} | người {a.users}")
    build(log)
    fp, fbase, h = CS.start_server(a.emb_dir, a.fastapi_port, run_dir / f"serve_{tag}.log", log)
    assert h["best_pt_sha256"] == meta["best_pt_sha256"] and h["seed"] == 1
    sp, sf, sbase = start_spring(a.spring_port, fbase, run_dir / f"spring_{tag}.log", log)
    res = {"health": h, "git": E.git_state(), "jar_sha256": E.sha256(JAR), "mock": [], "same_as_fastapi": [],
           "cors": {}, "latency_ms": {}, "fastapi_down": []}

    def compare_mock(sp_cl, fa_cl, path, params, mock_file):
        rs, rf = sp_cl.get("/api" + path, params=params), fa_cl.get(path, params=params)
        mock = json.loads((MOCK / mock_file).read_text(encoding="utf-8"))
        row = {"url": "/api" + path, "params": params, "mock": mock_file, "status": rs.status_code,
               "content_type": rs.headers.get("content-type"),
               "same_as_mock": rs.status_code == 200 and rs.json() == mock,
               "same_as_fastapi": rs.status_code == rf.status_code and rs.json() == rf.json()}
        res["mock"].append(row)
        if not (row["same_as_mock"] and row["same_as_fastapi"]):
            log(f"  LỆCH {row}")
        return rs.json()

    def compare_fastapi(sp_cl, fa_cl, path, params):
        rs, rf = sp_cl.get("/api" + path, params=params), fa_cl.get(path, params=params)
        row = {"url": "/api" + path, "params": params, "status_spring": rs.status_code, "status_fastapi": rf.status_code,
               "same": rs.status_code == rf.status_code and rs.json() == rf.json()}
        res["same_as_fastapi"].append(row)
        log(f"  {'TRÙNG' if row['same'] else 'LỆCH'} {path} {params}: Spring {rs.status_code}, FastAPI {rf.status_code}"
            + ("" if rs.status_code == 200 else f", lỗi {rs.json()['error']['code']}"))

    try:
        with httpx.Client(base_url=sbase, timeout=10) as s, httpx.Client(base_url=fbase, timeout=10) as f:
            log("bước 2: so với frontend/src/mock/ và với gọi thẳng FastAPI")
            for u in a.users:
                j = compare_mock(s, f, "/recommend", {"user_id": u, "k": 10}, f"recommend_{u}.json")
                ex = [it for it in j["items"] if it["explanation"] is not None]
                log(f"  người {u}: top-10 {[it['item_id'] for it in j['items']]}, {len(ex)} câu giải thích, ví dụ: "
                    f"{ex[0]['explanation']['text'] if ex else '-'}")
                compare_mock(s, f, f"/users/{u}/bodies", None, f"users_{u}_bodies.json")
            for fn in sorted((MOCK / "items").glob("*.json"), key=lambda p: int(p.stem)):
                compare_mock(s, f, f"/items/{fn.stem}", None, f"items/{fn.name}")
            n_ok = sum(r["same_as_mock"] and r["same_as_fastapi"] for r in res["mock"])
            log(f"  trùng mock và trùng FastAPI: {n_ok}/{len(res['mock'])} phản hồi")

            log("bước 3: cùng nội dung với gọi thẳng FastAPI (health, compat, lỗi)")
            compare_fastapi(s, f, "/health", None)
            for b, l in [(9022, 13448), (19071, 9696), (9022, 118), (9022, 105)]:
                compare_fastapi(s, f, "/compat", {"body_id": b, "lens_id": l})
            compare_fastapi(s, f, "/recommend", {"user_id": 99999})
            compare_fastapi(s, f, "/recommend", {"user_id": 409, "k": 0})
            compare_fastapi(s, f, "/compat", {"body_id": 9696, "lens_id": 19071})

            log("bước 4: CORS")
            r = s.get("/api/recommend", params={"user_id": 409, "k": 10}, headers={"Origin": VITE})
            res["cors"]["vite_allow_origin"] = r.headers.get("access-control-allow-origin")
            r2 = s.get("/api/recommend", params={"user_id": 409, "k": 10}, headers={"Origin": "http://evil.example"})
            res["cors"]["other_origin_status"] = r2.status_code
            log(f"  Origin {VITE} -> Access-Control-Allow-Origin {res['cors']['vite_allow_origin']}; "
                f"Origin lạ -> {r2.status_code}")

            log("bước 5: độ trễ (200 yêu cầu mỗi đường, xen kẽ, sau 20 khởi động)")
            ts, tf = [], []
            for i in range(220):
                for cl, path, acc in ((s, "/api/recommend", ts), (f, "/recommend", tf)):
                    t = time.perf_counter()
                    r = cl.get(path, params={"user_id": i, "k": 10})
                    dt = (time.perf_counter() - t) * 1000
                    assert r.status_code == 200, (path, i, r.status_code)
                    if i >= 20:
                        acc.append(dt)
            for name, xs in (("spring", ts), ("fastapi", tf)):
                res["latency_ms"][name] = {"n": len(xs), "p50": round(statistics.median(xs), 2),
                                           "p95": round(pct(xs, 95), 2), "max": round(max(xs), 2)}
            log(f"  {res['latency_ms']}")
    finally:
        for x in reversed(CS.tree(fp)):
            x.kill()
        fp.wait(30)

    log("bước 6: tắt FastAPI, gọi qua Spring")
    try:
        with httpx.Client(base_url=sbase, timeout=10) as s:
            for path in ("/api/recommend?user_id=409&k=10", "/api/health"):
                r = s.get(path)
                j = r.json()
                res["fastapi_down"].append({"url": path, "status": r.status_code, "body": j})
                log(f"  {path} -> {r.status_code} {json.dumps(j, ensure_ascii=False)}")
    finally:
        # java trong PATH trên Windows có thể là launcher sinh tiến trình con: diệt cả cây (sửa sau lần lan2, lần đó
        # tiến trình Spring con còn chạy sau khi script xong)
        for x in reversed(CS.tree(sp)):
            x.kill()
        sp.wait(30)
        sf.close()

    checks = {
        "mock_all_same": all(r["same_as_mock"] and r["same_as_fastapi"] for r in res["mock"]),
        "fastapi_all_same": all(r["same"] for r in res["same_as_fastapi"]),
        "cors": res["cors"]["vite_allow_origin"] == VITE and res["cors"]["other_origin_status"] == 403,
        "down_503": all(r["status"] == 503 and r["body"]["error"]["code"] == "MODEL_SERVICE_UNAVAILABLE"
                        for r in res["fastapi_down"]),
    }
    res["checks"] = checks
    res["n_mock"] = len(res["mock"])
    (run_dir / "summary.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"KẾT QUẢ: {checks} -> {'ĐẠT' if all(checks.values()) else 'KHÔNG ĐẠT'}; summary {run_dir / 'summary.json'}")
    log.close()
    sys.exit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
