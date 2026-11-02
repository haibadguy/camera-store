import type { Product } from "../components/catalog/CatalogProductCard";

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
    badge: "Mẫu catalog",
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
    badge: "Mẫu catalog",
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
    badge: "Mẫu catalog",
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
    badge: "Mẫu catalog",
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
    badge: "Mẫu catalog",
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
    badge: "Mẫu catalog",
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


export { CATALOG_PRODUCTS, DATASET_STATS };
