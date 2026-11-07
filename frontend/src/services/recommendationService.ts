import mockRecommend409 from "../mock/recommend_409.json";
import mockRecommend47 from "../mock/recommend_47.json";
import mockBodies409 from "../mock/users_409_bodies.json";
import mockBodies47 from "../mock/users_47_bodies.json";
import mockCompatPairs from "../mock/compat_pairs.json";

export type RecommendationProductDetail = {
  item_id: number;
  asin: string;
  title: string;
  type: string;
  type_label: string;
  mount?: string;
  khung?: string | null;
  categories?: string;
  focal_mm?: { min: number; max: number } | null;
  max_aperture_f?: { at_min_focal: number; at_max_focal: number } | null;
  usecases_label?: string[];
};

const mockItemModules = import.meta.glob<RecommendationProductDetail>(
  "../mock/items/*.json",
  { eager: true, import: "default" },
);

export type RecommendationBody = {
  item_id: number;
  asin: string;
  title: string;
  mount?: string;
  khung?: string | null;
  in_matrix?: boolean;
  source?: "train" | "val" | "test";
};

export const QUICK_USER_PROFILES = [
  { id: 409, bodyTitles: mockBodies409.bodies.map((body) => body.title) },
  { id: 47, bodyTitles: mockBodies47.bodies.map((body) => body.title) },
];

type BlockedRecommendationItem = Pick<RecommendationItem, "item_id" | "asin" | "title" | "type" | "type_label">;

export type RecommendationExplanation = {
  text: string;
  b_star: number;
  b_star_source: "train" | "val" | "test";
  candidate_bodies: number[];
  verified: boolean;
  errors: string[];
  rho?: string;
  c_star?: string | null;
};

export type RecommendationItem = {
  rank: number;
  item_id: number;
  asin: string;
  title: string;
  type: string;
  type_label: string;
  score: number;
  explanation: RecommendationExplanation | null;
  product?: RecommendationProductDetail;
};

export type RecommendationResponse = {
  user_id: number;
  k: number;
  exclude: "all_history" | "train_val";
  has_bodies: boolean;
  n_bodies: number;
  bodies?: RecommendationBody[];
  items: RecommendationItem[];
  mask: {
    rule: string;
    n_lenses_blocked: number;
    n_blocked_in_topk_before_mask: number;
    blocked_in_topk_before_mask: BlockedRecommendationItem[];
  };
};

export type HealthResponse = {
  status: string;
  model?: string;
  seed?: number;
  device?: string;
  n_users?: number;
  n_items?: number;
  contract_version?: string;
};

// --- Types cho /compat (hợp đồng mục 6.2) ---

export type CompatItemBrief = {
  item_id: number;
  asin: string;
  title: string;
  type: string;
  type_label: string;
};

// 5 mức tương thích theo hợp đồng 6.2
export type CompatLevel =
  | "compatible_with"
  | "crops_sensor"
  | "requires_adapter"
  | "incompatible"
  | "unknown";

export type CompatResponse = {
  body: CompatItemBrief;
  lens: CompatItemBrief;
  body_mount: string;
  lens_mount: string;
  body_khung: string;
  lens_khung: string | null;
  body_film: boolean;
  lens_uncertain: boolean;
  level: CompatLevel | null;
  level_label: string | null;
  rule_id: string | null;
  rule_note: string | null;
  crop_unknown: boolean | null;
  in_matrix: boolean;
  m: number | null;
  reason?: string | null;
  qd49_if_only_this_body: "chan" | "khong_chan" | "khong_cham_duoc";
};

// ---

type ApiEnvelope<T> = {
  data?: T;
  result?: T;
};

// Định dạng lỗi chung của hợp đồng (docs/api_contract.md mục 7, Spring giữ nguyên dạng):
// {"error": {"code": "USER_NOT_FOUND", "message": "...", "details": {...}}}
type ApiErrorBody = {
  error?: { code?: string; message?: string };
};

