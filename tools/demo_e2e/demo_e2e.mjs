// demo_e2e.mjs -- Kiểm giao diện demo trên trình duyệt thật (Edge có sẵn, Playwright). Viết 28/10/2026, sửa theo phản
// biện E:\DATN\reviews\redteam_code_lan1.md (S1, S4, D1, D4, P1) cùng ngày.
// Script này chỉ lái trình duyệt; bật / tắt FastAPI, Spring, Vite là việc của ai/service/check_demo.py.
//
//   node tools/demo_e2e/demo_e2e.mjs --phase up   --web http://127.0.0.1:5173 --api http://127.0.0.1:8098/api --out <thư mục>
//   node tools/demo_e2e/demo_e2e.mjs --phase down --web ... --api ... --out <thư mục>
//   node tools/demo_e2e/demo_e2e.mjs --phase mock --web <Vite chế độ dữ liệu mẫu> --api ... --out <thư mục>
//
// phase up  : FastAPI + Spring đang chạy. Người 409, 47 (nút chọn nhanh) và 178, 1476, 0 (ô nhập user_id): danh sách
//             trùng /api/recommend; ghi chú mặt nạ đúng câu Nam chốt 28/10, điền từ trường của API (n_lenses_blocked,
//             n_blocked_in_topk_before_mask, blocked_in_topk_before_mask, mọi thân của /api/users/{id}/bodies) và ống
//             bị bỏ ra phải không lắp được trên MỌI thân theo /api/compat (kiểm độc lập ý nghĩa QĐ 4-9); 409, 47 mở
//             chi tiết. Chữ cấm trên trang (hợp đồng 1.3). Người 99999 nhập vào ô. Bơm một câu verified = false.
// phase down: đã tắt FastAPI, Spring vẫn chạy: bấm người 409, xem giao diện báo lỗi gì.
// phase mock: Vite chế độ dữ liệu mẫu: nhãn "Dữ liệu mẫu" hiện, danh sách 409 trùng frontend/src/mock/recommend_409.json.
// Ghi ảnh màn hình vào <out>/screens/, kết quả vào <out>/e2e_<phase>.json; in từng bước ra stdout.

import { chromium } from "playwright-core";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, x, i, a) => (x.startsWith("--") ? [...acc, [x.slice(2), a[i + 1]]] : acc), []),
);
const { phase, web, api, out } = args;
if (!phase || !web || !api || !out) throw new Error("thiếu --phase / --web / --api / --out");
const screens = join(out, "screens");
mkdirSync(screens, { recursive: true });
const MOCK_DIR = fileURLToPath(new URL("../../frontend/src/mock/", import.meta.url));

// Người kiểm: nút chọn nhanh (409, 47) hoặc ô nhập; 178 nhiều hệ máy, 1476 có thân ngoài M (mặt nạ không chặn gì,
// ai/service/count_bodies_outside_m.py), 0 không có thân
const USERS = [
  { id: 409, how: "quick", detail: true }, { id: 47, how: "quick", detail: true },
  { id: 178, how: "input" }, { id: 1476, how: "input" }, { id: 0, how: "input" },
];
const UNKNOWN_USER = 99999;
const EXPECTED_ERROR = { unknown: "Không tìm thấy người dùng này.", down: "Dịch vụ gợi ý đang tạm dừng, thử lại sau." };
// Chữ trái hợp đồng 1.3 / quyết định của Nam 28/10 (dữ liệu là đánh giá, không phải đang dùng; all_history loại hẳn
// chứ không "ưu tiên"; không gắn "Gợi ý phù hợp" cho mọi mục; giải thích là post-hoc, không phải lý do mô hình chọn: chương 2, độ trung thực chưa chứng minh). So không phân biệt hoa thường.
const BANNED = ["đang dùng", "lịch sử sử dụng", "ưu tiên", "Gợi ý phù hợp", "vì sao gợi ý", "được chọn vì", "lý do gợi ý",
  "vì sao sản phẩm này phù hợp", "lý do sản phẩm phù hợp"];
