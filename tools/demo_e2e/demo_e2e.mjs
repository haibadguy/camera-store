// demo_e2e.mjs -- Kiểm giao diện demo trên trình duyệt thật (Edge có sẵn, Playwright). Viết 28/10/2026.
// Script này chỉ lái trình duyệt; bật / tắt FastAPI, Spring, Vite là việc của ai/service/check_demo.py.
//
//   node tools/demo_e2e/demo_e2e.mjs --phase up   --web http://127.0.0.1:5173 --api http://127.0.0.1:8098/api --out <thư mục>
//   node tools/demo_e2e/demo_e2e.mjs --phase down --web ... --api ... --out <thư mục>
//
// phase up  : FastAPI + Spring đang chạy. Người 409, 47: danh sách trên màn hình phải trùng /api/recommend (hạng, tên,
//             câu giải thích); mở chi tiết một sản phẩm. Người không tồn tại: giao diện không có ô nhập user_id, nên
//             chặn yêu cầu của nút 409 ở tầng mạng và đổi user_id thành 99999 (Spring trả lỗi thật).
// phase down: đã tắt FastAPI, Spring vẫn chạy: bấm người 409, xem giao diện báo lỗi gì.
// Ghi ảnh màn hình vào <out>/screens/, kết quả vào <out>/e2e_<phase>.json; in từng bước ra stdout.

import { chromium } from "playwright-core";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, x, i, a) => (x.startsWith("--") ? [...acc, [x.slice(2), a[i + 1]]] : acc), []),
);
const { phase, web, api, out } = args;
if (!phase || !web || !api || !out) throw new Error("thiếu --phase / --web / --api / --out");
const screens = join(out, "screens");
mkdirSync(screens, { recursive: true });

const USERS = [{ id: 409, body: "Nikon D3100" }, { id: 47, body: "Nikon D500" }];
const UNKNOWN_USER = 99999;
const log = (s) => console.log(s);
const res = { phase, web, api, checks: {}, users: [], requests: [], console_errors: [] };

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

async function shot(name) {
  await page.screenshot({ path: join(screens, name), fullPage: true });
  log(`  ảnh ${name}`);
}

async function openPicker() {
  await page.goto(web);
  await page.getByRole("button", { name: "Tư vấn thiết bị" }).click();
  await page.getByRole("heading", { name: "Bạn đang tìm món đồ tiếp theo?" }).waitFor();
}