const USER_NOT_FOUND_MESSAGE = "Không tìm thấy người dùng này.";
const SERVICE_DOWN_MESSAGE = "Dịch vụ gợi ý đang tạm dừng, thử lại sau.";

// Câu cho người dùng theo mã lỗi; message của backend là câu kỹ thuật (địa chỉ FastAPI, khoảng user_id) nên không hiện.
function toUserMessage(status: number, payload: unknown): string {
  const code = (payload as ApiErrorBody | null)?.error?.code;
  if (code === "USER_NOT_FOUND") return USER_NOT_FOUND_MESSAGE;
  // Spring: 503 FastAPI không chạy, 504 hết giờ, 502 FastAPI lỗi / trả dữ liệu hỏng (backend/README.md mục 2)
  if (code?.startsWith("MODEL_SERVICE_") || status >= 500) return SERVICE_DOWN_MESSAGE;
  return "Chưa tải được dữ liệu. Bạn thử lại sau nhé.";
}

// Chế độ dữ liệu mẫu (mặc định khi chạy Vite tay): đọc frontend/src/mock/, không gọi Spring / mô hình.
// run_demo.ps1 đặt VITE_RECOMMENDATION_SOURCE=api.
export const IS_MOCK_SOURCE = import.meta.env.VITE_RECOMMENDATION_SOURCE !== "api";

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8080/api").replace(/\/$/, "");
const REQUEST_TIMEOUT_MS = 10_000;

function isRecommendationResponse(value: unknown): value is RecommendationResponse {
  if (!value || typeof value !== "object") return false;
  const response = value as Partial<RecommendationResponse>;
  return typeof response.user_id === "number"
    && Array.isArray(response.items)
    && typeof response.mask === "object"
    && response.mask !== null;
}

function extractResponse(payload: unknown): RecommendationResponse {
  if (isRecommendationResponse(payload)) return payload;
  if (payload && typeof payload === "object") {
    const envelope = payload as ApiEnvelope<RecommendationResponse>;
    if (isRecommendationResponse(envelope.data)) return envelope.data;
    if (isRecommendationResponse(envelope.result)) return envelope.result;
  }
  throw new Error("Danh sách gợi ý chưa sẵn sàng. Bạn thử lại sau nhé.");
}

function toHistorySource(value: string): "train" | "val" | "test" {
  if (value === "train" || value === "val" || value === "test") return value;
  throw new Error("Thông tin thiết bị chưa sẵn sàng. Bạn thử lại sau nhé.");
}

function toExcludeMode(value: string): "all_history" | "train_val" {
  if (value === "all_history" || value === "train_val") return value;
  throw new Error("Danh sách gợi ý chưa sẵn sàng. Bạn thử lại sau nhé.");
}

function getMockResponse(userId: number): RecommendationResponse {
  const source = userId === 409 ? mockRecommend409 : userId === 47 ? mockRecommend47 : null;
  const bodies = userId === 409 ? mockBodies409.bodies : userId === 47 ? mockBodies47.bodies : null;
  if (!source || !bodies) {
    throw new Error("Bản xem trước hiện có hồ sơ 409 và 47. Bạn hãy chọn một trong hai hồ sơ này nhé.");
  }
  return {
    ...source,
    exclude: toExcludeMode(source.exclude),
    bodies: bodies.map((body) => ({
      item_id: body.item_id,
      asin: body.asin,
      title: body.title,
      mount: body.mount,
      khung: body.khung,
      in_matrix: body.in_matrix,
      source: toHistorySource(body.source),
    })),
    items: source.items.map((item) => ({
      ...item,
      explanation: item.explanation
        ? { ...item.explanation, b_star_source: toHistorySource(item.explanation.b_star_source) }
        : null,
      product: mockItemModules[`../mock/items/${item.item_id}.json`],
    })),
  };
}

