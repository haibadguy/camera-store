import { useEffect, useMemo, useState } from "react";
import "./styles.css";
import RecommendationDemo from "./RecommendationDemo";
import CompatibilityChecker from "./CompatibilityChecker";
import CatalogProfileSelector from "./components/catalog/CatalogProfileSelector";
import {
  formatVND,
  Product,
} from "./components/catalog/CatalogProductCard";
import CatalogFilterSidebar from "./components/catalog/CatalogFilterSidebar";
import CatalogProductGrid from "./components/catalog/CatalogProductGrid";
import CatalogDetailModal from "./components/catalog/CatalogDetailModal";
import {
  fetchCompatibility,
  fetchHealth,
  HealthResponse,
  IS_MOCK_SOURCE,
} from "./services/recommendationService";

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


const DATASET_STATS = [
  ["67.661", "người dùng"],
  ["27.940", "sản phẩm"],
  ["595.515", "tương tác"],
  ["72.720", "cặp tương thích M=1"],
];

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
    image: "/camera-placeholder.svg",
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
    image: "/camera-placeholder.svg",
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
    image: "/camera-placeholder.svg",
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
    image: "/camera-placeholder.svg",
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
    image: "/camera-placeholder.svg",
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
    image: "/camera-placeholder.svg",
    description: "Ống kính tiêu cự 85mm chuyên chụp chân dung, khẩu độ lớn f/1.4 tạo hiệu ứng bokeh mượt mà.",
    specs: { sensor: "Ống kính Prime", resolution: "N/A", mount: "Sony E", video: "AF êm ái", weight: "642g" },
    aiMatchScore: 97,
    aiReasons: [
      "Khẩu độ lớn f/1.4 cho khả năng xóa phông chân dung ấn tượng",
      "Thuộc dòng ống kính G Master cao cấp nhất của Sony",
      "Lấy nét tự động nhanh và êm ái khi quay phim"
    ],
    useCases: ["portrait", "event"],
    compatLensId: 9696,
  }
];

const makeCatalogProduct = (
  id: number,
  name: string,
  brand: string,
  category: string,
  price: number,
  mount: string,
  sensor: string,
  useCases: string[],
  badge?: string,
): Product => ({
  id,
  name,
  brand,
  category,
  price,
  rating: 4.7,
  reviewsCount: 24 + (id % 80),
  stock: 4 + (id % 12),
  badge,
  image: "/camera-placeholder.svg",
  description: `${name} là sản phẩm minh họa trong catalog thương mại của demo, dùng để trình bày cách lọc theo nhu cầu và thông số.`,
  specs: { sensor, resolution: "Theo thông số nhà sản xuất", mount, video: "Theo phiên bản", weight: "Đang cập nhật" },
  useCases,
  compatLensId: category === "Ống kính"
    ? mount === "Sony E" ? 9696
      : mount === "Nikon F" ? 15485
        : mount === "Canon EF" ? 13448
          : undefined
    : undefined,
});

