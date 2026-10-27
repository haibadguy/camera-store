"""
check_demo.py -- Kiểm đầu cuối giao diện demo: React (Vite, chế độ api) -> Spring Boot -> FastAPI seed 1 (nội dung 10).
Viết 28/10/2026; sửa cùng ngày theo phản biện E:\\DATN\\reviews\\redteam_code_lan1.md (Nam chốt 8 điểm).

Các bước:
  0. Đóng gói Spring (như check_backend.py) và kiểm tools/demo_e2e đã cài (npm install trong thư mục đó).
  1. Bật FastAPI seed 1, Spring như run_demo.ps1 (-Xmx512m, chỉ nghe 127.0.0.1, model-service.base-url trỏ tới
     FastAPI vừa bật), Vite dev với VITE_RECOMMENDATION_SOURCE=api và VITE_API_URL trỏ tới Spring. Mỗi tiến trình ghi
     log tên mới trong thư mục kết quả.
  2. Gọi qua Spring bằng HTTP: /api/recommend người 409, 47, 99999 (không tồn tại), 99999999999999999999 (vượt kiểu
     long, phải 404 USER_NOT_FOUND như FastAPI) -> ghi mã HTTP, mã lỗi.
  3. Trình duyệt (tools/demo_e2e/demo_e2e.mjs --phase up, Edge có sẵn trên máy): người 409, 47 (nút chọn nhanh), 178,
     1476, 0 (ô nhập) -> danh sách trùng /api/recommend, ghi chú mặt nạ đúng câu Nam chốt (điền từ trường API, ống bị
     bỏ không lắp được trên mọi thân theo /api/compat), chi tiết (409, 47) có thuộc tính của /api/items/{id}, không có
     chữ trái hợp đồng 1.3; người 99999 nhập vào ô -> "Không tìm thấy người dùng này."; ô nhập "abc" bị từ chối; bơm
     một câu verified = false -> hiện câu thay thế. Ảnh màn hình: <thư mục kết quả>/screens/.
  4. Độ trễ đầu cuối qua Spring: 1.000 yêu cầu /api/recommend?k=10 (exclude mặc định all_history, như giao diện), người
     chọn ngẫu nhiên như check_service.py (seed 20261014, không lặp), sau 50 yêu cầu khởi động, gửi lần lượt. Rồi cùng
     những người đó gọi thẳng FastAPI để tham khảo. Ghi RAM trống trước / sau mỗi lượt; RAM trống < 6 GB thì ghi
     "đo khi máy bận".
  5. Tắt FastAPI: HTTP /api/recommend qua Spring, rồi trình duyệt (--phase down) -> "Dịch vụ gợi ý đang tạm dừng, thử
     lại sau."
  6. Vite thứ hai ở chế độ dữ liệu mẫu (--phase mock): nhãn "Dữ liệu mẫu" hiện, danh sách 409 trùng
     frontend/src/mock/recommend_409.json, không gọi API.

Chạy (từ thư mục camera-store; cần JDK 21+, Maven, Node trong PATH; npm ci trong frontend/ và npm install trong
tools/demo_e2e/):
  ai\\.venv\\Scripts\\python.exe ai/service/check_demo.py --label <nhãn>
Kết quả: results/demo/check_demo_<nhãn>/ (thư mục mới): log, log FastAPI / Spring / Vite / trình duyệt, screens/,
e2e_up.json, e2e_down.json, e2e_mock.json, summary.json.
"""

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time

import httpx
import numpy as np
import psutil

import check_backend as CB   # build, start_spring, pct; nạp check_service (start_server, tree), common_05, eval_05

CS, C, E = CB.CS, CB.C, CB.E
FRONTEND = C.ROOT / "frontend"
E2E_DIR = C.ROOT / "tools" / "demo_e2e"
VITE_JS = FRONTEND / "node_modules" / "vite" / "bin" / "vite.js"
LAT_SEED = 20261014          # cùng seed chọn người với 08b_latency.py / check_service.py
BUSY_GB = 6.0                # RAM trống dưới mức này: ghi "đo khi máy bận" (CLAUDE.md, môi trường)
HUGE_USER = "99999999999999999999"
SPRING_JVM = ("-Xmx512m",)                       # như run_demo.ps1
SPRING_EXTRA = ("--server.address=127.0.0.1",)   # như run_demo.ps1


def free_gb():
    return round(psutil.virtual_memory().available / 2**30, 2)


def kill(p):
    for x in reversed(CS.tree(p)):
        try:
            x.kill()
        except psutil.NoSuchProcess:
            pass
    p.wait(30)


