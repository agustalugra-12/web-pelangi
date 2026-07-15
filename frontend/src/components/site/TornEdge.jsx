// Torn edge SVG divider. Use between colored sections.
// direction: 'top' or 'bottom'; color = background color of the following section
export default function TornEdge({ direction = "bottom", color = "#F7F3EA", className = "" }) {
  if (direction === "bottom") {
    return (
      <div className={`relative ${className}`} aria-hidden="true">
        <svg viewBox="0 0 1200 60" preserveAspectRatio="none" className="block w-full h-14 md:h-16">
          <path
            d="M0 0 C90 30 170 8 260 28 C350 48 420 12 520 30 C610 46 690 10 780 28 C870 46 950 12 1040 28 C1120 42 1170 20 1200 26 V60 H0 Z"
            fill={color}
          />
        </svg>
      </div>
    );
  }
  return (
    <div className={`relative ${className}`} aria-hidden="true">
      <svg viewBox="0 0 1200 60" preserveAspectRatio="none" className="block w-full h-14 md:h-16">
        <path
          d="M0 60 C90 30 170 52 260 32 C350 12 420 48 520 30 C610 14 690 50 780 32 C870 14 950 48 1040 32 C1120 18 1170 40 1200 34 V0 H0 Z"
          fill={color}
        />
      </svg>
    </div>
  );
}
