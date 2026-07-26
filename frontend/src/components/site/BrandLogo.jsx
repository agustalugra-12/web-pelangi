import { useContent } from "@/context/ContentContext";
import { faviconPath } from "@/lib/siteAssets";

// Circle-framed Pelangi logo with coin-flip animation
// Props:
//  - size: pixel size (default 56)
//  - variant: 'light' (cream circle, for dark backgrounds) | 'default' (paper circle for light bg)
//  - hoverFlip: on hover perform a coin flip (default true)
//  - autoFlip: periodic flip every 6s (default false)
export default function BrandLogo({
  size = 56,
  variant = "default",
  hoverFlip = true,
  autoFlip = false,
  className = "",
}) {
  const { _site } = useContent();
  const bg =
    variant === "light"
      ? "bg-cream border-cream shadow-paper"
      : "bg-paper border-mustard/40 shadow-paper-sm";
  return (
    <span
      className={`brand-logo relative inline-flex items-center justify-center rounded-full border-2 overflow-hidden ${bg} ${
        autoFlip ? "animate-coinFlipLoop" : ""
      } ${hoverFlip ? "group-hover:animate-coinFlip" : ""} ${className}`}
      style={{
        width: size,
        height: size,
        transformStyle: "preserve-3d",
        perspective: "800px",
      }}
      aria-hidden="true"
    >
      <img
        src={faviconPath(_site)}
        alt=""
        className="w-full h-full object-cover"
      />
    </span>
  );
}
