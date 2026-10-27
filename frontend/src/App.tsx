import { useMemo, useState } from "react";
import "./styles.css";
import RecommendationDemo from "./RecommendationDemo";

// SVG Icons for professional E-Commerce UI (No emojis!)
const SearchIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"></circle>
    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
  </svg>
);

const ShoppingBagIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
    <line x1="3" y1="6" x2="21" y2="6"></line>
    <path d="M16 10a4 4 0 0 1-8 0"></path>
  </svg>
);

const FilterIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
  </svg>
);

const SparkleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z"></path>
  </svg>
);

const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

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
    name: "Sony Alpha A7 IV Body",
    brand: "Sony",
    category: "Mirrorless",
    price: 54990000,
    originalPrice: 59990000,
    rating: 4.9,
    reviewsCount: 142,
    stock: 8,
    badge: "Bán chạy",
    image: "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=80",
    description: "Máy ảnh Full-frame hybrid trang bị cảm biến Exmor R 33.0 MP, quay phim 4K 60p 10-bit và hệ thống lấy nét Real-time Eye AF.",
    specs: { sensor: "Full-frame", resolution: "33.0 MP", mount: "Sony E", video: "4K 60p", weight: "658g" },
    aiMatchScore: 98,
    aiReasons: [
      "Cảm biến Full-frame 33MP tối ưu cho nhu cầu chụp chân dung & sự kiện",
      "Khả năng lấy nét mắt AI chính xác cao theo thời gian thực",
      "Nằm trong khoảng ngân sách 50 - 60 triệu đồng"
    ],
    useCases: ["portrait", "event", "vlog"]
  },
  {
    id: 2,
    name: "Canon EOS R6 Mark II Body",
    brand: "Canon",
    category: "Mirrorless",
    price: 58990000,
    originalPrice: 63500000,
    rating: 4.8,
    reviewsCount: 98,
    stock: 5,
    badge: "Khuyên dùng",
    image: "https://images.unsplash.com/photo-1606986628253-3b2f4a1a8b75?auto=format&fit=crop&w=800&q=80",
    description: "Tốc độ chụp liên tiếp 40 hình/giây, hệ thống chống rung IBIS 8 stop và lấy nét Dual Pixel CMOS AF II mượt mà.",
    specs: { sensor: "Full-frame", resolution: "24.2 MP", mount: "Canon RF", video: "4K 60p", weight: "670g" },
    aiMatchScore: 95,
    aiReasons: [
      "Tốc độ chụp 40fps đáp ứng tốt chụp thể thao và chuyển động nhanh",
      "Chống rung trong thân máy 8 stop hỗ trợ chụp thiếu sáng",
      "Tương thích với hệ sinh thái ống kính Canon RF"
    ],
    useCases: ["sports", "portrait", "event"]
  },
  {
    id: 3,
    name: "Fujifilm X-T5 Body (Black / Silver)",
    brand: "Fujifilm",
    category: "Mirrorless",
    price: 42990000,
    originalPrice: 45990000,
    rating: 4.9,
    reviewsCount: 165,
    stock: 12,
    badge: "Mới",
    image: "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=800&q=80",
    description: "Cảm biến APS-C X-Trans 5 HR 40.2 MP, giả lập màu phim Film Simulation độc quyền và thiết kế cơ học hoài cổ.",
    specs: { sensor: "APS-C", resolution: "40.2 MP", mount: "Fujifilm X", video: "6.2K 30p", weight: "557g" },
    aiMatchScore: 92,
    aiReasons: [
      "Trọng lượng nhẹ 557g thuận tiện cho du lịch và phượt",
      "19 chế độ giả lập màu phim không cần chỉnh sửa hậu kỳ",
      "Độ phân giải 40.2MP chi tiết cho ảnh phong cảnh"
    ],
    useCases: ["travel", "street", "portrait"]
  },
  {
    id: 4,
    name: "Sony ZV-E10 II Kit 16-50mm",
    brand: "Sony",
    category: "Vlog Camera",
    price: 22990000,
    originalPrice: 24500000,
    rating: 4.7,
    reviewsCount: 210,
    stock: 15,
    badge: "Giá tốt",
    image: "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=800&q=80",
    description: "Máy ảnh thiết kế chuyên dụng cho quay Vlog, màn hình xoay lật 180 độ, micro định hướng 3 khoang lọc gió.",
    specs: { sensor: "APS-C", resolution: "26.0 MP", mount: "Sony E", video: "4K 60p", weight: "377g" },
    aiMatchScore: 94,
    aiReasons: [
      "Ngân sách tối ưu dưới 25 triệu cho người mới bắt đầu quay phim",
      "Tích hợp tính năng Product Showcase và Background Defocus cho Vlogger",
      "Trọng lượng nhỏ gọn 377g dễ dàng mang theo hàng ngày"
    ],
    useCases: ["vlog", "travel"]
  },
  {
    id: 5,
    name: "Nikon Z6 III Body",
    brand: "Nikon",
    category: "Mirrorless",
    price: 64990000,
    originalPrice: 67900000,
    rating: 4.9,
    reviewsCount: 42,
    stock: 4,
    badge: "Nổi bật",
    image: "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?auto=format&fit=crop&w=800&q=80",
    description: "Cảm biến Partially-stacked CMOS 24.5 MP, quay phim 6K N-RAW và kính ngắm EVF độ sáng 4000 nits.",
    specs: { sensor: "Full-frame", resolution: "24.5 MP", mount: "Nikon Z", video: "6K 60p RAW", weight: "760g" },
    aiMatchScore: 89,
    aiReasons: [
      "Cảm biến Partially-stacked đọc dữ liệu nhanh, giảm hiện tượng rolling shutter",
      "Hỗ trợ định dạng video N-RAW chất lượng cao cho quay chuyên nghiệp",
      "Tương thích với hệ ngàm Nikon Z"
    ],
    useCases: ["sports", "vlog", "event"]
  },
  {
    id: 6,
    name: "Ống kính Sony FE 85mm f/1.4 GM II",
    brand: "Sony",
    category: "Ống kính",
    price: 47990000,
    originalPrice: 49900000,
    rating: 5.0,
    reviewsCount: 34,
    stock: 6,
    badge: "Cao cấp",
    image: "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?auto=format&fit=crop&w=800&q=80",
    description: "Ống kính tiêu cự 85mm chuyên chụp chân dung, khẩu độ lớn f/1.4 tạo hiệu ứng bokeh mượt mà.",
    specs: { sensor: "Ống kính Prime", resolution: "N/A", mount: "Sony E", video: "AF êm ái", weight: "642g" },
    aiMatchScore: 97,
    aiReasons: [
      "Khẩu độ lớn f/1.4 cho khả năng xóa phông chân dung ấn tượng",
      "Thuộc dòng ống kính G Master cao cấp nhất của Sony",
      "Lấy nét tự động nhanh và êm ái khi quay phim"
    ],
    useCases: ["portrait", "event"]
  }
];

