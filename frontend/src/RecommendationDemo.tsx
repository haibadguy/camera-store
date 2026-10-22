import { useMemo, useState } from "react";

type Body = {
  itemId: number;
  asin: string;
  title: string;
  mount: string;
  khung: string;
  source: "train" | "val";
  nLensesM1?: number;
};

type Explanation = {
  verified: true;
  bodyId: number;
  bodyTitle: string;
  bodySource: "train" | "val";
  candidateBodies: number[];
  usecase?: string;
  text?: string;
};

type Recommendation = {
  rank: number;
  itemId: number;
  asin: string;
  title: string;
  type: string;
  typeLabel: string;
  score?: number;
  explanation?: Explanation;
  details?: Array<[string, string]>;
};

type DemoUser = {
  id: number;
  historyCount?: number;
  bodies: Body[];
  blockedLenses: number;
  recommendations: Recommendation[];
  mask?: { blockedInTopK: Recommendation };
};

const demoUsers: DemoUser[] = [
  {
    id: 409,
    bodies: [{
      itemId: 9022,
      asin: "B00CIRLDC2",
      title: "Nikon D3100 DSLR Camera with 18-55mm f/3.5-5.6 Auto Focus-S Nikkor Zoom Lens",
      mount: "nikon_f",
      khung: "apsc",
      source: "train",
    }],
    blockedLenses: 814,
    recommendations: [
      {
        rank: 1,
        itemId: 1154,
        asin: "B000EVLS4C",
        title: "Canon PSC-55 Deluxe Leather Compact Case for SD430, …",
        type: "phu_kien",
        typeLabel: "phụ kiện",
        score: 7.377339839935303,
      },
      {
        rank: 2,
        itemId: 15485,
        asin: "B01DZP4UAM",
        title: "Nikon 55-200mm f/4-5.6G ED IF AF-S DX VR [Vibration Reduction] Nikkor Zoom Lens Bulk packaging (White box, New)",
        type: "ong",
        typeLabel: "ống kính",
        score: 6.998710632324219,
        explanation: {
          verified: true,
          bodyId: 9022,
          bodyTitle: "Nikon D3100 DSLR Camera with 18-55mm …",
          bodySource: "train",
          candidateBodies: [9022],
          usecase: "thể thao / chim",
          text: "Gợi ý Nikon 55-200mm f/4-5.6G ED IF AF-S DX VR [Vibration Reduction] Nikkor… vì ống này lắp trực tiếp được trên Nikon D3100 DSLR Camera with 18-55mm f/3.5-5.6 Auto Focus-S Nikkor Zo… bạn đã mua (ngàm nikon_f), và phù hợp chụp thể thao / chim (tiêu cự 55-200 mm, khẩu độ tối đa f/4-5.6).",
        },
        details: [
          ["Ngàm", "nikon_f"],
          ["Khung hình", "apsc"],
          ["Trong ma trận tương thích", "Có"],
          ["Tiêu cự", "55–200 mm"],
          ["Khẩu độ tối đa", "f/4 ở 55 mm · f/5.6 ở 200 mm"],
          ["Mục đích sử dụng", "thể thao / chim"],
        ],
      },
      {
        rank: 5,
        itemId: 1665,
        asin: "B000V9CQJI",
        title: "Canon EOS 40D 10.1MP Digital SLR Camera with EF 28-135mm …",
        type: "than",
        typeLabel: "thân máy",
        score: 6.5257649421691895,
      },
    ],
    mask: {
      blockedInTopK: {
        rank: 0,
        itemId: 13448,
        asin: "B00WUI9ITO",
        title: "Canon EF 24-70mm f/4.0L is USM Standard Zoom Lens - 6313B002",
        type: "ong",
        typeLabel: "ống kính",
      },
    },
  },
  {
    id: 47,
    historyCount: 10,
    bodies: [
      { itemId: 12369, asin: "B00PHRVRXU", title: "Nikon D4S 16.2 MP CMOS FX Digital SLR with Full 1080p HD Video (Body Only)", mount: "nikon_f", khung: "ff", source: "train", nLensesM1: 219 },
      { itemId: 14934, asin: "B01A7Q0J3Y", title: "Nikon D500 DX-Format Digital SLR (Body Only), Base", mount: "nikon_f", khung: "apsc", source: "val", nLensesM1: 219 },
    ],
    blockedLenses: 814,
    recommendations: [{
      rank: 1,
      itemId: 13466,
      asin: "",
      title: "Sản phẩm được API contract xác định là ống kính hạng 1",
      type: "ong",
      typeLabel: "ống kính",
      explanation: { verified: true, bodyId: 14934, bodyTitle: "Nikon D500 DX-Format Digital SLR (Body Only), Base", bodySource: "val", candidateBodies: [12369, 14934] },
    }],
  },
];

