export default function BrandMark() {
  return (
    <div className="brand-mark">
      <svg className="brand-glyph" viewBox="0 0 32 32" fill="none">
        <rect width="32" height="32" rx="6" fill="#1c2430" />
        <path
          d="M16 6 L25 10 V16 C25 21.5 21.2 25.8 16 27 C10.8 25.8 7 21.5 7 16 V10 Z"
          stroke="#f2f4f1"
          strokeWidth="2"
        />
        <path
          d="M12.5 16.3 L15 18.8 L20 13"
          stroke="#f2f4f1"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="brand-name">SentinelRAG</span>
    </div>
  );
}
