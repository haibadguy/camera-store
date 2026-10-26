export type RecommendationBody = {
  item_id: number;
  asin: string;
  title: string;
  mount?: string;
  khung?: string | null;
  source?: "train" | "val" | "test";
};

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
    blocked_in_topk_before_mask: RecommendationItem[];
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
  throw new Error("Backend trả về dữ liệu không khớp API contract recommendation.");
}

export async function fetchRecommendations(
  userId: number,
  signal?: AbortSignal,
): Promise<RecommendationResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    k: "10",
    exclude: "all_history",
  });
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
      const response = await fetch(`${API_URL}/recommendations?${params}`, {
        signal: timeoutController.signal,
      });
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