const CATALOG_PRODUCTS: Product[] = [
  ...PRODUCTS_DATA,
  makeCatalogProduct(7, "Canon EOS R8 Body", "Canon", "Mirrorless", 32990000, "Canon RF", "Full-frame", ["portrait", "travel"], "Nhỏ gọn"),
  makeCatalogProduct(8, "Canon EOS R50 Kit 18-45mm", "Canon", "Mirrorless", 18990000, "Canon RF-S", "APS-C", ["travel", "vlog"], "Người mới"),
  makeCatalogProduct(9, "Nikon Z5 Body", "Nikon", "Mirrorless", 27990000, "Nikon Z", "Full-frame", ["portrait", "travel"]),
  makeCatalogProduct(10, "Nikon Z fc Body", "Nikon", "Mirrorless", 23990000, "Nikon Z", "APS-C", ["street", "travel"], "Hoài cổ"),
  makeCatalogProduct(11, "Sony Alpha A6700 Body", "Sony", "Mirrorless", 31990000, "Sony E", "APS-C", ["sports", "travel"]),
  makeCatalogProduct(12, "Sony Alpha A7C II Body", "Sony", "Mirrorless", 49990000, "Sony E", "Full-frame", ["travel", "vlog"]),
  makeCatalogProduct(13, "Fujifilm X-S20 Body", "Fujifilm", "Mirrorless", 31990000, "Fujifilm X", "APS-C", ["vlog", "travel"]),
  makeCatalogProduct(14, "Fujifilm X100VI", "Fujifilm", "Compact", 44990000, "Tích hợp", "APS-C", ["street", "travel"], "Được quan tâm"),
  makeCatalogProduct(15, "Panasonic Lumix S5II Body", "Panasonic", "Mirrorless", 36990000, "L-Mount", "Full-frame", ["video", "event"]),
  makeCatalogProduct(16, "OM System OM-5 Body", "OM System", "Mirrorless", 24990000, "Micro Four Thirds", "Micro Four Thirds", ["travel", "nature"]),
  makeCatalogProduct(17, "Sony FE 24-70mm f/2.8 GM II", "Sony", "Ống kính", 52990000, "Sony E", "Full-frame", ["event", "portrait"]),
  makeCatalogProduct(18, "Canon RF 24-70mm f/2.8L IS USM", "Canon", "Ống kính", 59990000, "Canon RF", "Full-frame", ["event", "portrait"]),
  makeCatalogProduct(19, "Nikon Z 24-120mm f/4 S", "Nikon", "Ống kính", 29990000, "Nikon Z", "Full-frame", ["travel", "event"]),
  makeCatalogProduct(20, "Fujifilm XF 16-55mm f/2.8 R LM WR", "Fujifilm", "Ống kính", 31990000, "Fujifilm X", "APS-C", ["event", "street"]),
  makeCatalogProduct(21, "Sony FE 20-70mm f/4 G", "Sony", "Ống kính", 29990000, "Sony E", "Full-frame", ["travel", "vlog"]),
  makeCatalogProduct(22, "Canon RF 50mm f/1.8 STM", "Canon", "Ống kính", 5790000, "Canon RF", "Full-frame", ["portrait", "street"], "Giá tốt"),
  makeCatalogProduct(23, "Nikon Z 50mm f/1.8 S", "Nikon", "Ống kính", 13990000, "Nikon Z", "Full-frame", ["portrait", "street"]),
  makeCatalogProduct(24, "Fujifilm XF 35mm f/2 R WR", "Fujifilm", "Ống kính", 9990000, "Fujifilm X", "APS-C", ["street", "portrait"]),
  makeCatalogProduct(25, "Godox V1 Flash for Sony", "Godox", "Phụ kiện", 5990000, "Sony", "N/A", ["event", "portrait"]),
  makeCatalogProduct(26, "Peak Design Everyday Sling 6L", "Peak Design", "Phụ kiện", 2890000, "N/A", "N/A", ["travel", "street"]),
  makeCatalogProduct(27, "SanDisk Extreme Pro SDXC 256GB", "SanDisk", "Phụ kiện", 1290000, "N/A", "N/A", ["video", "travel"]),
  makeCatalogProduct(28, "DJI Mic 2 Wireless", "DJI", "Phụ kiện", 8990000, "N/A", "N/A", ["vlog", "video"]),
];

function DatasetScaleBanner({ health }: { health: HealthResponse | null }) {
  const live = health?.status === "ok";
  return (
    <section className="dataset-scale-banner" aria-label="Quy mô dữ liệu và trạng thái hệ thống">
      <div className="site-wrapper dataset-scale-inner">
        <div>
          <strong>Camera Recommender</strong>
          <span className="dataset-source">Amazon Electronics 2023 · tập đại diện trên giao diện</span>
        </div>
        <div className="dataset-stat-list">
          {DATASET_STATS.map(([value, label]) => (
            <span key={label}><strong>{value}</strong> {label}</span>
          ))}
        </div>
        <span className={`health-badge ${live ? "live" : IS_MOCK_SOURCE ? "mock" : "offline"}`}>
          {live ? `Live API · FastAPI seed ${health?.seed ?? 1}` : IS_MOCK_SOURCE ? "Dữ liệu mẫu" : "API chưa kết nối"}
        </span>
      </div>
    </section>
  );
}