const TECHNICAL_UI_WORDS = ["QĐ 4-9", "item_id", "contract", "nikon_f", "bảng tương thích", "điểm của mô hình", "run_demo.ps1", "HTTP"];
const log = (s) => console.log(s);
const res = { phase, web, api, checks: {}, users: [], requests: [], console_errors: [] };
const getJson = async (path) => (await fetch(`${api}${path}`)).json();

const browser = await chromium.launch({ channel: "msedge", headless: true });
res.browser = `msedge ${browser.version()}`;
const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
page.on("console", (m) => { if (m.type() === "error") res.console_errors.push(m.text()); });
page.on("pageerror", (e) => res.console_errors.push(`pageerror: ${e.message}`));
// Yêu cầu tới máy này (127.0.0.1 / localhost) ngoài Vite và Spring, vd gọi thẳng FastAPI, là sai kiến trúc.
// Yêu cầu ra Internet (ảnh unsplash của trang catalog) chỉ ghi lại.
const allowedOrigins = [new URL(web).origin, new URL(api).origin];
res.other_local_requests = [];
res.external_hosts = [];
page.on("request", (r) => {
  const u = new URL(r.url());
  if (!u.protocol.startsWith("http") || allowedOrigins.includes(u.origin)) return;
  if (["127.0.0.1", "localhost", "[::1]"].includes(u.hostname)) res.other_local_requests.push(r.url());
  else if (!res.external_hosts.includes(u.host)) res.external_hosts.push(u.host);
});
page.on("response", async (r) => {
  if (!new URL(r.url()).pathname.startsWith("/api/")) return;   // chỉ yêu cầu API, không tính file mã của Vite
  let body = null;
  try { body = await r.json(); } catch { /* không phải JSON */ }
  res.requests.push({ url: r.url(), status: r.status(), error: body?.error ?? null });
});

let shotNo = 0;
async function shot(name) {
  shotNo += 1;
  const file = `${phase === "up" ? "" : phase + "_"}${String(shotNo).padStart(2, "0")}_${name}.png`;
  await page.screenshot({ path: join(screens, file), fullPage: true });
  log(`  ảnh ${file}`);
}

async function openPicker() {
  await page.goto(web);
  await page.getByRole("button", { name: "Tư vấn thiết bị" }).click();
  await page.getByRole("heading", { name: "Chọn hồ sơ để bắt đầu" }).waitFor();
}

async function pickUser(id, how) {
  if (how === "quick") {
    await page.locator(".demo-user-card", { has: page.getByRole("heading", { name: `Hồ sơ ${id}`, exact: true }) })
      .getByRole("button", { name: "Xem các lựa chọn" }).click();
  } else {
    await page.locator("#demo-user-id").fill(String(id));
    await page.getByRole("form", { name: "Tìm hồ sơ khác" }).getByRole("button", { name: "Tìm gợi ý" }).click();
  }
}

// Đợi hết "Đang tải"; trả về "list" (có danh sách) hoặc "error" (có khung lỗi)
async function waitResult() {
  await page.locator(".demo-recommendation-card, [role=alert]").first().waitFor({ timeout: 15000 });
  return (await page.locator("[role=alert]").count()) ? "error" : "list";
}

async function errorShown() {
  const alert = page.locator("[role=alert]");
  return { title: (await alert.locator("strong").innerText()).trim(), message: (await alert.locator("p").innerText()).trim() };
}

async function bannedWords(where, row) {
  const text = await page.locator("main").innerText();
  for (const w of BANNED) if (text.toLowerCase().includes(w.toLowerCase())) row.mismatches.push(`${where}: có chữ "${w}"`);
  for (const w of TECHNICAL_UI_WORDS) if (text.includes(w)) row.mismatches.push(`${where}: còn thuật ngữ kỹ thuật "${w}"`);
  if (phase !== "mock" && await page.getByRole("note", { name: "Bản xem trước" }).count()) {
    row.mismatches.push(`${where}: chế độ api mà hiện nhãn "Bản xem trước"`);
  }
}

