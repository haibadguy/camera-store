import { FormEvent, useEffect, useRef, useState } from "react";
import {
  IS_MOCK_SOURCE,
  fetchProductDetail,
  fetchRecommendations,
  QUICK_USER_PROFILES,
  RecommendationExplanation,
  RecommendationItem,
  RecommendationBody,
  RecommendationProductDetail,
  RecommendationResponse,
} from "./services/recommendationService";

type Props = { onExit: () => void };

function formatMount(mount: string): string {
  return mount === "nikon_f" ? "Nikon F" : mount === "canon_ef" ? "Canon EF" : mount === "khong_co" ? "Không áp dụng" : mount;
}

function formatFrame(frame: string): string {
  return frame === "apsc" ? "APS-C" : frame === "ff" ? "Full-frame" : frame;
}

function formatCameraName(title: string): string {
  const nikonModel = title.match(/\bNikon\s+D\d+[A-Z]*/i);
  if (nikonModel) return nikonModel[0];
  return title.split(" (")[0].split(" with ")[0];
}

function joinNames(names: string[]): string {
  if (names.length <= 1) return names[0] ?? "máy ảnh của bạn";
  return `${names.slice(0, -1).join(", ")} và ${names[names.length - 1]}`;
}

function formatExplanation(text: string): string {
  return text
    .replace(/^Gợi ý .*?\bvì\s+/i, "Sản phẩm này được chọn vì ")
    .replace(/\s*\(ngàm [^)]+\),?/gi, "")
    .replace(/\b(Nikon\s+D\d+[A-Z]*)\b.*?(?=\s+bạn đã đánh giá)/gi, "$1")
    .replace(/\s+\/\s+/g, " và ")
    .replace(/\s+,/g, ",")
    .replace(/đánh giá\s+và/g, "đánh giá và")
    .trim();
}

function formatFocalRange(range: RecommendationProductDetail["focal_mm"]): string | null {
  if (!range) return null;
  return range.min === range.max ? `${range.min} mm` : `${range.min}–${range.max} mm`;
}

function formatAperture(aperture: RecommendationProductDetail["max_aperture_f"]): string | null {
  if (!aperture) return null;
  return aperture.at_min_focal === aperture.at_max_focal
    ? `f/${aperture.at_min_focal}`
    : `f/${aperture.at_min_focal}–${aperture.at_max_focal}`;
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
    <p>{trail}</p><button className="demo-link-button" onClick={onExit}>Quay về cửa hàng</button>
  </div></header>;
}

const USER_ID_PATTERN = /^\d{1,9}$/;

// Nhãn chế độ dữ liệu mẫu, hiện trên mọi trang của luồng tư vấn
function MockNotice() {
  if (!IS_MOCK_SOURCE) return null;
  return <aside className="demo-preview-note" role="note" aria-label="Bản xem trước"><strong>Bản xem trước</strong>
    <p>Các gợi ý bên dưới dùng dữ liệu mẫu để bạn xem trước cách tư vấn hoạt động.</p></aside>;
}