function SystemOverview({ onExit }: { onExit: () => void }) {
  return (
    <div className="demo-page">
      <header className="demo-header">
        <div className="demo-shell demo-header-content">
          <button className="demo-brand" onClick={onExit}>CAMERA STORE <span>Về hệ thống</span></button>
          <p>Giới thiệu đề tài và phạm vi demo</p>
          <button className="demo-link-button" onClick={onExit}>Quay về catalog</button>
        </div>
      </header>
      <main className="demo-shell demo-main system-overview">
        <span className="demo-eyebrow">Đồ án tốt nghiệp</span>
        <h1>Hệ thống tư vấn cá nhân hóa thiết bị nhiếp ảnh</h1>
        <p className="demo-lead">
          Mục tiêu là đề xuất sản phẩm tiếp theo từ dữ liệu đánh giá Amazon,
          đồng thời không đưa ống kính chắc chắn không tương thích vào danh sách.
        </p>
        <div className="system-overview-grid">
          <article><h2>1. Dữ liệu</h2><p>Amazon Electronics 2023, 67.661 người dùng, 27.940 sản phẩm và 595.515 tương tác sau tiền xử lý.</p></article>
          <article><h2>2. Mô hình</h2><p>LightGCN tạo điểm xếp hạng. Điểm chỉ có ý nghĩa khi so sánh các sản phẩm trong cùng một người dùng, không phải xác suất.</p></article>
          <article><h2>3. Ràng buộc</h2><p>Ma trận ngàm M và QĐ 4–9 chỉ chặn ống kính chắc chắn không lắp được trên mọi thân máy đã đánh giá.</p></article>
          <article><h2>4. Giải thích</h2><p>Giải thích là hậu nghiệm: tìm thân máy tương thích làm cầu nối u → b → l. Một số sản phẩm không đủ đường giải thích.</p></article>
        </div>
        <div className="system-flow"><strong>React</strong><span>→</span><strong>Spring Boot</strong><span>→</span><strong>FastAPI</strong><small>Spring là lớp nghiệp vụ; React không gọi trực tiếp dịch vụ mô hình.</small></div>
        <aside className="system-limitations">
          <h2>Phạm vi và giới hạn demo</h2>
          <ul>
            <li>Catalog có thông tin thương mại minh họa, không dùng để đánh giá mô hình.</li>
            <li>Lịch sử là đánh giá Amazon, không phải đơn hàng hay giỏ hàng của website.</li>
            <li>Chưa có đăng nhập, người dùng mới và cập nhật gợi ý theo giao dịch thật.</li>
            <li>Demo dùng seed 1 và dữ liệu đã xử lý; kết quả không đại diện cho mọi người dùng mới.</li>
          </ul>
        </aside>
      </main>
    </div>
  );
}

