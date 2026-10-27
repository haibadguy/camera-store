import { useEffect, useRef, useState } from "react";
import {
  fetchProductDetail,
  fetchRecommendations,
  RecommendationExplanation,
  RecommendationItem,
  RecommendationProductDetail,
  RecommendationResponse,
} from "./services/recommendationService";

type Props = { onExit: () => void };

function formatMount(mount: string): string {
  return mount === "nikon_f" ? "Nikon F" : mount === "canon_ef" ? "Canon EF" : mount;
}

function formatFrame(frame: string): string {
  return frame === "apsc" ? "APS-C" : frame === "ff" ? "Full-frame" : frame;
}

export default function RecommendationDemo({ onExit }: Props) {
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedItem, setSelectedItem] = useState<RecommendationItem | null>(null);
  const [response, setResponse] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestController = useRef<AbortController | null>(null);

  useEffect(() => () => {
    requestController.current?.abort();
  }, []);

  async function selectUser(userId: number) {
    requestController.current?.abort();
    const controller = new AbortController();
    requestController.current = controller;
    setSelectedUserId(userId);
    setSelectedItem(null);
    setResponse(null);
    setError(null);
    setLoading(true);
    try {
      setResponse(await fetchRecommendations(userId, controller.signal));
    } catch (requestError) {
      if (requestError instanceof DOMException && requestError.name === "AbortError") return;
      const message = requestError instanceof TypeError
        ? "Chưa kết nối được với cửa hàng. Bạn thử lại sau ít phút nhé."
        : requestError instanceof Error
          ? requestError.message
          : "Chưa tải được danh sách gợi ý. Bạn thử lại nhé.";
      setError(message);
    } finally {
      if (requestController.current === controller) {
        setLoading(false);
        requestController.current = null;
      }
    }
  }

  if (selectedUserId !== null && selectedItem) {
    return <ProductDetail item={selectedItem} userId={selectedUserId} onBack={() => setSelectedItem(null)} onExit={onExit} />;
  }
  if (selectedUserId !== null) {
    return (
      <RecommendationList
        userId={selectedUserId}
        response={response}
        loading={loading}
        error={error}
        onBack={() => { setSelectedUserId(null); setResponse(null); setError(null); }}
        onSelectItem={setSelectedItem}
        onRetry={() => { void selectUser(selectedUserId); }}
        onExit={onExit}
      />
    );
  }
  return <UserPicker onExit={onExit} onSelect={(id) => { void selectUser(id); }} />;
}

function DemoHeader({ onExit, trail }: { onExit: () => void; trail: string }) {
  return <header className="demo-header"><div className="demo-shell demo-header-content">
    <button className="demo-brand" onClick={onExit}>CAMERA STORE <span>Gợi ý thiết bị</span></button>
    <p>{trail}</p><button className="demo-link-button" onClick={onExit}>Quay về catalog</button>
  </div></header>;
}

function UserPicker({ onExit, onSelect }: { onExit: () => void; onSelect: (id: number) => void }) {
  return <div className="demo-page"><DemoHeader onExit={onExit} trail="Tư vấn chọn thiết bị" />
    <main className="demo-shell demo-main">
      <span className="demo-eyebrow">Tư vấn cá nhân</span><h1>Bạn đang tìm món đồ tiếp theo?</h1>
      <p className="demo-lead">Chọn một hồ sơ để xem những thiết bị được xếp hạng từ lịch sử sử dụng.</p>
      <section className="demo-user-grid" aria-label="Chọn thiết bị đang dùng">
        {[{ id: 409, name: "Nikon D3100" }, { id: 47, name: "Nikon D500" }].map(({ id, name }) => <article className="demo-user-card" key={id}>
          <div className="demo-card-topline"><span>Thiết bị đang dùng</span><strong>{name}</strong></div>
          <h2>Gợi ý dựa trên thiết bị đã có</h2>
          <p>Những món đã có sẽ được bỏ qua để danh sách tập trung vào lựa chọn mới.</p>
          <button className="demo-primary-button" onClick={() => onSelect(id)}>Xem gợi ý</button>
        </article>)}
      </section>
    </main>
  </div>;
}

