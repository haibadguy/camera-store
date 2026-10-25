"""
export_mock.py -- Lưu phản hồi THẬT của dịch vụ mô hình làm dữ liệu giả cho frontend (frontend/src/mock/). Viết 26/10/2026.

Tự bật run_service.py (như check_service.py, log tên mới), gọi qua HTTP với exclude=all_history (mặc định của demo):
  - /recommend?user_id=<u>&k=10&exclude=all_history  -> recommend_<u>.json
  - /users/<u>/bodies?exclude=all_history            -> users_<u>_bodies.json
  - /items/<id>                                       -> items/<id>.json, cho MỌI item_id xuất hiện trong các phản hồi trên:
    items[], path (b*, l), candidate_bodies, mask.blocked_in_topk_before_mask (ống bị mặt nạ chặn), bodies[].
Không rút gọn: ghi đúng JSON dịch vụ trả về (chỉ thêm thụt lề cho dễ đọc; kiểm đọc lại file = phản hồi). Không ghi đè:
dừng nếu thư mục đích đã có file trùng tên. Mỗi file ghi sha256 của nội dung gốc (byte HTTP) và của file vào manifest.

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/service/export_mock.py --emb-dir results/service/emb_s1_20261021 --users 409 47 --label <nhãn>
Kết quả: frontend/src/mock/ (dữ liệu giả), results/service/mock_fe_<nhãn>/ (log, log dịch vụ, manifest.json).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_service as CS   # noqa: E402  (start_server, tree; nạp common_05 / eval_05)

C, E = CS.C, CS.E
MODE = "all_history"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def item_ids(j):
    """Mọi item_id trong một phản hồi /recommend hoặc /users/{id}/bodies."""
    ids = set()
    for it in j.get("items", []):
        ids.add(it["item_id"])
        ex = it["explanation"]
        if ex is not None:
            ids.update(p["item_id"] for p in ex["path"] if p["kind"] == "item")
            ids.update(ex["candidate_bodies"])
    if "mask" in j:
        ids.update(x["item_id"] for x in j["mask"]["blocked_in_topk_before_mask"])
    ids.update(b["item_id"] for b in j.get("bodies", []))
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb-dir", default="results/service/emb_s1_20261021")
    ap.add_argument("--users", type=int, nargs="+", default=[409, 47])
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", default="frontend/src/mock")
    ap.add_argument("--port", type=int, default=8031)
    a = ap.parse_args()
    meta = json.loads((C.ROOT / a.emb_dir / "meta.json").read_text(encoding="utf-8"))
    run_dir = C.RESULTS_DIR / "service" / f"mock_fe_{a.label}"
    run_dir.mkdir(parents=True, exist_ok=False)
    out = C.ROOT / a.out
    tag = E.now_tag()
    log = E.Log(run_dir / f"export_mock_{tag}.log")
    log(f"export_mock | emb {a.emb_dir} (seed {meta['seed']}, best.pt {meta['best_pt_sha256']}) | git {E.git_state()} | "
        f"script sha256 {E.sha256(__file__)} | core.py sha256 {E.sha256(HERE / 'core.py')} | app.py sha256 "
        f"{E.sha256(HERE / 'app.py')} | người {a.users}, k = {a.k}, exclude = {MODE} -> {out.relative_to(C.ROOT)}")
    p, base, h = CS.start_server(a.emb_dir, a.port, run_dir / f"serve_{tag}.log", log)
    assert h["best_pt_sha256"] == meta["best_pt_sha256"] and h["embeddings_sha256"] == meta["embeddings_sha256"]
    files = []

    def save(cl, path, params, name):
        r = cl.get(path, params=params)
        assert r.status_code == 200, (path, params, r.status_code, r.text)
        j = r.json()
        fn = out / name
        fn.parent.mkdir(parents=True, exist_ok=True)
        with open(fn, "x", encoding="utf-8", newline="\n") as f:          # "x": không ghi đè
            f.write(json.dumps(j, ensure_ascii=False, indent=2) + "\n")
        assert json.loads(fn.read_text(encoding="utf-8")) == j
        files.append({"file": name, "url": str(r.url).removeprefix(base), "raw_sha256": hashlib.sha256(r.content).hexdigest(),
                      "file_sha256": E.sha256(fn), "process_ms": float(r.headers["X-Process-Time-Ms"])})
        log(f"  {files[-1]['url']} -> {name}")
        return j

    try:
        with httpx.Client(base_url=base, timeout=30) as cl:
            ids = set()
            for u in a.users:
                rec = save(cl, "/recommend", {"user_id": u, "k": a.k, "exclude": MODE}, f"recommend_{u}.json")
                bod = save(cl, f"/users/{u}/bodies", {"exclude": MODE}, f"users_{u}_bodies.json")
                ids |= item_ids(rec) | item_ids(bod)
                ex = [it for it in rec["items"] if it["explanation"] is not None]
                log(f"  người {u}: {rec['n_bodies']} thân, top-{a.k} {[it['item_id'] for it in rec['items']]}, "
                    f"{len(ex)} câu giải thích (verified: {[it['explanation']['verified'] for it in ex]}), "
                    f"bị mặt nạ gỡ khỏi top-{a.k}: {[x['item_id'] for x in rec['mask']['blocked_in_topk_before_mask']]}")
            log(f"  {len(ids)} sản phẩm khác nhau xuất hiện -> items/<id>.json")
            for i in sorted(ids):
                save(cl, f"/items/{i}", None, f"items/{i}.json")
    finally:
        for x in reversed(CS.tree(p)):
            x.kill()
        p.wait(30)
    man = {"health": h, "emb_meta": meta, "users": a.users, "k": a.k, "exclude": MODE, "item_ids": sorted(ids),
           "files": files}
    (run_dir / "manifest.json").write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"{len(files)} file -> {out.relative_to(C.ROOT)}; manifest {run_dir / 'manifest.json'}")
    log.close()


if __name__ == "__main__":
    main()
