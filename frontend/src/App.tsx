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
};

const PRODUCTS_DATA: Product[] = [
  {
    id: 1,
    name: "Máy ảnh Sony Alpha A7 IV (Chính Hãng)",
    brand: "Sony",
    category: "Mirrorless",
    price: 54990000,
    originalPrice: 59990000,
    rating: 4.9,
    reviewsCount: 142,
    stock: 8,
    badge: "Bán Chạy Nhất",
    image: "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=80",
    description: "Cảm biến Full-frame Exmor R 33.0 MP, quay phim 4K 60p 10-bit 4:2:2, lấy nét tự động AI bắt nét mắt theo thời gian thực.",
    specs: { sensor: "Full-frame 35mm", resolution: "33.0 MP", mount: "Sony E-mount", video: "4K 60p 10-bit", weight: "658g" },
    aiMatchScore: 98,
    aiReasons: [
      "Phù hợp hoàn hảo cho Chân dung & Sự kiện nhờ cảm biến Full-frame 33MP",
      "Hệ thống lấy nét mắt Real-time AF chuẩn xác nhất phân khúc",
      "Nằm đúng khoảng ngân sách 50 - 60 triệu VNĐ"
    ],
    useCases: ["portrait", "event", "vlog"]
  },
  {
    id: 2,
    name: "Máy ảnh Canon EOS R6 Mark II Body",
    brand: "Canon",
    category: "Mirrorless",
    price: 58990000,
    originalPrice: 63500000,
    rating: 4.8,
    reviewsCount: 98,
    stock: 5,
    badge: "Khuyên Dùng",
    image: "https://images.unsplash.com/photo-1606986628253-3b2f4a1a8b75?auto=format&fit=crop&w=800&q=80",
    description: "Tốc độ chụp liên tiếp 40 hình/giây, chống rung IBIS 8 stop, lấy nét Dual Pixel CMOS AF II nhận diện động vật & phương tiện.",
    specs: { sensor: "Full-frame CMOS", resolution: "24.2 MP", mount: "Canon RF-mount", video: "4K 60p 6K Oversampled", weight: "670g" },
    aiMatchScore: 95,
    aiReasons: [
      "Tốc độ chụp 40fps siêu nhanh lý tưởng cho thể thao & động vật",
      "Chống rung trong thân máy 8 stop hỗ trợ chụp đêm không cần tripod",
      "Tương thích hệ sinh thái Lens Canon RF cao cấp"
    ],
    useCases: ["sports", "portrait", "event"]
  },
  {
    id: 3,
    name: "Máy ảnh Fujifilm X-T5 Body (Silver)",
    brand: "Fujifilm",
    category: "Mirrorless",
    price: 42990000,
    originalPrice: 45990000,
    rating: 4.9,
    reviewsCount: 165,
    stock: 12,
    badge: "Màu Phim Đẹp",
    image: "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=800&q=80",
    description: "Cảm biến APS-C X-Trans CMOS 5 HR 40.2 MP, giả lập màu phim Film Simulation độc quyền, bánh xe điều khiển cơ học cổ điển.",
    specs: { sensor: "APS-C X-Trans V", resolution: "40.2 MP", mount: "Fujifilm X-mount", video: "6.2K 30p 10-bit", weight: "557g" },
    aiMatchScore: 92,
    aiReasons: [
      "Thiết kế hoài cổ gọn nhẹ (557g) lý tưởng cho phượt & du lịch",
      "19 chế độ giả lập màu phim trứ danh không cần chỉnh sửa post-prod",
      "Độ phân giải siêu cao 40.2MP cho chi tiết ảnh sắc nét"
    ],
    useCases: ["travel", "street", "portrait"]
  },
  {
    id: 4,
    name: "Máy ảnh Sony ZV-E10 II Kit 16-50mm",
    brand: "Sony",
    category: "Vlog Camera",
    price: 22990000,
    originalPrice: 24500000,
    rating: 4.7,
    reviewsCount: 210,
    stock: 15,
    badge: "Vlog & TikTok",
    image: "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=800&q=80",
    description: "Máy ảnh chuyên dụng sáng tạo nội dung, micro 3 khoang định hướng có lọc gió, nút làm mờ nền Product Showcase tiện lợi.",
    specs: { sensor: "APS-C Exmor R", resolution: "26.0 MP", mount: "Sony E-mount", video: "4K 60p 10-bit", weight: "377g" },
    aiMatchScore: 94,
    aiReasons: [
      "Ngân sách tối ưu dưới 25 triệu VNĐ cho người bắt đầu",
      "Thiết kế màn hình xoay lật 180 độ & micro chống ồn chuyên quay Vlog",
      "Trọng lượng siêu nhẹ 377g dễ dàng cầm tay cả ngày"
    ],
    useCases: ["vlog", "travel"]
  },
  {
    id: 5,
    name: "Máy ảnh Nikon Z6 III Body",
    brand: "Nikon",
    category: "Mirrorless",
    price: 64990000,
    originalPrice: 67900000,
    rating: 4.9,
    reviewsCount: 42,
    stock: 4,
    badge: "Công Nghệ Mới",
    image: "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?auto=format&fit=crop&w=800&q=80",
    description: "Cảm biến Partially-stacked CMOS 24.5 MP đột phá, kính ngắm EVF 5.76 triệu điểm ảnh độ sáng 4000 nits siêu thực.",
    specs: { sensor: "Full-frame Partially-stacked", resolution: "24.5 MP", mount: "Nikon Z-mount", video: "6K 60p N-RAW", weight: "760g" },
    aiMatchScore: 89,
    aiReasons: [
      "Cảm biến Partially-Stacked đọc dữ liệu cực nhanh chống biến dạng rolling shutter",
      "Quay video 6K 60p N-RAW trực tiếp vào thẻ nhớ",
      "Kính ngắm EVF sáng nhất thế giới 4000 nits"
    ],
    useCases: ["sports", "vlog", "event"]
  },
  {
    id: 6,
    name: "Ống kính Sony FE 85mm F1.4 GM II",
    brand: "Sony",
    category: "Ống kính",
    price: 47990000,
    originalPrice: 49900000,
    rating: 5.0,
    reviewsCount: 34,
    stock: 6,
    badge: "Master Chân Dung",
    image: "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?auto=format&fit=crop&w=800&q=80",
    description: "Ống kính chân dung tiêu cự vàng 85mm khẩu độ F1.4, mô-tơ lấy nét XD Linear êm ái, xóa phông Bokeh tròn mịn nghệ thuật.",
    specs: { sensor: "Ống kính Fix Chân dung", resolution: "N/A", mount: "Sony E-mount", video: "AF êm ái không thở", weight: "642g" },
    aiMatchScore: 97,
    aiReasons: [
      "Tiêu chuẩn vàng 85mm F1.4 cho ảnh chân dung xóa phông lung linh",
      "Thấu kính XA cao cấp triệt tiêu quang sai tuyệt đối",
      "Tương thích hoàn toàn với các body Sony Full-frame"
    ],
    useCases: ["portrait", "event"]
  }
];

