import { useMemo, useState } from "react";
import "./styles.css";

type CameraSpec = {
  sensor: string;
  resolution: string;
  mount: string;
  video: string;
  weight: string;
};

type Product = {
  id: number;
  name: string;
  brand: string;
  category: string;
  price: number;
  stock: number;
  badge?: string;
  image: string;
  description: string;
  specs: CameraSpec;
  aiReasons?: string[];
  useCases: string[];
};

const products: Product[] = [
  {
    id: 1,
    name: "Sony Alpha A7 IV",
    brand: "Sony",
    category: "Mirrorless",
    price: 54990000,
    stock: 5,
    badge: "Top AI Recommend",
    image: "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=85",
    description: "Máy ảnh Full-frame hybrid đỉnh cao cho cả chụp ảnh chân dung và quay phim chuyên nghiệp.",
    specs: { sensor: "Full-frame 35mm", resolution: "33.0 MP", mount: "Sony E-mount", video: "4K 60p 10-bit", weight: "658g" },
    aiReasons: [
      "Phù hợp chụp chân dung nhờ cảm biến Full-frame 33MP",
      "Tương thích ngàm Sony E-mount rộng rãi",
      "Quay phim 4K 60p sắc nét"
    ],
    useCases: ["portrait", "vlog", "travel"]
  },
  {
    id: 2,
    name: "Fujifilm X-T5",
    brand: "Fujifilm",
    category: "Mirrorless",
    price: 43990000,
    stock: 8,
    badge: "Phổ biến",
    image: "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=900&q=85",
    description: "Máy ảnh APS-C 40MP phong cách cổ điển, lý tưởng cho du lịch và nhiếp ảnh đường phố.",
    specs: { sensor: "APS-C X-Trans V", resolution: "40.2 MP", mount: "Fujifilm X-mount", video: "6.2K 30p", weight: "557g" },
    aiReasons: [
      "Nhỏ gọn nhẹ (557g) thích hợp phượt / du lịch",
      "Màu phim giả lập Fujifilm độc quyền",
      "Nằm trong ngân sách dưới 45 triệu"
    ],
    useCases: ["travel", "street"]
  },
  {
    id: 3,
    name: "Canon EOS R6 Mark II",
    brand: "Canon",
    category: "Mirrorless",
    price: 59990000,
    stock: 3,
    badge: "Chuyên nghiệp",
    image: "https://images.unsplash.com/photo-1606986628253-3b2f4a1a8b75?auto=format&fit=crop&w=900&q=85",
    description: "Tốc độ chụp 40fps siêu nhanh, lấy nét AI bắt nét mắt động vật và thể thao chuẩn xác.",
    specs: { sensor: "Full-frame Dual Pixel", resolution: "24.2 MP", mount: "Canon RF-mount", video: "4K 60p Oversampled", weight: "670g" },
    aiReasons: [
      "Tốc độ bắt nét AI 40fps cực đỉnh cho thể thao / động vật",
      "Cảm biến Full-frame khử nhiễu ISO cao xuất sắc",
      "Tương thích ngàm Canon RF"
    ],
    useCases: ["portrait", "sports", "vlog"]
  },
  {
    id: 4,
    name: "Sony ZV-E10 II",
    brand: "Sony",
    category: "Vlog Camera",
    price: 21990000,
    stock: 12,
    badge: "Giá tốt cho Vlog",
    image: "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=900&q=85",
    description: "Dòng máy ảnh chuyên dụng cho Vlogger, nhỏ gọn, micro 3 khoang lọc gió xuất sắc.",
    specs: { sensor: "APS-C Exmor R", resolution: "26.0 MP", mount: "Sony E-mount", video: "4K 60p", weight: "377g" },
    aiReasons: [
      "Tối ưu ngân sách dưới 25 triệu",
      "Chuyên dụng cho Vlogging và Livestream",
      "Siêu siêu nhẹ chỉ 377g"
    ],
    useCases: ["vlog", "travel"]
  },
  {
    id: 5,
    name: "Nikon Z6 III",
    brand: "Nikon",
    category: "Mirrorless",
    price: 64990000,
    stock: 4,
    badge: "Mới ra mắt",
    image: "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?auto=format&fit=crop&w=900&q=85",
    description: "Cảm biến Partially-stacked đầu tiên trên thế giới, màn hình xoay lật linh hoạt.",
    specs: { sensor: "Full-frame Stacked CMOS", resolution: "24.5 MP", mount: "Nikon Z-mount", video: "6K 60p N-RAW", weight: "760g" },
    aiReasons: [
      "Cảm biến Partially-stacked tốc độ xử lý tức thì",
      "Quay video 6K N-RAW chuyên nghiệp",
      "Tương thích ngàm Nikon Z"
    ],
    useCases: ["sports", "vlog", "portrait"]
  },
  {
    id: 6,
    name: "Sony FE 85mm F1.4 GM II",
    brand: "Sony",
    category: "Ống kính (Lens)",
    price: 47990000,
    stock: 6,
    badge: "Lens Chân dung",
    image: "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?auto=format&fit=crop&w=900&q=85",
    description: "Ống kính chân dung huyền thoại với khẩu độ F1.4 cho hiệu ứng Bokeh mịn màng.",
    specs: { sensor: "Ống kính Fix", resolution: "N/A", mount: "Sony E-mount", video: "AF bắt nét im lặng", weight: "642g" },
    aiReasons: [
      "Khẩu độ F1.4 xóa phông chân dung đỉnh cao",
      "Đạt chuẩn G Master cao cấp nhất của Sony"
    ],
    useCases: ["portrait"]
  }
];