type Props = { onExit: () => void };

export default function RecommendationDemo({ onExit }: Props) {
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null);
  const selectedUser = useMemo(() => demoUsers.find((user) => user.id === selectedUserId) ?? null, [selectedUserId]);
  const selectedItem = selectedUser?.recommendations.find((item) => item.itemId === selectedItemId) ?? null;

  if (selectedUser && selectedItem) return <ProductDetail item={selectedItem} user={selectedUser} onBack={() => setSelectedItemId(null)} onExit={onExit} />;
  if (selectedUser) return <RecommendationList user={selectedUser} onBack={() => setSelectedUserId(null)} onSelectItem={setSelectedItemId} onExit={onExit} />;
  return <UserPicker onExit={onExit} onSelect={(id) => { setSelectedUserId(id); setSelectedItemId(null); }} />;
}

function DemoHeader({ onExit, trail }: { onExit: () => void; trail: string }) {
  return <header className="demo-header"><div className="demo-shell demo-header-content">
    <button className="demo-brand" onClick={onExit}>CAMERA STORE <span>API 1.2 DEMO</span></button>
    <p>{trail}</p><button className="demo-link-button" onClick={onExit}>Quay về catalog</button>
  </div></header>;
}

function UserPicker({ onExit, onSelect }: { onExit: () => void; onSelect: (id: number) => void }) {
  return <div className="demo-page"><DemoHeader onExit={onExit} trail="Demo dữ liệu tĩnh theo docs/api_contract.md" />
    <main className="demo-shell demo-main">
      <span className="demo-eyebrow">Bước 1 / 3</span><h1>Chọn người dùng để xem gợi ý</h1>
      <p className="demo-lead">Hai hồ sơ mẫu bên dưới dùng đúng dữ liệu công bố trong API contract. Ứng dụng chưa gọi backend.</p>
      <section className="demo-user-grid" aria-label="Danh sách người dùng mẫu">
        {demoUsers.map((user) => <article className="demo-user-card" key={user.id}>
          <div className="demo-card-topline"><span>Người dùng</span><strong>#{user.id}</strong></div>
          <h2>{user.bodies.length} thân máy trong lịch sử</h2>
          {user.historyCount !== undefined && <p>{user.historyCount} sản phẩm trong lịch sử all_history</p>}
          <ul className="demo-body-list">{user.bodies.map((body) => <li key={body.itemId}><strong>{body.title}</strong><span>#{body.itemId} · {body.mount} · {body.khung} · nguồn {body.source}</span></li>)}</ul>
          <button className="demo-primary-button" onClick={() => onSelect(user.id)}>Xem danh sách gợi ý</button>
        </article>)}
      </section>
    </main>
  </div>;
}

function RecommendationList({ user, onBack, onSelectItem, onExit }: { user: DemoUser; onBack: () => void; onSelectItem: (id: number) => void; onExit: () => void }) {
  return <div className="demo-page"><DemoHeader onExit={onExit} trail={`Người dùng #${user.id} / Danh sách gợi ý`} />
    <main className="demo-shell demo-main">
      <button className="demo-back-button" onClick={onBack}>← Chọn người dùng khác</button>
      <span className="demo-eyebrow">Bước 2 / 3 · exclude: all_history</span><h1>Gợi ý cho người dùng #{user.id}</h1>
      <p className="demo-lead">Điểm chỉ dùng để xếp hạng trong cùng một người dùng, không phải phần trăm phù hợp.</p>
      <section className="demo-summary-grid" aria-label="Tóm tắt hồ sơ"><div><span>Thân máy dùng cho mặt nạ</span><strong>{user.bodies.length}</strong></div><div><span>Ống kính bị chặn</span><strong>{user.blockedLenses}</strong></div><div><span>Mục hiển thị từ contract</span><strong>{user.recommendations.length}</strong></div></section>
      {user.mask && <aside className="demo-mask-note"><strong>QĐ 4-9 (mặt nạ 15)</strong><p>Đã gỡ {user.mask.blockedInTopK.title} khỏi top-k trước mặt nạ. Đây là thông tin mặt nạ, không phải một gợi ý để mua.</p></aside>}
      <section className="demo-recommendations" aria-label="Danh sách gợi ý">
        {user.recommendations.map((item) => <article className="demo-recommendation-card" key={item.itemId}>
          <div className="demo-rank">#{item.rank}</div><div className="demo-recommendation-content">
            <div className="demo-type-row"><span>{item.typeLabel}</span><span>item_id {item.itemId}</span></div><h2>{item.title}</h2>
            {item.asin && <p className="demo-asin">ASIN: {item.asin}</p>}{item.score !== undefined && <p className="demo-score">Điểm xếp hạng: {item.score}</p>}
            {item.explanation && <ExplanationPanel explanation={item.explanation} />}
            <button className="demo-secondary-button" onClick={() => onSelectItem(item.itemId)}>Xem chi tiết theo contract</button>
          </div>
        </article>)}
      </section>
    </main>
  </div>;
}

function ExplanationPanel({ explanation }: { explanation: Explanation }) {
  return <section className="demo-explanation"><div className="demo-explanation-title">Giải thích đã xác minh</div>
    {explanation.text && <p>{explanation.text}</p>}<dl>
      <div><dt>Thân được chọn</dt><dd>#{explanation.bodyId} · {explanation.bodyTitle}</dd></div><div><dt>Nguồn thân</dt><dd>{explanation.bodySource}</dd></div><div><dt>Candidate bodies</dt><dd>{explanation.candidateBodies.join(", ")}</dd></div>{explanation.usecase && <div><dt>Mục đích</dt><dd>{explanation.usecase}</dd></div>}
    </dl>
  </section>;
}

function ProductDetail({ item, user, onBack, onExit }: { item: Recommendation; user: DemoUser; onBack: () => void; onExit: () => void }) {
  const attributes: Array<[string, string]> = item.details ?? [["Loại", item.typeLabel], ["item_id", String(item.itemId)], ...(item.asin ? [["ASIN", item.asin] as [string, string]] : [])];
  return <div className="demo-page"><DemoHeader onExit={onExit} trail={`Người dùng #${user.id} / Chi tiết sản phẩm`} />
    <main className="demo-shell demo-main"><button className="demo-back-button" onClick={onBack}>← Quay lại danh sách gợi ý</button><span className="demo-eyebrow">Bước 3 / 3 · item_id {item.itemId}</span>
      <article className="demo-detail-card"><div className="demo-detail-visual" aria-hidden="true">{item.typeLabel}</div><div className="demo-detail-content"><div className="demo-type-row"><span>{item.typeLabel}</span><span>Hạng #{item.rank}</span></div><h1>{item.title}</h1><p className="demo-lead">Thông tin hiển thị giới hạn trong các trường mà API contract đã công bố.</p>
        <dl className="demo-attributes">{attributes.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>{item.explanation && <ExplanationPanel explanation={item.explanation} />}
      </div></article>
    </main>
  </div>;
}
