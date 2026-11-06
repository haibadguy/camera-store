# %% [markdown]
# # camera-store v3 — chạy huấn luyện trên Kaggle
#
# Notebook này được sinh từ `kaggle/v3_runner.py` (định dạng `# %%`) bởi `kaggle/build_kaggle_package.py`.
# Kế hoạch: `docs/reviews/v3_eval_plan.md`; cách làm trên web: `kaggle/HUONG_DAN_KAGGLE.md`. Mỗi lần
# "Save Version → Save & Run All" là một **phiên bản** của notebook: code (commit git), dữ liệu (sha256), danh sách việc
# `JOBS`, log và kết quả đều nằm trong phiên bản đó.
#
# Quy tắc:
# 1. Code lấy từ dataset `camera-store-v3-code` (git bundle) và **checkout đúng commit** `EXPECT_COMMIT`; lệch thì dừng.
#    RecBole-GNN (SimGCL) cũng lấy từ bundle trong dataset đó, kiểm đúng commit.
# 2. Dữ liệu lấy từ dataset `camera-store-v3-data`; **kiểm sha256 từng file** với `manifest_sha256.json`; lệch thì dừng.
# 3. Seed: mỗi việc truyền `--seed` cho script (script tự đặt seed torch / numpy như khi chạy ở máy nhóm).
# 4. Log: mỗi việc ghi `logs/<việc>_<RUN_LABEL>_<thời điểm>.log` (tên mới, không ghi đè) + log của chính script.
# 5. Không chấm test trên Kaggle (script huấn luyện chỉ chấm val). Chấm test làm ở máy nhóm, theo kế hoạch.
# 6. Hai môi trường: "nhom" = python chính, cài đúng torch / PyG / numpy / scipy như `ai/requirements-lock.txt`;
#    "recbole" = venv /tmp/rbenv (thấy torch của python chính, còn numpy 1.26.4 / scipy 1.11.4 / recbole 1.2.1 ... riêng)
#    như venv RecBole ở máy nhóm (`ai/recbole/requirements-recbole-lock.txt`).

# %%
# ===== CẤU HÌNH CỦA PHIÊN BẢN NÀY (sửa trước khi Save Version) =====
EXPECT_COMMIT = "__COMMIT__"          # build_kaggle_package.py điền
ACCOUNT = "nam"                       # "nam" | "hai" | "quyen": chọn bộ việc của tài khoản này (PRESETS bên dưới)
RUN_LABEL = "thu_s1_" + ACCOUNT       # nhãn lần chạy; chạy tiếp ở phiên bản sau thì GIỮ NGUYÊN nhãn
RESUME = False                        # True khi chạy tiếp: phải thêm output của phiên bản trước làm input (xem dưới)
REQUIRE_GPU = "T4"                    # mỗi mô hình chạy mọi seed trên cùng loại GPU (kế hoạch mục 5) -> sai GPU thì dừng
JOB_DEADLINE_H = 8.5                  # sau mốc này (tính từ đầu phiên) ngắt việc đang chạy, lưu kết quả để chạy tiếp.
                                      # Giới hạn giờ / phiên của Kaggle CHƯA KIỂM CHỨNG -> để thận trọng 8,5 giờ.
INSTALL_EXACT_VERSIONS = True         # cài đúng phiên bản như file lock (cần bật Internet)

