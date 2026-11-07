/**
 * CompatibilityChecker.tsx
 * Công cụ tra cứu mức tương thích thân máy – ống kính dựa trên ma trận M và QĐ 4-9.
 * Gọi /api/compat qua Spring Boot (hoặc đọc mock) và hiển thị kết quả trực quan.
 */
import { FormEvent, useRef, useState } from "react";
import {
  CompatLevel,
  CompatResponse,
  IS_MOCK_SOURCE,
  fetchCompatibility,
} from "./services/recommendationService";

type Props = { onExit: () => void };

// Cặp ví dụ minh họa có trong mock (body_id, lens_id, nhãn ngắn)
const EXAMPLE_PAIRS: { bodyId: number; lensId: number; bodyName: string; lensName: string }[] = [
  {
    bodyId: 9022,
    lensId: 15485,
    bodyName: "Nikon D3100",
    lensName: "Nikon 55-200mm DX VR (Nikon F)",
  },
  {
    bodyId: 9022,
    lensId: 13448,
    bodyName: "Nikon D3100",
    lensName: "Canon EF 24-70mm f/4L (Canon EF)",
  },
  {
    bodyId: 19071,
    lensId: 9696,
    bodyName: "Sony a6000",
    lensName: "Sony 50mm f/1.8 (Sony E)",
  },
  {
    bodyId: 9022,
    lensId: 118,
    bodyName: "Nikon D3100",
    lensName: "Sigma 14mm Nikon F (ngàm không chắc)",
  },
  {
    bodyId: 9022,
    lensId: 105,
    bodyName: "Nikon D3100",
    lensName: "Nikon 28-105mm (ngàm không rõ)",
  },
];

// Màu sắc & biểu tượng theo 5 mức tương thích (hợp đồng mục 6.2)
type LevelMeta = {
  color: string;
  bg: string;
  border: string;
  icon: string;
  label: string;
  summary: string;
};

function getLevelMeta(level: CompatLevel | null): LevelMeta {
  switch (level) {
    case "compatible_with":
      return {
        color: "#166534", bg: "#f0fdf4", border: "#86efac",
        icon: "✓", label: "Lắp trực tiếp", summary: "Ống lắp trực tiếp lên thân, dùng đủ khung hình (M = 1).",
      };
    case "crops_sensor":
      return {
        color: "#92400e", bg: "#fffbeb", border: "#fcd34d",
        icon: "⚠", label: "Cắt khung cảm biến", summary: "Ống lắp được nhưng thiết kế cho cảm biến nhỏ hơn — ảnh sẽ bị cắt khung.",
      };
    case "requires_adapter":
      return {
        color: "#1e3a8a", bg: "#eff6ff", border: "#93c5fd",
        icon: "↔", label: "Cần ngàm chuyển", summary: "Ống lắp được thông qua ngàm chuyển chính hãng (M = 0).",
      };
    case "incompatible":
      return {
        color: "#991b1b", bg: "#fef2f2", border: "#fca5a5",
        icon: "✕", label: "Không tương thích", summary: "Ống không lắp được lên thân này (M = 0, không có ngàm chuyển).",
      };
    case "unknown":
      return {
        color: "#374151", bg: "#f9fafb", border: "#d1d5db",
        icon: "?", label: "Không xác định", summary: "Không đủ thông tin để xếp mức tương thích.",
      };
    default:
      return {
        color: "#374151", bg: "#f9fafb", border: "#d1d5db",
        icon: "–", label: "Chưa xếp được", summary: "Thân hoặc ống không xác định được đúng một ngàm.",
      };
  }
}

function formatMount(mount: string | null | undefined): string {
  if (!mount || mount === "khong_ro") return "Không rõ";
  const map: Record<string, string> = {
    nikon_f: "Nikon F", canon_ef: "Canon EF", sony_e: "Sony E",
    fuji_x: "Fujifilm X", micro_four_thirds: "Micro 4/3",
    canon_rf: "Canon RF", nikon_z: "Nikon Z", leica_m: "Leica M",
    pentax_k: "Pentax K", samsung_nx: "Samsung NX",
  };
  return map[mount] ?? mount;
}

