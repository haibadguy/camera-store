import { FormEvent, useEffect, useRef, useState } from "react";
import {
  IS_MOCK_SOURCE,
  fetchProductDetail,
  fetchRecommendations,
  RecommendationExplanation,
  RecommendationItem,
  RecommendationBody,
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

// Người dùng chọn nhanh và thân máy họ đã đánh giá (cả lịch sử, /api/users/{id}/bodies seed 1)
const QUICK_USERS = [
  { id: 409, bodies: "Nikon D3100" },
  { id: 47, bodies: "Nikon D4S, Nikon D500" },
];
const USER_ID_PATTERN = /^\d{1,9}$/;

// Nhãn chế độ dữ liệu mẫu, hiện trên mọi trang của luồng tư vấn
function MockNotice() {
  if (!IS_MOCK_SOURCE) return null;
  return <aside className="demo-mask-note" role="note" aria-label="Dữ liệu mẫu"><strong>Dữ liệu mẫu</strong>
    <p>Trang đang đọc phản hồi đã lưu sẵn, không gọi mô hình. Chạy run_demo.ps1 để dùng mô hình thật.</p></aside>;
}

function UserPicker({ onExit, onSelect }: { onExit: () => void; onSelect: (id: number) => void }) {
  const [userInput, setUserInput] = useState("");
  const [inputError, setInputError] = useState<string | null>(null);
  function submitUserId(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = userInput.trim();
    if (!USER_ID_PATTERN.test(value)) {
      setInputError("Mã người dùng là một số nguyên không âm, vd 409.");
      return;
    }
    setInputError(null);
    onSelect(Number(value));
  }
  return <div className="demo-page"><DemoHeader onExit={onExit} trail="Tư vấn chọn thiết bị" />
    <main className="demo-shell demo-main">
      <MockNotice />
      <span className="demo-eyebrow">Tư vấn cá nhân</span><h1>Bạn đang tìm món đồ tiếp theo?</h1>
      <p className="demo-lead">Chọn một người dùng có trong dữ liệu đánh giá Amazon. Gợi ý dựa vào những sản phẩm người đó đã đánh giá; ống kính được lọc theo thân máy bạn đã đánh giá.</p>
      <section className="demo-user-grid" aria-label="Chọn người dùng">
        {QUICK_USERS.map(({ id, bodies }) => <article className="demo-user-card" key={id}>
          <div className="demo-card-topline"><span>Thân máy bạn đã đánh giá</span><strong>{bodies}</strong></div>
          <h2>Người dùng {id}</h2>
          <p>Sản phẩm người này đã đánh giá sẽ không được gợi ý lại.</p>
          <button className="demo-primary-button" onClick={() => onSelect(id)}>Xem gợi ý</button>
        </article>)}
        <article className="demo-user-card">
          <form onSubmit={submitUserId} aria-label="Nhập mã người dùng">
            <div className="demo-card-topline"><label htmlFor="demo-user-id">Người dùng khác</label><strong>0 – 67.660</strong></div>
            <h2>Nhập mã người dùng</h2>
            <p><input id="demo-user-id" name="user_id" inputMode="numeric" autoComplete="off" placeholder="vd 178"
              value={userInput} onChange={(event) => setUserInput(event.target.value)} /></p>
            {inputError && <p role="alert">{inputError}</p>}
            <button className="demo-primary-button" type="submit">Xem gợi ý</button>
          </form>
        </article>
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
      <MockNotice />
      <button className="demo-back-button" onClick={onBack}>← Chọn người dùng khác</button>
      <span className="demo-eyebrow">Người dùng {userId}</span><h1>Những lựa chọn đáng xem</h1>
      {loading && <p role="status" className="demo-lead">Đang tải gợi ý...</p>}
      {error && <aside className="demo-mask-note" role="alert"><strong>Không tải được dữ liệu</strong><p>{error}</p><button className="demo-secondary-button" onClick={onRetry}>Thử lại</button></aside>}
      {response && <><p className="demo-lead">Những sản phẩm bạn đã đánh giá không có trong danh sách. Thứ tự theo điểm của mô hình gợi ý.</p>
        <section className="demo-summary-grid" aria-label="Tóm tắt hồ sơ"><div><span>Thân máy bạn đã đánh giá</span><strong>{response.n_bodies}</strong></div><div><span>Ống kính không lắp được trên máy nào của bạn</span><strong>{response.mask.n_lenses_blocked}</strong></div><div><span>Gợi ý dành cho bạn</span><strong>{response.items.length}</strong></div></section>
        <MaskNote response={response} />
        <section className="demo-recommendations" aria-label="Danh sách gợi ý">{response.items.map((item) => <article className="demo-recommendation-card" key={item.item_id}>
          <div className="demo-rank">#{item.rank}</div><div className="demo-recommendation-content"><div className="demo-type-row"><span>{item.type_label}</span></div><h2>{item.title}</h2>
          {item.explanation && <ExplanationPanel explanation={item.explanation} />}
          <button className="demo-secondary-button" onClick={() => onSelectItem(item)}>Xem thông tin sản phẩm</button></div>
        </article>)}</section>
      </>}
    </main>
  </div>;
}

// Mặt nạ QĐ 4-9 (hợp đồng 2.3, 4.2): chặn ống kính mà MỌI thân của người dùng đều không lắp được; người không có thân,
// hoặc có thân chưa nằm trong bảng tương thích M, không bị chặn ống nào. Hai con số khác nhau: n_lenses_blocked tính
// trên cả catalog, n_blocked_in_topk_before_mask là số ống bị gỡ khỏi chính danh sách này.
function MaskNote({ response }: { response: RecommendationResponse }) {
  const bodies: RecommendationBody[] = response.bodies ?? [];
  const { n_lenses_blocked: nBlocked, n_blocked_in_topk_before_mask: nRemoved, blocked_in_topk_before_mask: removed } = response.mask;
  const outsideMatrix = bodies.filter((body) => body.in_matrix === false);
  return <aside className="demo-mask-note" aria-label="Lọc ống kính theo máy của bạn"><strong>Lọc ống kính theo máy của bạn</strong>
    {bodies.length > 0 && <ul className="demo-body-list">{bodies.map((body) => <li key={body.item_id}>
      <strong>{body.title}</strong><span>Thân máy bạn đã đánh giá{body.in_matrix === false ? " · chưa có trong bảng tương thích" : ""}</span>
    </li>)}</ul>}
    {bodies.length === 0 && <p>Bạn chưa đánh giá thân máy nào nên không có ống kính nào bị loại.</p>}
    {nBlocked > 0 && <p>Có {nBlocked} ống kính không lắp được trên bất kỳ máy nào của bạn nên không được gợi ý.</p>}
    {bodies.length > 0 && nBlocked === 0 && outsideMatrix.length > 0 && <p>Máy {outsideMatrix.map((body) => body.title).join(", ")} chưa có trong bảng tương thích nên hệ thống không loại ống kính nào.</p>}
    {nRemoved > 0 && <p>Trong danh sách này, {nRemoved} ống đã bị bỏ ra (vd {removed[0].title}).</p>}
  </aside>;
}

function ExplanationPanel({ explanation }: { explanation: RecommendationExplanation }) {
  return <section className="demo-explanation"><div className="demo-explanation-title">Gợi ý này liên quan gì tới máy của bạn?</div><p>{explanation.verified ? explanation.text : "Chưa đủ thông tin để giải thích gợi ý này."}</p>
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
    <main className="demo-shell demo-main"><MockNotice /><button className="demo-back-button" onClick={onBack}>← Quay lại danh sách gợi ý</button><span className="demo-eyebrow">Thông tin sản phẩm</span>
      <article className="demo-detail-card"><div className="demo-detail-visual" aria-hidden="true">{item.type_label}</div><div className="demo-detail-content"><div className="demo-type-row"><span>{item.type_label}</span><span>Hạng #{item.rank}</span></div><h1>{item.title}</h1><p className="demo-lead">Thông tin sản phẩm{item.explanation ? " và liên hệ với máy bạn đã đánh giá" : ""}.</p>
        {productLoading && <p role="status" className="demo-lead">Đang tải thông tin sản phẩm...</p>}
        {productError && <p role="alert" className="demo-lead">{productError}</p>}
        <dl className="demo-attributes"><div><dt>Loại sản phẩm</dt><dd>{item.type_label}</dd></div>{product?.mount && <div><dt>Ngàm</dt><dd>{formatMount(product.mount)}</dd></div>}{product?.khung && <div><dt>Định dạng</dt><dd>{formatFrame(product.khung)}</dd></div>}{product?.usecases_label?.length ? <div><dt>Phù hợp với</dt><dd>{product.usecases_label.join(", ")}</dd></div> : null}</dl>{item.explanation && <ExplanationPanel explanation={item.explanation} />}
      </div></article>
    </main>
  </div>;
}
