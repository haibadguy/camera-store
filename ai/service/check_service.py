"""
check_service.py -- Kiểm dịch vụ mô hình (nội dung 10). Viết 21/10/2026.

Giai đoạn "http" (mặc định): tự bật run_service.py (tiến trình con, log tên mới), rồi qua HTTP:
  1. Khớp với kết quả đã lưu: ở chế độ giống lúc chấm test (exclude=train_val: bỏ sản phẩm train + item val; mặt nạ
     QĐ 4-9), /recommend k = 10 phải trả ĐÚNG top-10 (cùng thứ tự) của mảng đã lưu
     results/cakg/test_final_20261015/lightgcn_s<seed>/test_mat_na_qd49_top20_full.npy (sha256 kiểm với result.json qua
     09_explain_lightgcn.load_saved) và ĐÚNG câu / b* / ρ / c* của results/final_system/explain_test_20261016/
     lightgcn_s<seed>/explanations.jsonl (sha256 kiểm với summary.json); ống không có câu đã lưu thì API phải trả null.
       nhóm A: 20 người lấy ngẫu nhiên trong 67.661 người (seed --parity-seed);
       nhóm B: 20 người lấy ngẫu nhiên trong những người CÓ câu giải thích đã lưu (cùng rng, không trùng A), để phép so
       câu không rỗng (đa số người không có thân nên không có câu).
  2. Hợp đồng: các mã lỗi / định dạng lỗi chung, /items, /users/{id}/bodies, /compat trả đúng trường.
  3. Độ trễ qua HTTP: 1.000 yêu cầu /recommend?user_id=u&k=10 (chế độ mặc định exclude=all_history: bỏ train + val + test), người chọn như
     08b_latency.py (seed 20261014), 50 yêu cầu khởi động không tính, gửi lần lượt (một kết nối keep-alive);
     p50 / p95 / p99 / max của thời gian phía khách (gồm HTTP + JSON) và phía máy chủ (header X-Process-Time-Ms).
Giai đoạn "all": không qua HTTP, gọi RecommenderCore trực tiếp cho MỌI người của tập test (exclude=train_val) và so như
  bước 1 (số phụ, để biết có lệch nào do chấm trên CPU so với lúc chấm test trên GPU không).
Giai đoạn "history" (thêm 21/10, phiên sau): không qua HTTP, MỌI người, chế độ mặc định all_history (thân cho mặt nạ và
  giải thích lấy từ train + val + test). Phải = 0: lỗi sự kiện (verify_explanation, "đã mua b*" kiểm bằng lịch sử), b*
  không phải thân trong lịch sử (kiểm độc lập), ống trong top-10 vi phạm QĐ 4-9 với thân cả lịch sử (common_05.judge_lens),
  sản phẩm trả về nằm trong lịch sử. Đếm so với khi chỉ dùng thân train (cùng chế độ all_history, recommend(view="train")):
  số người đổi mặt nạ (tăng / giảm số ống bị chặn), đổi top-10, thêm / bớt câu giải thích.

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/service/check_service.py --emb-dir results/service/emb_s1_20261021 --label <nhãn>
  ai\\.venv\\Scripts\\python.exe ai/service/check_service.py --emb-dir ... --label <nhãn> --stage all
Kết quả: results/service/check_<stage>_<nhãn>/ (thư mục mới): log, summary.json.
"""

import argparse
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
import numpy as np
import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pipeline"))
sys.path.insert(0, str(HERE))
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

X09 = importlib.import_module("09_explain_lightgcn")
LAT = importlib.import_module("08b_latency")
EXPL_SAVED = C.ROOT / "results" / "final_system" / "explain_test_20261016"
OUT_ROOT = C.RESULTS_DIR / "service"


# -- kết quả đã lưu ---------------------------------------------------------------