def start_vite(port, api_base, log_file, log, source="api"):
    node = shutil.which("node")
    assert node and VITE_JS.exists(), "không thấy node hoặc frontend/node_modules (chạy npm ci trong frontend/)"
    env = dict(os.environ, VITE_RECOMMENDATION_SOURCE=source, VITE_API_URL=api_base)
    cmd = [node, str(VITE_JS), "--host", "127.0.0.1", "--port", str(port), "--strictPort"]
    v = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    log(f"bật Vite: node {v} | VITE_RECOMMENDATION_SOURCE={source} VITE_API_URL={api_base} | {' '.join(cmd[1:])}")
    f = open(log_file, "x", encoding="utf-8")
    p = subprocess.Popen(cmd, cwd=FRONTEND, env=env, stdout=f, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    t = time.perf_counter()
    while time.perf_counter() - t < 60:
        if p.poll() is not None:
            sys.exit(f"DỪNG: Vite thoát (mã {p.returncode}), xem {log_file}")
        try:
            if httpx.get(base, timeout=2).status_code == 200:
                log(f"Vite sẵn sàng sau {time.perf_counter() - t:.1f}s: {base}")
                return p, f, base
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    kill(p)
    sys.exit("DỪNG: Vite không lên sau 60 s")


def run_browser(phase, web, api, run_dir, tag, log):
    node = shutil.which("node")
    cmd = [node, str(E2E_DIR / "demo_e2e.mjs"), "--phase", phase, "--web", web, "--api", api, "--out", str(run_dir)]
    log(f"trình duyệt, phase {phase}: node {' '.join(cmd[1:])}")
    r = subprocess.run(cmd, cwd=C.ROOT, capture_output=True, text=True, encoding="utf-8", timeout=300)
    with open(run_dir / f"browser_{phase}_{tag}.log", "x", encoding="utf-8") as f:
        f.write(r.stdout + r.stderr)
    for line in r.stdout.splitlines():
        log("  | " + line)
    if r.returncode != 0:
        log(r.stderr[-3000:])
        return None
    return json.loads((run_dir / f"e2e_{phase}.json").read_text(encoding="utf-8"))


def latency(cl, path, users, warmup, log, name):
    """Gửi lần lượt; trả số liệu phía khách (ms) của các yêu cầu sau warmup."""
    ram_before = free_gb()
    xs, server = [], []
    for i, u in enumerate(users):
        t = time.perf_counter()
        r = cl.get(path, params={"user_id": u, "k": 10})
        dt = (time.perf_counter() - t) * 1000
        assert r.status_code == 200 and len(r.json()["items"]) == 10, (name, u, r.status_code)
        if i >= warmup:
            xs.append(dt)
            if "X-Process-Time-Ms" in r.headers:
                server.append(float(r.headers["X-Process-Time-Ms"]))
    ram_after = free_gb()
    v = np.array(xs)
    out = {f"p{q}": round(float(np.percentile(v, q)), 2) for q in (50, 95, 99)}
    out.update(max=round(float(v.max()), 2), mean=round(float(v.mean()), 2), n=len(xs), warmup=warmup,
               ram_free_gb_before=ram_before, ram_free_gb_after=ram_after,
               busy=min(ram_before, ram_after) < BUSY_GB)
    if server:
        out["fastapi_server_p50_ms"] = round(statistics.median(server), 2)
    log(f"  {name}: p50 {out['p50']} ms, p95 {out['p95']} ms, p99 {out['p99']} ms, max {out['max']} ms, TB {out['mean']} ms "
        f"({out['n']} yêu cầu sau {warmup} khởi động) | RAM trống trước {ram_before} GB, sau {ram_after} GB"
        + (" -> ĐO KHI MÁY BẬN (RAM trống < 6 GB)" if out["busy"] else ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb-dir", default="results/service/emb_s1_20261021")
    ap.add_argument("--label", required=True)
    ap.add_argument("--fastapi-port", type=int, default=8061)
    ap.add_argument("--spring-port", type=int, default=8098)
    # 5173: cổng Vite mặc định, đúng cors.allowed-origins mặc định của Spring (không đổi cấu hình CORS khi kiểm)
    ap.add_argument("--vite-port", type=int, default=5173)
    ap.add_argument("--vite-mock-port", type=int, default=5174)
    ap.add_argument("--n-latency", type=int, default=1000)
    ap.add_argument("--warmup", type=int, default=50)
    a = ap.parse_args()
    run_dir = C.RESULTS_DIR / "demo" / f"check_demo_{a.label}"
    run_dir.mkdir(parents=True, exist_ok=False)
    tag = E.now_tag()
    log = E.Log(run_dir / f"check_demo_{tag}.log")
    meta = json.loads((C.ROOT / a.emb_dir / "meta.json").read_text(encoding="utf-8"))
    log(f"check_demo | emb {a.emb_dir} (seed {meta['seed']}) | git {E.git_state()} | script sha256 "
        f"{E.sha256(__file__)} | demo_e2e.mjs sha256 {E.sha256(E2E_DIR / 'demo_e2e.mjs')} | RAM trống {free_gb()} GB")
    assert (E2E_DIR / "node_modules" / "playwright-core").exists(), "chạy npm install trong tools/demo_e2e/"
    CB.build(log)
    res = {"git": E.git_state(), "jar_sha256": E.sha256(CB.JAR), "http": [], "latency_ms": {}, "fastapi_down_http": []}
    fp, fbase, h = CS.start_server(a.emb_dir, a.fastapi_port, run_dir / f"serve_{tag}.log", log)
    assert h["best_pt_sha256"] == meta["best_pt_sha256"] and h["seed"] == 1
    res["health"] = h
    sp = vp = mp = None
    try:
        sp, sf, sbase = CB.start_spring(a.spring_port, fbase, run_dir / f"spring_{tag}.log", log, SPRING_JVM, SPRING_EXTRA)
        api = sbase + "/api"
        vp, vf, web = start_vite(a.vite_port, api, run_dir / f"vite_{tag}.log", log)

        log("bước 2: HTTP qua Spring")
        with httpx.Client(timeout=10) as cl:
            for u in (409, 47, 99999, HUGE_USER):
                r = cl.get(api + "/recommend", params={"user_id": u, "k": 10, "exclude": "all_history"})
                j = r.json()
                row = {"user_id": u, "status": r.status_code}
                if r.status_code == 200:
                    row.update(n_items=len(j["items"]), n_bodies=j["n_bodies"],
                               n_lenses_blocked=j["mask"]["n_lenses_blocked"],
                               n_explanations=sum(it["explanation"] is not None for it in j["items"]))
                else:
                    row["error"] = j["error"]
                res["http"].append(row)
                log(f"  người {u}: {json.dumps(row, ensure_ascii=False)}")

        log("bước 3: trình duyệt, FastAPI + Spring đang chạy")
        res["e2e_up"] = run_browser("up", web, api, run_dir, tag, log)

        log(f"bước 4: độ trễ đầu cuối qua Spring ({a.n_latency} yêu cầu, sau {a.warmup} khởi động)")
        users = np.random.default_rng(LAT_SEED).choice(C.N_USERS, a.warmup + a.n_latency, replace=False).tolist()
        res["latency_users"] = {"seed": LAT_SEED, "n": len(users), "first5": users[:5]}
        with httpx.Client(timeout=10) as cl:
            res["latency_ms"]["spring"] = latency(cl, api + "/recommend", users, a.warmup, log,
                                                  "qua Spring (khách -> Spring -> FastAPI)")
            res["latency_ms"]["fastapi_direct"] = latency(cl, fbase + "/recommend", users, a.warmup, log,
                                                          "gọi thẳng FastAPI (tham khảo)")

        log("bước 5: tắt FastAPI")
        kill(fp)
        fp = None
        with httpx.Client(timeout=10) as cl:
            r = cl.get(api + "/recommend", params={"user_id": 409, "k": 10, "exclude": "all_history"})
            res["fastapi_down_http"] = {"status": r.status_code, "body": r.json()}
            log(f"  HTTP qua Spring: {r.status_code} {json.dumps(r.json(), ensure_ascii=False)}")
        res["e2e_down"] = run_browser("down", web, api, run_dir, tag, log)

        log("bước 6: Vite chế độ dữ liệu mẫu")
        mp, mf, mweb = start_vite(a.vite_mock_port, api, run_dir / f"vite_mock_{tag}.log", log, source="mock")
        res["e2e_mock"] = run_browser("mock", mweb, api, run_dir, tag, log)
    finally:
        for p in (fp, sp, vp, mp):
            if p is not None:
                kill(p)
        log(f"đã tắt mọi tiến trình đã bật; RAM trống {free_gb()} GB")

    up, down, mock = res["e2e_up"] or {}, res["e2e_down"] or {}, res["e2e_mock"] or {}
    upc, downc, mockc = up.get("checks", {}), down.get("checks", {}), mock.get("checks", {})
    http = {str(r["user_id"]): r for r in res["http"]}
    checks = {
        "http_409_47_ok": http["409"]["status"] == 200 and http["47"]["status"] == 200,
        "http_unknown_404": http["99999"]["status"] == 404 and http["99999"]["error"]["code"] == "USER_NOT_FOUND",
        # phản biện S2: số vượt kiểu long qua Spring phải trùng FastAPI (404), không phải 422
        "http_huge_user_404": http[HUGE_USER]["status"] == 404 and http[HUGE_USER]["error"]["code"] == "USER_NOT_FOUND",
        "browser_users_same_as_api": bool(up.get("users")) and all(upc.get(f"user_{r['user_id']}", False) for r in up["users"])
                                     and len(up["users"]) == 5,
        "browser_unknown_message": upc.get("unknown_user_message", False),
        "browser_bad_input_rejected": upc.get("bad_input_rejected", False),
        "browser_verified_false_hidden": upc.get("verified_false_hidden", False),
        "http_down_503": res["fastapi_down_http"].get("status") == 503,
        "browser_down_message": downc.get("fastapi_down_message", False),
        "browser_mock_label_and_list": mockc.get("mock_label_and_list", False),
        "browser_only_calls_spring": all(c.get("only_spring", False) for c in (upc, downc, mockc)),
        "browser_no_console_error": all(c.get("no_console_error_except_http", False) for c in (upc, downc, mockc)),
    }
    res["checks"] = checks
    (run_dir / "summary.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"KẾT QUẢ: {checks} -> {'ĐẠT' if all(checks.values()) else 'KHÔNG ĐẠT'}; summary {run_dir / 'summary.json'}")
    log.close()
    sys.exit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
