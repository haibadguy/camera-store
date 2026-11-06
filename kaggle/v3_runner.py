# %% [markdown]
# # camera-store v3 — chạy huấn luyện trên Kaggle (mẫu, chưa chạy)
#
# Notebook này được sinh từ `kaggle/v3_runner.py` (định dạng `# %%`) bởi `kaggle/build_kaggle_package.py`.
# Kế hoạch: `docs/reviews/v3_eval_plan.md`. Mỗi lần "Save Version → Save & Run All" là một **phiên bản** của
# notebook: code (commit git), dữ liệu (sha256), danh sách việc `JOBS`, log và kết quả đều nằm trong phiên bản đó.
#
# Quy tắc:
# 1. Code lấy từ dataset `camera-store-v3-code` (git bundle) và **checkout đúng commit** `EXPECT_COMMIT`; lệch thì dừng.
# 2. Dữ liệu lấy từ dataset `camera-store-v3-data`; **kiểm sha256 từng file** với `manifest_sha256.json`; lệch thì dừng.
# 3. Seed: mỗi việc truyền `--seed` cho script (script tự đặt seed torch / numpy như khi chạy ở máy nhóm).
# 4. Log: mỗi việc ghi `logs/<việc>_<RUN_LABEL>_<thời điểm>.log` (tên mới, không ghi đè) + log của chính script.
# 5. Không chấm test trên Kaggle (script huấn luyện chỉ nhận val). Chấm test làm ở máy nhóm, theo kế hoạch.

# %%
# ===== CẤU HÌNH CỦA PHIÊN BẢN NÀY (sửa trước khi Save Version) =====
EXPECT_COMMIT = "__COMMIT__"          # build_kaggle_package.py điền
RUN_LABEL = "kaggle_v3_lan1"          # nhãn lần chạy, đổi mỗi phiên bản
# Mỗi việc: (tên, đường dẫn script tính từ thư mục camera-store, danh sách tham số).
# Thư mục kết quả đặt trong results/kaggle/<RUN_LABEL>/<tên>. Ví dụ (KHÔNG phải lưới đã chốt):
JOBS = [
    # ("lightgcn_l2-1e-03_s1", "ai/pipeline/05b_lightgcn_train.py",
    #  ["--l2", "1e-3", "--seed", "1", "--max-epoch", "1000"]),
]
INSTALL_EXACT_VERSIONS = True         # cài đúng torch / PyG / numpy / scipy như ai/requirements-lock.txt (cần Internet)
TIME_BUDGET_H = 11.0                  # phiên Kaggle tối đa ~12 giờ (chưa kiểm chứng); không bắt đầu việc mới sau mốc này

# %%
import hashlib, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path

T_START = time.time()
INP = Path("/kaggle/input")
WORK = Path("/kaggle/working")
REPO = WORK / "camera-store"
LOGS = WORK / "logs"
LOGS.mkdir(exist_ok=True)

def sh(cmd, **kw):
    print("$", cmd if isinstance(cmd, str) else " ".join(map(str, cmd)), flush=True)
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=True, text=True, capture_output=True, **kw).stdout

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def find_input(name):
    c = [p for p in INP.rglob(name)]
    assert len(c) == 1, f"không tìm thấy đúng một {name} trong {INP}: {c}"
    return c[0]

# %%
# ===== Môi trường =====
env = {"python": platform.python_version(), "time_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}
try:
    env["nvidia_smi"] = sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader")
except Exception as e:  # không có GPU
    env["nvidia_smi"] = f"không có GPU: {e}"
print(json.dumps(env, indent=2, ensure_ascii=False))

# %%
# ===== Code: clone git bundle, checkout đúng commit =====
bundle = find_input("camera-store.bundle")
if REPO.exists():
    shutil.rmtree(REPO)
sh(["git", "clone", "--quiet", str(bundle), str(REPO)])
sh(["git", "-C", str(REPO), "checkout", "--quiet", EXPECT_COMMIT])
head = sh(["git", "-C", str(REPO), "rev-parse", "HEAD"]).strip()
assert head == EXPECT_COMMIT, f"commit {head} khác {EXPECT_COMMIT}"
env["commit"] = head
print("commit", head)

# %%
# ===== Thư viện =====
if INSTALL_EXACT_VERSIONS:
    req = REPO / "kaggle" / "requirements-kaggle.txt"
    print(sh([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])[-2000:])
import torch  # noqa: E402
env["torch"] = torch.__version__
env["cuda_available"] = torch.cuda.is_available()
env["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
(LOGS / f"pip_freeze_{RUN_LABEL}.txt").write_text(sh([sys.executable, "-m", "pip", "freeze"]), encoding="utf-8")
print(json.dumps(env, indent=2, ensure_ascii=False))

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
(LOGS / f"env_{RUN_LABEL}.json").write_text(json.dumps(env, indent=2, ensure_ascii=False), encoding="utf-8")

# %%
# ===== (Tùy chọn) chạy tiếp từ phiên bản trước =====
# Phiên Kaggle có giới hạn giờ. train_05.run lưu last.pt ở mỗi lần chấm val và tự chạy tiếp nếu thấy last.pt.
# Muốn chạy tiếp: thêm output của phiên bản trước làm input, đặt RESUME_FROM = thư mục ".../out/<RUN_LABEL cũ>/results",
# giữ NGUYÊN RUN_LABEL và JOBS như phiên bản trước (cấu hình phải trùng, train_05 kiểm config.json).
RESUME_FROM = None
if RESUME_FROM:
    shutil.copytree(Path(RESUME_FROM), REPO / "results" / "kaggle" / RUN_LABEL, dirs_exist_ok=True)
    env["resumed_from"] = str(RESUME_FROM)

# %%
# ===== Chạy các việc =====
os.environ["PYTHONHASHSEED"] = "0"
done = []
for name, script, args in JOBS:
    if (time.time() - T_START) / 3600 > TIME_BUDGET_H:
        print(f"Hết ngân sách {TIME_BUDGET_H} giờ, không chạy {name}")
        break
    run_dir = f"results/kaggle/{RUN_LABEL}/{name}"
    lp = LOGS / f"{name}_{RUN_LABEL}_{time.strftime('%Y%m%d_%H%M%S')}.log"
    assert not lp.exists()
    t0 = time.time()
    with open(lp, "w", encoding="utf-8") as f:
        p = subprocess.run([sys.executable, script, *args, "--run-dir", run_dir], cwd=REPO, stdout=f,
                           stderr=subprocess.STDOUT, text=True)
    done.append({"name": name, "script": script, "args": args, "returncode": p.returncode,
                 "minutes": round((time.time() - t0) / 60, 1), "log": lp.name})
    print(done[-1], flush=True)

# %%
# ===== Gom kết quả để lưu cùng phiên bản (checkpoint + result.json + log) =====
OUT = WORK / "out" / RUN_LABEL
src = REPO / "results" / "kaggle" / RUN_LABEL
if src.exists():
    shutil.copytree(src, OUT / "results", dirs_exist_ok=True)
shutil.copytree(LOGS, OUT / "logs", dirs_exist_ok=True)
summary = {"env": env, "jobs": done,
           "outputs_sha256": {str(p.relative_to(OUT)): sha256(p) for p in sorted(OUT.rglob("*")) if p.is_file()}}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(done, indent=2, ensure_ascii=False))
