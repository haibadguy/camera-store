import { useEffect, useRef, useState } from "react";
import {
  fetchRecommendations,
  RecommendationExplanation,
  RecommendationItem,
  RecommendationResponse,
} from "./services/recommendationService";

type Props = { onExit: () => void };

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
      <section className="demo-user-grid" aria-label="Danh sách người dùng kiểm thử">
        {[409, 47].map((userId) => <article className="demo-user-card" key={userId}>
          <div className="demo-card-topline"><span>Hồ sơ số</span><strong>0{userId}</strong></div>
          <h2>Gợi ý dựa trên thiết bị đã có</h2>
          <p>Những món đã có sẽ được bỏ qua để danh sách tập trung vào lựa chọn mới.</p>
          <button className="demo-primary-button" onClick={() => onSelect(userId)}>Xem gợi ý</button>
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
  return <div className="demo-page"><DemoHeader onExit={onExit} trail={`Người dùng #${userId} / Danh sách gợi ý`} />
    <main className="demo-shell demo-main">
      <button className="demo-back-button" onClick={onBack}>← Chọn người dùng khác</button>
      <span className="demo-eyebrow">Danh sách dành riêng cho bạn</span><h1>Những lựa chọn đáng xem</h1>
      {loading && <p role="status" className="demo-lead">Đang tải gợi ý...</p>}
      {error && <aside className="demo-mask-note" role="alert"><strong>Không tải được dữ liệu</strong><p>{error}</p><button className="demo-secondary-button" onClick={onRetry}>Thử lại</button></aside>}
      {response && <><p className="demo-lead">Điểm chỉ dùng để xếp hạng trong cùng một người dùng, không phải phần trăm phù hợp.</p>
        <section className="demo-summary-grid" aria-label="Tóm tắt hồ sơ"><div><span>Thân máy trong hồ sơ</span><strong>{response.n_bodies}</strong></div><div><span>Ống kính không phù hợp</span><strong>{response.mask.n_lenses_blocked}</strong></div><div><span>Sản phẩm được chọn</span><strong>{response.items.length}</strong></div></section>
        {response.mask.n_blocked_in_topk_before_mask > 0 && <aside className="demo-mask-note"><strong>{response.mask.rule}</strong><p>Đã gỡ {response.mask.n_blocked_in_topk_before_mask} sản phẩm vi phạm khỏi top-k trước mặt nạ.</p></aside>}
        <section className="demo-recommendations" aria-label="Danh sách gợi ý">{response.items.map((item) => <article className="demo-recommendation-card" key={item.item_id}>
          <div className="demo-rank">#{item.rank}</div><div className="demo-recommendation-content"><div className="demo-type-row"><span>{item.type_label}</span><span>item_id {item.item_id}</span></div><h2>{item.title}</h2>
          {item.asin && <p className="demo-asin">ASIN: {item.asin}</p>}<p className="demo-score">Điểm xếp hạng: {item.score}</p>
          {item.explanation && <ExplanationPanel explanation={item.explanation} />}
          <button className="demo-secondary-button" onClick={() => onSelectItem(item)}>Xem thông tin sản phẩm</button></div>
        </article>)}</section>
      </>}
    </main>
  </div>;
}

function ExplanationPanel({ explanation }: { explanation: RecommendationExplanation }) {
  return <section className="demo-explanation"><div className="demo-explanation-title">Giải thích đã xác minh</div><p>{explanation.verified ? explanation.text : "Giải thích chưa được xác minh nên không hiển thị nội dung."}</p>
    <dl><div><dt>Thân được chọn</dt><dd>#{explanation.b_star}</dd></div><div><dt>Nguồn thân</dt><dd>{explanation.b_star_source}</dd></div><div><dt>Candidate bodies</dt><dd>{explanation.candidate_bodies.join(", ")}</dd></div></dl>
  </section>;
}

function ProductDetail({ item, userId, onBack, onExit }: { item: RecommendationItem; userId: number; onBack: () => void; onExit: () => void }) {
  return <div className="demo-page"><DemoHeader onExit={onExit} trail={`Người dùng #${userId} / Chi tiết sản phẩm`} />
    <main className="demo-shell demo-main"><button className="demo-back-button" onClick={onBack}>← Quay lại danh sách gợi ý</button><span className="demo-eyebrow">Bước 3 / 3 · item_id {item.item_id}</span>
      <article className="demo-detail-card"><div className="demo-detail-visual" aria-hidden="true">{item.type_label}</div><div className="demo-detail-content"><div className="demo-type-row"><span>{item.type_label}</span><span>Hạng #{item.rank}</span></div><h1>{item.title}</h1><p className="demo-lead">Thông tin hiển thị giới hạn trong các trường API đã công bố.</p>
        <dl className="demo-attributes"><div><dt>item_id</dt><dd>{item.item_id}</dd></div><div><dt>ASIN</dt><dd>{item.asin || "Không có"}</dd></div><div><dt>Điểm</dt><dd>{item.score}</dd></div></dl>{item.explanation && <ExplanationPanel explanation={item.explanation} />}
      </div></article>
    </main>
  </div>;
}