function formatKhung(khung: string | null | undefined): string {
  if (!khung || khung === "khong_ro") return "Không rõ";
  const map: Record<string, string> = {
    ff: "Full-frame (35mm)", apsc: "APS-C", mft: "Micro 4/3",
    apsh: "APS-H", medium_format: "Medium Format",
  };
  return map[khung] ?? khung;
}

// Thẻ hiển thị thuộc tính kỹ thuật
function SpecBadge({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <span style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.05em", color: "#6b7280" }}>
        {label}
      </span>
      <span style={{ fontSize: 13, fontWeight: 600, color: "#111827" }}>{value}</span>
    </div>
  );
}

// Kết quả tương thích
function CompatResult({ result }: { result: CompatResponse }) {
  const meta = getLevelMeta(result.level);

  return (
    <div style={{
      border: `2px solid ${meta.border}`, borderRadius: 12,
      background: meta.bg, padding: "20px 24px", marginTop: 24,
    }}>
      {/* Mức tương thích */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <div style={{
          width: 40, height: 40, borderRadius: "50%",
          background: meta.color, color: "#fff",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 18, fontWeight: 700, flexShrink: 0,
        }}>
          {meta.icon}
        </div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: meta.color }}>{meta.label}</div>
          <div style={{ fontSize: 13, color: "#4b5563", marginTop: 2 }}>
            {result.level_label ?? meta.summary}
          </div>
        </div>
      </div>

      {/* Lý do khi không xếp được mức */}
      {result.reason && (
        <p style={{ fontSize: 13, color: "#6b7280", background: "#f3f4f6", borderRadius: 6, padding: "8px 12px", margin: "12px 0 0" }}>
          ⓘ {result.reason}
        </p>
      )}

      {/* Thông tin kỹ thuật */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(2, 1fr)",
        gap: 16, marginTop: 16,
        paddingTop: 16, borderTop: `1px solid ${meta.border}`,
      }}>
        {/* Cột thân máy */}
        <div>
          <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#9ca3af", marginBottom: 8 }}>
            Thân máy
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#111827", marginBottom: 10 }}>
            {result.body.title.length > 60
              ? result.body.title.slice(0, 60) + "…"
              : result.body.title}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <SpecBadge label="Ngàm" value={formatMount(result.body_mount)} />
            <SpecBadge label="Cảm biến" value={formatKhung(result.body_khung)} />
            {result.body_film && <SpecBadge label="Loại" value="Máy phim" />}
          </div>
        </div>

        {/* Cột ống kính */}
        <div>
          <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#9ca3af", marginBottom: 8 }}>
            Ống kính
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#111827", marginBottom: 10 }}>
            {result.lens.title.length > 60
              ? result.lens.title.slice(0, 60) + "…"
              : result.lens.title}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <SpecBadge label="Ngàm" value={formatMount(result.lens_mount)} />
            <SpecBadge label="Cảm biến thiết kế" value={formatKhung(result.lens_khung)} />
            {result.lens_uncertain && (
              <SpecBadge label="Ngàm" value="Không chắc (QĐ 4)" />
            )}
          </div>
        </div>
      </div>

      {/* Thông tin ma trận M và QĐ 4-9 */}
      <div style={{
        marginTop: 16, paddingTop: 16, borderTop: `1px solid ${meta.border}`,
        display: "flex", gap: 20, flexWrap: "wrap",
      }}>
        <SpecBadge
          label="Ma trận M"
          value={result.in_matrix
            ? (result.m === 1 ? "M = 1 (tương thích)" : result.m === 0 ? "M = 0 (không tương thích)" : "Trong M")
            : "Không có trong M"}
        />
        <SpecBadge
          label="Mặt nạ QĐ 4-9 (nếu chỉ có thân này)"
          value={
            result.qd49_if_only_this_body === "chan"
              ? "Chặn ống này"
              : result.qd49_if_only_this_body === "khong_chan"
              ? "Không chặn"
              : "Không chấm được"
          }
        />
        {result.crop_unknown && (
          <SpecBadge label="Cắt khung" value="Chưa rõ máy có tự cắt khung không (QĐ 11)" />
        )}
      </div>

      {/* Luật quyết định */}
      {result.rule_note && (
        <div style={{
          marginTop: 12, fontSize: 12, color: "#6b7280",
          background: "#f9fafb", borderRadius: 6, padding: "8px 12px",
        }}>
          <strong>Luật áp dụng:</strong>{" "}
          {result.rule_id && <code style={{ fontSize: 11 }}>{result.rule_id}</code>}
          {" — "}{result.rule_note}
        </div>
      )}
    </div>
  );
}

