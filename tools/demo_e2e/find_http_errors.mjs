// find_http_errors.mjs -- Tìm tài nguyên nào trả lỗi HTTP (>= 400) khi mở trang demo. Viết 02/11/2026, để trả lời câu
// hỏi của phản biện E:\DATN\reviews\redteam_ch123_lan2.md mục 1.2: lỗi console "404 (Not Found)" ở cả ba pha của
// check_demo (kể cả pha dữ liệu mẫu, không gọi API nào) là tài nguyên gì. demo_e2e.mjs chỉ ghi chữ của lỗi console,
// không ghi địa chỉ; script này ghi địa chỉ của mọi phản hồi lỗi.
// Chỉ lái trình duyệt; bật / tắt dịch vụ là việc của ai/service/check_run_demo.py.
//
//   node tools/demo_e2e/find_http_errors.mjs --web http://127.0.0.1:5173 --out <file json>
//
// Các bước giống phần đầu của demo_e2e.mjs: mở trang chủ, bấm "Tư vấn thiết bị", chọn nhanh người 409, đợi danh sách
// (hoặc khung lỗi).

import { chromium } from "playwright-core";
import { writeFileSync } from "node:fs";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, x, i, a) => (x.startsWith("--") ? [...acc, [x.slice(2), a[i + 1]]] : acc), []),
);
const { web, out } = args;
if (!web || !out) throw new Error("thiếu --web / --out");
const log = (s) => console.log(s);
const res = { web, steps: [], http_errors: [], request_failed: [], console_errors: [] };
let step = "";

const browser = await chromium.launch({ channel: "msedge", headless: true });
res.browser = `msedge ${browser.version()}`;
const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
page.on("console", (m) => { if (m.type() === "error") res.console_errors.push({ step, text: m.text(), url: m.location()?.url ?? null }); });
page.on("pageerror", (e) => res.console_errors.push({ step, text: `pageerror: ${e.message}`, url: null }));
page.on("response", (r) => {
  if (r.status() >= 400) res.http_errors.push({ step, url: r.url(), status: r.status(), status_text: r.statusText(), resource_type: r.request().resourceType() });
});
page.on("requestfailed", (r) => res.request_failed.push({ step, url: r.url(), error: r.failure()?.errorText ?? null }));

try {
  step = "mở trang chủ";
  res.steps.push(step);
  await page.goto(web, { waitUntil: "networkidle" });
  step = "bấm Tư vấn thiết bị";
  res.steps.push(step);
  await page.getByRole("button", { name: "Tư vấn thiết bị" }).click();
  await page.getByRole("heading", { name: "Bạn đang tìm món đồ tiếp theo?" }).waitFor();
  step = "chọn nhanh người 409";
  res.steps.push(step);
  await page.locator(".demo-user-card", { has: page.getByRole("heading", { name: "Người dùng 409", exact: true }) })
    .getByRole("button", { name: "Xem gợi ý" }).click();
  await page.locator(".demo-recommendation-card, [role=alert]").first().waitFor({ timeout: 15000 });
  await page.waitForLoadState("networkidle");
  res.list_shown = (await page.locator(".demo-recommendation-card").count()) > 0;
} finally {
  await browser.close();
}

log(`trình duyệt: ${res.browser}; các bước: ${res.steps.join(" -> ")}; danh sách hiện: ${res.list_shown}`);
log(`phản hồi HTTP >= 400 (${res.http_errors.length}):`);
for (const e of res.http_errors) log(`  [${e.step}] ${e.status} ${e.status_text} ${e.resource_type} ${e.url}`);
log(`yêu cầu hỏng (${res.request_failed.length}): ${JSON.stringify(res.request_failed)}`);
log(`lỗi console (${res.console_errors.length}):`);
for (const e of res.console_errors) log(`  [${e.step}] ${e.text} | ${e.url}`);
writeFileSync(out, JSON.stringify(res, null, 2), { flag: "wx" });
