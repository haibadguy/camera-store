import CatalogProductCard, { Product } from "./CatalogProductCard";

type Props = {
  products: Product[];
  compatibilityStatus: Record<number, "compatible" | "incompatible" | "unknown">;
  compatibilityEnabled: boolean;
  onDetail: (product: Product) => void;
  onAddToCart: (product: Product) => void;
  onReset: () => void;
};

export default function CatalogProductGrid({ products, compatibilityStatus, compatibilityEnabled, onDetail, onAddToCart, onReset }: Props) {
  if (products.length === 0) {
    return (
      <div className="no-products-card">
        <h3>Không tìm thấy sản phẩm phù hợp</h3>
        <p>Rất tiếc, không có máy ảnh nào khớp với các tiêu chí lọc hiện tại của bạn.</p>
        <button type="button" className="secondary-action-btn dark" onClick={onReset}>Xóa bộ lọc tìm kiếm</button>
      </div>
    );
  }
  return (
    <div className="products-grid">
      {products.map((product) => (
        <CatalogProductCard
          key={product.id}
          product={product}
          compatibility={compatibilityEnabled ? compatibilityStatus[product.id] : undefined}
          onDetail={onDetail}
          onAddToCart={() => onAddToCart(product)}
        />
      ))}
    </div>
  );
}
