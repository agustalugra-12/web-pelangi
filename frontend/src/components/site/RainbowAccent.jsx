// Thin rainbow accent bar in Pelangi brand colors (green / yellow / red).
// Use as a divider under section headings, or as a top border on cards.
// Props:
//  - width: e.g. 'w-16', 'w-24' (default w-20)
//  - align: 'left' | 'center' | 'right'
export default function RainbowAccent({ width = "w-20", align = "left", className = "" }) {
  const justify =
    align === "center" ? "mx-auto" : align === "right" ? "ml-auto" : "";
  return (
    <span
      className={`inline-flex ${width} ${justify} ${className}`}
      aria-hidden="true"
    >
      <span className="flex-1 h-1 bg-emerald-600 rounded-full"></span>
      <span className="flex-1 h-1 bg-yellow-400 rounded-full mx-1"></span>
      <span className="flex-1 h-1 bg-red-500 rounded-full"></span>
    </span>
  );
}
