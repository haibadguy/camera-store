"""
train_05.py — Vòng huấn luyện BPR dùng chung cho LightGCN (05b) và R-GCN (05c), theo docs/reviews/n5_eval_plan.md
mục 7 (QĐ 5-5). Viết 09/10/2026, sửa lỗi L5, L11, L12 (một phần), L14 của kế hoạch mục 2.

  - Mỗi epoch: mỗi cặp train (u, i) lấy 1 âm mẫu j đều trong các sản phẩm u CHƯA có trong train (numpy, không vòng
    Python); xáo cặp bằng MỘT bộ sinh số cho cả lần chạy (L11: bản cũ tạo lại rng mỗi epoch).
  - Chấm NDCG@20 full ranking trên val mỗi `eval_every` epoch; giữ checkpoint tốt nhất; dừng khi `patience` lần chấm
    liên tiếp không tăng; chạy hết `max_epoch` mà chưa dừng thì ghi "chưa chắc hội tụ".
  - Chạy tiếp được: ở mỗi lần chấm lưu last.pt (mô hình, Adam, trạng thái mọi bộ sinh số, lịch sử). Chạy lại đúng
    lệnh cũ thì tiếp từ lần chấm gần nhất. Mỗi lần gọi ghi log tên mới (train_<thời điểm>.log), không ghi đè.
  - Không bao giờ chấm test (script này chỉ nhận val).

Thêm 14/10/2026 cho CaKG-Rec / KGAT (docs/reviews/cakg_eval_plan.md mục 4, 10, 12). Mọi phần thêm là TÙY CHỌN: mô hình
không có các hàm dưới đây (LightGCN 05b, R-GCN 05c) thì vòng huấn luyện chạy y như trước, chỉ thêm cột VRAM:
  - VRAM: mỗi epoch ghi đỉnh max_memory_allocated / max_memory_reserved (MiB) của phần huấn luyện (vram_*) và, ở epoch
    có chấm, của phần chấm val (vram_eval_*) vào lịch sử (đặt lại đỉnh trước mỗi phần); result.json thêm
    peak_vram_allocated_mib, peak_vram_reserved_mib (đỉnh huấn luyện, mọi epoch, mọi lần gọi) và
    peak_vram_eval_allocated_mib, peak_vram_eval_reserved_mib (đỉnh lúc chấm val trong vòng huấn luyện);
  - model.after_epoch(np_rng, log) -> dict: chạy sau các bước BPR của epoch, trước khi chấm (KGAT: pha TransR và
    tính lại attention); thời gian tính vào giây / epoch;
  - model.epoch_stats() -> dict: các thành phần loss trung bình của epoch (CaKG-Rec: BPR, L_comp), ghi vào lịch sử;
  - model.aux_state_dict() / model.load_aux_state_dict(d): trạng thái ngoài state_dict (KGAT: Adam của pha TransR),
    lưu vào last.pt để chạy tiếp;
  - monitor(model, ev) -> dict: số theo dõi ở mỗi lần chấm (CaKG-Rec: NDCG@20 val SAU mặt nạ), KHÔNG dùng để chọn;
  - final_evals {tên: fn(model, ev) -> score_batch}: chấm đầy đủ thêm trên val với checkpoint tốt nhất (CaKG-Rec:
    điểm sau mặt nạ), lưu mảng với tiền tố "<tên>_" và kết quả ở result.json[tên];
  - code_files: các file code ghi sha256 vào config.json (cùng train_05.py).
"""

import json
import os
import time
from pathlib import Path

import numpy as np
import torch

import common_05 as C
import eval_05 as E


class NegSampler:
    """Âm mẫu đều trong [0, n_items) trừ sản phẩm user có trong train. Khóa u * n_items + i đã sắp xếp."""
    def __init__(self, pair_u, pair_i, n_items):
        self.n_items = n_items
        self.keys = np.unique(pair_u.astype(np.int64) * n_items + pair_i)

    def sample(self, users, rng):
        neg = rng.integers(0, self.n_items, size=len(users))
        bad = np.arange(len(users))
        while len(bad):
            k = users[bad] * self.n_items + neg[bad]
            pos = np.searchsorted(self.keys, k)
            hit = (pos < len(self.keys)) & (self.keys[np.minimum(pos, len(self.keys) - 1)] == k)
            bad = bad[hit]
            neg[bad] = rng.integers(0, self.n_items, size=len(bad))
        return neg


def train_pairs(train):
    u = np.array([uid for uid, its in train.items() for _ in its], dtype=np.int64)
    i = np.array([iid for its in train.values() for iid in sorted(its)], dtype=np.int64)
    return u, i


def _atomic_save(obj, path):
    tmp = Path(str(path) + ".tmp")
    torch.save(obj, tmp)
    os.replace(tmp, path)


def _mib(x):
    return round(x / 2 ** 20, 1)