export default function App() {
  const [activeView, setActiveView] = useState<"catalog" | "recommendation" | "compat" | "about">("catalog");
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
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [compatibilityProfile, setCompatibilityProfile] = useState<409 | 47 | null>(null);
  const [compatibilityStatus, setCompatibilityStatus] = useState<Record<number, "compatible" | "incompatible" | "unknown">>({});

  useEffect(() => {
    const controller = new AbortController();
    void fetchHealth(controller.signal).then(setHealth).catch(() => setHealth(null));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (compatibilityProfile === null) {
      setCompatibilityStatus({});
      return;
    }
    const bodyIds = compatibilityProfile === 409 ? [9022] : [12369, 14934];
    const controller = new AbortController();
    const lensProducts = CATALOG_PRODUCTS.filter((product) => product.compatLensId !== undefined);
    void Promise.all(
      lensProducts.map(async (product) => {
        const checks = await Promise.allSettled(
          bodyIds.map((bodyId) => fetchCompatibility(bodyId, product.compatLensId!, controller.signal)),
        );
        const successful = checks
          .filter((check): check is PromiseFulfilledResult<Awaited<ReturnType<typeof fetchCompatibility>>> => check.status === "fulfilled")
          .map((check) => check.value);
        if (successful.length === 0) return [product.id, "unknown"] as const;
        return [
          product.id,
          successful.some((result) => result.level === "compatible_with" || result.level === "crops_sensor")
            ? "compatible"
            : successful.every((result) => result.level === "incompatible")
              ? "incompatible"
              : "unknown",
        ] as const;
      }),
    ).then((entries) => setCompatibilityStatus(Object.fromEntries(entries) as Record<number, "compatible" | "incompatible" | "unknown">))
      .catch(() => setCompatibilityStatus({}));
    return () => controller.abort();
  }, [compatibilityProfile]);

  const filteredProducts = useMemo(() => {
    let result = CATALOG_PRODUCTS.filter((p) => {
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
  if (activeView === "compat") {
    return <CompatibilityChecker onExit={() => setActiveView("catalog")} />;
  }
  if (activeView === "about") {
    return <SystemOverview onExit={() => setActiveView("catalog")} />;
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
                <span className="btn-top-label">Lọc theo nhu cầu</span>
                <span className="btn-main-label">Chọn máy tham khảo</span>
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
          <button className="nav-item" onClick={() => setActiveView("compat")}>
            Kiểm tra tương thích
          </button>
          <button className="nav-item" onClick={() => setActiveView("about")}>
            Về hệ thống
          </button>
        </div>
      </nav>

      <DatasetScaleBanner health={health} />

      {/* 4. PROMO HERO BANNER */}
      <section className="promo-banner-section">
        <div className="site-wrapper promo-container">
          <div className="promo-text-wrap">
          <span className="promo-tag">CATALOG MINH HỌA · NGHIÊN CỨU GỢI Ý</span>
            <h1>Tư Vấn Chọn Máy Ảnh Phù Hợp Nhu Cầu & Ngân Sách</h1>
            <p>
            Catalog này minh họa giao diện cửa hàng. Luồng nghiên cứu chính là
            <strong> Tư vấn thiết bị</strong>: LightGCN xếp hạng từ dữ liệu đánh giá,
            sau đó áp mặt nạ tương thích và hiển thị giải thích hậu nghiệm.
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
        <CatalogFilterSidebar
          selectedUseCase={selectedUseCase}
          maxPrice={maxPrice}
          selectedBrand={selectedBrand}
          selectedMount={selectedMount}
          hasFilters={selectedBrand !== "All" || selectedUseCase !== "All" || selectedMount !== "All" || maxPrice < 70000000}
          onUseCaseChange={setSelectedUseCase}
          onPriceChange={setMaxPrice}
          onBrandChange={setSelectedBrand}
          onMountChange={setSelectedMount}
          onReset={resetFilters}
        />

        {/* PRODUCT LIST CONTENT */}
        <section className="catalog-products-section">
          {/* Toolbar */}
          <div className="catalog-toolbar">
            <div className="toolbar-left">
              <h2>Danh sách thiết bị nhiếp ảnh <span className="catalog-demo-label">dữ liệu thương mại minh họa</span></h2>
              <span className="results-count">Hiển thị {filteredProducts.length} sản phẩm</span>
            </div>

            <CatalogProfileSelector value={compatibilityProfile} onChange={setCompatibilityProfile} />

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

          <CatalogProductGrid
            products={filteredProducts}
            compatibilityStatus={compatibilityStatus}
            compatibilityEnabled={compatibilityProfile !== null}
            onDetail={setDetailProduct}
            onAddToCart={() => setCartCount((count) => count + 1)}
            onReset={resetFilters}
          />
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
              <span className="dialog-badge"><SparkleIcon /> Bộ lọc nhu cầu tham khảo</span>
              <h2>Lọc thiết bị theo nhu cầu</h2>
              <p>Đây là bộ lọc minh họa cho catalog, không phải mô hình LightGCN của đề tài.</p>
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
                  <h4>Bạn có thương hiệu cụ thể nào không?</h4>
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
                  <SparkleIcon /> Lọc và hiển thị thiết bị tham khảo
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 7. PRODUCT DETAIL SPECS DIALOG */}
      {detailProduct && (
        <CatalogDetailModal
          product={detailProduct}
          onClose={() => setDetailProduct(null)}
          onAddToCart={() => { setCartCount((count) => count + 1); setDetailProduct(null); }}
        />
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
