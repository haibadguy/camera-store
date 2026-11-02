export type CameraSpec = {
  sensor: string;
  resolution: string;
  mount: string;
  video: string;
  weight: string;
};

export type Product = {
  id: number;
  name: string;
  brand: string;
  category: string;
  price: number;
  originalPrice?: number;
  rating: number;
  reviewsCount: number;
  stock: number;
  badge?: string;
  image: string;
  description: string;
  specs: CameraSpec;
  aiMatchScore?: number;
  aiReasons?: string[];
  useCases: string[];
  compatLensId?: number;
};

export const formatVND = (amount: number) => new Intl.NumberFormat("vi-VN").format(amount) + " ₫";

type Props = {
  product: Product;
  compatibility?: "compatible" | "incompatible" | "unknown";
  onDetail: (product: Product) => void;
  onAddToCart: () => void;
};

export default function CatalogProductCard({ product, compatibility, onDetail, onAddToCart }: Props) {
  return (
    <article className="product-card">
      <div className="product-image-container" onClick={() => onDetail(product)}>
        <img src={product.image} alt={product.name} />
        {product.badge && <span className="status-badge">{product.badge}</span>}
        {product.aiMatchScore && <span className="ai-score-badge">Điểm minh họa {product.aiMatchScore}%</span>}
        {compatibility === "compatible" && <span className="compatibility-badge compatible">Tương thích với hồ sơ</span>}
        {compatibility === "incompatible" && <span className="compatibility-badge incompatible">Không tương thích với hồ sơ</span>}
      </div>
      <div className="product-card-body">
        <div className="product-brand-meta">{product.brand} • {product.category}</div>
        <h3 className="product-title" onClick={() => onDetail(product)}>{product.name}</h3>
        <div className="rating-summary">
          <span className="star-icon">★</span>
          <span className="score">{product.rating}</span>
          <span className="count">({product.reviewsCount} đánh giá)</span>
        </div>
        <div className="specs-pills-row">
          <span className="spec-pill">{product.specs.sensor}</span>
          <span className="spec-pill">{product.specs.resolution}</span>
          <span className="spec-pill">Ngàm {product.specs.mount}</span>
        </div>
        {product.aiReasons && product.aiReasons.length > 0 && (
          <div className="ai-reason-container">
            <div className="reason-title">Tiêu chí minh họa:</div>
            <ul className="reason-list">
              {product.aiReasons.map((reason) => <li key={reason}>✓ {reason}</li>)}
            </ul>
          </div>
        )}
        <div className="price-stock-row">
          <div className="price-container">
            <span className="main-price">{formatVND(product.price)}</span>
            {product.originalPrice && <span className="old-price">{formatVND(product.originalPrice)}</span>}
          </div>
          <div className="stock-indicator"><span className="status-dot"></span> Còn hàng</div>
        </div>
        <div className="card-buttons-row">
          <button className="add-cart-btn" onClick={onAddToCart}>Thêm vào giỏ</button>
          <button className="view-detail-btn" onClick={() => onDetail(product)}>Chi tiết</button>
        </div>
      </div>
    </article>
  );
}