# Đợt "thu" (HỎI 10, Nam chốt 06/11): mỗi baseline seed 1, một cấu hình; chỉ val. Việc: (tên, môi trường, script, tham số).
# "{GNN}" được thay bằng thư mục RecBole-GNN đã clone. Trần 1.000 epoch, chấm val mỗi 10 epoch, dừng sau 5 lần không tăng.
PRESETS = {
    "nam": [   # KGIN: mặc định RecBole (d 64, 4 ý định, node dropout 0,5), context_hops = 2 (giữa lưới {1, 2, 3})
        ("kgin_hops2_s1", "recbole", "ai/recbole/run_recbole.py",
         ["--model", "KGIN", "--seed", "1", "--epochs", "1000", "--group-eval", "--set", "context_hops=2"]),
    ],
    "hai": [   # SimGCL: mặc định RecBole-GNN, λ = 0,01 (giữa lưới đã đăng ký {0,005; 0,01; 0,05})
        ("simgcl_lam0.01_s1", "recbole", "ai/recbole/run_recbole.py",
         ["--model", "SimGCL", "--seed", "1", "--epochs", "1000", "--group-eval", "--gnn", "{GNN}",
          "--set", "lambda=0.01"]),
    ],
    "quyen": [  # BPR-MF code nhóm (số chính, HỎI 5), UltraGCN (cấu hình Electronics của tác giả), BPR RecBole (đối chiếu)
        ("bprmf_l2-1e-04_s1", "nhom", "ai/pipeline/05d_bprmf_train.py", ["--l2", "1e-4", "--seed", "1"]),
        ("ultragcn_electronics_s1", "nhom", "ai/pipeline/05e_ultragcn_train.py", ["--seed", "1"]),
        ("recbole_bpr_s1", "recbole", "ai/recbole/run_recbole.py",
         ["--model", "BPR", "--seed", "1", "--epochs", "1000", "--group-eval"]),
    ],
}
JOBS = PRESETS[ACCOUNT]

# %%
import hashlib, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path

T_START = time.time()
INP = Path("/kaggle/input")
WORK = Path("/kaggle/working")
REPO = WORK / "camera-store"
GNN_DIR = Path("/tmp/recbole_gnn_src")
RB_ENV = Path("/tmp/rbenv")
LOGS = WORK / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

def sh(cmd, **kw):
    print("$", cmd if isinstance(cmd, str) else " ".join(map(str, cmd)), flush=True)
    r = subprocess.run(cmd, shell=isinstance(cmd, str), text=True, capture_output=True, **kw)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:], sep="\n")
        raise RuntimeError(f"lệnh lỗi (mã {r.returncode})")
    return r.stdout

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

UNZ = Path("/tmp/unz")

def find_input(name):
    c = [p for p in INP.rglob(name)] + ([p for p in UNZ.rglob(name)] if UNZ.exists() else [])
    assert len(c) == 1, f"không tìm thấy đúng một {name} trong {INP}: {c}"
    return c[0]

# Tải lên dạng .zip: thường Kaggle tự giải nén (CHƯA KIỂM CHỨNG); nếu input vẫn là file .zip thì giải nén ra /tmp/unz.
import zipfile
for z in sorted(INP.rglob("camera-store-v3-*.zip")):
    key = "camera-store.bundle" if "code" in z.name else "manifest_sha256.json"
    if not list(INP.rglob(key)):
        print("giải nén", z)
        zipfile.ZipFile(z).extractall(UNZ / z.stem)

def hours():
    return (time.time() - T_START) / 3600

# %%
# ===== Môi trường =====
env = {"python": platform.python_version(), "time_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
       "account_preset": ACCOUNT, "run_label": RUN_LABEL}
try:
    env["nvidia_smi"] = sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader")
except Exception as e:  # không có GPU
    env["nvidia_smi"] = f"không có GPU: {e}"
print(json.dumps(env, indent=2, ensure_ascii=False))
assert REQUIRE_GPU in env["nvidia_smi"], f"cần GPU {REQUIRE_GPU} (Settings → Accelerator), đang có: {env['nvidia_smi']}"

# %%
# ===== Code: clone git bundle, checkout đúng commit; RecBole-GNN =====
bundle = find_input("camera-store.bundle")
if REPO.exists():
    shutil.rmtree(REPO)
sh(["git", "clone", "--quiet", str(bundle), str(REPO)])
sh(["git", "-C", str(REPO), "checkout", "--quiet", EXPECT_COMMIT])
head = sh(["git", "-C", str(REPO), "rev-parse", "HEAD"]).strip()
assert head == EXPECT_COMMIT, f"commit {head} khác {EXPECT_COMMIT}"
env["commit"] = head
gnn_expect = find_input("RECBOLE_GNN_COMMIT.txt").read_text().strip()
if GNN_DIR.exists():
    shutil.rmtree(GNN_DIR)