async function readList() {
  const cards = page.locator(".demo-recommendation-card");
  const shown = [];
  for (let i = 0; i < await cards.count(); i++) {
    const c = cards.nth(i);
    const exp = c.locator(".demo-explanation p");
    shown.push({
      rank: Number(await c.locator(".demo-rank strong").innerText()),
      title: (await c.locator("h2").innerText()).trim(),
      explanation: (await exp.count()) ? (await exp.innerText()).trim() : null,
    });
  }
  return shown;
}

function compareList(shown, items, row) {
  // Giao diện chỉ hiện lời giải thích đã được xác minh.
  const want = items.map((it) => ({
    rank: it.rank, title: it.title.trim(),
    explanation: it.explanation?.verified ? formatExplanation(it.explanation.text) : null,
  }));
  if (shown.length !== want.length) row.mismatches.push(`số mục: màn hình ${shown.length}, dữ liệu ${want.length}`);
  want.forEach((w, i) => {
    const s = shown[i] ?? {};
    for (const k of ["rank", "title", "explanation"]) {
      if (s[k] !== w[k]) row.mismatches.push(`hạng ${w.rank} ${k}: màn hình ${JSON.stringify(s[k])}, dữ liệu ${JSON.stringify(w[k])}`);
    }
  });
  return want;
}

function formatCameraName(title) {
  return title.match(/\bNikon\s+D\d+[A-Z]*/i)?.[0] ?? title.split(" (")[0].split(" with ")[0];
}

function joinNames(names) {
  if (names.length <= 1) return names[0] ?? "máy ảnh của bạn";
  return `${names.slice(0, -1).join(", ")} và ${names[names.length - 1]}`;
}

function formatExplanation(text) {
  return text.replace(/^Gợi ý .*?\bvì\s+ống này\s+/i, "Ống kính này ")
    .replace(/\s*\(ngàm [^)]+\),?/gi, "")
    .replace(/\b(Nikon\s+D\d+[A-Z]*)\b.*?(?=\s+bạn đã đánh giá)/gi, "$1")
    .replace(/\s+\/\s+/g, " và ")
    .replace(/\s+,/g, ",").replace(/đánh giá\s+và/g, "đánh giá và").trim();
}

// Câu ghi chú mặt nạ mong đợi: đúng câu Nam chốt 28/10, điền từ trường của API (không theo code React)
function expectedMaskSentences(rec, bodies) {
  const n = rec.mask.n_lenses_blocked;
  const m = rec.mask.n_blocked_in_topk_before_mask;
  const names = bodies.map((body) => formatCameraName(body.title));
  const machineLabel = bodies.length > 1 ? `các máy ${joinNames(names)}` : `máy ${joinNames(names)}`;
  const want = [];
  if (bodies.length === 0) want.push("Hồ sơ này chưa có máy ảnh nên hệ thống chưa ẩn ống kính nào.");
  if (n > 0) want.push(`Đã ẩn ${n} ống kính không lắp được trên ${machineLabel} của bạn.`);
  const outside = bodies.filter((b) => b.in_matrix === false);
  if (bodies.length > 0 && n === 0 && outside.length === 0) want.push(`Không có ống kính nào cần ẩn với ${machineLabel} của bạn.`);
  if (bodies.length > 0 && n === 0 && outside.length > 0) want.push(`Chưa đủ dữ liệu để kiểm tra ống kính phù hợp với ${machineLabel}.`);
  if (m > 0) want.push(`${m} sản phẩm không tương thích đã được loại khỏi kết quả đang xem.`);
  return want;
}