async function pickUser(body) {
  await page.locator(".demo-user-card", { hasText: body }).getByRole("button", { name: "Xem gợi ý" }).click();
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

async function checkUser({ id, body }, idx) {
  const expected = await (await fetch(`${api}/recommend?user_id=${id}&k=10&exclude=all_history`)).json();
  log(`người ${id} (${body}): API trả ${expected.items.length} mục, n_bodies ${expected.n_bodies}, ` +
      `ống bị chặn ${expected.mask.n_lenses_blocked}, bị gỡ khỏi top-10 ${expected.mask.n_blocked_in_topk_before_mask}`);
  await openPicker();
  if (idx === 0) await shot("02_chon_ho_so.png");
  await pickUser(body);
  const kind = await waitResult();
  const row = { user_id: id, kind, mismatches: [] };
  if (kind !== "list") {
    row.error = await errorShown();
    log(`  LỖI: giao diện báo lỗi ${JSON.stringify(row.error)}`);
    res.users.push(row);
    return false;
  }
  const cards = page.locator(".demo-recommendation-card");
  const n = await cards.count();
  const shown = [];
  for (let i = 0; i < n; i++) {
    const c = cards.nth(i);
    const exp = c.locator(".demo-explanation p");
    shown.push({
      rank: Number((await c.locator(".demo-rank").innerText()).replace("#", "")),
      title: (await c.locator("h2").innerText()).trim(),
      explanation: (await exp.count()) ? (await exp.innerText()).trim() : null,
    });
  }
  // Giao diện hiện câu khi verified, ngược lại hiện câu thay thế (RecommendationDemo.ExplanationPanel)
  const want = expected.items.map((it) => ({
    rank: it.rank,
    title: it.title.trim(),
    explanation: it.explanation
      ? (it.explanation.verified ? it.explanation.text.trim() : "Chưa đủ thông tin để giải thích gợi ý này.")
      : null,
  }));
  if (shown.length !== want.length) row.mismatches.push(`số mục: màn hình ${shown.length}, API ${want.length}`);
  want.forEach((w, i) => {
    const s = shown[i] ?? {};
    for (const k of ["rank", "title", "explanation"]) {
      if (s[k] !== w[k]) row.mismatches.push(`hạng ${w.rank} ${k}: màn hình ${JSON.stringify(s[k])}, API ${JSON.stringify(w[k])}`);
    }
  });
  const summary = await page.locator(".demo-summary-grid strong").allInnerTexts();
  const wantSummary = [expected.n_bodies, expected.mask.n_lenses_blocked, expected.items.length].map(String);
  if (JSON.stringify(summary) !== JSON.stringify(wantSummary)) {
    row.mismatches.push(`ô tóm tắt: màn hình ${summary}, API ${wantSummary}`);
  }
  const maskNote = page.locator("aside.demo-mask-note:not([role=alert]) p");
  row.mask_note = (await maskNote.count()) ? (await maskNote.innerText()).trim() : null;
  // Ghi chú mặt nạ hiện khi có ống bị gỡ khỏi top-k, nêu tên thân đầu tiên của /api/users/{id}/bodies
  const bodies = (await (await fetch(`${api}/users/${id}/bodies?exclude=all_history`)).json()).bodies;
  const wantNote = expected.mask.n_blocked_in_topk_before_mask > 0
    ? `Đã ẩn ${expected.mask.n_lenses_blocked} ống kính không lắp được trên ${bodies[0].title}.` : null;
  if (row.mask_note !== wantNote) {
    row.mismatches.push(`ghi chú mặt nạ: màn hình ${JSON.stringify(row.mask_note)}, mong đợi ${JSON.stringify(wantNote)}`);
  }
  row.n_items = n;
  row.n_explanations = shown.filter((s) => s.explanation !== null).length;
  row.shown = shown;
  log(`  màn hình: ${n} mục, ${row.n_explanations} câu giải thích, ô tóm tắt ${summary}, ghi chú mặt nạ: ${row.mask_note}`);
  log(`  so với API: ${row.mismatches.length ? "LỆCH " + JSON.stringify(row.mismatches) : "TRÙNG hạng, tên, câu giải thích, ô tóm tắt"}`);
  await shot(`0${3 + 2 * idx}_goi_y_${id}.png`);

  // Chi tiết: ống kính đầu tiên có câu giải thích (nếu không có thì hạng 1)
  const pos = Math.max(0, shown.findIndex((s) => s.explanation !== null));
  await cards.nth(pos).getByRole("button", { name: "Xem thông tin sản phẩm" }).click();
  await page.locator(".demo-detail-card").waitFor();
  await page.locator(".demo-detail-card [role=status]").waitFor({ state: "detached", timeout: 15000 });
  const detailError = page.locator(".demo-detail-card [role=alert]");
  if (await detailError.count()) row.mismatches.push(`trang chi tiết báo lỗi: ${await detailError.innerText()}`);
  const dts = await page.locator(".demo-attributes dt").allInnerTexts();
  const dds = await page.locator(".demo-attributes dd").allInnerTexts();
  row.detail = { rank: shown[pos].rank, title: (await page.locator(".demo-detail-card h1").innerText()).trim(),
                 attributes: Object.fromEntries(dts.map((t, i) => [t, dds[i]])) };
  log(`  chi tiết hạng ${row.detail.rank}: ${row.detail.title} | thuộc tính ${JSON.stringify(row.detail.attributes)}`);
  if (row.detail.title !== want[pos].title) row.mismatches.push("tên ở trang chi tiết khác danh sách");
  // Thuộc tính mong đợi từ /api/items/{id}, cùng cách ghi với RecommendationDemo (formatMount, formatFrame)
  const prod = await (await fetch(`${api}/items/${expected.items[pos].item_id}`)).json();
  const mountName = { nikon_f: "Nikon F", canon_ef: "Canon EF" }[prod.mount] ?? prod.mount;
  const frameName = { apsc: "APS-C", ff: "Full-frame" }[prod.khung] ?? prod.khung;
  const wantAttr = { "Loại sản phẩm": expected.items[pos].type_label };
  if (prod.mount) wantAttr["Ngàm"] = mountName;
  if (prod.khung) wantAttr["Định dạng"] = frameName;
  if (prod.usecases_label?.length) wantAttr["Phù hợp với"] = prod.usecases_label.join(", ");
  if (JSON.stringify(row.detail.attributes) !== JSON.stringify(wantAttr)) {
    row.mismatches.push(`thuộc tính chi tiết: màn hình ${JSON.stringify(row.detail.attributes)}, /api/items ${JSON.stringify(wantAttr)}`);
  }
  await shot(`0${4 + 2 * idx}_chi_tiet_${id}_hang${row.detail.rank}.png`);
  await page.getByRole("button", { name: "← Quay lại danh sách gợi ý" }).click();
  await page.locator(".demo-recommendation-card").first().waitFor();
  res.users.push(row);
  return row.mismatches.length === 0;
}

try {
  if (phase === "up") {
    await page.goto(web);
    await shot("01_trang_chu.png");
    for (const [i, u] of USERS.entries()) res.checks[`user_${u.id}`] = await checkUser(u, i);

    log(`người không tồn tại: đổi user_id của yêu cầu nút 409 thành ${UNKNOWN_USER} ở tầng mạng`);
    await openPicker();
    await page.route("**/api/recommend?*", (route) => {
      const u = new URL(route.request().url());
      u.searchParams.set("user_id", String(UNKNOWN_USER));
      route.continue({ url: u.toString() });
    });
    await page.route("**/api/users/*/bodies*", (route) => {
      const u = new URL(route.request().url());
      u.pathname = u.pathname.replace(/\/users\/\d+\//, `/users/${UNKNOWN_USER}/`);
      route.continue({ url: u.toString() });
    });
    await pickUser("Nikon D3100");
    const kind = await waitResult();
    await page.unrouteAll();
    res.unknown_user = { kind, ...(kind === "error" ? await errorShown() : {}) };
    log(`  giao diện: ${JSON.stringify(res.unknown_user)}`);
    await shot("07_nguoi_khong_ton_tai.png");
    res.checks.unknown_user_error_shown = kind === "error";
  } else {
    log("FastAPI đã tắt: bấm người 409");
    await openPicker();
    await pickUser("Nikon D3100");
    const kind = await waitResult();
    res.fastapi_down = { kind, ...(kind === "error" ? await errorShown() : {}) };
    log(`  giao diện: ${JSON.stringify(res.fastapi_down)}`);
    await shot("08_tat_fastapi.png");
    res.checks.fastapi_down_error_shown = kind === "error";
  }
} finally {
  // Yêu cầu gợi ý chỉ đi tới Spring (/api/recommend); trang không gọi dịch vụ nào khác trên máy (nên không gọi
  // thẳng FastAPI)
  res.checks.only_spring = res.requests.length > 0 && res.requests.every((r) => r.url.startsWith(api + "/"))
    && res.other_local_requests.length === 0;
  res.checks.no_console_error_except_http = res.console_errors.every((t) => t.includes("Failed to load resource"));
  log(`yêu cầu API của trang: ${JSON.stringify(res.requests)}`);
  log(`yêu cầu tới dịch vụ khác trên máy (phải rỗng): ${JSON.stringify(res.other_local_requests)}; ` +
      `máy chủ Internet: ${JSON.stringify(res.external_hosts)}`);
  log(`lỗi console: ${JSON.stringify(res.console_errors)}`);
  await browser.close();
  writeFileSync(join(out, `e2e_${phase}.json`), JSON.stringify(res, null, 2), "utf8");
  log(`KẾT QUẢ ${phase}: ${JSON.stringify(res.checks)}`);
}