def load_reference(seed, log):
    d, sv = X09.load_saved("test", seed)                     # kiểm sha256 mảng với result.json
    summ = json.loads((EXPL_SAVED / "summary.json").read_text(encoding="utf-8"))
    fn = EXPL_SAVED / f"lightgcn_s{seed}" / "explanations.jsonl"
    sha = E.sha256(fn)
    assert sha == summ["seeds"][str(seed)]["explanations_sha256"], f"sha256 khác summary.json: {fn}"
    expl = {}
    with open(fn, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            expl[(r["u"], r["l"])] = r
    log(f"kết quả đã lưu: top-20 {d.relative_to(C.ROOT)} (sha256 khớp result.json); câu {fn.relative_to(C.ROOT)} "
        f"(sha256 khớp summary.json, {len(expl):,} câu)")
    return {"row_of": {int(u): r for r, u in enumerate(sv["users"].tolist())}, "top": sv["top20_full"],
            "expl": expl, "users_with_expl": sorted({u for (u, _) in expl})}


def compare_user(u, resp, ref):
    """So một phản hồi /recommend (exclude=train_val, k=10) với kết quả đã lưu. Trả về dict đếm."""
    saved_top = ref["top"][ref["row_of"][u], :10].tolist()
    api_top = [it["item_id"] for it in resp["items"]]
    res = {"u": u, "top_match": api_top == saved_top, "n_expl_saved": 0, "n_expl_api": 0, "n_expl_match": 0,
           "n_expl_mismatch": 0, "max_abs_bscore_diff": 0.0, "n_unverified": 0, "scores_sorted": True}
    sc = [it["score"] for it in resp["items"]]
    res["scores_sorted"] = all(a >= b for a, b in zip(sc, sc[1:]))
    if not res["top_match"]:
        res["api_top"], res["saved_top"] = api_top, saved_top
    for it in resp["items"]:
        l, a = it["item_id"], it["explanation"]
        s = ref["expl"].get((u, l))
        res["n_expl_saved"] += s is not None
        res["n_expl_api"] += a is not None
        if s is None and a is None:
            continue
        ok = (s is not None and a is not None and a["text"] == s["sentence"] and a["b_star"] == s["b_star"]
              and a["rho"] == s["rho"] and a["c_star"] == s["c_star"]
              and [p.get("item_id", p.get("id")) for p in a["path"]] == [u, s["b_star"], l] + ([s["c_star"]] if s["c_star"] else []))
        if ok:
            res["n_expl_match"] += 1
            res["max_abs_bscore_diff"] = max(res["max_abs_bscore_diff"],
                                             abs(a["b_star_score"] - s["e_score"][str(s["b_star"])]))
            res["n_unverified"] += not a["verified"]
        else:
            res["n_expl_mismatch"] += 1
            res.setdefault("mismatch", []).append({"l": l, "api": a and a["text"], "saved": s and s["sentence"]})
    return res


def total(rows):
    keys = ("n_expl_saved", "n_expl_api", "n_expl_match", "n_expl_mismatch", "n_unverified")
    out = {"n_users": len(rows), "n_top_match": sum(r["top_match"] for r in rows),
           "n_scores_sorted": sum(r["scores_sorted"] for r in rows)}
    out.update({k: sum(r[k] for r in rows) for k in keys})
    out["max_abs_bscore_diff"] = max((r["max_abs_bscore_diff"] for r in rows), default=0.0)
    return out


def log_group(name, rows, log):
    t = total(rows)
    log(f"  nhóm {name}: top-10 khớp {t['n_top_match']}/{t['n_users']} người | câu đã lưu {t['n_expl_saved']}, API "
        f"{t['n_expl_api']}, khớp {t['n_expl_match']}, lệch {t['n_expl_mismatch']} | câu không qua kiểm sự kiện "
        f"{t['n_unverified']} | |Δ e_b*ᵀe_l| lớn nhất {t['max_abs_bscore_diff']:.2e} | điểm giảm dần "
        f"{t['n_scores_sorted']}/{t['n_users']}")
    for r in rows:
        if not r["top_match"] or r["n_expl_mismatch"]:
            log(f"    LỆCH u {r['u']}: {json.dumps({k: r[k] for k in r if k in ('api_top', 'saved_top', 'mismatch')}, ensure_ascii=False)}")
    return t


def history_stage(emb_dir, log):
    from core import RecommenderCore
    core = RecommenderCore(emb_dir, device="cpu", log=log)
    vh, vt = core.views["history"], core.views["train"]
    it, ctx = core.item_type, core.ctx
    keys = ["n_fact_errors", "n_bstar_not_owned", "n_viol_qd49_hist", "n_items_in_history", "n_lens_top10",
            "n_expl_hist", "n_expl_train", "n_expl_bstar_val_test", "users_mask_more", "users_mask_less",
            "users_mask_new", "users_has_bodies_new", "users_top10_changed", "users_more_expl", "users_less_expl",
            "users_expl_new"]
    c = dict.fromkeys(keys, 0)
    examples = []
    t = time.time()
    for u in range(C.N_USERS):
        r = core.recommend(u, 10, "all_history")
        r0 = core.recommend(u, 10, "all_history", view="train")
        hb = vh.bodies.get(u, set())
        nh, nt = int(vh.cmask[u].sum()), int(vt.cmask[u].sum())
        c["users_mask_more"] += nh > nt
        c["users_mask_less"] += nh < nt
        c["users_mask_new"] += nt == 0 and nh > 0
        c["users_has_bodies_new"] += u not in vt.bodies and u in vh.bodies
        top, top0 = [x["item_id"] for x in r["items"]], [x["item_id"] for x in r0["items"]]
        c["users_top10_changed"] += top != top0
        c["n_items_in_history"] += sum(i in core.history[u] for i in top)
        eh = [x["explanation"] for x in r["items"] if x["explanation"] is not None]
        et = [x for x in r0["items"] if x["explanation"] is not None]
        c["n_expl_hist"] += len(eh)
        c["n_expl_train"] += len(et)
        c["users_more_expl"] += len(eh) > len(et)
        c["users_less_expl"] += len(eh) < len(et)
        c["users_expl_new"] += len(et) == 0 and len(eh) > 0
        for x in r["items"]:
            if it[x["item_id"]] == 1:
                c["n_lens_top10"] += 1
                c["n_viol_qd49_hist"] += C.judge_lens(x["item_id"], hb, ctx) is True
        for e in eh:
            c["n_fact_errors"] += len(e["errors"])
            b = e["b_star"]
            c["n_bstar_not_owned"] += not (b in core.history[u] and it[b] == 0 and b in hb)
            if e["b_star_source"] != "train":
                c["n_expl_bstar_val_test"] += 1
                if len(examples) < 3:
                    examples.append({"u": u, "l": e["path"][2]["item_id"], "b_star": b, "source": e["b_star_source"],
                                     "text": e["text"]})
        if (u + 1) % 10000 == 0:
            log(f"  {u + 1:,} người ({time.time() - t:.0f}s)")
    log(f"  người có thân: train {len(vt.bodies):,}, cả lịch sử {len(vh.bodies):,} (thêm {c['users_has_bodies_new']:,})")
    log(f"  PHẢI = 0: lỗi sự kiện {c['n_fact_errors']} | b* không phải thân trong lịch sử {c['n_bstar_not_owned']} | ống "
        f"vi phạm QĐ 4-9 với thân cả lịch sử trong top-10 {c['n_viol_qd49_hist']} (trên {c['n_lens_top10']:,} ống) | "
        f"sản phẩm trả về nằm trong lịch sử {c['n_items_in_history']}")
    log(f"  mặt nạ so với chỉ thân train: tăng số ống bị chặn {c['users_mask_more']:,} người (trong đó trước 0 ống, nay > 0: "
        f"{c['users_mask_new']:,}), giảm {c['users_mask_less']:,} người")
    log(f"  top-10 đổi: {c['users_top10_changed']:,} người | câu giải thích: {c['n_expl_hist']:,} (chỉ thân train: "
        f"{c['n_expl_train']:,}); b* ở val / test: {c['n_expl_bstar_val_test']:,} câu | thêm câu {c['users_more_expl']:,} "
        f"người (trong đó trước 0 câu, nay > 0: {c['users_expl_new']:,}), bớt câu {c['users_less_expl']:,} người")
    for e in examples:
        log(f"  ví dụ: {e}")
    return {**c, "n_users": C.N_USERS, "n_users_with_bodies_train": len(vt.bodies),
            "n_users_with_bodies_history": len(vh.bodies), "examples": examples}


# -- máy chủ ------------------------------------------------------------------------

def start_server(emb_dir, port, log_file, log):
    cmd = [sys.executable, str(HERE / "run_service.py"), "--emb-dir", emb_dir, "--port", str(port),
           "--log-file", str(log_file)]
    p = subprocess.Popen(cmd, cwd=C.ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t = time.perf_counter()
    base = f"http://127.0.0.1:{port}"
    while time.perf_counter() - t < 300:
        if p.poll() is not None:
            sys.exit(f"DỪNG: dịch vụ thoát (mã {p.returncode}), xem {log_file}")
        try:
            h = httpx.get(base + "/health", timeout=2).json()
            log(f"dịch vụ sẵn sàng sau {time.perf_counter() - t:.1f}s (tính cả khởi động Python): {h}")
            return p, base, h
        except httpx.HTTPError:
            time.sleep(0.5)
    p.kill()
    sys.exit("DỪNG: dịch vụ không lên sau 300 s")


def tree(p):
    """Tiến trình dịch vụ và các tiến trình con (trên Windows, python.exe của venv khởi chạy một tiến trình con)."""
    pp = psutil.Process(p.pid)
    return [pp] + pp.children(recursive=True)


def contract_checks(cl, log):
    """Mã lỗi / định dạng lỗi chung và các trường chính của mỗi điểm cuối."""
    cases = [("/recommend?user_id=67661", 404, "USER_NOT_FOUND"), ("/recommend?user_id=-1", 404, "USER_NOT_FOUND"),
             ("/recommend?user_id=11&k=0", 422, "INVALID_PARAM"), ("/recommend?user_id=11&k=51", 422, "INVALID_PARAM"),
             ("/recommend?user_id=x", 422, "INVALID_PARAM"), ("/recommend", 422, "INVALID_PARAM"),
             ("/recommend?user_id=11&exclude=train", 422, "INVALID_PARAM"), ("/items/27940", 404, "ITEM_NOT_FOUND"),
             ("/users/67661/bodies", 404, "USER_NOT_FOUND"), ("/compat?body_id=9696&lens_id=19071", 400, "NOT_A_BODY"),
             ("/compat?body_id=19071&lens_id=19071", 400, "NOT_A_LENS"), ("/khong-co", 404, "NOT_FOUND")]
    ok = 0
    for path, st, code in cases:
        r = cl.get(path)
        j = r.json()
        good = r.status_code == st and set(j) == {"error"} and j["error"]["code"] == code and \
            set(j["error"]) == {"code", "message", "details"}
        ok += good
        if not good:
            log(f"  SAI hợp đồng: {path} -> {r.status_code} {j}")
    fields = {"/recommend?user_id=11&k=50": {"user_id", "k", "exclude", "has_bodies", "n_bodies", "items", "mask"},
              "/items/9696": {"item_id", "asin", "title", "type", "mount", "khung", "in_matrix"},
              "/users/11/bodies": {"user_id", "n_bodies", "bodies", "n_lenses_blocked"},
              "/compat?body_id=19071&lens_id=9696": {"level", "rule_id", "rule_note", "m", "qd49_if_only_this_body"}}
    for path, need in fields.items():
        r = cl.get(path)
        good = r.status_code == 200 and need <= set(r.json())
        if path.startswith("/recommend"):
            good &= len(r.json()["items"]) == 50
        ok += good
        if not good:
            log(f"  SAI hợp đồng: {path} -> {r.status_code}, thiếu {need - set(r.json())}")
    n = len(cases) + len(fields)
    log(f"hợp đồng: {ok}/{n} trường hợp đúng (mã lỗi, định dạng lỗi chung, trường chính)")
    return {"n_cases": n, "n_ok": ok}


def latency_http(cl, n, warmup, log):
    users = np.random.default_rng(LAT.SEED).choice(C.N_USERS, warmup + n, replace=False).tolist()
    train, val, test = C.load_train(), C.load_pos("val"), C.load_pos("test")
    tc, ts, n_s, n_hist = [], [], 0, 0          # n_hist: sản phẩm trả về nằm trong train / val / test (phải = 0)
    for k, u in enumerate(users):
        t = time.perf_counter()
        r = cl.get("/recommend", params={"user_id": u, "k": 10})
        j = r.json()
        dt = time.perf_counter() - t
        assert r.status_code == 200, (u, r.status_code, j)
        n_hist += sum(it["item_id"] in train[u] or it["item_id"] in (val[u], test[u]) for it in j["items"])
        if k >= warmup:
            tc.append(dt * 1000)
            ts.append(float(r.headers["X-Process-Time-Ms"]))
            n_s += sum(it["explanation"] is not None for it in j["items"])
    out = {}
    for nm, v in (("client_ms", np.array(tc)), ("server_ms", np.array(ts))):
        out[nm] = {f"p{q}": float(np.percentile(v, q)) for q in (50, 95, 99)}
        out[nm].update(max=float(v.max()), mean=float(v.mean()))
    out.update(n_requests=n, warmup=warmup, n_sentences=n_s, n_items_in_history=n_hist, user_seed=LAT.SEED, k=10, exclude="all_history")
    for nm, lab in (("client_ms", "phía khách (HTTP + JSON)"), ("server_ms", "phía máy chủ")):
        s = out[nm]
        log(f"  {lab}: p50 {s['p50']:.2f} ms, p95 {s['p95']:.2f} ms, p99 {s['p99']:.2f} ms, max {s['max']:.2f} ms, "
            f"TB {s['mean']:.2f} ms")
    log(f"  ({n:,} yêu cầu sau {warmup} khởi động, gửi lần lượt; {n_s:,} câu giải thích)")
    log(f"  sản phẩm trả về nằm trong lịch sử (train / val / test) của người đó, trên cả {warmup + n:,} yêu cầu: {n_hist} "
        f"(phải = 0)")
    return out


# -- chính ------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb-dir", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--stage", default="http", choices=["http", "all", "history"])
    ap.add_argument("--port", type=int, default=8021)
    ap.add_argument("--n-parity", type=int, default=20)
    ap.add_argument("--parity-seed", type=int, default=20261021)
    ap.add_argument("--n-latency", type=int, default=1000)
    ap.add_argument("--warmup", type=int, default=50)
    a = ap.parse_args()
    meta = json.loads((C.ROOT / a.emb_dir / "meta.json").read_text(encoding="utf-8"))
    out_dir = OUT_ROOT / f"check_{a.stage}_{a.label}"
    out_dir.mkdir(parents=True, exist_ok=False)
    tag = E.now_tag()
    log = E.Log(out_dir / f"check_{tag}.log")
    git = E.git_state()
    log(f"check_service | giai đoạn {a.stage} | emb {a.emb_dir} (seed {meta['seed']}, best.pt {meta['best_pt_sha256']}) "
        f"| git {git} | script sha256 {E.sha256(__file__)} | core.py sha256 {E.sha256(HERE / 'core.py')} | "
        f"app.py sha256 {E.sha256(HERE / 'app.py')} | máy {LAT.machine()}")
    ref = load_reference(meta["seed"], log)
    res = {"stage": a.stage, "git": git, "emb_meta": meta, "parity_seed": a.parity_seed}

    if a.stage == "history":
        res["history"] = history_stage(C.ROOT / a.emb_dir, log)
    elif a.stage == "all":
        from core import RecommenderCore
        core = RecommenderCore(C.ROOT / a.emb_dir, device="cpu", log=log)
        rows, t = [], time.time()
        for n, u in enumerate(sorted(ref["row_of"])):
            rows.append(compare_user(u, core.recommend(u, 10, "train_val"), ref))
            if (n + 1) % 10000 == 0:
                log(f"  {n + 1:,} người ({time.time() - t:.0f}s)")
        res["all"] = log_group("mọi người dùng tập test", rows, log)
        res["all"]["mismatch_users"] = [r for r in rows if not r["top_match"] or r["n_expl_mismatch"]]
    else:
        rng = np.random.default_rng(a.parity_seed)
        users_a = sorted(rng.choice(C.N_USERS, a.n_parity, replace=False).tolist())
        pool_b = [u for u in ref["users_with_expl"] if u not in set(users_a)]
        users_b = sorted(int(x) for x in rng.choice(pool_b, a.n_parity, replace=False))
        log(f"nhóm A ({a.n_parity} người ngẫu nhiên, seed {a.parity_seed}): {users_a}")
        log(f"nhóm B ({a.n_parity} người có câu đã lưu, cùng rng): {users_b}")
        p, base, h = start_server(a.emb_dir, a.port, out_dir / f"serve_{tag}.log", log)
        assert h["best_pt_sha256"] == meta["best_pt_sha256"] and h["embeddings_sha256"] == meta["embeddings_sha256"]
        res["health"] = h
        try:
            with httpx.Client(base_url=base, timeout=30) as cl:
                log("\n1. Khớp với kết quả đã lưu (exclude=train_val, k=10):")
                for name, us in (("A", users_a), ("B", users_b)):
                    rows = [compare_user(u, cl.get("/recommend", params={"user_id": u, "k": 10,
                                                                         "exclude": "train_val"}).json(), ref)
                            for u in us]
                    res[f"parity_{name}"] = {"users": us, **log_group(name, rows, log),
                                             "n_users_with_expl": sum(r["n_expl_api"] > 0 for r in rows),
                                             "per_user": rows}
                log("\n2. Hợp đồng:")
                res["contract"] = contract_checks(cl, log)
                log("\n3. Độ trễ qua HTTP (/recommend k=10, exclude=all_history):")
                res["latency_http"] = latency_http(cl, a.n_latency, a.warmup, log)
                res["latency_http"]["server_rss_mib"] = sum(x.memory_info().rss for x in tree(p)) / 2 ** 20
                log(f"  bộ nhớ dịch vụ (RSS, cả tiến trình con) sau khi đo: {res['latency_http']['server_rss_mib']:.0f} MiB")
        finally:
            for x in reversed(tree(p)):
                x.kill()
            p.wait(30)
    (out_dir / "summary.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {out_dir / 'summary.json'}")
    log.close()


if __name__ == "__main__":
    main()