async function checkUser({ id, how, detail }) {
  const rec = await getJson(`/recommend?user_id=${id}&k=10&exclude=all_history`);
  const bodies = (await getJson(`/users/${id}/bodies?exclude=all_history`)).bodies;
  log(`người ${id} (${how === "quick" ? "nút chọn nhanh" : "ô nhập"}): API ${rec.items.length} mục, ${bodies.length} thân ` +
      `(ngoài M: ${bodies.filter((b) => b.in_matrix === false).length}), ống bị chặn ${rec.mask.n_lenses_blocked}, ` +
      `bị bỏ khỏi top-10 ${rec.mask.n_blocked_in_topk_before_mask}`);
  await openPicker();
  const row = { user_id: id, how, mismatches: [] };
  if (id === 409) {
    await bannedWords("trang chọn người", row);
    // Thân ghi trên nút chọn nhanh phải là thân của người đó theo /api/users/{id}/bodies
    for (const u of [409, 47]) {
      const card = page.locator(".demo-user-card", { has: page.getByRole("heading", { name: `Hồ sơ ${u}`, exact: true }) });
      const names = (await card.locator(".demo-profile-devices span").allInnerTexts()).map((x) => x.trim());
      const titles = (await getJson(`/users/${u}/bodies?exclude=all_history`)).bodies.map((b) => formatCameraName(b.title));
      if (JSON.stringify(names) !== JSON.stringify(titles)) {
        row.mismatches.push(`nút chọn nhanh ${u}: ghi ${JSON.stringify(names)}, API ${JSON.stringify(titles)}`);
      }
    }
    await shot("chon_nguoi_dung");
  }
  await pickUser(id, how);
  row.kind = await waitResult();
  if (row.kind !== "list") {
    row.error = await errorShown();
    log(`  LỖI: giao diện báo lỗi ${JSON.stringify(row.error)}`);
    res.users.push(row);
    return false;
  }
  const shown = await readList();
  const want = compareList(shown, rec.items, row);
  const eyebrow = (await page.locator(".demo-eyebrow").first().innerText()).trim();
  if (eyebrow.toLowerCase() !== `hồ sơ ${id}`) row.mismatches.push(`nhãn hồ sơ: ${eyebrow}`);
  const summary = await page.locator(".demo-summary-grid strong").allInnerTexts();
  const wantSummary = [bodies.length, rec.mask.n_lenses_blocked, rec.items.length].map(String);
  if (JSON.stringify(summary) !== JSON.stringify(wantSummary)) row.mismatches.push(`ô tóm tắt: màn hình ${summary}, API ${wantSummary}`);

  // Ghi chú mặt nạ: mọi thân, đúng các câu, không thừa câu
  const note = page.getByRole("complementary", { name: "Ống kính phù hợp với máy của bạn" });
  const noteBodies = await note.locator(".demo-profile-devices span").allInnerTexts();
  if (JSON.stringify(noteBodies.map((t) => t.trim())) !== JSON.stringify(bodies.map((b) => formatCameraName(b.title)))) {
    row.mismatches.push(`thân trong ghi chú: ${JSON.stringify(noteBodies)}, API ${JSON.stringify(bodies.map((b) => formatCameraName(b.title)))}`);
  }
  row.mask_sentences = (await note.locator(":scope > p").allInnerTexts()).map((t) => t.trim());
  const wantSentences = expectedMaskSentences(rec, bodies);
  if (JSON.stringify(row.mask_sentences) !== JSON.stringify(wantSentences)) {
    row.mismatches.push(`câu mặt nạ: màn hình ${JSON.stringify(row.mask_sentences)}, mong đợi ${JSON.stringify(wantSentences)}`);
  }
  // Kiểm độc lập ý nghĩa: ống bị bỏ ra không lắp được (M = 0) trên MỌI thân, và không có trong danh sách
  row.removed_check = [];
  for (const lens of rec.mask.blocked_in_topk_before_mask) {
    const ms = [];
    for (const b of bodies) ms.push((await getJson(`/compat?body_id=${b.item_id}&lens_id=${lens.item_id}`)).m);
    row.removed_check.push({ lens: lens.item_id, m_per_body: ms });
    if (!ms.length || ms.some((m) => m !== 0)) row.mismatches.push(`ống bị bỏ ${lens.item_id} có thân lắp được: m ${ms}`);
    if (shown.some((s) => s.title === lens.title.trim())) row.mismatches.push(`ống bị bỏ ${lens.item_id} vẫn trong danh sách`);
  }
  await bannedWords(`danh sách người ${id}`, row);
  row.n_items = shown.length;
  row.n_explanations = shown.filter((s) => s.explanation !== null).length;
  row.shown = shown;
  log(`  màn hình: ${shown.length} mục, ${row.n_explanations} câu giải thích, ô tóm tắt ${summary}`);
  log(`  thân trong ghi chú: ${JSON.stringify(noteBodies)}`);
  log(`  câu mặt nạ: ${JSON.stringify(row.mask_sentences)}; ống bị bỏ / m theo từng thân: ${JSON.stringify(row.removed_check)}`);
  await shot(`goi_y_${id}`);

  if (detail) {
    // Chi tiết: ống kính đầu tiên có câu giải thích (nếu không có thì hạng 1)
    const pos = Math.max(0, shown.findIndex((s) => s.explanation !== null));
    await page.locator(".demo-recommendation-card").nth(pos).getByRole("button", { name: "Xem thông tin sản phẩm" }).click();
    await page.locator(".demo-detail-card").waitFor();
    await page.locator(".demo-detail-card [role=status]").waitFor({ state: "detached", timeout: 15000 });
    const detailError = page.locator(".demo-detail-card [role=alert]");
    if (await detailError.count()) row.mismatches.push(`trang chi tiết báo lỗi: ${await detailError.innerText()}`);
    const dts = await page.locator(".demo-attributes dt").allInnerTexts();
    const dds = await page.locator(".demo-attributes dd").allInnerTexts();
    row.detail = { rank: shown[pos].rank, title: (await page.locator(".demo-detail-card h1").innerText()).trim(),
                   attributes: Object.fromEntries(dts.map((t, i) => [t, dds[i]])) };
    if (row.detail.title !== want[pos].title) row.mismatches.push("tên ở trang chi tiết khác danh sách");
    // Thuộc tính mong đợi từ /api/items/{id}
    const prod = await getJson(`/items/${rec.items[pos].item_id}`);
    const wantAttr = { "Loại sản phẩm": rec.items[pos].type_label };
    if (prod.mount) wantAttr["Loại ngàm"] = { nikon_f: "Nikon F", canon_ef: "Canon EF", khong_co: "Không áp dụng" }[prod.mount] ?? prod.mount;
    if (prod.khung) wantAttr["Kích thước cảm biến"] = { apsc: "APS-C", ff: "Full-frame" }[prod.khung] ?? prod.khung;
    if (prod.focal_mm) wantAttr["Tiêu cự"] = prod.focal_mm.min === prod.focal_mm.max
      ? `${prod.focal_mm.min} mm` : `${prod.focal_mm.min}–${prod.focal_mm.max} mm`;
    if (prod.max_aperture_f) wantAttr["Khẩu độ tối đa"] = prod.max_aperture_f.at_min_focal === prod.max_aperture_f.at_max_focal
      ? `f/${prod.max_aperture_f.at_min_focal}` : `f/${prod.max_aperture_f.at_min_focal}–${prod.max_aperture_f.at_max_focal}`;
    if (prod.usecases_label?.length) wantAttr["Phù hợp để chụp"] = prod.usecases_label.join(", ");
    if (JSON.stringify(row.detail.attributes) !== JSON.stringify(wantAttr)) {
      row.mismatches.push(`thuộc tính chi tiết: màn hình ${JSON.stringify(row.detail.attributes)}, /api/items ${JSON.stringify(wantAttr)}`);
    }
    await bannedWords(`chi tiết người ${id}`, row);
    log(`  chi tiết hạng ${row.detail.rank}: ${row.detail.title} | thuộc tính ${JSON.stringify(row.detail.attributes)}`);
    await shot(`chi_tiet_${id}_hang${row.detail.rank}`);
  }
  log(`  so với API: ${row.mismatches.length ? "LỆCH " + JSON.stringify(row.mismatches) : "TRÙNG"}`);
  res.users.push(row);
  return row.mismatches.length === 0;
}

