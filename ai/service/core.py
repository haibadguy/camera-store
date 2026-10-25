"""
core.py -- Lõi dịch vụ mô hình (nội dung 10): hệ thống cuối = LightGCN + mặt nạ QĐ 4-9 + giải thích theo đường.
Viết 21/10/2026. KHÔNG viết lại logic: mọi bước gọi đúng hàm đã dùng lúc chấm test / đo giải thích:
  - xếp hạng, quy tắc hòa π         : eval_05.full_rank, eval_05.tie_keys (seed 20261009)
  - mặt nạ (15) QĐ 4-9               : eval_05.certain_violation_mask + eval_cakg.mask_scorer
  - thân của người dùng              : common_05.build_train_bodies (thân trong train)
  - đường, b*, c*, câu, kiểm sự kiện : 09_explain_lightgcn.LGExplainer, eval_cakg.sentence, eval_cakg.verify_explanation
  - mức tương thích + luật           : 03_mount_compat.Rules trên ai/config/mount_rules.toml (tự kiểm với compat_pairs.csv)
Embedding (eU, eI) đọc từ file do export_embeddings.py ghi (kiểm sha256), chấm trên CPU (hoặc thiết bị chọn).

Ví dụ một yêu cầu /recommend (u có thân Sony a6000 trong train, k = 10, exclude = all_history):
  điểm s_i = eU[u] · eI[i] cho 27.940 sản phẩm -> bỏ mọi sản phẩm u đã có (train + val + test) -> ống ngàm khác mà mọi thân của u đều
  M = 0 (không "không biết") được gán −∞ -> lấy 10 sản phẩm điểm cao nhất (hòa: π nhỏ hơn đứng trước) -> với mỗi ống
  trong top-10: b* = thân lắp được có e_bᵀe_l lớn nhất, câu "Gợi ý … vì ống này lắp trực tiếp được trên … (ngàm sony_e)".
"""

import copy
import csv
import importlib
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

PIPE = Path(__file__).resolve().parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
import cakg_model as CK  # noqa: E402
import common_05 as C    # noqa: E402
import eval_05 as E      # noqa: E402
import eval_cakg as EC   # noqa: E402

X09 = importlib.import_module("09_explain_lightgcn")      # LGExplainer (b*, c* của hệ thống cuối)
M03 = importlib.import_module("03_mount_compat")          # Rules (bộ áp luật tương thích của nội dung 3)

RULES_TOML = C.ROOT / "ai" / "config" / "mount_rules.toml"
TYPE_LABEL = {"than": "thân máy", "ong": "ống kính", "phu_kien": "phụ kiện", "khac": "khác"}
TYPE_OF_CODE = {v: k for k, v in C.ITEM_TYPE_CODE.items()}
LEVEL_LABEL = {"compatible_with": "lắp trực tiếp, dùng đủ khung hình (M = 1)",
               "crops_sensor": "lắp trực tiếp, ống cho cảm biến nhỏ hơn nên ảnh bị cắt khung (M = 1)",
               "requires_adapter": "cần ngàm chuyển chính hãng (M = 0)",
               "incompatible": "không lắp được (M = 0)",
               "unknown": "không biết (M = 0, không dùng cho mặt nạ và CVR)"}
EXCLUDE_MODES = ("all_history", "train_val")   # mặc định: bỏ cả lịch sử (Nam chốt 21/10); train_val: như lúc chấm test
# Thân máy dùng cho mặt nạ và giải thích (Nam chốt 21/10, phiên sau): all_history -> thân trong CẢ lịch sử (train + val +
# test); train_val -> thân trong train, đúng như lúc chấm test.
MODE_VIEW = {"all_history": "history", "train_val": "train"}
# Cụm chỉ cạnh owns trong câu (Nam chốt 26/10): dữ liệu là đánh giá Amazon, không phải lịch sử mua -> all_history nói
# "bạn đã đánh giá"; train_val giữ đúng câu của eval_cakg.sentence ("bạn đã mua") để so được với câu đã lưu lúc chấm.
SENTENCE_OWNS = " bạn đã mua (ngàm "
OWNS_PHRASE = {"all_history": " bạn đã đánh giá (ngàm ", "train_val": SENTENCE_OWNS}