sh(["git", "clone", "--quiet", str(find_input("recbole_gnn.bundle")), str(GNN_DIR)])
sh(["git", "-C", str(GNN_DIR), "checkout", "--quiet", gnn_expect])
env["recbole_gnn_commit"] = sh(["git", "-C", str(GNN_DIR), "rev-parse", "HEAD"]).strip()
assert env["recbole_gnn_commit"] == gnn_expect
print("commit", head, "| RecBole-GNN", gnn_expect)

# %%
# ===== Thư viện: môi trường "nhom" (python chính) =====
if INSTALL_EXACT_VERSIONS:
    req = REPO / "kaggle" / "requirements-kaggle.txt"
    print(sh([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])[-2000:])
import torch  # noqa: E402
env["torch"] = torch.__version__
env["cuda_available"] = torch.cuda.is_available()
env["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
(LOGS / f"pip_freeze_nhom_{RUN_LABEL}_{time.strftime('%Y%m%d_%H%M%S')}.txt").write_text(
    sh([sys.executable, "-m", "pip", "freeze"]), encoding="utf-8")
print(json.dumps(env, indent=2, ensure_ascii=False))

# %%
# ===== Thư viện: môi trường "recbole" (chỉ tạo khi có việc cần) =====
RB_PY = None
if any(e == "recbole" for _, e, _, _ in JOBS):
    if RB_ENV.exists():
        shutil.rmtree(RB_ENV)
    sh([sys.executable, "-m", "venv", "--system-site-packages", str(RB_ENV)])
    RB_PY = str(RB_ENV / "bin" / "python")
    print(sh([RB_PY, "-m", "pip", "install", "-q", "--no-deps", "-r",
              str(REPO / "kaggle" / "requirements-kaggle-recbole.txt")])[-2000:])
    chk = sh([RB_PY, "-c", "import json, numpy, scipy, pandas, torch, torch_geometric, recbole; print(json.dumps("
              "{'numpy': numpy.__version__, 'scipy': scipy.__version__, 'pandas': pandas.__version__, "
              "'torch': torch.__version__, 'pyg': torch_geometric.__version__, 'recbole': recbole.__version__, "
              "'cuda': torch.cuda.is_available()}))"])
    env["recbole_env"] = json.loads(chk.strip().splitlines()[-1])
    print(env["recbole_env"])
    assert env["recbole_env"]["numpy"] == "1.26.4" and env["recbole_env"]["recbole"] == "1.2.1", env["recbole_env"]
    assert env["recbole_env"]["torch"] == env["torch"], "venv RecBole phải dùng torch của python chính"
    (LOGS / f"pip_freeze_recbole_{RUN_LABEL}_{time.strftime('%Y%m%d_%H%M%S')}.txt").write_text(
        sh([RB_PY, "-m", "pip", "freeze"]), encoding="utf-8")

# %%
# ===== Dữ liệu: chép vào repo (KHÔNG symlink: eval_05.inputs_sha256 cần đường dẫn nằm trong repo), kiểm sha256 =====
man_p = find_input("manifest_sha256.json")
DATA_ROOT = man_p.parent
man = json.loads(man_p.read_text(encoding="utf-8"))
bad = []
for rel, h in man["files"].items():
    src, dst = DATA_ROOT / rel, REPO / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    if sha256(dst) != h:
        bad.append(rel)
assert not bad, f"sha256 lệch: {bad}"
env["data_manifest_sha256"] = sha256(man_p)
env["data_packaged_from_commit"] = man["commit"]
env["data_files_checked"] = len(man["files"])
print(f"Đã kiểm {len(man['files'])} file dữ liệu: sha256 khớp")

# %%
# ===== (Tùy chọn) chạy tiếp từ phiên bản trước =====
# Mỗi việc lưu trạng thái chạy tiếp ở mỗi lần chấm val (train_05: last.pt; RecBole --group-eval: last_state.pth).
# Muốn chạy tiếp: "Add Input" → Your Work / Notebooks → output của phiên bản trước của CHÍNH notebook này, đặt RESUME = True,
# GIỮ NGUYÊN ACCOUNT, RUN_LABEL và JOBS (cấu hình phải trùng: script tự kiểm). Việc đã có result.json được bỏ qua.
RES = REPO / "results" / "kaggle" / RUN_LABEL
if RESUME:
    c = [p for p in INP.rglob(RUN_LABEL) if p.is_dir() and p.parent.name == "out" and (p / "results").is_dir()]
    assert len(c) == 1, f"cần đúng một thư mục .../out/{RUN_LABEL}/results trong input, thấy: {c}"
    prev = c[0]
    shutil.copytree(prev / "results", RES, dirs_exist_ok=True)
    shutil.copytree(prev / "logs", LOGS / "truoc", dirs_exist_ok=True)   # log các phiên bản trước, giữ nguyên
    prev_sum = json.loads((prev / "summary.json").read_text(encoding="utf-8"))
    env["resumed_from"] = {"path": str(prev), "prev_env": prev_sum.get("env"), "prev_jobs": prev_sum.get("jobs")}
    assert prev_sum["env"]["commit"] == EXPECT_COMMIT, "phiên bản trước chạy commit khác -> không chạy tiếp được"
    print("Chạy tiếp từ", prev)
(LOGS / f"env_{RUN_LABEL}_{time.strftime('%Y%m%d_%H%M%S')}.json").write_text(
    json.dumps(env, indent=2, ensure_ascii=False), encoding="utf-8")

# %%
# ===== Chạy các việc (ngắt khi tới JOB_DEADLINE_H, trạng thái chạy tiếp đã lưu ở lần chấm val gần nhất) =====
OUT = WORK / "out" / RUN_LABEL

def collect(done):
    if RES.exists():
        shutil.copytree(RES, OUT / "results", dirs_exist_ok=True)
    shutil.copytree(LOGS, OUT / "logs", dirs_exist_ok=True)
    summary = {"env": env, "jobs": done,
               "outputs_sha256": {str(p.relative_to(OUT)): sha256(p) for p in sorted(OUT.rglob("*"))
                                  if p.is_file() and p.name != "summary.json"}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

os.environ["PYTHONHASHSEED"] = "0"
os.environ["PYTHONIOENCODING"] = "utf-8"
done = []
for name, which, script, args in JOBS:
    run_dir = f"results/kaggle/{RUN_LABEL}/{name}"
    if (REPO / run_dir / "result.json").exists():
        done.append({"name": name, "status": "đã xong ở phiên bản trước"})
        print(done[-1], flush=True)
        continue
    left = JOB_DEADLINE_H - hours()
    if left < 0.25:
        done.append({"name": name, "status": f"không chạy: còn {left:.2f} giờ trước mốc {JOB_DEADLINE_H}"})
        print(done[-1], flush=True)
        continue
    py = sys.executable if which == "nhom" else RB_PY
    argv = [py, *(["-W", "ignore"] if which == "recbole" else []), script,
            *[x.replace("{GNN}", str(GNN_DIR)) for x in args], "--run-dir", run_dir]
    lp = LOGS / f"{name}_{RUN_LABEL}_{time.strftime('%Y%m%d_%H%M%S')}.log"
    assert not lp.exists()
    t0 = time.time()
    with open(lp, "w", encoding="utf-8") as f:
        f.write("$ " + " ".join(argv) + "\n")
        f.flush()
        try:
            p = subprocess.run(argv, cwd=REPO, stdout=f, stderr=subprocess.STDOUT, text=True, timeout=left * 3600)
            status = "xong" if p.returncode == 0 else f"lỗi (mã {p.returncode})"
        except subprocess.TimeoutExpired:
            status = f"ngắt ở mốc {JOB_DEADLINE_H} giờ -> chạy tiếp ở phiên bản sau (RESUME = True)"
    done.append({"name": name, "env": which, "script": script, "args": args, "status": status,
                 "result_json": (REPO / run_dir / "result.json").exists(),
                 "minutes": round((time.time() - t0) / 60, 1), "log": lp.name})
    print(done[-1], flush=True)
    collect(done)          # gom sau mỗi việc: phiên bị dừng giữa chừng vẫn còn phần đã xong
    if status.startswith("lỗi"):
        print("\n".join(lp.read_text(encoding="utf-8").splitlines()[-30:]))

# %%
# ===== Gom kết quả để lưu cùng phiên bản (checkpoint + result.json + log) =====
collect(done)
print(json.dumps(done, indent=2, ensure_ascii=False))
