import mockRecommend409 from "../mock/recommend_409.json";
import mockRecommend47 from "../mock/recommend_47.json";
import mockBodies409 from "../mock/users_409_bodies.json";
import mockBodies47 from "../mock/users_47_bodies.json";

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
  source?: "train" | "val" | "test";
};

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

type ApiEnvelope<T> = {
  data?: T;
  result?: T;
  message?: string;
  error?: string;
};

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
  throw new Error("Backend trả về dữ liệu gợi ý không hợp lệ.");
}

function toHistorySource(value: string): "train" | "val" | "test" {
  if (value === "train" || value === "val" || value === "test") return value;
  throw new Error("Dữ liệu lịch sử thiết bị không hợp lệ.");
}

function toExcludeMode(value: string): "all_history" | "train_val" {
  if (value === "all_history" || value === "train_val") return value;
  throw new Error("Chế độ lọc lịch sử thiết bị không hợp lệ.");
}

function getMockResponse(userId: number): RecommendationResponse {
  const source = userId === 409 ? mockRecommend409 : userId === 47 ? mockRecommend47 : null;
  const bodies = userId === 409 ? mockBodies409.bodies : userId === 47 ? mockBodies47.bodies : null;
  if (!source || !bodies) {
    throw new Error("Hồ sơ này chưa có dữ liệu tư vấn.");
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

async function fetchLiveRecommendations(
  userId: number,
  signal?: AbortSignal,
): Promise<RecommendationResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    k: "10",
    exclude: "all_history",
  });
  const response = await fetch(`${API_URL}/recommend?${params}`, { signal });
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`Backend trả về HTTP ${response.status} nhưng không có JSON hợp lệ.`);
  }
  if (!response.ok) {
    const error = payload as ApiEnvelope<unknown>;
    throw new Error(error.message ?? error.error ?? `Không thể lấy gợi ý (HTTP ${response.status}).`);
  }
  return extractResponse(payload);
}

export async function fetchRecommendations(
  userId: number,
  signal?: AbortSignal,
): Promise<RecommendationResponse> {
  if (import.meta.env.VITE_RECOMMENDATION_SOURCE !== "api") {
    return Promise.resolve(getMockResponse(userId));
  }
  try {
    const timeoutController = new AbortController();
    let timedOut = false;
    const timeoutId = setTimeout(() => {
      timedOut = true;
      timeoutController.abort();
    }, REQUEST_TIMEOUT_MS);
    const abortExternalRequest = () => timeoutController.abort();
    signal?.addEventListener("abort", abortExternalRequest, { once: true });

    try {
      return await fetchLiveRecommendations(userId, timeoutController.signal);
    } catch (error) {
      if (timedOut) {
        throw new Error("Hệ thống phản hồi hơi lâu. Bạn thử lại nhé.");
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
      signal?.removeEventListener("abort", abortExternalRequest);
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError" && signal?.aborted) {
      throw error;
    }
    throw error;
  }
}
