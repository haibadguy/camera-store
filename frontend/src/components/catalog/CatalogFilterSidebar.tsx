import { formatVND } from "./CatalogProductCard";

type Props = {
  selectedUseCase: string;
  maxPrice: number;
  selectedBrand: string;
  selectedMount: string;
  hasFilters: boolean;
  onUseCaseChange: (value: string) => void;
  onPriceChange: (value: number) => void;
  onBrandChange: (value: string) => void;
  onMountChange: (value: string) => void;
  onReset: () => void;
};

export default function CatalogFilterSidebar({
  selectedUseCase,
  maxPrice,
  selectedBrand,
  selectedMount,
  hasFilters,
  onUseCaseChange,
  onPriceChange,
  onBrandChange,
  onMountChange,
  onReset,
}: Props) {
  return (
    <aside className="sidebar-filter-panel">
      <div className="filter-panel-header">
        <div className="panel-title"><span aria-hidden="true">⌕</span><span>Bộ lọc tìm kiếm</span></div>
        {hasFilters && <button className="reset-filter-btn" onClick={onReset}>Xóa lọc</button>}
      </div>
      <div className="filter-block">
        <h4 className="filter-heading">Nhu cầu sử dụng</h4>
        <div className="filter-options-list">
          {[
            ["All", "Tất cả nhu cầu"],
            ["portrait", "Chụp chân dung & xóa phông"],
            ["travel", "Du lịch & phượt gọn nhẹ"],
            ["vlog", "Quay Vlogging & Content"],
            ["sports", "Chụp thể thao & chuyển động"],
          ].map(([id, name]) => (
            <label key={id} className="radio-option">
              <input type="radio" name="usecase-radio" checked={selectedUseCase === id} onChange={() => onUseCaseChange(id)} />
              <span>{name}</span>
            </label>
          ))}
        </div>
      </div>
      <div className="filter-block">
        <h4 className="filter-heading">Ngân sách tối đa</h4>
        <div className="price-range-container">
          <div className="price-current-value">{formatVND(maxPrice)}</div>
          <input type="range" min={20000000} max={70000000} step={5000000} value={maxPrice} onChange={(event) => onPriceChange(Number(event.target.value))} />
          <div className="range-bounds"><span>20 triệu</span><span>70 triệu+</span></div>
        </div>
      </div>
      <div className="filter-block">
        <h4 className="filter-heading">Thương hiệu</h4>
        <div className="chip-options-grid">
          {["All", "Sony", "Canon", "Fujifilm", "Nikon"].map((brand) => (
            <button key={brand} className={selectedBrand === brand ? "chip-btn active" : "chip-btn"} onClick={() => onBrandChange(brand)}>
              {brand === "All" ? "Tất cả" : brand}
            </button>
          ))}
        </div>
      </div>
      <div className="filter-block">
        <h4 className="filter-heading">Ngàm Lens tương thích</h4>
        <select className="select-field" value={selectedMount} onChange={(event) => onMountChange(event.target.value)}>
          <option value="All">Tất cả ngàm lens</option>
          <option value="Sony E">Sony E-mount</option>
          <option value="Canon RF">Canon RF-mount</option>
          <option value="Fujifilm X">Fujifilm X-mount</option>
          <option value="Nikon Z">Nikon Z-mount</option>
        </select>
      </div>
    </aside>
  );
}