const formatPrice = (price: number) => `${new Intl.NumberFormat("vi-VN").format(price)} VNĐ`;

export default function App() {
  const [view, setView] = useState<"store" | "consultant">("store");
  const [selectedBrand, setSelectedBrand] = useState("All");
  const [selectedUseCase, setSelectedUseCase] = useState("All");
  const [maxBudget, setMaxBudget] = useState<number>(70000000);
  const [mountFilter, setMountFilter] = useState("All");
  const [activeModalProduct, setActiveModalProduct] = useState<Product | null>(null);

  // AI Filtering logic (Constraint + Recommendation)
  const recommendedProducts = useMemo(() => {
    return products.filter((item) => {
      const matchBrand = selectedBrand === "All" || item.brand === selectedBrand;
      const matchUseCase = selectedUseCase === "All" || item.useCases.includes(selectedUseCase);
      const matchBudget = item.price <= maxBudget;
      const matchMount = mountFilter === "All" || item.specs.mount.toLowerCase().includes(mountFilter.toLowerCase());
      return matchBrand && matchUseCase && matchBudget && matchMount;
    });
  }, [selectedBrand, selectedUseCase, maxBudget, mountFilter]);

  return (
    <div className="app-shell">
      {/* Top Banner */}
      <div className="announcement">
        🎉 <strong>ĐỒ ÁN CAMERA STORE:</strong> DEMO HỆ THỐNG GỢI Ý & TƯ VẤN MÁY ẢNH AI (RECOMMENDATION SYSTEM)
      </div>

      {/* Header */}
      <header className="topbar">
        <div className="brand" onClick={() => setView("store")}>
          <span className="brand-mark">📷</span>
          <span>CAMERA STORE <small>AI Powered</small></span>
        </div>
        <nav className="main-nav">
          <button className={view === "store" ? "nav-link active" : "nav-link"} onClick={() => setView("store")}>
            Danh mục máy ảnh
          </button>
          <button className={view === "consultant" ? "nav-link active ai-highlight" : "nav-link ai-highlight"} onClick={() => setView("consultant")}>
            ✨ Tư vấn AI cá nhân hóa
          </button>
        </nav>
        <div className="top-actions">
          <button className="primary-button small" onClick={() => setView("consultant")}>
            🤖 Trợ lý AI Tư Vấn
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-container">
        {/* HERO SECTION */}
        <section className="hero-banner">
          <div className="hero-content">
            <span className="badge-ai">✨ AI Recommendation Engine 2.0</span>
            <h1>Tìm chiếc Máy Ảnh Hoàn Hảo Dành Riêng Cho Bạn</h1>
            <p>
              Hệ thống AI phân tích thông số kỹ thuật (Camera Specs), ngân sách và nhu cầu thực tế 
              để đưa ra gợi ý **chính xác kèm lý do giải thích minh bạch (Explainable Recommendations)**.
            </p>
            <div className="hero-buttons">
              <button className="primary-button Large" onClick={() => setView("consultant")}>
                Bắt đầu Tư vấn AI Ngay →
              </button>
              <button className="secondary-button" onClick={() => setView("store")}>
                Xem tất cả sản phẩm
              </button>
            </div>
          </div>
        </section>

        {/* AI CONSULTANT MODAL / SECTION */}
        {view === "consultant" && (
          <section className="ai-consultant-section">
            <div className="consultant-header">
              <h2>🤖 Trợ Lý Tư Vấn Máy Ảnh AI (Constraint & Explainable Engine)</h2>
              <p>Hãy chọn các tiêu chí ràng buộc của bạn, AI sẽ tự động phân tích và đưa ra máy ảnh tối ưu nhất!</p>
            </div>

            <div className="filter-card-grid">
              {/* Constraint 1: Ngân sách */}
              <div className="filter-box">
                <label>💰 Ngân sách tối đa:</label>
                <div className="budget-value">{formatPrice(maxBudget)}</div>
                <input
                  type="range"
                  min={20000000}
                  max={70000000}
                  step={5000000}
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(Number(e.target.value))}
                />
              </div>

              {/* Constraint 2: Nhu cầu chụp */}
              <div className="filter-box">
                <label>🎯 Nhu cầu chụp chính:</label>
                <select value={selectedUseCase} onChange={(e) => setSelectedUseCase(e.target.value)}>
                  <option value="All">Tất cả nhu cầu</option>
                  <option value="portrait">📸 Chụp Chân dung (Portrait)</option>
                  <option value="travel">✈️ Phượt / Du lịch (Travel)</option>
                  <option value="vlog">🎥 Quay Vlogging / Youtube</option>
                  <option value="sports">🏃 Chụp Thể thao / Động vật (Sports)</option>
                </select>
              </div>

              {/* Constraint 3: Hãng sản xuất */}
              <div className="filter-box">
                <label>🏢 Thương hiệu yêu thích:</label>
                <select value={selectedBrand} onChange={(e) => setSelectedBrand(e.target.value)}>
                  <option value="All">Tất cả thương hiệu</option>
                  <option value="Sony">Sony</option>
                  <option value="Canon">Canon</option>
                  <option value="Fujifilm">Fujifilm</option>
                  <option value="Nikon">Nikon</option>
                </select>
              </div>

              {/* Constraint 4: Ngàm Lens */}
              <div className="filter-box">
                <label>🔌 Tương thích Ngàm (Lens Mount):</label>
                <select value={mountFilter} onChange={(e) => setMountFilter(e.target.value)}>
                  <option value="All">Tất cả ngàm</option>
                  <option value="Sony E-mount">Sony E-mount</option>
                  <option value="Canon RF-mount">Canon RF-mount</option>
                  <option value="Fujifilm X-mount">Fujifilm X-mount</option>
                  <option value="Nikon Z-mount">Nikon Z-mount</option>
                </select>
              </div>
            </div>
          </section>
        )}

        {/* PRODUCT CATALOG GRID */}
        <section className="catalog-section">
          <div className="section-title">
            <h3>
              {view === "consultant"
                ? `🎯 Kết quả AI Gợi Ý (${recommendedProducts.length} sản phẩm phù hợp)`
                : "📸 Danh Sách Máy Ảnh & Thiết Bị"}
            </h3>
            <span className="results-count">Hiển thị {recommendedProducts.length} / {products.length} máy ảnh</span>
          </div>

          <div className="products-grid">
            {recommendedProducts.length === 0 ? (
              <div className="no-results">
                <span>🔍</span>
                <p>Không tìm thấy máy ảnh nào khớp hoàn toàn với ràng buộc của bạn.</p>
                <button className="secondary-button" onClick={() => { setMaxBudget(70000000); setSelectedBrand("All"); setSelectedUseCase("All"); setMountFilter("All"); }}>
                  Đặt lại bộ lọc
                </button>
              </div>
            ) : (
              recommendedProducts.map((item) => (
                <div key={item.id} className="product-card">
                  <div className="card-image-wrap">
                    <img src={item.image} alt={item.name} />
                    {item.badge && <span className="card-badge">{item.badge}</span>}
                  </div>

                  <div className="card-body">
                    <div className="card-brand">{item.brand} • {item.category}</div>
                    <h4 className="card-title">{item.name}</h4>
                    <p className="card-desc">{item.description}</p>

                    {/* Camera Specs preview */}
                    <div className="specs-pills">
                      <span>📷 {item.specs.sensor}</span>
                      <span>📐 {item.specs.resolution}</span>
                      <span>🔌 {item.specs.mount}</span>
                    </div>

                    {/* EXPLAINABLE REASONS (Giải thích lý do gợi ý) */}
                    {item.aiReasons && item.aiReasons.length > 0 && (
                      <div className="ai-reasons-box">
                        <div className="reasons-header">💡 Lý do AI gợi ý cho bạn:</div>
                        <ul>
                          {item.aiReasons.map((reason, index) => (
                            <li key={index}>✓ {reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="card-footer">
                      <div className="price-tag">{formatPrice(item.price)}</div>
                      <button className="primary-button small" onClick={() => setActiveModalProduct(item)}>
                        Xem Thông Số Chi Tiết
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* MODAL CHI TIẾT CAMERA SPECS */}
        {activeModalProduct && (
          <div className="modal-overlay" onClick={() => setActiveModalProduct(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <button className="modal-close" onClick={() => setActiveModalProduct(null)}>✕</button>
              <div className="modal-header">
                <span className="modal-brand">{activeModalProduct.brand}</span>
                <h2>{activeModalProduct.name}</h2>
                <div className="modal-price">{formatPrice(activeModalProduct.price)}</div>
              </div>

              <div className="modal-body">
                <img src={activeModalProduct.image} alt={activeModalProduct.name} className="modal-img" />

                <h4>📋 Bảng Thông Số Kỹ Thuật Chi Tiết (Camera Specifications):</h4>
                <table className="specs-table">
                  <tbody>
                    <tr><td>Cảm biến (Sensor)</td><td><strong>{activeModalProduct.specs.sensor}</strong></td></tr>
                    <tr><td>Độ phân giải (Resolution)</td><td><strong>{activeModalProduct.specs.resolution}</strong></td></tr>
                    <tr><td>Ngàm Lens (Mount)</td><td><strong>{activeModalProduct.specs.mount}</strong></td></tr>
                    <tr><td>Quay Video (Video Specs)</td><td><strong>{activeModalProduct.specs.video}</strong></td></tr>
                    <tr><td>Trọng lượng (Weight)</td><td><strong>{activeModalProduct.specs.weight}</strong></td></tr>
                  </tbody>
                </table>

                {activeModalProduct.aiReasons && (
                  <div className="ai-reasons-box highlighted">
                    <div className="reasons-header">🤖 Phân tích AI Recommendation:</div>
                    <ul>
                      {activeModalProduct.aiReasons.map((r, i) => (
                        <li key={i}>✅ {r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>© 2026 Camera Store — Đồ Án Hệ Thống Gợi Ý Cá Nhân Hóa Thiết Bị Nhiếp Ảnh</p>
      </footer>
    </div>
  );
}