const formatVND = (amount: number) => {
  return new Intl.NumberFormat("vi-VN").format(amount) + " ₫";
};

export default function App() {
  const [activeView, setActiveView] = useState<"catalog" | "recommendation">("catalog");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBrand, setSelectedBrand] = useState("All");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [maxPrice, setMaxPrice] = useState<number>(70000000);
  const [selectedMount, setSelectedMount] = useState("All");
  const [selectedUseCase, setSelectedUseCase] = useState("All");
  const [sortBy, setSortBy] = useState<"featured" | "price-asc" | "price-desc" | "rating">("featured");

  const [cartCount, setCartCount] = useState(0);
  const [isAiWizardOpen, setIsAiWizardOpen] = useState(false);
  const [detailProduct, setDetailProduct] = useState<Product | null>(null);

  // Wizard state
  const [wizardStep, setWizardStep] = useState(1);
  const [wizardBudget, setWizardBudget] = useState(50000000);
  const [wizardNeed, setWizardNeed] = useState("portrait");
  const [wizardBrand, setWizardBrand] = useState("All");

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

  const applyWizardFilter = () => {
    setMaxPrice(wizardBudget);
    setSelectedUseCase(wizardNeed);
    setSelectedBrand(wizardBrand);
    setIsAiWizardOpen(false);
    setWizardStep(1);
  };

  const resetFilters = () => {
    setSearchQuery("");
    setSelectedBrand("All");
    setSelectedCategory("All");
    setMaxPrice(70000000);
    setSelectedMount("All");
    setSelectedUseCase("All");
    setSortBy("featured");
  };

  if (activeView === "recommendation") {
    return <RecommendationDemo onExit={() => setActiveView("catalog")} />;
  }

  return (
    <div className="store-container">
      {/* 1. TOP UTILITY BAR */}
      <div className="top-utility-bar">
        <div className="site-wrapper top-utility-content">
          <div className="utility-info">
            <span>Hệ thống Showroom: Hà Nội • TP.HCM • Đà Nẵng</span>
            <span className="bullet-sep">•</span>
            <span>Hotline: 1900 6789</span>
          </div>
          <div className="utility-links">
            <a href="#support">Trợ giúp & Bảo hành</a>
            <a href="#tradein">Thu cũ đổi mới</a>
            <a href="#store-finder">Hệ thống cửa hàng</a>
          </div>
        </div>
      </div>

      {/* 2. MAIN STORE HEADER */}
      <header className="site-header">
        <div className="site-wrapper header-content">
          {/* Logo */}
          <div className="site-logo" onClick={resetFilters}>
            <span className="logo-main">CAMERA STORE</span>
            <span className="logo-sub">Hệ thống máy ảnh & thiết bị nhiếp ảnh</span>
          </div>

          {/* Search Bar */}
          <div className="header-search-wrap">
            <div className="search-input-box">
              <SearchIcon />
              <input
                type="text"
                placeholder="Tìm kiếm máy ảnh, ống kính, thiết bị..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button className="clear-btn" onClick={() => setSearchQuery("")}>
                  <CloseIcon />
                </button>
              )}
            </div>
          </div>

          {/* Header Actions */}
          <div className="header-right-actions">
            <button className="ai-consult-button" onClick={() => setIsAiWizardOpen(true)}>
              <SparkleIcon />
              <div className="btn-label-wrap">
                <span className="btn-top-label">Gợi ý thông minh</span>
                <span className="btn-main-label">Tư vấn chọn máy</span>
              </div>
            </button>

            <div className="shopping-cart-widget">
              <div className="cart-icon-container">
                <ShoppingBagIcon />
                {cartCount > 0 && <span className="cart-badge-count">{cartCount}</span>}
              </div>
              <div className="cart-text">
                <span className="cart-label">Giỏ hàng</span>
                <span className="cart-sub">{cartCount} sản phẩm</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 3. CATEGORY NAVIGATION BAR */}
      <nav className="site-nav">
        <div className="site-wrapper nav-content">
          <button className={selectedCategory === "All" ? "nav-item active" : "nav-item"} onClick={() => setSelectedCategory("All")}>
            Tất cả sản phẩm
          </button>
          <button className={selectedCategory === "Mirrorless" ? "nav-item active" : "nav-item"} onClick={() => setSelectedCategory("Mirrorless")}>
            Máy ảnh Mirrorless
          </button>
          <button className={selectedCategory === "Ống kính" ? "nav-item active" : "nav-item"} onClick={() => setSelectedCategory("Ống kính")}>
            Ống kính (Lens)
          </button>
          <button className={selectedCategory === "Vlog Camera" ? "nav-item active" : "nav-item"} onClick={() => setSelectedCategory("Vlog Camera")}>
            Máy ảnh Compact & Vlog
          </button>
          <button className="nav-item ai-recommend-link" onClick={() => setIsAiWizardOpen(true)}>
            <SparkleIcon /> Tư vấn AI theo nhu cầu
          </button>
          <button className="nav-item api-demo-link" onClick={() => setActiveView("recommendation")}>
            Tư vấn thiết bị
          </button>
        </div>
      </nav>

      {/* 4. PROMO HERO BANNER */}
      <section className="promo-banner-section">
        <div className="site-wrapper promo-container">
          <div className="promo-text-wrap">
            <span className="promo-tag">HỆ THỐNG GỢI Ý TỰ ĐỘNG</span>
            <h1>Tư Vấn Chọn Máy Ảnh Phù Hợp Nhu Cầu & Ngân Sách</h1>
            <p>
              Thuật toán tự động phân tích thông số kỹ thuật (Cảm biến, Ngàm Lens, ISO) kết hợp ràng buộc ngân sách 
              để đưa ra danh sách sản phẩm tối ưu kèm <strong>lý do giải thích chi tiết</strong>.
            </p>
            <div className="promo-actions">
              <button className="primary-action-btn" onClick={() => setIsAiWizardOpen(true)}>
                <SparkleIcon /> Bắt đầu tư vấn ngay
              </button>
              <button className="secondary-action-btn" onClick={() => setSelectedCategory("Mirrorless")}>
                Xem máy ảnh Mirrorless
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 5. MAIN CATALOG LAYOUT */}
      <main className="site-wrapper main-layout">
        {/* SIDEBAR FILTER */}
        <aside className="sidebar-filter-panel">
          <div className="filter-panel-header">
            <div className="panel-title">
              <FilterIcon />
              <span>Bộ lọc tìm kiếm</span>
            </div>
            {(selectedBrand !== "All" || selectedUseCase !== "All" || selectedMount !== "All" || maxPrice < 70000000) && (
              <button className="reset-filter-btn" onClick={resetFilters}>Xóa lọc</button>
            )}
          </div>

          {/* Filter Group: Nhu cầu */}
          <div className="filter-block">
            <h4 className="filter-heading">Nhu cầu sử dụng</h4>
            <div className="filter-options-list">
              {[
                { id: "All", name: "Tất cả nhu cầu" },
                { id: "portrait", name: "Chụp chân dung & xóa phông" },
                { id: "travel", name: "Du lịch & phượt gọn nhẹ" },
                { id: "vlog", name: "Quay Vlogging & Content" },
                { id: "sports", name: "Chụp thể thao & chuyển động" }
              ].map((item) => (
                <label key={item.id} className="radio-option">
                  <input
                    type="radio"
                    name="usecase-radio"
                    checked={selectedUseCase === item.id}
                    onChange={() => setSelectedUseCase(item.id)}
                  />
                  <span>{item.name}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Filter Group: Ngân sách */}
          <div className="filter-block">
            <h4 className="filter-heading">Ngân sách tối đa</h4>
            <div className="price-range-container">
              <div className="price-current-value">{formatVND(maxPrice)}</div>
              <input
                type="range"
                min={20000000}
                max={70000000}
                step={5000000}
                value={maxPrice}
                onChange={(e) => setMaxPrice(Number(e.target.value))}
              />
              <div className="range-bounds">
                <span>20 triệu</span>
                <span>70 triệu+</span>
              </div>
            </div>
          </div>

          {/* Filter Group: Hãng sản xuất */}
          <div className="filter-block">
            <h4 className="filter-heading">Thương hiệu</h4>
            <div className="chip-options-grid">
              {["All", "Sony", "Canon", "Fujifilm", "Nikon"].map((brand) => (
                <button
                  key={brand}
                  className={selectedBrand === brand ? "chip-btn active" : "chip-btn"}
                  onClick={() => setSelectedBrand(brand)}
                >
                  {brand === "All" ? "Tất cả" : brand}
                </button>
              ))}
            </div>
          </div>

          {/* Filter Group: Ngàm Lens */}
          <div className="filter-block">
            <h4 className="filter-heading">Ngàm Lens tương thích</h4>
            <select
              className="select-field"
              value={selectedMount}
              onChange={(e) => setSelectedMount(e.target.value)}
            >
              <option value="All">Tất cả ngàm lens</option>
              <option value="Sony E">Sony E-mount</option>
              <option value="Canon RF">Canon RF-mount</option>
              <option value="Fujifilm X">Fujifilm X-mount</option>
              <option value="Nikon Z">Nikon Z-mount</option>
            </select>
          </div>
        </aside>

        {/* PRODUCT LIST CONTENT */}
        <section className="catalog-products-section">
          {/* Toolbar */}
          <div className="catalog-toolbar">
            <div className="toolbar-left">
              <h2>Danh sách thiết bị nhiếp ảnh</h2>
              <span className="results-count">Hiển thị {filteredProducts.length} sản phẩm</span>
            </div>

            <div className="toolbar-right">
              <label>Sắp xếp:</label>
              <select
                className="select-field sort-select"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
              >
                <option value="featured">Sản phẩm nổi bật</option>
                <option value="price-asc">Giá: Thấp đến Cao</option>
                <option value="price-desc">Giá: Cao đến Thấp</option>
                <option value="rating">Đánh giá cao nhất</option>
              </select>
            </div>
          </div>

          {/* Active filter tags */}
          {(selectedBrand !== "All" || selectedUseCase !== "All" || selectedMount !== "All" || maxPrice < 70000000) && (
            <div className="active-filter-tags">
              <span className="tag-label">Bộ lọc đang áp dụng:</span>
              {selectedBrand !== "All" && <span className="filter-tag">Hãng: {selectedBrand}</span>}
              {selectedUseCase !== "All" && <span className="filter-tag">Nhu cầu: {selectedUseCase}</span>}
              {selectedMount !== "All" && <span className="filter-tag">Ngàm: {selectedMount}</span>}
              {maxPrice < 70000000 && <span className="filter-tag">Dưới: {formatVND(maxPrice)}</span>}
              <button className="clear-tags-btn" onClick={resetFilters}>Xóa tất cả</button>
            </div>
          )}

          {/* Products Grid */}
          {filteredProducts.length === 0 ? (
            <div className="no-products-card">
              <h3>Không tìm thấy sản phẩm phù hợp</h3>
              <p>Rất tiếc, không có máy ảnh nào khớp với các tiêu chí lọc hiện tại của bạn.</p>
              <button className="secondary-action-btn dark" onClick={resetFilters}>Xóa bộ lọc tìm kiếm</button>
            </div>
          ) : (
            <div className="products-grid">
              {filteredProducts.map((product) => (
                <article key={product.id} className="product-card">
                  {/* Image wrap */}
                  <div className="product-image-container" onClick={() => setDetailProduct(product)}>
                    <img src={product.image} alt={product.name} />
                    {product.badge && <span className="status-badge">{product.badge}</span>}
                    {product.aiMatchScore && (
                      <span className="ai-score-badge">Mức độ phù hợp {product.aiMatchScore}%</span>
                    )}
                  </div>

                  {/* Card Info */}
                  <div className="product-card-body">
                    <div className="product-brand-meta">{product.brand} • {product.category}</div>
                    <h3 className="product-title" onClick={() => setDetailProduct(product)}>
                      {product.name}
                    </h3>

                    {/* Rating */}
                    <div className="rating-summary">
                      <span className="star-icon">★</span>
                      <span className="score">{product.rating}</span>
                      <span className="count">({product.reviewsCount} đánh giá)</span>
                    </div>

                    {/* Technical Specs Tags */}
                    <div className="specs-pills-row">
                      <span className="spec-pill">{product.specs.sensor}</span>
                      <span className="spec-pill">{product.specs.resolution}</span>
                      <span className="spec-pill">Ngàm {product.specs.mount}</span>
                    </div>

                    {/* AI EXPLAINABLE REASONS BOX */}
                    {product.aiReasons && product.aiReasons.length > 0 && (
                      <div className="ai-reason-container">
                        <div className="reason-title">
                          <SparkleIcon /> Lý do gợi ý phù hợp:
                        </div>
                        <ul className="reason-list">
                          {product.aiReasons.map((reason, idx) => (
                            <li key={idx}>
                              <CheckIcon /> {reason}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Price and Stock */}
                    <div className="price-stock-row">
                      <div className="price-container">
                        <span className="main-price">{formatVND(product.price)}</span>
                        {product.originalPrice && (
                          <span className="old-price">{formatVND(product.originalPrice)}</span>
                        )}
                      </div>
                      <div className="stock-indicator">
                        <span className="status-dot"></span> Còn hàng
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="card-buttons-row">
                      <button className="add-cart-btn" onClick={() => setCartCount(cartCount + 1)}>
                        Thêm vào giỏ
                      </button>
                      <button className="view-detail-btn" onClick={() => setDetailProduct(product)}>
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

      {/* 6. AI CONSULTANT WIZARD MODAL */}
      {isAiWizardOpen && (
        <div className="dialog-overlay" onClick={() => setIsAiWizardOpen(false)}>
          <div className="wizard-dialog-box" onClick={(e) => e.stopPropagation()}>
            <button className="dialog-close-btn" onClick={() => setIsAiWizardOpen(false)}>
              <CloseIcon />
            </button>

            <div className="wizard-dialog-header">
              <span className="dialog-badge"><SparkleIcon /> Thuật toán gợi ý cá nhân hóa</span>
              <h2>Trợ Lý Tư Vấn Chọn Máy Ảnh</h2>
              <p>Phân tích thông số kỹ thuật và nhu cầu sử dụng để tìm thiết bị tối ưu dành cho bạn.</p>
            </div>

            {/* Steps indicator */}
            <div className="wizard-step-tracker">
              <span className={wizardStep >= 1 ? "step-item active" : "step-item"}>1. Nhu cầu chụp</span>
              <span className="step-sep">•</span>
              <span className={wizardStep >= 2 ? "step-item active" : "step-item"}>2. Ngân sách</span>
              <span className="step-sep">•</span>
              <span className={wizardStep >= 3 ? "step-item active" : "step-item"}>3. Thương hiệu</span>
            </div>

            <div className="wizard-dialog-body">
              {wizardStep === 1 && (
                <div className="step-view">
                  <h4>Chọn nhu cầu chụp ảnh chính của bạn:</h4>
                  <div className="cards-selection-grid">
                    {[
                      { id: "portrait", title: "Chụp chân dung & xóa phông", desc: "Ưu tiên cảm biến Full-frame và ống kính khẩu độ lớn f/1.4 - f/1.8" },
                      { id: "travel", title: "Du lịch & phượt gọn nhẹ", desc: "Thân máy nhỏ gọn dưới 600g, màu ảnh đẹp và ống kính đa dụng" },
                      { id: "vlog", title: "Quay Vlogging & Content Creator", desc: "Màn hình xoay lật 180 độ, quay phim 4K 60p và lấy nét mắt mượt mà" },
                      { id: "sports", title: "Chụp thể thao & chuyển động", desc: "Tốc độ chụp liên tiếp siêu nhanh 20-40fps và tự động lấy nét AI" }
                    ].map((item) => (
                      <div
                        key={item.id}
                        className={wizardNeed === item.id ? "selection-card active" : "selection-card"}
                        onClick={() => setWizardNeed(item.id)}
                      >
                        <strong>{item.title}</strong>
                        <p>{item.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {wizardStep === 2 && (
                <div className="step-view">
                  <h4>Ngân sách dự kiến đầu tư của bạn:</h4>
                  <div className="budget-picker-box">
                    <div className="budget-value-display">{formatVND(wizardBudget)}</div>
                    <input
                      type="range"
                      min={20000000}
                      max={70000000}
                      step={5000000}
                      value={wizardBudget}
                      onChange={(e) => setWizardBudget(Number(e.target.value))}
                    />
                    <div className="picker-range-info">
                      <span>Dưới 25 triệu</span>
                      <span>50 - 70 triệu+</span>
                    </div>
                  </div>
                </div>
              )}

              {wizardStep === 3 && (
                <div className="step-view">
                  <h4>Bạn có ưu tiên thương hiệu cụ thể nào không?</h4>
                  <div className="brands-list-options">
                    {[
                      { id: "All", name: "Tất cả thương hiệu (Hệ thống tự chọn máy ảnh tối ưu nhất)" },
                      { id: "Sony", name: "Sony Alpha (Hệ sinh thái ống kính đa dạng nhất)" },
                      { id: "Canon", name: "Canon EOS R (Màu da đẹp và lấy nét Dual Pixel)" },
                      { id: "Fujifilm", name: "Fujifilm X (Giả lập màu phim độc quyền)" },
                      { id: "Nikon", name: "Nikon Z (Độ bền bỉ và chất lượng kính ngắm cao)" }
                    ].map((b) => (
                      <div
                        key={b.id}
                        className={wizardBrand === b.id ? "brand-row-card active" : "brand-row-card"}
                        onClick={() => setWizardBrand(b.id)}
                      >
                        <span>{b.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="wizard-dialog-footer">
              {wizardStep > 1 && (
                <button className="secondary-action-btn dark" onClick={() => setWizardStep(wizardStep - 1)}>
                  Quay lại
                </button>
              )}

              {wizardStep < 3 ? (
                <button className="primary-action-btn" onClick={() => setWizardStep(wizardStep + 1)}>
                  Tiếp theo →
                </button>
              ) : (
                <button className="apply-ai-btn" onClick={applyWizardFilter}>
                  <SparkleIcon /> Lọc và hiển thị gợi ý phù hợp
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 7. PRODUCT DETAIL SPECS DIALOG */}
      {detailProduct && (
        <div className="dialog-overlay" onClick={() => setDetailProduct(null)}>
          <div className="detail-dialog-box" onClick={(e) => e.stopPropagation()}>
            <button className="dialog-close-btn" onClick={() => setDetailProduct(null)}>
              <CloseIcon />
            </button>

            <div className="detail-dialog-layout">
              <div className="detail-media-wrap">
                <img src={detailProduct.image} alt={detailProduct.name} />
              </div>

              <div className="detail-specs-wrap">
                <div className="product-brand-meta">{detailProduct.brand} • {detailProduct.category}</div>
                <h2>{detailProduct.name}</h2>
                <div className="detail-price">{formatVND(detailProduct.price)}</div>

                <p className="detail-description">{detailProduct.description}</p>

                <h4>Thông số kỹ thuật chi tiết:</h4>
                <table className="specs-table">
                  <tbody>
                    <tr><td>Cảm biến (Sensor)</td><td><strong>{detailProduct.specs.sensor}</strong></td></tr>
                    <tr><td>Độ phân giải</td><td><strong>{detailProduct.specs.resolution}</strong></td></tr>
                    <tr><td>Ngàm Lens tương thích</td><td><strong>{detailProduct.specs.mount}</strong></td></tr>
                    <tr><td>Quay video</td><td><strong>{detailProduct.specs.video}</strong></td></tr>
                    <tr><td>Trọng lượng body</td><td><strong>{detailProduct.specs.weight}</strong></td></tr>
                  </tbody>
                </table>

                {detailProduct.aiReasons && (
                  <div className="ai-reason-container highlight">
                    <div className="reason-title"><SparkleIcon /> Đánh giá tư vấn AI:</div>
                    <ul className="reason-list">
                      {detailProduct.aiReasons.map((r, idx) => (
                        <li key={idx}><CheckIcon /> {r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <button className="add-cart-large-btn" onClick={() => { setCartCount(cartCount + 1); setDetailProduct(null); }}>
                  Thêm vào giỏ hàng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 8. FOOTER */}
      <footer className="site-footer">
        <div className="site-wrapper footer-content">
          <div className="footer-column">
            <h4>CAMERA STORE</h4>
            <p>Hệ thống bán lẻ máy ảnh, ống kính chính hãng. Tích hợp công nghệ AI Recommendation System tư vấn cá nhân hóa.</p>
          </div>
          <div className="footer-column">
            <h4>Sản Phẩm Nổi Bật</h4>
            <ul>
              <li>Máy ảnh Full-frame Sony Alpha</li>
              <li>Máy ảnh Canon EOS R Series</li>
              <li>Máy ảnh Fujifilm X Series</li>
              <li>Máy ảnh Nikon Z Series</li>
            </ul>
          </div>
          <div className="footer-column">
            <h4>Chính Sách Khách Hàng</h4>
            <ul>
              <li>Bảo hành chính hãng 24 tháng</li>
              <li>Đổi trả miễn phí trong 30 ngày</li>
              <li>Chương trình Thu cũ đổi mới</li>
              <li>Hỗ trợ kỹ thuật 24/7</li>
            </ul>
          </div>
        </div>
        <div className="footer-copyright">
          <div className="site-wrapper">
            <p>© 2026 Camera Store Project. Designed with E-Commerce Best Practices.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
