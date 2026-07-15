import RainbowAccent from "@/components/site/RainbowAccent";

export default function SectionHeading({ eyebrow, title, italicWord, subtitle, align = "center", light = false }) {
  const textColor = light ? "text-cream" : "text-teal-deep";
  const eyebrowColor = light ? "text-mustard-soft" : "text-mustard-deep";
  const subColor = light ? "text-cream/80" : "text-teal-deep/70";
  return (
    <div className={`max-w-2xl ${align === "center" ? "mx-auto text-center" : ""}`}>
      {eyebrow && (
        <p className={`font-script text-2xl ${eyebrowColor} mb-2`}>{eyebrow}</p>
      )}
      <h2 className={`font-display font-semibold ${textColor} text-3xl md:text-4xl lg:text-5xl leading-tight`}>
        {title}{" "}
        {italicWord && <span className="italic text-mustard-deep">{italicWord}</span>}
      </h2>
      <div className={`mt-5 flex ${align === "center" ? "justify-center" : ""}`}>
        <RainbowAccent width="w-20" />
      </div>
      {subtitle && (
        <p className={`mt-4 ${subColor} text-base md:text-lg`}>{subtitle}</p>
      )}
    </div>
  );
}