async function getJson(path: string, signal?: AbortSignal): Promise<unknown> {
  const response = await fetch(`${API_URL}${path}`, { signal });
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    if (response.ok) throw new Error("Cửa hàng chưa nhận được dữ liệu. Bạn thử lại sau nhé.");
  }

  if (!response.ok) throw new Error(toUserMessage(response.status, payload));
  return payload;
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  if (IS_MOCK_SOURCE) {
    return { status: "mock", model: "Dữ liệu mẫu", contract_version: "1.3" };
  }
  return withTimeout(async (timeoutSignal) => {
    const payload = await getJson("/health", timeoutSignal);
    const health = payload as Partial<HealthResponse> | null;
    if (!health || typeof health.status !== "string") {
      throw new Error("Backend trả về trạng thái hệ thống không hợp lệ.");
    }
    return health as HealthResponse;
  }, signal);
}

type BodiesPayload = { bodies: Array<RecommendationBody & { source: string }> };

async function fetchLiveRecommendations(
  userId: number,
  signal?: AbortSignal,
): Promise<RecommendationResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    k: "10",
    exclude: "all_history",
  });
  // Thân máy cùng chế độ exclude với /recommend: đúng tập thân dùng cho mặt nạ (hợp đồng mục 6.1)
  const [payload, bodiesPayload] = await Promise.all([
    getJson(`/recommend?${params}`, signal),
    getJson(`/users/${userId}/bodies?exclude=all_history`, signal),
  ]);
  const response = extractResponse(payload);
  const bodies = (bodiesPayload as BodiesPayload | null)?.bodies;
  if (!Array.isArray(bodies)) throw new Error("Thông tin thiết bị chưa sẵn sàng. Bạn thử lại sau nhé.");
  return {
    ...response,
    bodies: bodies.map((body) => ({
      item_id: body.item_id,
      asin: body.asin,
      title: body.title,
      mount: body.mount,
      khung: body.khung,
      in_matrix: body.in_matrix,
      source: toHistorySource(body.source),
    })),
  };
}

