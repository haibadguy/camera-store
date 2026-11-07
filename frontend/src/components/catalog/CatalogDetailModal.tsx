import { Product, formatVND } from "./CatalogProductCard";

type Props = {
  product: Product;
  onClose: () => void;
  onAddToCart: () => void;
};

export default function CatalogDetailModal({ product, onClose, onAddToCart }: Props) {
  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="detail-dialog-box" role="dialog" aria-modal="true" aria-labelledby="catalog-detail-title" onClick={(event) => event.stopPropagation()}>
        <button type="button" className="dialog-close-btn" aria-label="Đóng chi tiết sản phẩm" onClick={onClose}>×</button>
        <div className="detail-dialog-layout">
        <div className="detail-media-wrap"><img src={product.image} alt={product.name} /></div>
        <div className="detail-specs-wrap">
          <div className="product-brand-meta">{product.brand} • {product.category}</div>
          <h2 id="catalog-detail-title">{product.name}</h2>
          <div className="detail-price">{formatVND(product.price)}</div>
          <p className="detail-description">{product.description}</p>
          <h4>Thông số kỹ thuật chi tiết:</h4>
          <table className="specs-table"><tbody>
            <tr><td>Cảm biến (Sensor)</td><td><strong>{product.specs.sensor}</strong></td></tr>
            <tr><td>Độ phân giải</td><td><strong>{product.specs.resolution}</strong></td></tr>
            <tr><td>Ngàm Lens tương thích</td><td><strong>{product.specs.mount}</strong></td></tr>
            <tr><td>Quay video</td><td><strong>{product.specs.video}</strong></td></tr>
            <tr><td>Trọng lượng body</td><td><strong>{product.specs.weight}</strong></td></tr>
          </tbody></table>
          <p className="catalog-demo-note">Thông số và giá chỉ để minh họa giao diện, không có giao dịch thật.</p>
          <button type="button" className="add-cart-large-btn" onClick={onAddToCart}>Chọn trong demo</button>
        </div>
        </div>
      </div>
    </div>
  );
}