// Form nhập ID thủ công
function ManualIdForm({
  onSubmit,
  loading,
}: {
  onSubmit: (bodyId: number, lensId: number) => void;
  loading: boolean;
}) {
  const bodyRef = useRef<HTMLInputElement>(null);
  const lensRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const bodyVal = bodyRef.current?.value.trim() ?? "";
    const lensVal = lensRef.current?.value.trim() ?? "";
    const bodyId = parseInt(bodyVal, 10);
    const lensId = parseInt(lensVal, 10);
    if (!/^\d+$/.test(bodyVal) || !/^\d+$/.test(lensVal) || isNaN(bodyId) || isNaN(lensId)) {
      setError("Vui lòng nhập số nguyên hợp lệ cho cả hai ID (0 – 27.939).");
      return;
    }
    setError(null);
    onSubmit(bodyId, lensId);
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <label style={{ fontSize: 12, color: "#6b7280" }} htmlFor="compat-body-id">
          Item ID thân máy (0 – 27.939)
        </label>
        <input
          id="compat-body-id"
          ref={bodyRef}
          type="text"
          inputMode="numeric"
          placeholder="vd 9022"
          style={{
            padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 6,
            fontSize: 14, width: 140, outline: "none",
          }}
        />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <label style={{ fontSize: 12, color: "#6b7280" }} htmlFor="compat-lens-id">
          Item ID ống kính (0 – 27.939)
        </label>
        <input
          id="compat-lens-id"
          ref={lensRef}
          type="text"
          inputMode="numeric"
          placeholder="vd 13448"
          style={{
            padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 6,
            fontSize: 14, width: 140, outline: "none",
          }}
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        style={{
          padding: "9px 20px", background: "#111827", color: "#fff",
          border: "none", borderRadius: 6, fontSize: 14, fontWeight: 600,
          cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.6 : 1,
        }}
      >
        {loading ? "Đang tra…" : "Tra cứu"}
      </button>
      {error && (
        <p role="alert" style={{ width: "100%", color: "#991b1b", fontSize: 13, margin: 0 }}>
          {error}
        </p>
      )}
    </form>
  );
}