function RecommendationList({
  userId, response, loading, error, onBack, onSelectItem, onRetry, onExit,
}: {
  userId: number;
  response: RecommendationResponse | null;
  loading: boolean;
  error: string | null;
  onBack: () => void;
  onSelectItem: (item: RecommendationItem) => void;
  onRetry: () => void;
  onExit: () => void;
}) {
  return <div className="demo-page"><DemoHeader onExit={onExit} trail="Danh sách gợi ý dành riêng cho bạn" />
    <main className="demo-shell demo-main">
      <button className="demo-back-button" onClick={onBack}>← Chọn người dùng khác</button>
      <span className="demo-eyebrow">Danh sách dành riêng cho bạn</span><h1>Những lựa chọn đáng xem</h1>
      {loading && <p role="status" className="demo-lead">Đang tải gợi ý...</p>}
      {error && <aside className="demo-mask-note" role="alert"><strong>Không tải được dữ liệu</strong><p>{error}</p><button className="demo-secondary-button" onClick={onRetry}>Thử lại</button></aside>}
      {response && <><p className="demo-lead">Danh sách được chọn từ lịch sử thiết bị của bạn, ưu tiên những món chưa xuất hiện trước đây.</p>
        <section className="demo-summary-grid" aria-label="Tóm tắt hồ sơ"><div><span>Thân máy đang dùng</span><strong>{response.n_bodies}</strong></div><div><span>Ống kính không lắp được</span><strong>{response.mask.n_lenses_blocked}</strong></div><div><span>Gợi ý dành cho bạn</span><strong>{response.items.length}</strong></div></section>
        {response.mask.n_blocked_in_topk_before_mask > 0 && <aside className="demo-mask-note"><strong>Đã lọc sản phẩm không tương thích</strong><p>Đã ẩn {response.mask.n_lenses_blocked} ống kính không lắp được trên {response.bodies?.[0]?.title ?? "thiết bị của bạn"}.</p></aside>}
        <section className="demo-recommendations" aria-label="Danh sách gợi ý">{response.items.map((item) => <article className="demo-recommendation-card" key={item.item_id}>
          <div className="demo-rank">#{item.rank}</div><div className="demo-recommendation-content"><div className="demo-type-row"><span>{item.type_label}</span><span>Gợi ý phù hợp</span></div><h2>{item.title}</h2>
          {item.explanation && <ExplanationPanel explanation={item.explanation} />}
          <button className="demo-secondary-button" onClick={() => onSelectItem(item)}>Xem thông tin sản phẩm</button></div>
        </article>)}</section>
      </>}
    </main>
  </div>;
}

function ExplanationPanel({ explanation }: { explanation: RecommendationExplanation }) {
  return <section className="demo-explanation"><div className="demo-explanation-title">Vì sao gợi ý món này?</div><p>{explanation.verified ? explanation.text : "Chưa đủ thông tin để giải thích gợi ý này."}</p>
  </section>;
}

function ProductDetail({ item, userId, onBack, onExit }: { item: RecommendationItem; userId: number; onBack: () => void; onExit: () => void }) {
  // Chế độ mock đã gắn sẵn item.product; chế độ api lấy từ /api/items/{id} khi mở trang
  const [product, setProduct] = useState<RecommendationProductDetail | undefined>(item.product);
  const [productError, setProductError] = useState<string | null>(null);
  useEffect(() => {
    if (item.product) return;
    const controller = new AbortController();
    fetchProductDetail(item.item_id, controller.signal)
      .then(setProduct)
      .catch((requestError) => {
        if (requestError instanceof DOMException && requestError.name === "AbortError") return;
        setProductError(requestError instanceof TypeError
          ? "Chưa kết nối được với cửa hàng. Bạn thử lại sau ít phút nhé."
          : requestError instanceof Error ? requestError.message : "Chưa tải được thông tin sản phẩm.");
      });
    return () => controller.abort();
  }, [item]);
  const productLoading = !product && !productError;
  return <div className="demo-page"><DemoHeader onExit={onExit} trail="Thông tin sản phẩm" />
    <main className="demo-shell demo-main"><button className="demo-back-button" onClick={onBack}>← Quay lại danh sách gợi ý</button><span className="demo-eyebrow">Thông tin sản phẩm</span>
      <article className="demo-detail-card"><div className="demo-detail-visual" aria-hidden="true">{item.type_label}</div><div className="demo-detail-content"><div className="demo-type-row"><span>{item.type_label}</span><span>Hạng #{item.rank}</span></div><h1>{item.title}</h1><p className="demo-lead">Thông tin sản phẩm và lý do được đề xuất cho bạn.</p>
        {productLoading && <p role="status" className="demo-lead">Đang tải thông tin sản phẩm...</p>}
        {productError && <p role="alert" className="demo-lead">{productError}</p>}
        <dl className="demo-attributes"><div><dt>Loại sản phẩm</dt><dd>{item.type_label}</dd></div>{product?.mount && <div><dt>Ngàm</dt><dd>{formatMount(product.mount)}</dd></div>}{product?.khung && <div><dt>Định dạng</dt><dd>{formatFrame(product.khung)}</dd></div>}{product?.usecases_label?.length ? <div><dt>Phù hợp với</dt><dd>{product.usecases_label.join(", ")}</dd></div> : null}</dl>{item.explanation && <ExplanationPanel explanation={item.explanation} />}
      </div></article>
    </main>
  </div>;
}
