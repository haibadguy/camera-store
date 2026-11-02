type Props = {
  value: 409 | 47 | null;
  onChange: (value: 409 | 47 | null) => void;
};

export default function CatalogProfileSelector({ value, onChange }: Props) {
  return (
    <div className="catalog-profile-strip">
      <label htmlFor="catalog-profile">Đối chiếu tương thích theo hồ sơ:</label>
      <select
        id="catalog-profile"
        className="select-field"
        value={value ?? ""}
        onChange={(event) => {
          const nextValue = event.target.value;
          onChange(nextValue === "" ? null : Number(nextValue) as 409 | 47);
        }}
      >
        <option value="">Không đối chiếu</option>
        <option value="409">User 409 · Nikon D3100</option>
        <option value="47">User 47 · Nikon D4S + D500</option>
      </select>
      {value !== null && (
        <span className="catalog-profile-note">
          Kết quả gọi `/api/compat` qua Spring; chỉ các ống có item_id đối chiếu được mới hiện nhãn.
        </span>
      )}
    </div>
  );
}
