"""
06v2_select.py -- Chọn biến thể CaKG-Rec v2 trên VAL và kiểm điều kiện DỪNG 1 (docs/reviews/cakg_v2_plan.md mục 4).
Viết 16/10/2026. CHỈ đọc / chấm VAL; không đọc mảng test, không chấm test.

Đầu vào: thư mục dò của 06_val_sweep.py --group v2 (3 lần chạy seed 1: A lens_gate, B loo_hu, C body_hardneg; mỗi lần có
result.json, mảng val_* (trước mặt nạ) và val_mask_* (mặt nạ QĐ 4-9)). LightGCN seed 1–3 (checkpoint nội dung 5,
n5_final.toml, kiểm sha256) được CHẤM LẠI trên val ở đây (trước mặt nạ và mặt nạ QĐ 4-9). CaKG-Rec v1 seed 1 (mảng val đã
lưu lúc dò, kiểm sha256) chỉ để đối chiếu.

Quy tắc (đăng ký trước, kế hoạch mục 4.2):
  (a) điều kiện phụ, kịch bản "ống cho người có thân", nhóm lắp được (904 người val), chỉ ống, SAU mặt nạ QĐ 4-9:
      khoảng 95% bootstrap ghép cặp (B = 2000, seed 20261009) của Recall@10 (biến thể − LightGCN + mặt nạ seed 1) có cận
      trên > 0 ("không kém có ý nghĩa");
  (b) hơn LightGCN + mặt nạ: NDCG@20 val SAU mặt nạ QĐ 4-9 của biến thể > NDCG@20 val của LightGCN + mặt nạ ở CẢ 3 seed;
  (c) trong các biến thể đạt (a) và (b): chọn NDCG@20 val TRƯỚC mặt nạ lớn nhất (chỉ số chọn như kế hoạch lần 1);
  không biến thể nào đạt (a) và (b) -> DỪNG: không chạy seed 2, 3, không chấm test lần 2; hệ thống cuối = LightGCN + mặt nạ.
Ví dụ: A 0,0406 / 0,0406 (trước / sau mặt nạ), (a) đạt; B 0,0408 / 0,0408, (a) KHÔNG đạt (cận trên −0,002);
  LightGCN + mặt nạ 0,04044 / 0,04040 / 0,04053 -> A đạt (b) (0,0406 > 0,04053), B bị loại ở (a) -> chọn A.
In thêm (mô tả, không dùng để chọn): số thân / ống / phụ kiện trong top-10 (trước mặt nạ) của người có thân; Recall@10 của
người có thân tách item val có / không có nút trong H; khoảng bootstrap NDCG@20 (biến thể − LightGCN + mặt nạ s1).

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/06v2_select.py --sweep-dir results/cakg/val_sweep_v2_<nhãn>
Mỗi lần chạy ghi vào thư mục MỚI <sweep-dir>/select_<thời điểm>/ (log, json, md, mảng LightGCN chấm lại).
"""

import argparse
import importlib
import json
import sys
import tomllib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

T06 = importlib.import_module("06_cakg_train")
VSW = importlib.import_module("06_val_sweep")
N5_TOML = C.ROOT / "ai" / "config" / "n5_final.toml"
V1_S1 = C.ROOT / "results" / "cakg" / "val_sweep_20261014" / "val_cakg_lam1-1e-01_s1"
B_BOOT, BOOT_SEED = 2000, E.BOOT_SEED


def hit(r, k=10):
    return (r <= k).astype(np.float64)


def ndcg(r, k=20):
    return np.where(r <= k, 1.0 / np.log2(r + 1.0), 0.0)


def load_arrays(d, prefix, shas):
    """Mảng val đã lưu của một lần chạy; kiểm sha256 với result.json."""
    out = {}
    for nm in ("users", "rank_full", "top20_full", "scn_users", "rank_lens_only"):
        fn = d / f"{prefix}{nm}.npy"
        assert E.sha256(fn) == shas[fn.name], f"sha256 khác result.json: {fn}"
        out[nm] = np.load(fn)
    return out