@dataclass
class BodyView:
    """Một tập thân máy của mọi người dùng và những thứ dựng từ nó (cùng hàm, chỉ khác dict lịch sử truyền vào).
    owned: dict lịch sử dùng để kiểm "bạn đã mua / đã đánh giá b*" (pctx.train của verify_explanation)."""
    owned: dict
    bodies: dict
    cmask: np.ndarray
    cmask_t: torch.Tensor
    pctx: object
    xp: object


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details or {}


def _single_mount(m):
    return m not in ("khong_co", "khong_ro", "nhieu", "") and ">" not in m


def _range(v, keys):
    """(x1, x2) chuỗi của cạnh has_spec -> {keys[0]: x1, keys[1]: x2} số; x2 rỗng (ống một tiêu cự / khẩu độ không đổi)
    -> x2 = x1. Vd ống 55-200mm f/4-5.6: tiêu cự {"min": 55, "max": 200}, khẩu độ tối đa {"at_min_focal": 4,
    "at_max_focal": 5.6} (f/4 ở 55 mm, f/5.6 ở 200 mm)."""
    if v is None:
        return None
    lo = float(v[0])
    return {keys[0]: lo, keys[1]: float(v[1]) if v[1] else lo}


class RecommenderCore:
    def __init__(self, emb_dir, device="cpu", log=print):
        t0 = time.perf_counter()
        self.device = torch.device(device)
        emb_dir = Path(emb_dir)
        self.meta = json.loads((emb_dir / "meta.json").read_text(encoding="utf-8"))
        fn = emb_dir / "embeddings.npz"
        sha = E.sha256(fn)
        assert sha == self.meta["embeddings_sha256"], f"sha256 embeddings.npz khác meta.json: {fn}"
        z = np.load(fn)
        self.eU = torch.as_tensor(z["eU"], device=self.device)
        self.eI = torch.as_tensor(z["eI"], device=self.device)
        assert self.eU.shape[0] == C.N_USERS and self.eI.shape[0] == C.N_ITEMS

        self.train = C.load_train()
        assert len(self.train) == C.N_USERS, "mọi người dùng phải có sản phẩm trong train"
        self.val = C.load_pos("val")
        self.test = C.load_pos("test")
        self.item_type = C.load_item_type()
        self.ctx = C.load_cvr_context()
        self.history = {u: self.train[u] | {self.val[u], self.test[u]} for u in range(C.N_USERS)}
        self.pi = E.tie_keys()
        self.pctx = EC.PathContext(self.train, self.item_type)
        H = CK.build_h()
        self.has_edge = EC.h_edge_checker(H)
        self.order = list(H.node_names["usecase"])
        self.attrs = self.pctx.attrs
        self.lens_t = None
        self.views = {"train": self._view(self.train, self.pctx), "history": self._view(self.history, None)}
        self.bodies = self.views["train"].bodies            # thân trong train (QĐ 4-9 như lúc chấm)
        self.m1_per_body = Counter(b for (b, _) in self.ctx.m1)

        self.rules = M03.Rules(RULES_TOML)
        self.rule_note = {r["id"]: r.get("note", "") for r in self.rules.rules}
        self._check_rules(log)
        self.startup_s = time.perf_counter() - t0
        log(f"RecommenderCore: {self.meta['model']} seed {self.meta['seed']} | best.pt {self.meta['best_pt_sha256'][:12]}… | "
            f"embeddings {sha[:12]}… | thiết bị {self.device} | {C.N_USERS:,} người, {C.N_ITEMS:,} sản phẩm | "
            f"người có thân: train {len(self.bodies):,}, cả lịch sử {len(self.views['history'].bodies):,} | "
            f"nạp {self.startup_s:.1f}s")

    def _view(self, owned, pctx):
        """Dựng mặt nạ (15) QĐ 4-9 và bộ giải thích từ thân trong `owned` ({uid: tập sản phẩm}). pctx None: bản sao nông
        của self.pctx với .train = owned (verify_explanation kiểm "đã mua b*" bằng owned; mọi cạnh khác vẫn của đồ thị)."""
        bodies = C.build_train_bodies(owned, None, self.item_type)
        lens, cmask = E.certain_violation_mask(bodies, self.ctx)
        if self.lens_t is None:
            self.lens_t = torch.as_tensor(lens, device=self.device)
            self.lens_col = {int(l): j for j, l in enumerate(lens.tolist())}
        assert np.array_equal(lens, self.lens_t.cpu().numpy())
        if pctx is None:
            pctx = copy.copy(self.pctx)
            pctx.train = owned
        return BodyView(owned, bodies, cmask, torch.as_tensor(cmask, device=self.device), pctx,
                        X09.LGExplainer(self.eI.cpu(), bodies, pctx, self.order))

    # -- tự kiểm lúc khởi động ---------------------------------------------------
    def _level(self, b, l):
        ab, al = self.attrs[b], self.attrs[l]
        return self.rules.level(ab["mount"], ab["khung"] or "khong_ro", al["mount"], al["khung"] or "khong_ro",
                                ab["may_phim"] == "True")

    def _check_rules(self, log):
        """Rules.level trên item_attributes.csv phải cho đúng mức / luật / cờ đã ghi trong compat_pairs.csv (đầu ra
        của 03_mount_compat), và số cặp M = 1 / "không biết" phải trùng CvrContext."""
        n, n_m1, n_unk = 0, 0, 0
        with open(C.DATA_DIR / "kg" / "compat_pairs.csv", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                b, l = int(r["body_iid"]), int(r["lens_iid"])
                assert self._level(b, l) == (r["level"], r["rule_id"], r["crop_unknown"] == "1"), r
                n += 1
                if r["lens_uncertain"] == "0":
                    n_m1 += r["level"] in M03.DIRECT
                    n_unk += r["level"] == "unknown"
        assert n_m1 == len(self.ctx.m1) and n_unk == len(self.ctx.unknown), (n_m1, len(self.ctx.m1), n_unk)
        log(f"  kiểm luật tương thích: {n:,} cặp của compat_pairs.csv trùng Rules.level; M = 1 {n_m1:,}, "
            f"không biết {n_unk:,} (trùng CvrContext)")

    # -- kiểm đầu vào ---------------------------------------------------------------
    def check_user(self, u):
        if not 0 <= u < C.N_USERS:
            raise ApiError(404, "USER_NOT_FOUND", f"Không có người dùng {u} trong dữ liệu (chỉ phục vụ user_id "
                           f"0..{C.N_USERS - 1}; chưa hỗ trợ người dùng mới).", {"user_id": u})

    def check_item(self, i, field="item_id"):
        if not 0 <= i < C.N_ITEMS:
            raise ApiError(404, "ITEM_NOT_FOUND", f"Không có sản phẩm {i} (item_id 0..{C.N_ITEMS - 1}).", {field: i})

    # -- thông tin sản phẩm ---------------------------------------------------------
    def item_brief(self, i):
        a = self.attrs[i]
        return {"item_id": i, "asin": a["parent_asin"], "title": a["title"], "type": a["item_type"],
                "type_label": TYPE_LABEL[a["item_type"]]}

    def item_info(self, i):
        self.check_item(i)
        a, p = self.attrs[i], self.pctx
        d = self.item_brief(i)
        typ = a["item_type"]
        d.update({
            "mount": a["mount"] or None, "khung": a["khung"] or None, "may_phim": a["may_phim"] == "True",
            "mount_uncertain": a["uncertain"] == "True", "mount_source": a["mount_source"] or None,
            "categories": a["categories"],
            "in_matrix": (i in self.ctx.bodies_in_m) if typ == "than" else (i in self.ctx.lenses_in_m) if typ == "ong"
            else False,
            "focal_mm": _range(p.focal.get(i), ("min", "max")),
            "max_aperture_f": _range(p.aperture.get(i), ("at_min_focal", "at_max_focal")),
            "usecases": list(p.suit.get(i, [])),
            "usecases_label": [EC.USECASE_VI[c] for c in p.suit.get(i, [])],
        })
        if typ == "than":
            d["n_lenses_m1"] = self.m1_per_body.get(i, 0)
        return d

    def source(self, u, i):
        """Sản phẩm i nằm ở phần nào của lịch sử người u: train / val / test."""
        return "train" if i in self.train[u] else "val" if i == self.val[u] else "test" if i == self.test[u] else None

    def check_mode(self, mode):
        if mode not in EXCLUDE_MODES:
            raise ApiError(422, "INVALID_PARAM", f"exclude phải là một trong {EXCLUDE_MODES}.", {"exclude": mode})
        return self.views[MODE_VIEW[mode]]

    def user_bodies(self, u, mode="all_history"):
        self.check_user(u)
        v = self.check_mode(mode)
        bs = sorted(v.bodies.get(u, ()))
        out = []
        for b in bs:
            d = self.item_info(b)
            out.append({**{k: d[k] for k in ("item_id", "asin", "title", "mount", "khung", "may_phim", "in_matrix",
                                             "n_lenses_m1")}, "source": self.source(u, b)})
        return {"user_id": u, "exclude": mode, "n_history_items": len(v.owned[u]), "n_bodies": len(bs), "bodies": out,
                "n_lenses_blocked": int(v.cmask[u].sum())}

    # -- tương thích một cặp --------------------------------------------------------
    def compat(self, b, l):
        self.check_item(b, "body_id")
        self.check_item(l, "lens_id")
        if self.attrs[b]["item_type"] != "than":
            raise ApiError(400, "NOT_A_BODY", f"Sản phẩm {b} không phải thân máy.", {"body_id": b,
                           "type": self.attrs[b]["item_type"]})
        if self.attrs[l]["item_type"] != "ong":
            raise ApiError(400, "NOT_A_LENS", f"Sản phẩm {l} không phải ống kính.", {"lens_id": l,
                           "type": self.attrs[l]["item_type"]})
        ab, al = self.attrs[b], self.attrs[l]
        res = {"body": self.item_brief(b), "lens": self.item_brief(l), "body_mount": ab["mount"] or None,
               "lens_mount": al["mount"] or None, "body_khung": ab["khung"] or None, "lens_khung": al["khung"] or None,
               "body_film": ab["may_phim"] == "True", "lens_uncertain": al["uncertain"] == "True"}
        if not (_single_mount(ab["mount"]) and _single_mount(al["mount"])):
            res.update(level=None, level_label=None, rule_id=None, rule_note=None, crop_unknown=None, m=None,
                       in_matrix=False, reason="thân hoặc ống không xác định được đúng một ngàm: không có trong ma "
                                               "trận M, không xếp mức")
        else:
            lev, rid, cu = self._level(b, l)
            res.update(level=lev, level_label=LEVEL_LABEL[lev], rule_id=rid or None,
                       rule_note=self.rule_note.get(rid) if rid else "không luật nào khớp -> mức mặc định "
                                                                     f"'{self.rules.default}' (khác ngàm, không có ngàm "
                                                                     "chuyển chính hãng trong bảng luật)",
                       crop_unknown=bool(cu), in_matrix=b in self.ctx.bodies_in_m and l in self.ctx.lenses_in_m)
            res["m"] = int((b, l) in self.ctx.m1) if res["in_matrix"] else None
            if res["in_matrix"]:
                assert res["m"] == int(lev in M03.DIRECT) and ((b, l) in self.ctx.unknown) == (lev == "unknown")
            else:
                res["reason"] = "ống 'không chắc' ngàm (QĐ 4): có mức theo luật nhưng không có trong M, mặt nạ không chặn"
        v = C.judge_lens(l, {b}, self.ctx)
        res["qd49_if_only_this_body"] = {True: "chan", False: "khong_chan", None: "khong_cham_duoc"}[v]
        return res

    # -- gợi ý ----------------------------------------------------------------------
    def _split(self, u, exclude):
        ex = set(self.train[u])
        ex.add(self.val[u])                       # cả hai chế độ đều bỏ train + val
        if exclude == "all_history":
            ex.add(self.test[u])
        dummy = next(i for i in range(C.N_ITEMS) if i not in ex)
        ex = sorted(ex)
        # full_rank cần một "item cần đoán" để tính hạng; dịch vụ chỉ dùng top-k (không phụ thuộc item này),
        # nên đặt một ứng viên bất kỳ (iid nhỏ nhất không bị loại).
        return E.Split("serve", np.array([u]), np.array([dummy]), np.array([0, len(ex)]), np.array(ex, dtype=np.int64))

    def explain(self, u, l, v, exclude):
        """Giải thích cho ống l trong top-k của u (người có thân trong góc nhìn v), hoặc None nếu không có đường
        u → b → l. Cụm "bạn đã mua" / "bạn đã đánh giá" theo chế độ exclude (OWNS_PHRASE)."""
        if self.item_type[l] != 1 or u not in v.bodies:
            return None
        ex = v.xp.explain(u, l)
        if ex is None:
            return None
        s = EC.sentence(ex, v.pctx)
        assert s.count(SENTENCE_OWNS) == 1, s
        s = s.replace(SENTENCE_OWNS, OWNS_PHRASE[exclude])
        err = EC.verify_explanation(ex, s, v.pctx, self.has_edge)
        b, c = ex["b_star"], ex["c_star"]
        path = [{"kind": "user", "id": u}, {"kind": "item", "role": "body", **self.item_brief(b)},
                {"kind": "item", "role": "lens", **self.item_brief(l)}]
        edges = ["owns", ex["rho"]]
        if c is not None:
            path.append({"kind": "usecase", "id": c, "label": EC.USECASE_VI[c]})
            edges.append("suitable_for")
        return {"text": s, "path": path, "edges": edges, "b_star": b, "rho": ex["rho"], "c_star": c,
                "b_star_score": ex["e_score"][b], "b_star_source": self.source(u, b),
                "candidate_bodies": ex["cand_bodies"],
                "verified": not err, "errors": err}

    def recommend(self, u, k=10, exclude="all_history", view=None):
        """view: chỉ để kiểm (check_service --stage history) — ép góc nhìn thân khác MODE_VIEW[exclude]."""
        self.check_user(u)
        v = self.check_mode(exclude) if view is None else self.views[view]
        sp = self._split(u, exclude)

        def score(uids):
            return self.eU[uids] @ self.eI.T

        masked = EC.mask_scorer(score, self.lens_t, v.cmask_t)
        dev = self.device
        top0 = E.full_rank(score, sp, self.pi, k_max=k, k_list=[k], device=dev)["top"][0].tolist()
        top = E.full_rank(masked, sp, self.pi, k_max=k, k_list=[k], device=dev)["top"][0].tolist()
        S = score(torch.as_tensor([u], device=dev))[0]
        blocked_top0 = [i for i in top0 if i in self.lens_col and v.cmask[u, self.lens_col[i]]]
        items = []
        for r, i in enumerate(top, 1):
            items.append({"rank": r, **self.item_brief(i), "score": float(S[i]), "explanation": self.explain(u, i, v, exclude)})
        return {"user_id": u, "k": k, "exclude": exclude, "has_bodies": u in v.bodies,
                "n_bodies": len(v.bodies.get(u, ())), "items": items,
                "mask": {"rule": "QĐ 4-9 (mặt nạ 15)", "n_lenses_blocked": int(v.cmask[u].sum()),
                         "n_blocked_in_topk_before_mask": len(blocked_top0),
                         "blocked_in_topk_before_mask": [self.item_brief(i) for i in blocked_top0]}}

    def health(self):
        return {"status": "ok", "model": self.meta["model"], "seed": self.meta["seed"],
                "best_pt_sha256": self.meta["best_pt_sha256"], "embeddings_sha256": self.meta["embeddings_sha256"],
                "device": str(self.device), "n_users": C.N_USERS, "n_items": C.N_ITEMS,
                "n_users_with_bodies": {"train": len(self.bodies), "all_history": len(self.views["history"].bodies)}, "startup_s": round(self.startup_s, 2)}