const formatVND = (amount: number) => {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount);
};

export default function App() {
  // Search & Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBrand, setSelectedBrand] = useState("All");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [maxPrice, setMaxPrice] = useState<number>(70000000);
  const [selectedMount, setSelectedMount] = useState("All");
  const [selectedUseCase, setSelectedUseCase] = useState("All");
  const [sortBy, setSortBy] = useState<"featured" | "price-asc" | "price-desc" | "rating">("featured");

  // UI States
  const [cart, setCart] = useState<Product[]>([]);
  const [isAiWizardOpen, setIsAiWizardOpen] = useState(false);
  const [detailModalProduct, setDetailModalProduct] = useState<Product | null>(null);

  // Wizard States
  const [wizardStep, setWizardStep] = useState(1);
  const [wizardBudget, setWizardBudget] = useState(50000000);
  const [wizardNeed, setWizardNeed] = useState("portrait");
  const [wizardBrand, setWizardBrand] = useState("All");

  // Filtered products logic
  const filteredProducts = useMemo(() => {
    let result = PRODUCTS_DATA.filter((p) => {
      const matchSearch = searchQuery === "" || `${p.name} ${p.brand} ${p.category}`.toLowerCase().includes(searchQuery.toLowerCase());
      const matchBrand = selectedBrand === "All" || p.brand === selectedBrand;
      const matchCategory = selectedCategory === "All" || p.category === selectedCategory;
      const matchPrice = p.price <= maxPrice;
      const matchMount = selectedMount === "All" || p.specs.mount.toLowerCase().includes(selectedMount.toLowerCase());
      const matchUseCase = selectedUseCase === "All" || p.useCases.includes(selectedUseCase);
      return matchSearch && matchBrand && matchCategory && matchPrice && matchMount && matchUseCase;
    });

    if (sortBy === "price-asc") result.sort((a, b) => a.price - b.price);
    if (sortBy === "price-desc") result.sort((a, b) => b.price - a.price);
    if (sortBy === "rating") result.sort((a, b) => b.rating - a.rating);

    return result;
  }, [searchQuery, selectedBrand, selectedCategory, maxPrice, selectedMount, selectedUseCase, sortBy]);

  const addToCart = (product: Product) => {
    if (!cart.some((item) => item.id === product.id)) {
      setCart([...cart, product]);
    }
  };

  const applyAiWizardResult = () => {
    setMaxPrice(wizardBudget);
    setSelectedUseCase(wizardNeed);
    setSelectedBrand(wizardBrand);
    setIsAiWizardOpen(false);
    setWizardStep(1);
  };

  const resetAllFilters = () => {
    setSearchQuery("");
    setSelectedBrand("All");
    setSelectedCategory("All");
    setMaxPrice(70000000);
    setSelectedMount("All");
    setSelectedUseCase("All");
    setSortBy("featured");
  };

  return (
    <div className="store-app">
      {/* 1. TOP UTILITY HEADER BAR */}
      <div className="utility-bar">
        <div className="utility-container">
          <div className="utility-left">
            <span>📍 Hệ thống Showroom: Hà Nội • TP. Hồ Chí Minh • Đà Nẵng</span>
            <span className="divider">|</span>
            <span>📞 Hotline tư vấn: <strong>1900 6789</strong> (8:00 - 21:30)</span>
          </div>
          <div className="utility-right">
            <a href="#support">Tra cứu đơn hàng</a>
            <a href="#tradein">Thu cũ đổi mới máy ảnh</a>
            <a href="#blog">Kinh nghiệm nhiếp ảnh</a>
          </div>
        </div>
      </div>

      {/* 2. MAIN NAVIGATION HEADER */}
      <header className="main-header">
        <div className="header-container">
          {/* Logo */}
          <div className="logo-brand" onClick={resetAllFilters}>
            <div className="logo-icon">📷</div>
            <div className="logo-text">
              <span className="brand-name">CAMERA STORE</span>
              <span className="brand-tagline">Chuyên Thiết Bị Nhiếp Ảnh & Tư Vấn AI</span>
            </div>
          </div>

          {/* Main Search Bar */}
          <div className="search-bar-wrap">
            <div className="search-input-group">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                placeholder="Nhập tên máy ảnh, ống kính, thương hiệu (vd: Sony A7 IV, Canon R6...)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button className="clear-search" onClick={() => setSearchQuery("")}>✕</button>
              )}
            </div>
          </div>

          {/* Right Header Utilities */}
          <div className="header-actions">
            <button className="ai-advisor-btn" onClick={() => setIsAiWizardOpen(true)}>
              <span className="sparkle-icon">✨</span>
              <div className="btn-text">
                <small>Chưa biết chọn máy nào?</small>
                <strong>Trợ Lý Tư Vấn AI</strong>
              </div>
            </button>

            <div className="cart-widget">
              <div className="cart-icon-wrap">
                🛒
                {cart.length > 0 && <span className="cart-badge">{cart.length}</span>}
              </div>
              <div className="cart-info">
                <small>Giỏ hàng</small>
                <strong>{cart.length} sản phẩm</strong>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 3. CATEGORY NAVIGATION STRIP */}
      <nav className="category-strip">
        <div className="strip-container">
          <button className={selectedCategory === "All" ? "strip-item active" : "strip-item"} onClick={() => setSelectedCategory("All")}>
            Tất Cả Sản Phẩm
          </button>
          <button className={selectedCategory === "Mirrorless" ? "strip-item active" : "strip-item"} onClick={() => setSelectedCategory("Mirrorless")}>
            Máy Ảnh Mirrorless
          </button>
          <button className={selectedCategory === "Ống kính" ? "strip-item active" : "strip-item"} onClick={() => setSelectedCategory("Ống kính")}>
            Ống Kính (Lens)
          </button>
          <button className={selectedCategory === "Vlog Camera" ? "strip-item active" : "strip-item"} onClick={() => setSelectedCategory("Vlog Camera")}>
            Máy Ảnh Vlog & Compact
          </button>
          <button className="strip-item ai-tab" onClick={() => setIsAiWizardOpen(true)}>
            🤖 Thuật Toán Gợi Ý AI (Cosine Specs)
          </button>
        </div>
      </nav>

      {/* 4. PROMOTIONAL PROMO HERO BANNER */}
      <section className="hero-promo-section">
        <div className="hero-banner-container">
          <div className="banner-content">
            <span className="banner-tag">🔥 CHƯƠNG TRÌNH ĐẶC BIỆT</span>
            <h1>Tư Vấn & Gợi Ý Máy Ảnh Chuẩn Xác Nhờ Thuật Toán AI</h1>
            <p>
              Hệ thống tự động đối chiếu thông số kỹ thuật (Camera Specs: Cảm biến, Ngàm Lens, ISO) 
              với ngân sách và nhu cầu của bạn để đưa ra danh sách sản phẩm tối ưu nhất kèm <strong>lý do giải thích minh bạch</strong>.
            </p>
            <div className="banner-buttons">
              <button className="btn-primary-large" onClick={() => setIsAiWizardOpen(true)}>
                ✨ Mở Trợ Lý Tư Vấn AI Ngay
              </button>
              <button className="btn-outline-large" onClick={() => setSelectedCategory("Mirrorless")}>
                Xem Danh Mục Máy Ảnh Full-Frame
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 5. MAIN CATALOG & SIDEBAR FILTER SECTION */}
      <main className="catalog-main-layout">
        {/* SIDEBAR FILTER PANEL */}
        <aside className="filter-sidebar">
          <div className="sidebar-header">
            <h3>⚙️ Bộ Lọc Tìm Kiếm</h3>
            {(selectedBrand !== "All" || selectedUseCase !== "All" || selectedMount !== "All" || maxPrice < 70000000) && (
              <button className="btn-reset-filters" onClick={resetAllFilters}>Xóa bộ lọc</button>
            )}
          </div>

          {/* Filter: Nhu cầu chụp */}
          <div className="filter-group">
            <h4 className="filter-title">🎯 Nhu Cầu Sử Dụng</h4>
            <div className="radio-list">
              {[
                { id: "All", label: "Tất cả nhu cầu" },
                { id: "portrait", label: "📸 Chụp Chân dung & Xóa phông" },
                { id: "travel", label: "✈️ Phượt & Du lịch gọn nhẹ" },
                { id: "vlog", label: "🎥 Quay Vlogging & Youtube" },
                { id: "sports", label: "🏃 Chụp Thể thao & Động vật" }
              ].map((item) => (
                <label key={item.id} className="radio-item">
                  <input
                    type="radio"
                    name="usecase"
                    checked={selectedUseCase === item.id}
                    onChange={() => setSelectedUseCase(item.id)}
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Filter: Ngân sách */}
          <div className="filter-group">
            <h4 className="filter-title">💰 Ngân Sách Tối Đa</h4>
            <div className="price-slider-wrap">
              <div className="price-display">{formatVND(maxPrice)}</div>
              <input
                type="range"
                min={20000000}
                max={70000000}
                step={5000000}
                value={maxPrice}
                onChange={(e) => setMaxPrice(Number(e.target.value))}
              />
              <div className="price-range-labels">
                <span>20 Tr</span>
                <span>70 Tr+</span>
              </div>
            </div>
          </div>

          {/* Filter: Thương hiệu */}
          <div className="filter-group">
            <h4 className="filter-title">🏢 Hãng Sản Xuất</h4>
            <div className="checkbox-list">
              {["All", "Sony", "Canon", "Fujifilm", "Nikon"].map((brand) => (
                <button
                  key={brand}
                  className={selectedBrand === brand ? "filter-chip active" : "filter-chip"}
                  onClick={() => setSelectedBrand(brand)}
                >
                  {brand === "All" ? "Tất cả hãng" : brand}
                </button>
              ))}
            </div>
          </div>

          {/* Filter: Tương thích Ngàm Lens */}
          <div className="filter-group">
            <h4 className="filter-title">🔌 Ngàm Lens Tương Thích</h4>
            <select
              className="select-control"
              value={selectedMount}
              onChange={(e) => setSelectedMount(e.target.value)}
            >
              <option value="All">Tất cả ngàm lens</option>
              <option value="Sony E-mount">Sony E-mount</option>
              <option value="Canon RF-mount">Canon RF-mount</option>
              <option value="Fujifilm X-mount">Fujifilm X-mount</option>
              <option value="Nikon Z-mount">Nikon Z-mount</option>
            </select>
          </div>
        </aside>

        {/* PRODUCTS GRID CONTENT AREA */}
        <section className="products-content-area">
          {/* Toolbar Header */}
          <div className="products-toolbar">
            <div className="toolbar-info">
              <h2>Danh Sách Thiết Bị Nhiếp Ảnh</h2>
              <span className="count-badge">Tìm thấy {filteredProducts.length} sản phẩm</span>
            </div>

            <div className="sort-controls">
              <label>Sắp xếp theo:</label>
              <select
                className="select-control"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
              >
                <option value="featured">Sản Phẩm Nổi Bật</option>
                <option value="price-asc">Giá: Thấp đến Cao</option>
                <option value="price-desc">Giá: Cao đến Thấp</option>
                <option value="rating">Đánh Giá Cao Nhất</option>
              </select>
            </div>
          </div>

          {/* Active Applied Filters Bar */}
          {(selectedBrand !== "All" || selectedUseCase !== "All" || selectedMount !== "All" || maxPrice < 70000000) && (
            <div className="active-filters-bar">
              <span className="bar-label">Bộ lọc đang bật:</span>
              {selectedBrand !== "All" && <span className="active-tag">Hãng: {selectedBrand}</span>}
              {selectedUseCase !== "All" && <span className="active-tag">Nhu cầu: {selectedUseCase}</span>}
              {selectedMount !== "All" && <span className="active-tag">Ngàm: {selectedMount}</span>}
              {maxPrice < 70000000 && <span className="active-tag">Dưới: {formatVND(maxPrice)}</span>}
              <button className="clear-all-text" onClick={resetAllFilters}>Xóa tất cả</button>
            </div>
          )}

          {/* Product Cards Grid */}
          {filteredProducts.length === 0 ? (
            <div className="empty-catalog-box">
              <div className="empty-icon">📷</div>
              <h3>Không tìm thấy máy ảnh phù hợp</h3>
              <p>Rất tiếc, không có sản phẩm nào khớp hoàn toàn với các bộ lọc bạn đã chọn.</p>
              <button className="btn-secondary" onClick={resetAllFilters}>Xóa bộ lọc để xem tất cả</button>
            </div>
          ) : (
            <div className="ecommerce-products-grid">
              {filteredProducts.map((product) => (
                <article key={product.id} className="ecom-product-card">
                  {/* Card Thumbnail & Badge */}
                  <div className="card-thumb-area" onClick={() => setDetailModalProduct(product)}>
                    <img src={product.image} alt={product.name} />
                    {product.badge && <span className="badge-promo">{product.badge}</span>}
                    {product.aiMatchScore && (
                      <span className="badge-ai-match">🤖 AI Match {product.aiMatchScore}%</span>
                    )}
                  </div>

                  {/* Card Body Information */}
                  <div className="card-info-area">
                    <div className="brand-meta">{product.brand} • {product.category}</div>
                    <h3 className="product-name" onClick={() => setDetailModalProduct(product)}>
                      {product.name}
                    </h3>

                    {/* Ratings */}
                    <div className="rating-row">
                      <span className="stars">★★★★★</span>
                      <span className="rating-score">{product.rating}</span>
                      <span className="reviews-count">({product.reviewsCount} đánh giá)</span>
                    </div>

                    {/* Key Technical Specs Grid */}
                    <div className="key-specs-grid">
                      <div className="spec-pill">📷 {product.specs.sensor}</div>
                      <div className="spec-pill">📐 {product.specs.resolution}</div>
                      <div className="spec-pill">🔌 {product.specs.mount}</div>
                    </div>

                    {/* EXPLAINABLE REASONS (GIẢI THÍCH LÝ DO GỢI Ý CỦA AI) */}
                    {product.aiReasons && product.aiReasons.length > 0 && (
                      <div className="ai-explainable-box">
                        <div className="explain-header">💡 Lý do AI gợi ý cho bạn:</div>
                        <ul className="explain-list">
                          {product.aiReasons.map((reason, i) => (
                            <li key={i}>✓ {reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Price & Stock Status */}
                    <div className="price-and-stock">
                      <div className="price-block">
                        <div className="current-price">{formatVND(product.price)}</div>
                        {product.originalPrice && (
                          <div className="original-price">{formatVND(product.originalPrice)}</div>
                        )}
                      </div>
                      <div className="stock-status">
                        <span className="green-dot">●</span> Còn hàng
                      </div>
                    </div>

                    {/* Card Actions */}
                    <div className="card-actions">
                      <button className="btn-add-cart" onClick={() => addToCart(product)}>
                        🛒 Thêm vào giỏ
                      </button>
                      <button className="btn-quick-view" onClick={() => setDetailModalProduct(product)}>
                        Chi tiết
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>

      {/* 6. AI RECOMMENDATION WIZARD DIALOG MODAL */}
      {isAiWizardOpen && (
        <div className="modal-backdrop" onClick={() => setIsAiWizardOpen(false)}>
          <div className="wizard-modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setIsAiWizardOpen(false)}>✕</button>

            <div className="wizard-header">
              <span className="sparkle-badge">✨ Thuật Toán AI Recommendation Engine</span>
              <h2>Trợ Lý Tư Vấn Máy Ảnh Thông Minh</h2>
              <p>Trả lời 3 câu hỏi nhanh, AI sẽ lọc và đưa ra các máy ảnh tối ưu nhất dành riêng cho bạn!</p>
            </div>

            {/* Step Indicator */}
            <div className="wizard-steps-indicator">
              <div className={wizardStep >= 1 ? "step-dot active" : "step-dot"}>1. Nhu cầu</div>
              <div className={wizardStep >= 2 ? "step-dot active" : "step-dot"}>2. Ngân sách</div>
              <div className={wizardStep >= 3 ? "step-dot active" : "step-dot"}>3. Thương hiệu</div>
            </div>

            <div className="wizard-body">
              {wizardStep === 1 && (
                <div className="wizard-step-content">
                  <h3>Bước 1: Nhu cầu chụp ảnh chính của bạn là gì?</h3>
                  <div className="options-grid">
                    {[
                      { id: "portrait", icon: "📸", title: "Chụp Chân Dung & Xóa Phông", desc: "Ưu tiên cảm biến Full-frame & ống kính khẩu lớn F1.4/F1.8" },
                      { id: "travel", icon: "✈️", title: "Phượt & Du Lịch Gọn Nhẹ", desc: "Ưu tiên body nhỏ gọn nhẹ dưới 600g & ống kính Zoom đa dụng" },
                      { id: "vlog", icon: "🎥", title: "Quay Vlogging & Content Creator", desc: "Ưu tiên màn hình xoay lật, quay 4K 60p & chống rung mượt mà" },
                      { id: "sports", icon: "🏃", title: "Chụp Thể Thao & Động Vật", desc: "Ưu tiên tốc độ chụp liên tiếp siêu nhanh 20-40fps & bắt nét AI" }
                    ].map((opt) => (
                      <div
                        key={opt.id}
                        className={wizardNeed === opt.id ? "option-card selected" : "option-card"}
                        onClick={() => setWizardNeed(opt.id)}
                      >
                        <span className="option-icon">{opt.icon}</span>
                        <div>
                          <strong>{opt.title}</strong>
                          <p>{opt.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {wizardStep === 2 && (
                <div className="wizard-step-content">
                  <h3>Bước 2: Ngân sách dự kiến đầu tư của bạn?</h3>
                  <div className="budget-slider-box">
                    <div className="big-budget-display">{formatVND(wizardBudget)}</div>
                    <input
                      type="range"
                      min={20000000}
                      max={70000000}
                      step={5000000}
                      value={wizardBudget}
                      onChange={(e) => setWizardBudget(Number(e.target.value))}
                    />
                    <div className="budget-hints">
                      <span>Dưới 25 triệu (Tối ưu)</span>
                      <span>50 - 70 triệu (Chuyên nghiệp)</span>
                    </div>
                  </div>
                </div>
              )}

              {wizardStep === 3 && (
                <div className="wizard-step-content">
                  <h3>Bước 3: Bạn có ưu tiên thương hiệu cụ thể nào không?</h3>
                  <div className="brands-option-grid">
                    {[
                      { id: "All", name: "Tất cả thương hiệu (AI tự chọn tối ưu nhất)" },
                      { id: "Sony", name: "Sony Alpha (Hệ sinh thái ngàm E đa dạng)" },
                      { id: "Canon", name: "Canon EOS R (Màu da đẹp & Lấy nét AF đỉnh cao)" },
                      { id: "Fujifilm", name: "Fujifilm (Màu phim giả lập độc quyền)" },
                      { id: "Nikon", name: "Nikon Z (Độ bền bỉ & Khả năng xử lý N-RAW)" }
                    ].map((b) => (
                      <div
                        key={b.id}
                        className={wizardBrand === b.id ? "brand-option-item selected" : "brand-option-item"}
                        onClick={() => setWizardBrand(b.id)}
                      >
                        <strong>{b.name}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="wizard-footer">
              {wizardStep > 1 && (
                <button className="btn-secondary" onClick={() => setWizardStep(wizardStep - 1)}>
                  ← Quay lại
                </button>
              )}

              {wizardStep < 3 ? (
                <button className="btn-primary" onClick={() => setWizardStep(wizardStep + 1)}>
                  Tiếp theo →
                </button>
              ) : (
                <button className="btn-accent-finish" onClick={applyAiWizardResult}>
                  🚀 Phân Tích & Hiển Thị Gợi Ý AI
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 7. PRODUCT DETAIL SPECS MODAL */}
      {detailModalProduct && (
        <div className="modal-backdrop" onClick={() => setDetailModalProduct(null)}>
          <div className="detail-modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setDetailModalProduct(null)}>✕</button>

            <div className="detail-grid">
              <div className="detail-image-box">
                <img src={detailModalProduct.image} alt={detailModalProduct.name} />
              </div>

              <div className="detail-info-box">
                <span className="brand-meta">{detailModalProduct.brand} • {detailModalProduct.category}</span>
                <h2>{detailModalProduct.name}</h2>
                <div className="price-tag-large">{formatVND(detailModalProduct.price)}</div>

                <p className="detail-desc">{detailModalProduct.description}</p>

                <h4>📋 Bảng Thông Số Kỹ Thuật (Camera Specifications):</h4>
                <table className="specs-table-detail">
                  <tbody>
                    <tr><td>Cảm biến (Sensor)</td><td><strong>{detailModalProduct.specs.sensor}</strong></td></tr>
                    <tr><td>Độ phân giải (Resolution)</td><td><strong>{detailModalProduct.specs.resolution}</strong></td></tr>
                    <tr><td>Ngàm Lens (Mount)</td><td><strong>{detailModalProduct.specs.mount}</strong></td></tr>
                    <tr><td>Quay Video (Video Specs)</td><td><strong>{detailModalProduct.specs.video}</strong></td></tr>
                    <tr><td>Trọng lượng (Weight)</td><td><strong>{detailModalProduct.specs.weight}</strong></td></tr>
                  </tbody>
                </table>

                {detailModalProduct.aiReasons && (
                  <div className="ai-explainable-box highlight-detail">
                    <div className="explain-header">🤖 Phân tích Thuật Toán Gợi Ý AI:</div>
                    <ul className="explain-list">
                      {detailModalProduct.aiReasons.map((r, i) => (
                        <li key={i}>✓ {r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="detail-actions">
                  <button className="btn-add-cart-large" onClick={() => { addToCart(detailModalProduct); setDetailModalProduct(null); }}>
                    🛒 Thêm Vào Giỏ Hàng
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 8. FOOTER */}
      <footer className="main-footer">
        <div className="footer-container">
          <div className="footer-col">
            <h4>CAMERA STORE</h4>
            <p>Hệ thống bán lẻ máy ảnh, ống kính chính hãng hàng đầu Việt Nam. Tích hợp AI Recommendation System tư vấn cá nhân hóa.</p>
          </div>
          <div className="footer-col">
            <h4>Danh Mục Sản Phẩm</h4>
            <ul>
              <li>Máy ảnh Mirrorless</li>
              <li>Ống kính Sony E-mount</li>
              <li>Ống kính Canon RF</li>
              <li>Máy quay Vlog chuyên nghiệp</li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>Chính Sách & Trợ Giúp</h4>
            <ul>
              <li>Chính sách bảo hành 24 tháng</li>
              <li>Đổi trả trong 30 ngày</li>
              <li>Chương trình Thu cũ đổi mới</li>
              <li>Hướng dẫn thanh toán trả góp 0%</li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2026 Camera Store Project. Designed with E-Commerce Best Practices.</p>
        </div>
      </footer>
    </div>
  );
}