def mechanism(arr, ev, has_h_item, mounts):
    """Người có thân (ev.bodies), top-10 trước mặt nạ: TB số thân / ống / phụ kiện / khác; tỉ lệ thân cùng ngàm với một
    thân đã có; Recall@10 tách item val có / không có nút trong H."""
    users, top, rank = arr["users"], arr["top20_full"][:, :10], arr["rank_full"]
    sel = np.array([u in ev.bodies for u in users.tolist()])
    tt = ev.item_type[top[sel]]
    mix = {E.TYPE_NAME[t]: float((tt == t).sum(1).mean()) for t in range(4)}
    same, nb = 0, 0
    for u, row in zip(users[sel].tolist(), top[sel]):
        um = {mounts[b] for b in ev.bodies[u] if b in mounts}
        for it in row.tolist():
            if ev.item_type[it] == 0:
                nb += 1
                same += it in mounts and mounts[it] in um
    pos = ev.split.pos
    hh = has_h_item[pos]
    r10 = hit(rank)
    return {"n_users_body": int(sel.sum()), "top10_mix_body_users": mix,
            "frac_same_mount_bodies": same / nb if nb else float("nan"),
            "recall@10_body_users": float(r10[sel].mean()),
            "recall@10_body_users_item_has_h": float(r10[sel & hh].mean()), "n_item_has_h": int((sel & hh).sum()),
            "recall@10_body_users_item_no_h": float(r10[sel & ~hh].mean()), "n_item_no_h": int((sel & ~hh).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep-dir", required=True)
    a = ap.parse_args()
    sw = Path(a.sweep_dir).resolve()
    runs = VSW.GROUPS["v2"][1]
    missing = [nm for nm, *_ in runs if not (sw / nm / "result.json").exists()]
    if missing:
        print(f"CHƯA ĐỦ: các lần chạy chưa xong {missing}. Gõ lại lệnh dò (06_val_sweep.py --group v2 ...) để chạy tiếp, "
              f"rồi chạy lại script này.", flush=True)
        sys.exit(3)
    out = sw / f"select_{E.now_tag()}"
    out.mkdir(parents=True, exist_ok=False)
    log = E.Log(out / "select.log")
    log(f"06v2_select | {sw} | git {E.git_state()} | script sha256 {E.sha256(__file__)} | CHỈ VAL")

    train = C.load_train()
    ev = E.EvalContext("val", train)
    users = ev.split.users
    lab = dict(zip(users.tolist(), ev.scn_lab.tolist()))
    H = CK.build_h()
    has_h_item = np.zeros(C.N_ITEMS, bool)
    has_h_item[list(H.item_loc)] = True
    mounts = CK.body_mounts()

    # -- các lần chạy v2 ----------------------------------------------------
    M = {}
    codes = set()
    for nm, _, _, variant in runs:
        d = sw / nm
        r = json.loads((d / "result.json").read_text(encoding="utf-8"))
        c = json.loads((d / "config.json").read_text(encoding="utf-8"))
        assert r["cfg"].get("variant") == variant and r["cfg"]["seed"] == 1, f"cfg sai: {d}"
        codes.add(json.dumps([c.get("code_sha256"), c["inputs_sha256"]], sort_keys=True))
        pre, post = load_arrays(d, "val_", r["val"]["arrays_sha256"]), \
            load_arrays(d, "val_mask_", r["val_mask"]["arrays_sha256"])
        assert np.array_equal(pre["users"], users) and np.array_equal(post["users"], users)
        M[variant] = {"dir": str(d.relative_to(C.ROOT)), "pre": pre, "post": post, "res": r,
                      "git_start": c["git"], "git_finish": r["git_at_finish"]}
        log(f"{variant:<13} {nm}: commit {c['git']['commit'][:7]}{' (dirty)' if c['git']['dirty'] else ''} | best epoch "
            f"{r['best_epoch']} / chạy {r['epochs_run']} ({'CHƯA CHẮC HỘI TỤ' if r['chua_chac_hoi_tu'] else 'dừng sớm'})"
            f" | {r['median_sec_per_epoch']:.1f} s/epoch")
    log(f"Mọi lần chạy v2 cùng sha256 code + đầu vào: {'CÓ' if len(codes) == 1 else 'KHÔNG — xem config.json'}")
    if any(m["git_start"]["dirty"] or m["git_finish"]["dirty"] for m in M.values()):
        log("CẢNH BÁO: có lần chạy huấn luyện trên cây git không sạch (ghi vào kế hoạch mục 9 nếu dùng kết quả).")

    # -- CaKG-Rec v1 seed 1 (đối chiếu) ---------------------------------------
    r1 = json.loads((V1_S1 / "result.json").read_text(encoding="utf-8"))
    V1 = {"pre": load_arrays(V1_S1, "val_", r1["val"]["arrays_sha256"]),
          "post": load_arrays(V1_S1, "val_mask_", r1["val_mask"]["arrays_sha256"]), "res": r1}

    # -- LightGCN s1–s3: chấm lại trên val, trước mặt nạ và mặt nạ QĐ 4-9 -------
    n5 = tomllib.loads(N5_TOML.read_text(encoding="utf-8"))
    lens_t, cmask_t = T06.MaskCache().get(ev)        # đúng mặt nạ QĐ 4-9 mà 06_cakg_train dùng cho val_mask_*
    L = {}
    for rr in n5["lightgcn"]["runs"]:
        s = rr["seed"]
        m, _, sha = EC.load_lightgcn(C.ROOT / rr["dir"], train, expect_sha=rr["best_pt_sha256"])
        d = out / f"lightgcn_s{s}"
        d.mkdir()
        log(f"\nLightGCN seed {s} ({rr['dir']}, best.pt sha256 khớp n5_final.toml): chấm lại val")
        sf = m.score_fn()
        res_pre = E.evaluate(sf, ev, log=log, save_dir=d, prefix="val_")
        res_post = E.evaluate(T06.mask_scorer(sf, lens_t, cmask_t), ev, log=log, save_dir=d, prefix="val_mask_")
        L[s] = {"pre": load_arrays(d, "val_", res_pre["arrays_sha256"]),
                "post": load_arrays(d, "val_mask_", res_post["arrays_sha256"]),
                "res": {"val": res_pre, "val_mask": res_post}}
        del m

    # -- điều kiện phụ (a) và (b) --------------------------------------------
    def scn_series(arr):
        su = arr["scn_users"]
        g = np.array([lab[u] for u in su.tolist()])
        return su[g == "lap_duoc"], hit(arr["rank_lens_only"][g == "lap_duoc"])

    su0, l_ref = scn_series(L[1]["post"])
    lgcn_mask_nd = {s: float(ndcg(L[s]["post"]["rank_full"]).mean()) for s in L}
    lgcn_pre_nd = {s: float(ndcg(L[s]["pre"]["rank_full"]).mean()) for s in L}
    thr = max(lgcn_mask_nd.values())
    log(f"\nNgưỡng (b): NDCG@20 val LightGCN + mặt nạ QĐ 4-9 s1 / s2 / s3 = "
        + " / ".join(f"{lgcn_mask_nd[s]:.5f}" for s in sorted(L)) + f" -> phải > {thr:.5f}")
    rows, decision = {}, {}
    nd_ref = ndcg(L[1]["post"]["rank_full"])
    for v, mm in M.items():
        su, lv = scn_series(mm["post"])
        assert np.array_equal(su, su0)
        bs = E.bootstrap_paired({"v": (lv, None), "ref": (l_ref, None)}, pairs=[("v", "ref")], B=B_BOOT, seed=BOOT_SEED)
        nd_pre, nd_post = float(ndcg(mm["pre"]["rank_full"]).mean()), float(ndcg(mm["post"]["rank_full"]).mean())
        assert abs(nd_pre - mm["res"]["val"]["full"]["ndcg@20"]) < 1e-12
        bn = E.bootstrap_paired({"v": (ndcg(mm["post"]["rank_full"]), None), "ref": (nd_ref, None)},
                                pairs=[("v", "ref")], B=B_BOOT, seed=BOOT_SEED)
        ok_a = bs["v - ref"][2] > 0
        ok_b = nd_post > thr
        rows[v] = {"dir": mm["dir"], "ndcg@20_truoc_mat_na": nd_pre, "ndcg@20_mat_na": nd_post,
                   "lap_duoc_R@10_chi_ong_mat_na": bs["v"][0], "lap_duoc_R@10_LightGCN_mat_na_s1": bs["ref"][0],
                   "lap_duoc_hieu_vs_LightGCN_mat_na_s1": bs["v - ref"],
                   "ndcg@20_mat_na_hieu_vs_LightGCN_mat_na_s1": bn["v - ref"],
                   "dieu_kien_phu_a": bool(ok_a), "hon_LightGCN_mat_na_b": bool(ok_b),
                   "best_epoch": mm["res"]["best_epoch"], "epochs_run": mm["res"]["epochs_run"],
                   "chua_chac_hoi_tu": mm["res"]["chua_chac_hoi_tu"],
                   "co_che": mechanism(mm["pre"], ev, has_h_item, mounts)}
    ref_rows = {f"LightGCN s{s}": {"ndcg@20_truoc_mat_na": lgcn_pre_nd[s], "ndcg@20_mat_na": lgcn_mask_nd[s],
                                   "co_che": mechanism(L[s]["pre"], ev, has_h_item, mounts)} for s in sorted(L)}
    ref_rows["CaKG-Rec v1 s1"] = {"ndcg@20_truoc_mat_na": float(ndcg(V1["pre"]["rank_full"]).mean()),
                                  "ndcg@20_mat_na": float(ndcg(V1["post"]["rank_full"]).mean()),
                                  "co_che": mechanism(V1["pre"], ev, has_h_item, mounts)}
    su1, l1 = scn_series(V1["post"])
    assert np.array_equal(su1, su0)
    ref_rows["CaKG-Rec v1 s1"]["lap_duoc_R@10_chi_ong_mat_na"] = float(l1.mean())

    eligible = [v for v in rows if rows[v]["dieu_kien_phu_a"] and rows[v]["hon_LightGCN_mat_na_b"]]
    chosen = max(eligible, key=lambda v: rows[v]["ndcg@20_truoc_mat_na"]) if eligible else None
    decision = {"eligible": eligible, "chosen": chosen,
                "dung": chosen is None,
                "ket_luan": (f"chọn biến thể {chosen}; bước tiếp: chạy seed 2, 3 (kế hoạch mục 4.3), kiểm điều kiện DỪNG 2"
                             if chosen else "DỪNG: không biến thể nào đạt (a) và (b). Không chạy seed 2, 3, không chấm "
                                            "test lần 2. Hệ thống cuối = LightGCN + mặt nạ QĐ 4-9.")}

    # -- in bảng --------------------------------------------------------------
    md = ["# CaKG-Rec v2 — chọn biến thể trên VAL (06v2_select.py)", "",
          f"Thư mục dò: `{sw.relative_to(C.ROOT)}`; git {E.git_state()['commit'][:7]}. Một seed (1) mỗi biến thể; "
          f"LightGCN chấm lại 3 seed. Bootstrap ghép cặp B = {B_BOOT}, seed {BOOT_SEED}.", "",
          "| Mô hình | NDCG@20 trước mặt nạ | NDCG@20 mặt nạ | R@10 chỉ ống, lắp được (mặt nạ) | hiệu vs LightGCN + mặt nạ s1 [95%] | (a) | (b) |",
          "|---|---|---|---|---|---|---|"]
    for v, x in rows.items():
        h = x["lap_duoc_hieu_vs_LightGCN_mat_na_s1"]
        md.append(f"| {v} | {x['ndcg@20_truoc_mat_na']:.5f} | {x['ndcg@20_mat_na']:.5f} | "
                  f"{x['lap_duoc_R@10_chi_ong_mat_na']:.4f} | {h[0]:+.4f} [{h[1]:+.4f}; {h[2]:+.4f}] | "
                  f"{'đạt' if x['dieu_kien_phu_a'] else 'KHÔNG'} | {'đạt' if x['hon_LightGCN_mat_na_b'] else 'KHÔNG'} |")
    for k, x in ref_rows.items():
        ld = x.get("lap_duoc_R@10_chi_ong_mat_na")
        if ld is None and k == "LightGCN s1":
            ld = rows[next(iter(rows))]["lap_duoc_R@10_LightGCN_mat_na_s1"]
        md.append(f"| {k} | {x['ndcg@20_truoc_mat_na']:.5f} | {x['ndcg@20_mat_na']:.5f} | "
                  f"{'' if ld is None else f'{ld:.4f}'} | | | |")
    md += ["", "**Mô tả (không dùng để chọn)** — người có thân, top-10 trước mặt nạ, val:", "",
           "| Mô hình | thân | ống | phụ kiện | thân cùng ngàm | R@10 người có thân | item có h | item không có h | NDCG@20 mặt nạ − LightGCN + mặt nạ s1 [95%] |",
           "|---|---|---|---|---|---|---|---|---|"]
    for k, x in list(rows.items()) + list(ref_rows.items()):
        c = x["co_che"]
        mx = c["top10_mix_body_users"]
        h = x.get("ndcg@20_mat_na_hieu_vs_LightGCN_mat_na_s1")
        fs = c["frac_same_mount_bodies"]
        fs_txt = "—" if fs != fs else f"{fs:.1%}"              # không có thân nào trong top-10: không tính được
        md.append(f"| {k} | {mx['than']:.2f} | {mx['ong']:.2f} | {mx['phu_kien']:.2f} | {fs_txt} | "
                  f"{c['recall@10_body_users']:.4f} | "
                  f"{c['recall@10_body_users_item_has_h']:.4f} | {c['recall@10_body_users_item_no_h']:.4f} | "
                  + (f"{h[0]:+.5f} [{h[1]:+.5f}; {h[2]:+.5f}]" if h else "") + " |")
    md += ["", f"**Kết luận theo quy tắc đăng ký trước:** {decision['ket_luan']}"]
    for line in md:
        log(line)
    (out / "select.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / "select.json").write_text(json.dumps({"git": E.git_state(), "sweep_dir": str(sw.relative_to(C.ROOT)),
                                                 "nguong_b": thr, "lightgcn_mask_ndcg20": lgcn_mask_nd,
                                                 "variants": rows, "refs": ref_rows, "decision": decision},
                                                indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {out}")
    log.close()


if __name__ == "__main__":
    main()