// Bơm một câu verified = false vào phản hồi thật của người 47: giao diện phải ẩn câu chưa được xác minh.
async function checkVerifiedFalse() {
  await openPicker();
  let injected = null;
  await page.route("**/api/recommend?*", async (route) => {
    const resp = await route.fetch();
    const j = await resp.json();
    const it = j.items.find((x) => x.explanation);
    injected = { rank: it.rank, text: it.explanation.text };
    it.explanation.verified = false;
    it.explanation.errors = ["kiểm thử: bơm verified = false"];
    await route.fulfill({ response: resp, json: j });
  });
  await pickUser(47, "quick");
  await waitResult();
  await page.unrouteAll();
  const shown = await readList();
  const s = shown.find((x) => x.rank === injected.rank);
  const ok = s?.explanation === null && !shown.some((x) => x.explanation === injected.text);
  res.verified_false = { injected_rank: injected.rank, shown: s?.explanation };
  log(`bơm verified = false ở hạng ${injected.rank} của người 47: màn hình "${s?.explanation}" -> ${ok ? "ĐÚNG" : "SAI"}`);
  await shot("verified_false_bom_thu");
  return ok;
}

async function checkCatalogSurface() {
  await page.goto(web);
  const row = { mismatches: [] };
  const cardCount = await page.locator(".product-card").count();
  if (cardCount !== 28) row.mismatches.push(`catalog có ${cardCount} thẻ, cần đúng 28`);

  for (const profile of ["409", "47"]) {
    await page.locator("#catalog-profile").selectOption(profile);
    try {
      await page.locator(".compatibility-badge").first().waitFor({ timeout: 10000 });
    } catch {
      row.mismatches.push(`không hiện badge compatibility sau khi chọn User ${profile}`);
    }
    if (await page.locator("#catalog-profile").inputValue() !== profile) {
      row.mismatches.push(`selector profile không giữ User ${profile}`);
    }
  }

  await page.getByRole("button", { name: "Bắt đầu tư vấn ngay" }).click();
  if (await page.getByRole("heading", { name: "Lọc thiết bị theo nhu cầu" }).count() !== 1) {
    row.mismatches.push("wizard catalog không mở đúng tiêu đề");
  }
  await page.locator(".dialog-overlay").first().click({ position: { x: 2, y: 2 } });
  res.catalog = { card_count: cardCount, profiles: ["409", "47"], mismatches: row.mismatches };
  log(`catalog: ${cardCount} thẻ, profiles 409/47 compatibility và wizard: ${row.mismatches.length ? "LỆCH " + JSON.stringify(row.mismatches) : "ĐẠT"}`);
  await shot("catalog_surface");
  return row.mismatches.length === 0;
}