function UserPicker({ onExit, onSelect }: { onExit: () => void; onSelect: (id: number) => void }) {
  const [userInput, setUserInput] = useState("");
  const [inputError, setInputError] = useState<string | null>(null);
  function submitUserId(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = userInput.trim();
    if (!USER_ID_PATTERN.test(value)) {
      setInputError("Mã hồ sơ cần là một số, ví dụ 409.");
      return;
    }
    setInputError(null);
    onSelect(Number(value));
  }
  return <div className="demo-page"><DemoHeader onExit={onExit} trail="Tìm thiết bị phù hợp với bạn" />
    <main className="demo-shell demo-main">
      <MockNotice />
      <span className="demo-eyebrow">Tư vấn dành riêng cho bạn</span><h1>Chọn hồ sơ để bắt đầu</h1>
      <p className="demo-lead">Hệ thống dựa trên những sản phẩm đã đánh giá để chọn ra các thiết bị phù hợp và tự động ẩn những ống kính không lắp được trên máy của bạn.</p>
      <section className="demo-user-grid" aria-label="Chọn hồ sơ gợi ý">
        {QUICK_USER_PROFILES.map(({ id, bodyTitles }) => <article className="demo-user-card" key={id}>
          <div className="demo-card-topline"><span>Hồ sơ có sẵn</span><strong>{bodyTitles.length} máy ảnh</strong></div>
          <h2>Hồ sơ {id}</h2>
          <div className="demo-profile-devices" aria-label="Máy ảnh trong hồ sơ">
            {bodyTitles.map((title) => <span key={title}>{formatCameraName(title)}</span>)}
          </div>
          <p>Những sản phẩm đã đánh giá sẽ không xuất hiện lại trong danh sách.</p>
          <button className="demo-primary-button" onClick={() => onSelect(id)}>Xem các lựa chọn</button>
        </article>)}
        <article className="demo-user-card">
          <form className="demo-user-form" onSubmit={submitUserId} aria-label="Tìm hồ sơ khác">
            <div className="demo-card-topline"><label htmlFor="demo-user-id">Hồ sơ khác</label><strong>0 – 67.660</strong></div>
            <h2>Nhập mã hồ sơ</h2>
            <p><input id="demo-user-id" name="user_id" inputMode="numeric" autoComplete="off" placeholder="vd 178"
              value={userInput} onChange={(event) => setUserInput(event.target.value)} /></p>
            {inputError && <p role="alert">{inputError}</p>}
            <button className="demo-primary-button" type="submit">Tìm gợi ý</button>
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
  return <div className="demo-page"><DemoHeader onExit={onExit} trail="Các lựa chọn dành riêng cho bạn" />
    <main className="demo-shell demo-main">
      <MockNotice />
      <button className="demo-back-button" onClick={onBack}>← Chọn hồ sơ khác</button>
      <span className="demo-eyebrow">Hồ sơ {userId}</span><h1>Những lựa chọn đáng xem</h1>
      {loading && <p role="status" className="demo-lead">Đang tải gợi ý...</p>}
      {error && <aside className="demo-mask-note" role="alert"><strong>Không tải được dữ liệu</strong><p>{error}</p><button className="demo-secondary-button" onClick={onRetry}>Thử lại</button></aside>}
      {response && <><p className="demo-lead">Những sản phẩm đã đánh giá sẽ không xuất hiện lại. Các lựa chọn phù hợp hơn được xếp ở phía trước.</p>
        <section className="demo-summary-grid" aria-label="Tóm tắt gợi ý"><div><span>Máy ảnh trong hồ sơ</span><strong>{response.n_bodies}</strong></div><div><span>Ống kính đã ẩn</span><strong>{response.mask.n_lenses_blocked}</strong></div><div><span>Sản phẩm gợi ý</span><strong>{response.items.length}</strong></div></section>
        <MaskNote response={response} />
        <section className="demo-recommendations" aria-label="Danh sách gợi ý">{response.items.map((item) => <article className="demo-recommendation-card" key={item.item_id}>
          <div className="demo-rank"><span>Gợi ý</span><strong>{item.rank}</strong></div><div className="demo-recommendation-content"><div className="demo-type-row"><span>{item.type_label}</span></div><h2>{item.title}</h2>
          {item.explanation?.verified && <ExplanationPanel explanation={item.explanation} />}
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
  const { n_lenses_blocked: nBlocked, n_blocked_in_topk_before_mask: nRemoved } = response.mask;
  const outsideMatrix = bodies.filter((body) => body.in_matrix === false);
  const bodyNames = bodies.map((body) => formatCameraName(body.title));
  const machineLabel = bodies.length > 1 ? `các máy ${joinNames(bodyNames)}` : `máy ${joinNames(bodyNames)}`;
  return <aside className="demo-mask-note" aria-label="Ống kính phù hợp với máy của bạn"><strong>Đã kiểm tra độ tương thích</strong>
    {bodies.length > 0 && <div className="demo-profile-devices demo-profile-devices-compact">{bodyNames.map((name) => <span key={name}>{name}</span>)}</div>}
    {bodies.length === 0 && <p>Hồ sơ này chưa có máy ảnh nên hệ thống chưa ẩn ống kính nào.</p>}
    {nBlocked > 0 && <p>Đã ẩn <strong>{nBlocked} ống kính</strong> không lắp được trên {machineLabel} của bạn.</p>}
    {bodies.length > 0 && nBlocked === 0 && outsideMatrix.length === 0 && <p>Không có ống kính nào cần ẩn với {machineLabel} của bạn.</p>}
    {bodies.length > 0 && nBlocked === 0 && outsideMatrix.length > 0 && <p>Chưa đủ dữ liệu để kiểm tra ống kính phù hợp với {machineLabel}.</p>}
    {nRemoved > 0 && <p>{nRemoved} sản phẩm không tương thích đã được loại khỏi kết quả đang xem.</p>}
  </aside>;
}

function ExplanationPanel({ explanation }: { explanation: RecommendationExplanation }) {
  return <section className="demo-explanation"><div className="demo-explanation-title">Vì sao sản phẩm này phù hợp?</div><p>{formatExplanation(explanation.text)}</p>
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
      <article className="demo-detail-card"><div className="demo-detail-visual" aria-hidden="true">{item.type_label}</div><div className="demo-detail-content"><div className="demo-type-row"><span>{item.type_label}</span><span>Gợi ý số {item.rank}</span></div><h1>{item.title}</h1><p className="demo-lead">Thông tin chính giúp bạn cân nhắc sản phẩm này{item.explanation?.verified ? " và lý do sản phẩm phù hợp với máy của bạn" : ""}.</p>
        {productLoading && <p role="status" className="demo-lead">Đang tải thông tin sản phẩm...</p>}
        {productError && <p role="alert" className="demo-lead">{productError}</p>}
        <dl className="demo-attributes"><div><dt>Loại sản phẩm</dt><dd>{item.type_label}</dd></div>{product?.mount && <div><dt>Loại ngàm</dt><dd>{formatMount(product.mount)}</dd></div>}{product?.khung && <div><dt>Kích thước cảm biến</dt><dd>{formatFrame(product.khung)}</dd></div>}{formatFocalRange(product?.focal_mm) && <div><dt>Tiêu cự</dt><dd>{formatFocalRange(product?.focal_mm)}</dd></div>}{formatAperture(product?.max_aperture_f) && <div><dt>Khẩu độ tối đa</dt><dd>{formatAperture(product?.max_aperture_f)}</dd></div>}{product?.usecases_label?.length ? <div><dt>Phù hợp để chụp</dt><dd>{product.usecases_label.join(", ")}</dd></div> : null}</dl>{item.explanation?.verified && <ExplanationPanel explanation={item.explanation} />}
      </div></article>
    </main>
  </div>;
}