export default function CompatibilityChecker({ onExit }: Props) {
  const [result, setResult] = useState<CompatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  async function lookup(bodyId: number, lensId: number) {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await fetchCompatibility(bodyId, lensId, controller.signal);
      setResult(data);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(err instanceof Error ? err.message : "Không tra cứu được. Bạn thử lại nhé.");
    } finally {
      if (controllerRef.current === controller) {
        setLoading(false);
        controllerRef.current = null;
      }
    }
  }

  return (
    <div className="demo-page">
      {/* Header giống luồng tư vấn để nhất quán UX */}
      <header className="demo-header">
        <div className="demo-shell demo-header-content">
          <button type="button" className="demo-brand" onClick={onExit}>
            CAMERA RECOMMENDER <span>Compatibility</span>
          </button>
          <p>Tra cứu mức tương thích thân máy – ống kính dựa trên ma trận M và quy tắc ngàm</p>
          <button type="button" className="demo-link-button" onClick={onExit}>
            Quay về catalog
          </button>
        </div>
      </header>

      <main className="demo-shell demo-main">
        {/* Nhãn chế độ dữ liệu mẫu */}
        {IS_MOCK_SOURCE && (
          <aside className="demo-mask-note" role="note" aria-label="Dữ liệu mẫu">
            <strong>Dữ liệu mẫu</strong>
            <p>
              Chỉ có 5 cặp mẫu bên dưới. Bật chế độ API (<code>VITE_RECOMMENDATION_SOURCE=api</code>
              ) để tra cứu bất kỳ cặp nào trong 27.940 sản phẩm.
            </p>
          </aside>
        )}

        <span className="demo-eyebrow">Ma trận tương thích M</span>
        <h1>Kiểm tra thân máy – ống kính có lắp được không?</h1>
        <p className="demo-lead">
          Hệ thống áp dụng 22 quy tắc ngàm chính hãng (Nội dung 3) để xếp mức tương thích.
          Kết quả này chính là cơ sở của Mặt nạ QĐ 4-9 trong hệ thống gợi ý — ống kính không lắp được
          trên mọi thân của người dùng sẽ bị lọc khỏi danh sách gợi ý.
        </p>

        {/* Cặp ví dụ minh họa */}
        <section aria-label="Cặp ví dụ">
          <h2 style={{ fontSize: 15, fontWeight: 700, color: "#374151", marginBottom: 12 }}>
            Cặp ví dụ (từ dữ liệu kiểm thử)
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
              gap: 10,
              marginBottom: 28,
            }}
          >
            {EXAMPLE_PAIRS.map((pair) => (
              <button type="button"
                key={`${pair.bodyId}-${pair.lensId}`}
                onClick={() => void lookup(pair.bodyId, pair.lensId)}
                disabled={loading}
                style={{
                  textAlign: "left", padding: "12px 16px",
                  border: "1px solid #e5e7eb", borderRadius: 8,
                  background: "#fff", cursor: loading ? "not-allowed" : "pointer",
                  transition: "border-color 0.15s, box-shadow 0.15s",
                  opacity: loading ? 0.7 : 1,
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "#6b7280";
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 1px 4px rgba(0,0,0,.08)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "#e5e7eb";
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = "none";
                }}
              >
                <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 4 }}>
                  Thân #{pair.bodyId} · Ống #{pair.lensId}
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#111827", marginBottom: 2 }}>
                  {pair.bodyName}
                </div>
                <div style={{ fontSize: 12, color: "#4b5563" }}>+ {pair.lensName}</div>
              </button>
            ))}
          </div>
        </section>

        {/* Nhập ID thủ công (chỉ có ý nghĩa khi chạy live API) */}
        {!IS_MOCK_SOURCE && (
          <section aria-label="Nhập ID tùy chỉnh" style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700, color: "#374151", marginBottom: 12 }}>
              Tra cứu theo Item ID
            </h2>
            <ManualIdForm onSubmit={(b, l) => void lookup(b, l)} loading={loading} />
          </section>
        )}

        {/* Trạng thái loading */}
        {loading && (
          <p role="status" className="demo-lead">
            Đang tra cứu tương thích…
          </p>
        )}

        {/* Lỗi */}
        {error && (
          <aside className="demo-mask-note" role="alert">
            <strong>Không tra cứu được</strong>
            <p>{error}</p>
          </aside>
        )}

        {/* Kết quả */}
        {result && <CompatResult result={result} />}

        {/* Chú thích học thuật */}
        <aside
          className="demo-mask-note"
          role="note"
          style={{ marginTop: 32 }}
          aria-label="Ghi chú kỹ thuật"
        >
          <strong>Ghi chú kỹ thuật (Nội dung 3 & 4)</strong>
          <p>
            Ma trận M gồm <strong>72.720 cặp M = 1</strong> (lắp trực tiếp) và <strong>5.846 cặp "không biết"</strong>.
            Các số liệu phân loại được đo trong lần đo 3 trên holdout H733; chi tiết nguồn, script và giới hạn xem
            <code>docs/STATUS.md</code> và <code>docs/api_contract.md</code>.
          </p>
          <p>
            <strong>Mặt nạ QĐ 4-9:</strong> chặn ống mà <em>mọi</em> thân của người dùng đều M = 0
            và không có cặp "không biết". Người 409 (Nikon D3100): 814 ống bị chặn.
            Ống ngoài M (ngàm không chắc) <em>không bao giờ bị chặn</em>.
          </p>
        </aside>
      </main>
    </div>
  );
}