def run(model_name, cfg, build_model, run_dir, extra_argv=None, monitor=None, final_evals=None, code_files=()):
    """cfg: dict cấu hình (seed, lr, batch, max_epoch, eval_every, patience, ... ) — lưu ở config.json, chạy tiếp
    phải đúng cấu hình cũ. build_model(train, log) -> (model, optimizer_params); model có
      .loss(u, i, j) -> loss (tensor), .score_fn() -> hàm score_batch(uids) cho eval_05 (đã ở chế độ eval).
    Trả về dict kết quả (cũng ghi ở result.json)."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    if (run_dir / "result.json").exists():
        print(f"Đã xong từ trước, bỏ qua: {run_dir / 'result.json'}", flush=True)
        return json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    log = E.Log(run_dir / f"train_{E.now_tag()}.log")
    stop_after = cfg.pop("_stop_after", None)       # chỉ để kiểm thử "bị ngắt giữa chừng"
    cfg_path = run_dir / "config.json"
    if cfg_path.exists():
        old = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert old["cfg"] == cfg, f"cấu hình khác lần chạy trước, không chạy tiếp:\n cũ {old['cfg']}\n mới {cfg}"
        log(f"Chạy tiếp {run_dir} (cấu hình giống lần trước)")
    else:
        cfg_path.write_text(json.dumps({"model": model_name, "cfg": cfg, "git": E.git_state(),
                                        "inputs_sha256": E.inputs_sha256(),
                                        "code_sha256": {Path(p).name: E.sha256(p)
                                                        for p in [__file__, *code_files]},
                                        "device": str(E.DEVICE),
                                        "torch": torch.__version__, "argv": extra_argv}, indent=2,
                                       ensure_ascii=False), encoding="utf-8")
    log(f"{model_name} | {cfg} | git {E.git_state()} | thiết bị {E.DEVICE}"
        + (f" ({torch.cuda.get_device_name(0)})" if E.DEVICE.type == "cuda" else ""))

    seed = cfg["seed"]
    torch.manual_seed(seed)
    np_rng = np.random.default_rng(seed)
    t_load = time.time()
    train = C.load_train()
    ev = E.EvalContext("val", train)
    pu, pi_ = train_pairs(train)
    sampler = NegSampler(pu, pi_, C.N_ITEMS)
    log(f"Nạp dữ liệu {time.time() - t_load:.1f}s | cặp train {len(pu):,} | người dùng val {len(ev.split.users):,}")
    model, params = build_model(train, log)
    opt = torch.optim.Adam(params, lr=cfg["lr"])
    pu_t = torch.as_tensor(pu, device=E.DEVICE)
    pi_t = torch.as_tensor(pi_, device=E.DEVICE)

    st = {"epoch": 0, "best": -1.0, "best_epoch": 0, "bad": 0, "stopped": False, "history": []}
    last = run_dir / "last.pt"
    if last.exists():
        ck = torch.load(last, map_location="cpu", weights_only=False)   # trạng thái RNG phải ở CPU
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        if hasattr(model, "load_aux_state_dict"):
            model.load_aux_state_dict(ck["aux"])
        np_rng.bit_generator.state = ck["np_rng"]
        torch.set_rng_state(ck["torch_rng"])
        if E.DEVICE.type == "cuda":
            torch.cuda.set_rng_state_all(ck["cuda_rng"])
        st = ck["state"]
        log(f"Nạp last.pt: đã xong epoch {st['epoch']}, tốt nhất NDCG@20 val = {st['best']:.5f} ở epoch "
            f"{st['best_epoch']}, {st['bad']} lần chấm không tăng")

    def val_ndcg20():
        model.eval()
        fr = E.full_rank(model.score_fn(), ev.split, ev.pi)
        extra = monitor(model, ev) if monitor is not None else {}
        model.train()
        return float(np.where(fr["rank"] <= 20, 1.0 / np.log2(fr["rank"] + 1.0), 0.0).mean()), extra

    B = cfg["batch"]
    n = len(pu)
    epochs_this_call = 0
    model.train()
    while not st["stopped"] and st["epoch"] < cfg["max_epoch"]:
        ep = st["epoch"] + 1
        t0 = time.time()
        if E.DEVICE.type == "cuda":
            torch.cuda.reset_peak_memory_stats()
        neg = torch.as_tensor(sampler.sample(pu, np_rng), device=E.DEVICE)
        perm = torch.as_tensor(np_rng.permutation(n), device=E.DEVICE)
        t_s = time.time() - t0
        tot, nb = 0.0, 0
        for s in range(0, n, B):
            idx = perm[s:s + B]
            opt.zero_grad(set_to_none=True)
            loss = model.loss(pu_t[idx], pi_t[idx], neg[idx])
            loss.backward()
            opt.step()
            tot += float(loss)
            nb += 1
        parts = model.epoch_stats() if hasattr(model, "epoch_stats") else {}
        if hasattr(model, "after_epoch"):
            parts.update(model.after_epoch(np_rng, log))
        if E.DEVICE.type == "cuda":
            torch.cuda.synchronize()
        t_ep = time.time() - t0
        rec = {"epoch": ep, "loss": tot / nb, "sec": round(t_ep, 2), "sec_sampling": round(t_s, 2), **parts}
        if E.DEVICE.type == "cuda":
            rec["vram_alloc_mib"] = _mib(torch.cuda.max_memory_allocated())
            rec["vram_reserved_mib"] = _mib(torch.cuda.max_memory_reserved())
        st["epoch"] = ep
        epochs_this_call += 1
        msg = f"  epoch {ep:>3}/{cfg['max_epoch']} | loss {tot / nb:.5f} | {t_ep:.1f}s (âm mẫu + xáo {t_s:.2f}s)"
        if parts:
            msg += " | " + " ".join(f"{k} {v:.5f}" if isinstance(v, float) else f"{k} {v}" for k, v in parts.items())
        if ep % cfg["eval_every"] == 0 or ep == cfg["max_epoch"]:
            t1 = time.time()
            if E.DEVICE.type == "cuda":
                torch.cuda.reset_peak_memory_stats()
            nd, extra = val_ndcg20()
            if E.DEVICE.type == "cuda":
                rec["vram_eval_alloc_mib"] = _mib(torch.cuda.max_memory_allocated())
                rec["vram_eval_reserved_mib"] = _mib(torch.cuda.max_memory_reserved())
            rec["val_ndcg@20"] = nd
            rec.update(extra)
            rec["sec_eval"] = round(time.time() - t1, 2)
            msg += f" | val NDCG@20 {nd:.5f} ({rec['sec_eval']:.1f}s)"
            if extra:
                msg += " | theo dõi (không dùng để chọn): " + " ".join(f"{k} {v:.5f}" for k, v in extra.items())
            if nd > st["best"]:
                st.update(best=nd, best_epoch=ep, bad=0)
                _atomic_save({"model": model.state_dict(), "epoch": ep, "val_ndcg@20": nd}, run_dir / "best.pt")
                msg += " *tốt nhất*"
            else:
                st["bad"] += 1
                msg += f" (không tăng {st['bad']}/{cfg['patience']})"
                if st["bad"] >= cfg["patience"]:
                    st["stopped"] = True
            st["history"].append(rec)
            _atomic_save({"model": model.state_dict(), "opt": opt.state_dict(), "np_rng": np_rng.bit_generator.state,
                          "torch_rng": torch.get_rng_state(),
                          "cuda_rng": torch.cuda.get_rng_state_all() if E.DEVICE.type == "cuda" else None,
                          "aux": model.aux_state_dict() if hasattr(model, "aux_state_dict") else None,
                          "state": st}, last)
        else:
            st["history"].append(rec)
        log(msg)
        if stop_after is not None and epochs_this_call >= stop_after and not st["stopped"]:
            log(f"Dừng giả lập sau {stop_after} epoch (kiểm thử chạy tiếp); trạng thái lưu tới lần chấm gần nhất.")
            log.close()
            return None

    if st["best_epoch"] == 0:
        raise RuntimeError("chưa có lần chấm val nào")
    converged = st["stopped"]
    log(f"Kết thúc: {'dừng sớm' if converged else 'CHẠM GIỚI HẠN EPOCH -> chưa chắc hội tụ'} ở epoch {st['epoch']}; "
        f"tốt nhất epoch {st['best_epoch']}, NDCG@20 val {st['best']:.5f}")
    model.load_state_dict(torch.load(run_dir / "best.pt", map_location=E.DEVICE, weights_only=False)["model"])
    model.eval()
    log("Chấm đầy đủ trên val với checkpoint tốt nhất:")
    res = E.evaluate(model.score_fn(), ev, log=log, save_dir=run_dir, prefix="val_")
    epoch_secs = [h["sec"] for h in st["history"]]
    out = {"model": model_name, "cfg": cfg, "split": "val", "best_epoch": st["best_epoch"],
           "best_val_ndcg@20_during_training": st["best"], "epochs_run": st["epoch"],
           "stopped_early": converged, "chua_chac_hoi_tu": not converged,
           "median_sec_per_epoch": float(np.median(epoch_secs)), "history": st["history"],
           "git_at_finish": E.git_state(), "val": res}
    for key, src in (("peak_vram_allocated_mib", "vram_alloc_mib"), ("peak_vram_reserved_mib", "vram_reserved_mib"),
                     ("peak_vram_eval_allocated_mib", "vram_eval_alloc_mib"),
                     ("peak_vram_eval_reserved_mib", "vram_eval_reserved_mib")):
        vals = [h[src] for h in st["history"] if src in h]
        if vals:
            out[key] = max(vals)
    log(f"NDCG@20 val chấm lại từ best.pt: {res['full']['ndcg@20']:.5f} (lúc huấn luyện {st['best']:.5f})")
    for name, fn in (final_evals or {}).items():
        log(f"Chấm đầy đủ trên val, {name}:")
        out[name] = E.evaluate(fn(model, ev), ev, log=log, save_dir=run_dir, prefix=f"{name}_")
    (run_dir / "result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {run_dir / 'result.json'}")
    log.close()
    return out
