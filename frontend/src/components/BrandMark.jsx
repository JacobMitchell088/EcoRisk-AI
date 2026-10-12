// A survey crosshair (the search radius) around a leaf (the species it protects).
export default function BrandMark({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <circle cx="16" cy="16" r="11" fill="none" stroke="#25586A" strokeWidth="2.4" />
      <path
        d="M16 1.8v5.4M16 24.8v5.4M1.8 16h5.4M24.8 16h5.4"
        stroke="#25586A"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <g transform="rotate(40 16 16)">
        <path d="M16 9.6c4.1 2.6 4.1 10.2 0 12.8-4.1-2.6-4.1-10.2 0-12.8z" fill="#4E7A45" />
        <path d="M16 12.6v7" stroke="#F9FAF7" strokeWidth="1.2" strokeLinecap="round" />
      </g>
    </svg>
  );
}
