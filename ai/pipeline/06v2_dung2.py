"""
06v2_dung2.py -- Kiểm điều kiện DỪNG 2 của CaKG-Rec v2 trên VAL, trung bình 3 seed (docs/reviews/cakg_v2_plan.md mục
4.3). Viết 16/10/2026, sau bước 1 (06v2_select.py đã chọn biến thể) và TRƯỚC khi chạy seed 2, 3. CHỈ đọc mảng VAL đã
lưu, không tính lại điểm, không dùng GPU, không đọc / chấm test.

Đầu vào:
  --select-dir: thư mục select_<thời điểm> của 06v2_select.py (biến thể chọn, lần chạy seed 1, và mảng val của LightGCN
                seed 1–3 đã chấm lại ở bước 1 — dùng lại đúng các mảng đó, kiểm NDCG@20 tính lại = select.json);
  --seeds-dir:  thư mục của 06_val_sweep.py --group v2seeds (seed 2, 3 của biến thể đó).
Kiểm trước: đủ 3 seed (thiếu thì in CHƯA ĐỦ, thoát mã 3, không ghi gì); cfg seed 2, 3 = cfg seed 1 trừ seed; sha256 code
+ đầu vào = seed 1; sha256 mảng = result.json; git sạch lúc bắt đầu / kết thúc huấn luyện (không sạch: cảnh báo).

Quy tắc (đã đăng ký, kế hoạch mục 4.3):
  (a') kịch bản "ống cho người có thân", nhóm lắp được (904 người val), Recall@10 chỉ ống, SAU mặt nạ QĐ 4-9; chỉ số từng
       người = trung bình 3 seed; khoảng 95% bootstrap ghép cặp (B = 2000, seed 20261009) của hiệu (v2 − LightGCN + mặt nạ,
       cũng trung bình 3 seed) có cận trên > 0;
  (b') trung bình 3 seed NDCG@20 val SAU mặt nạ của v2 > trung bình 3 seed của LightGCN + mặt nạ.
  Đạt cả hai -> bước tiếp: ghi ai/config/cakg_v2_final.toml, commit, rồi mới viết script chấm test lần 2.
  Không đạt -> DỪNG: không chấm test lần 2; hệ thống cuối = LightGCN + mặt nạ QĐ 4-9.
Ví dụ: v2 NDCG@20 sau mặt nạ 0,04062 / 0,04050 / 0,04058 -> TB 0,04057; LightGCN + mặt nạ 0,04044 / 0,04040 / 0,04053
  -> TB 0,04046 -> (b') đạt. Người 1 nhóm lắp được: v2 trúng ở seed 1, 3, trượt ở seed 2 -> 2/3; LightGCN + mặt nạ 1/3
  -> hiệu của người này +1/3; bootstrap trên 904 hiệu như vậy.

Chạy (từ thư mục camera-store):
  ai\\.venv\\Scripts\\python.exe ai/pipeline/06v2_dung2.py --select-dir <...>/select_<...> --seeds-dir results/cakg/val_sweep_<nhãn>
Mỗi lần chạy ghi vào thư mục MỚI <seeds-dir>/dung2_<thời điểm>/ (log, json, md).
"""