try {
  if (phase === "up") {
    await page.goto(web);
    await shot("trang_chu");
    res.checks.catalog_surface = await checkCatalogSurface();
    for (const u of USERS) res.checks[`user_${u.id}`] = await checkUser(u);

    log(`người không tồn tại: nhập ${UNKNOWN_USER} vào ô mã người dùng`);
    await openPicker();
    await pickUser(UNKNOWN_USER, "input");
    const kind = await waitResult();
    res.unknown_user = { kind, ...(kind === "error" ? await errorShown() : {}) };
    log(`  giao diện: ${JSON.stringify(res.unknown_user)}`);
    await shot("nguoi_khong_ton_tai");
    res.checks.unknown_user_message = res.unknown_user.message === EXPECTED_ERROR.unknown;

    log("ô nhập sai dạng: abc");
    await openPicker();
    await page.locator("#demo-user-id").fill("abc");
    await page.getByRole("form", { name: "Tìm hồ sơ khác" }).getByRole("button", { name: "Tìm gợi ý" }).click();
    const inputAlert = page.getByRole("form", { name: "Tìm hồ sơ khác" }).getByRole("alert");
    res.bad_input = (await inputAlert.count()) ? (await inputAlert.innerText()).trim() : null;
    log(`  giao diện: ${JSON.stringify(res.bad_input)}`);
    res.checks.bad_input_rejected = res.bad_input !== null
      && (await page.getByRole("heading", { name: "Chọn hồ sơ để bắt đầu" }).count()) === 1;

    res.checks.verified_false_hidden = await checkVerifiedFalse();
  } else if (phase === "down") {
    log("FastAPI đã tắt: bấm người 409");
    await openPicker();
    await pickUser(409, "quick");
    const kind = await waitResult();
    res.fastapi_down = { kind, ...(kind === "error" ? await errorShown() : {}) };
    log(`  giao diện: ${JSON.stringify(res.fastapi_down)}`);
    await shot("tat_fastapi");
    res.checks.fastapi_down_message = res.fastapi_down.message === EXPECTED_ERROR.down;
  } else {
    log("Vite chế độ dữ liệu mẫu: nhãn và danh sách người 409");
    await openPicker();
    const labelOnPicker = await page.getByRole("note", { name: "Bản xem trước" }).isVisible();
    const row = { user_id: 409, how: "mock", mismatches: [] };
    await bannedWords("trang chọn hồ sơ", row);
    await shot("du_lieu_mau_chon_nguoi");
    await pickUser(409, "quick");
    await waitResult();
    const labelOnList = await page.getByRole("note", { name: "Bản xem trước" }).isVisible();
    compareList(await readList(), JSON.parse(readFileSync(join(MOCK_DIR, "recommend_409.json"), "utf8")).items, row);
    await bannedWords("danh sách gợi ý", row);
    const backBox = await page.getByRole("button", { name: "Chọn hồ sơ khác" }).boundingBox();
    const eyebrowBox = await page.locator(".demo-eyebrow").first().boundingBox();
    const backButtonSeparated = Boolean(backBox && eyebrowBox && backBox.y + backBox.height <= eyebrowBox.y);
    if (!backButtonSeparated) row.mismatches.push("nút Chọn hồ sơ khác còn chồng lên nội dung bên cạnh");
    log(`  nhãn "Bản xem trước": trang chọn ${labelOnPicker}, danh sách ${labelOnList}; so với recommend_409.json: ` +
        `${row.mismatches.length ? "LỆCH " + JSON.stringify(row.mismatches) : "TRÙNG"}`);
    await shot("du_lieu_mau_goi_y_409");
    await page.locator(".demo-recommendation-card").first().getByRole("button", { name: "Xem thông tin sản phẩm" }).click();
    await page.locator(".demo-detail-card").waitFor();
    await bannedWords("chi tiết sản phẩm", row);
    const detailBackVisible = await page.getByRole("button", { name: "Quay lại danh sách gợi ý" }).isVisible();
    if (!detailBackVisible) row.mismatches.push("trang chi tiết thiếu nút quay lại danh sách");
    await shot("du_lieu_mau_chi_tiet_409");
    res.mock = { label_on_picker: labelOnPicker, label_on_list: labelOnList, back_button_separated: backButtonSeparated,
                 detail_back_visible: detailBackVisible, mismatches: row.mismatches };
    res.checks.mock_label_and_list = labelOnPicker && labelOnList && backButtonSeparated && detailBackVisible && row.mismatches.length === 0
      && res.requests.length === 0;
  }
} finally {
  // Chế độ api: yêu cầu chỉ đi tới Spring (/api/...), không gọi dịch vụ nào khác trên máy (nên không gọi thẳng FastAPI).
  // Chế độ mẫu: không có yêu cầu API nào.
  res.checks.only_spring = (phase === "mock" ? res.requests.length === 0
    : res.requests.length > 0 && res.requests.every((r) => r.url.startsWith(api + "/"))) && res.other_local_requests.length === 0;
  res.checks.no_console_error_except_http = res.console_errors.every((t) => t.includes("Failed to load resource"));
  log(`yêu cầu API của trang: ${res.requests.length} (${JSON.stringify([...new Set(res.requests.map((r) => r.status))])})`);
  log(`yêu cầu tới dịch vụ khác trên máy (phải rỗng): ${JSON.stringify(res.other_local_requests)}; ` +
      `máy chủ Internet: ${JSON.stringify(res.external_hosts)}`);
  log(`lỗi console: ${JSON.stringify(res.console_errors)}`);
  await browser.close();
  writeFileSync(join(out, `e2e_${phase}.json`), JSON.stringify(res, null, 2), "utf8");
  log(`KẾT QUẢ ${phase}: ${JSON.stringify(res.checks)}`);
}