// Chạy một yêu cầu API với thời gian chờ REQUEST_TIMEOUT_MS; signal của người gọi vẫn hủy được yêu cầu.
async function withTimeout<T>(run: (signal: AbortSignal) => Promise<T>, signal?: AbortSignal): Promise<T> {
  const timeoutController = new AbortController();
  let timedOut = false;
  const timeoutId = setTimeout(() => {
    timedOut = true;
    timeoutController.abort();
  }, REQUEST_TIMEOUT_MS);
  const abortExternalRequest = () => timeoutController.abort();
  signal?.addEventListener("abort", abortExternalRequest, { once: true });

  try {
    return await run(timeoutController.signal);
  } catch (error) {
    if (timedOut) {
      throw new Error("Hệ thống phản hồi hơi lâu. Bạn thử lại nhé.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    signal?.removeEventListener("abort", abortExternalRequest);
  }
}

export async function fetchRecommendations(
  userId: number,
  signal?: AbortSignal,
): Promise<RecommendationResponse> {
  if (IS_MOCK_SOURCE) {
    return Promise.resolve(getMockResponse(userId));
  }
  return withTimeout((timeoutSignal) => fetchLiveRecommendations(userId, timeoutSignal), signal);
}

// Chi tiết sản phẩm cho trang chi tiết: chế độ mock đọc frontend/src/mock/items, chế độ api gọi /api/items/{id}.
export async function fetchProductDetail(
  itemId: number,
  signal?: AbortSignal,
): Promise<RecommendationProductDetail> {
  if (IS_MOCK_SOURCE) {
    const product = mockItemModules[`../mock/items/${itemId}.json`];
    if (!product) throw new Error("Chưa có thông tin chi tiết cho sản phẩm này.");
    return product;
  }
  return withTimeout(async (timeoutSignal) => {
    const payload = await getJson(`/items/${itemId}`, timeoutSignal);
    const product = payload as Partial<RecommendationProductDetail> | null;
    if (typeof product?.item_id !== "number" || typeof product.title !== "string") {
      throw new Error("Thông tin sản phẩm chưa sẵn sàng. Bạn thử lại sau nhé.");
    }
    return product as RecommendationProductDetail;
  }, signal);
}

// Tra cứu mức tương thích thân máy – ống kính (hợp đồng mục 6.2, /api/compat?body_id=&lens_id=).
// Chế độ mock: tìm trong compat_pairs.json theo body_id + lens_id.
// Chế độ api: gọi Spring Boot /api/compat.
function getMockCompat(bodyId: number, lensId: number): CompatResponse | null {
  const pair = mockCompatPairs.find(
    (p) => p.body_id === bodyId && p.lens_id === lensId,
  );
  if (!pair) return null;
  const level = pair.level;
  const levelLabel = pair.level_label;
  const ruleId = pair.rule_id;
  const ruleNote = pair.rule_note;
  const cropUnknown = pair.crop_unknown;
  const matrixValue = pair.m;
  const reason = pair.reason;
  const decision = pair.qd49_if_only_this_body;
  if (!isCompatItemBrief(pair.body) || !isCompatItemBrief(pair.lens)
    || typeof pair.body_mount !== "string"
    || typeof pair.lens_mount !== "string"
    || typeof pair.body_khung !== "string"
    || (pair.lens_khung !== null && typeof pair.lens_khung !== "string")
    || typeof pair.body_film !== "boolean"
    || typeof pair.lens_uncertain !== "boolean"
    || (level !== null && !isCompatLevel(level))
    || (levelLabel !== null && typeof levelLabel !== "string")
    || (ruleId !== null && typeof ruleId !== "string")
    || (ruleNote !== null && typeof ruleNote !== "string")
    || (cropUnknown !== null && typeof cropUnknown !== "boolean")
    || typeof pair.in_matrix !== "boolean"
    || (matrixValue !== null && typeof matrixValue !== "number")
    || (reason !== null && reason !== undefined && typeof reason !== "string")
    || !isCompatDecision(decision)) {
    throw new Error("Dữ liệu compatibility mẫu không đúng hợp đồng.");
  }
  return {
    body: pair.body,
    lens: pair.lens,
    body_mount: pair.body_mount,
    lens_mount: pair.lens_mount,
    body_khung: pair.body_khung,
    lens_khung: pair.lens_khung,
    body_film: pair.body_film,
    lens_uncertain: pair.lens_uncertain,
    level,
    level_label: levelLabel,
    rule_id: ruleId,
    rule_note: ruleNote,
    crop_unknown: cropUnknown,
    in_matrix: pair.in_matrix,
    m: matrixValue,
    reason,
    qd49_if_only_this_body: decision,
  };
}

function isCompatItemBrief(value: unknown): value is CompatItemBrief {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return typeof item.item_id === "number"
    && typeof item.asin === "string"
    && typeof item.title === "string"
    && typeof item.type === "string"
    && typeof item.type_label === "string";
}

function isCompatLevel(value: unknown): value is CompatLevel {
  return value === "compatible_with"
    || value === "crops_sensor"
    || value === "requires_adapter"
    || value === "incompatible"
    || value === "unknown";
}

function isCompatDecision(value: unknown): value is CompatResponse["qd49_if_only_this_body"] {
  return value === "chan" || value === "khong_chan" || value === "khong_cham_duoc";
}

export async function fetchCompatibility(
  bodyId: number,
  lensId: number,
  signal?: AbortSignal,
): Promise<CompatResponse> {
  if (IS_MOCK_SOURCE) {
    const result = getMockCompat(bodyId, lensId);
    if (!result) {
      throw new Error(
        `Dữ liệu mẫu chưa có cặp thân ${bodyId} – ống ${lensId}. Bật chế độ API để tra cứu mọi cặp.`,
      );
    }
    return Promise.resolve(result);
  }
  return withTimeout(async (timeoutSignal) => {
    const params = new URLSearchParams({ body_id: String(bodyId), lens_id: String(lensId) });
    const payload = await getJson(`/compat?${params}`, timeoutSignal);
    const compat = payload as Partial<CompatResponse> | null;
    if (!compat || typeof compat.body_mount !== "string") {
      throw new Error("Backend trả về dữ liệu tương thích không hợp lệ.");
    }
    return compat as CompatResponse;
  }, signal);
}