import argparse
import importlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SEL = importlib.import_module("06v2_select")          # load_arrays, mechanism, hit, ndcg (dùng lại, không sửa)
VSW = importlib.import_module("06_val_sweep")
B_BOOT, BOOT_SEED = SEL.B_BOOT, SEL.BOOT_SEED


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--select-dir", required=True)
    ap.add_argument("--seeds-dir", required=True)
    ap.add_argument("--smoke", action="store_true", help="(kiểm thử) seed 2, 3 chạy thử 1 epoch: bỏ qua max_epoch, eval_every")
    a = ap.parse_args()
    sd, kd = Path(a.select_dir).resolve(), Path(a.seeds_dir).resolve()
    sel, d1, runs23 = VSW.v2seeds_runs(sd)
    v = sel["decision"]["chosen"]
    dirs = {1: d1, **{int(nm[-1]): kd / nm for nm, *_ in runs23}}
    missing = [str(d) for d in dirs.values() if not (d / "result.json").exists()]
    if missing:
        print(f"CHƯA ĐỦ: chưa xong {missing}. Gõ lại lệnh 06_val_sweep.py --group v2seeds ... để chạy tiếp, rồi chạy lại "
              f"script này.", flush=True)
        sys.exit(3)
    out = kd / f"dung2_{E.now_tag()}"
    out.mkdir(parents=True, exist_ok=False)
    log = E.Log(out / "dung2.log")
    log(f"06v2_dung2 | biến thể {v} | select {sd} | seeds {kd} | git {E.git_state()} | script sha256 "
        f"{E.sha256(__file__)} | CHỈ VAL, chỉ đọc mảng đã lưu" + (" | SMOKE: không phải kết quả" if a.smoke else ""))

    train = C.load_train()
    ev = E.EvalContext("val", train)
    users = ev.split.users
    lab = dict(zip(users.tolist(), ev.scn_lab.tolist()))
    H = CK.build_h()
    has_h_item = np.zeros(C.N_ITEMS, bool)
    has_h_item[list(H.item_loc)] = True
    mounts = CK.body_mounts()

    # -- 3 seed của v2 -----------------------------------------------------------
    c1 = json.loads((d1 / "config.json").read_text(encoding="utf-8"))
    V, warn = {}, False
    for s, d in sorted(dirs.items()):
        c = json.loads((d / "config.json").read_text(encoding="utf-8"))
        r = json.loads((d / "result.json").read_text(encoding="utf-8"))
        ign = ("max_epoch", "eval_every") if a.smoke and s != 1 else ()
        want = {**c1["cfg"], "seed": s}
        assert ({k: x for k, x in c["cfg"].items() if k not in ign}
                == {k: x for k, x in want.items() if k not in ign}), f"cfg khác cfg seed 1 (trừ seed): {d}"
        assert c["code_sha256"] == c1["code_sha256"] and c["inputs_sha256"] == c1["inputs_sha256"], \
            f"sha256 code / đầu vào khác seed 1: {d}"
        warn |= c["git"]["dirty"] or r["git_at_finish"]["dirty"]
        pre = SEL.load_arrays(d, "val_", r["val"]["arrays_sha256"])
        post = SEL.load_arrays(d, "val_mask_", r["val_mask"]["arrays_sha256"])
        assert np.array_equal(pre["users"], users) and np.array_equal(post["users"], users)
        V[s] = {"dir": str(d.relative_to(C.ROOT)), "pre": pre, "post": post, "res": r}
        log(f"  {v} seed {s}: {V[s]['dir']} | commit {c['git']['commit'][:7]}{' (dirty)' if c['git']['dirty'] else ''} | "
            f"best epoch {r['best_epoch']} / chạy {r['epochs_run']} "
            f"({'CHƯA CHẮC HỘI TỤ' if r['chua_chac_hoi_tu'] else 'dừng sớm'}) | {r['median_sec_per_epoch']:.1f} s/epoch | "
            f"cfg = seed 1 trừ seed, sha256 code + đầu vào = seed 1: CÓ")
    if warn:
        log("CẢNH BÁO: có lần chạy huấn luyện trên cây git không sạch.")

    # -- LightGCN s1–s3: mảng val đã chấm lại ở bước 1 ----------------------------
    L = {}
    for s in (1, 2, 3):
        d = sd / f"lightgcn_s{s}"
        L[s] = {"post": {nm: np.load(d / f"val_mask_{nm}.npy") for nm in
                         ("users", "rank_full", "scn_users", "rank_lens_only")}}
        assert np.array_equal(L[s]["post"]["users"], users)
        nd = float(SEL.ndcg(L[s]["post"]["rank_full"]).mean())
        assert nd == sel["lightgcn_mask_ndcg20"][str(s)], f"mảng LightGCN s{s} khác select.json"
        log(f"  LightGCN + mặt nạ seed {s}: {d.relative_to(C.ROOT)} | NDCG@20 val tính lại {nd:.5f} = select.json | "
            f"sha256 val_mask_rank_full.npy {E.sha256(d / 'val_mask_rank_full.npy')[:12]}…")

    def scn(arr):
        su = arr["scn_users"]
        g = np.array([lab[u] for u in su.tolist()]) == "lap_duoc"
        return su[g], SEL.hit(arr["rank_lens_only"][g])

    su0 = scn(L[1]["post"])[0]
    for x in list(V.values()) + list(L.values()):
        assert np.array_equal(scn(x["post"])[0], su0)
    lv = np.mean([scn(V[s]["post"])[1] for s in V], axis=0)
    ll = np.mean([scn(L[s]["post"])[1] for s in L], axis=0)
    ndv = np.mean([SEL.ndcg(V[s]["post"]["rank_full"]) for s in V], axis=0)
    ndl = np.mean([SEL.ndcg(L[s]["post"]["rank_full"]) for s in L], axis=0)
    bs = E.bootstrap_paired({"v": (lv, None), "ref": (ll, None)}, pairs=[("v", "ref")], B=B_BOOT, seed=BOOT_SEED)
    bn = E.bootstrap_paired({"v": (ndv, None), "ref": (ndl, None)}, pairs=[("v", "ref")], B=B_BOOT, seed=BOOT_SEED)
    per_seed = {s: {"ndcg@20_truoc_mat_na": float(SEL.ndcg(V[s]["pre"]["rank_full"]).mean()),
                    "ndcg@20_mat_na": float(SEL.ndcg(V[s]["post"]["rank_full"]).mean()),
                    "lap_duoc_R@10_chi_ong_mat_na": float(scn(V[s]["post"])[1].mean()),
                    "co_che": SEL.mechanism(V[s]["pre"], ev, has_h_item, mounts)} for s in V}
    lg_nd = {s: float(SEL.ndcg(L[s]["post"]["rank_full"]).mean()) for s in L}
    lg_ld = {s: float(scn(L[s]["post"])[1].mean()) for s in L}
    m_v = float(np.mean([per_seed[s]["ndcg@20_mat_na"] for s in V]))
    m_l = float(np.mean(list(lg_nd.values())))
    ok_a, ok_b = bs["v - ref"][2] > 0, m_v > m_l
    passed = bool(ok_a and ok_b)
    concl = (f"ĐẠT DỪNG 2 ({v}): bước tiếp ghi ai/config/cakg_v2_final.toml, commit, rồi mới viết script chấm test lần 2"
             if passed else "DỪNG 2: không đạt. Không chấm test lần 2. Hệ thống cuối = LightGCN + mặt nạ QĐ 4-9.")

    md = [f"# CaKG-Rec v2 — kiểm DỪNG 2 trên VAL, 3 seed ({v}) (06v2_dung2.py)", "",
          f"git {E.git_state()['commit'][:7]}; chỉ đọc mảng val đã lưu. Bootstrap ghép cặp B = {B_BOOT}, seed {BOOT_SEED}; "
          f"chỉ số từng người = trung bình 3 seed.", "",
          "| Mô hình | seed | NDCG@20 trước mặt nạ | NDCG@20 mặt nạ | R@10 chỉ ống, lắp được (mặt nạ) | best epoch |",
          "|---|---|---|---|---|---|"]
    for s in sorted(V):
        x = per_seed[s]
        md.append(f"| {v} | {s} | {x['ndcg@20_truoc_mat_na']:.5f} | {x['ndcg@20_mat_na']:.5f} | "
                  f"{x['lap_duoc_R@10_chi_ong_mat_na']:.4f} | {V[s]['res']['best_epoch']} |")
    for s in sorted(L):
        md.append(f"| LightGCN + mặt nạ | {s} | | {lg_nd[s]:.5f} | {lg_ld[s]:.4f} | |")
    h, hn = bs["v - ref"], bn["v - ref"]
    md += ["", f"- (b') TB 3 seed NDCG@20 val sau mặt nạ: {v} {m_v:.5f} vs LightGCN + mặt nạ {m_l:.5f} -> "
               f"**{'đạt' if ok_b else 'KHÔNG đạt'}** (mô tả: hiệu theo người {hn[0]:+.5f} [{hn[1]:+.5f}; {hn[2]:+.5f}])",
           f"- (a') nhóm lắp được ({len(su0)} người), Recall@10 chỉ ống sau mặt nạ, TB 3 seed: {bs['v'][0]:.4f} vs "
           f"{bs['ref'][0]:.4f}, hiệu {h[0]:+.4f} [{h[1]:+.4f}; {h[2]:+.4f}] -> cận trên > 0: "
           f"**{'đạt' if ok_a else 'KHÔNG đạt'}**", "",
           "**Mô tả (không dùng để quyết)** — người có thân, top-10 trước mặt nạ, val:", "",
           "| seed | thân | ống | phụ kiện | thân cùng ngàm | R@10 người có thân | item có h | item không có h |",
           "|---|---|---|---|---|---|---|---|"]
    for s in sorted(V):
        c = per_seed[s]["co_che"]
        mx, fs = c["top10_mix_body_users"], c["frac_same_mount_bodies"]
        md.append(f"| {s} | {mx['than']:.2f} | {mx['ong']:.2f} | {mx['phu_kien']:.2f} | "
                  f"{'—' if fs != fs else f'{fs:.1%}'} | {c['recall@10_body_users']:.4f} | "
                  f"{c['recall@10_body_users_item_has_h']:.4f} | {c['recall@10_body_users_item_no_h']:.4f} |")
    md += ["", f"**Kết luận theo quy tắc đăng ký trước:** {concl}"]
    for line in md:
        log(line)
    (out / "dung2.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / "dung2.json").write_text(json.dumps({
        "git": E.git_state(), "variant": v, "select_dir": str(sd.relative_to(C.ROOT)), "seeds_dir": str(kd.relative_to(C.ROOT)),
        "runs": {s: V[s]["dir"] for s in V}, "per_seed": per_seed, "lightgcn_mask_ndcg20": lg_nd,
        "lightgcn_mask_lap_duoc_R@10": lg_ld, "mean_ndcg20_mask": {"v2": m_v, "lightgcn_mask": m_l},
        "a_lap_duoc_hieu": h, "ndcg20_mask_hieu_theo_nguoi": hn, "dieu_kien_a": bool(ok_a), "dieu_kien_b": bool(ok_b),
        "dat_dung2": passed, "ket_luan": concl}, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"-> {out}")
    log.close()


if __name__ == "__main__":
    main()
