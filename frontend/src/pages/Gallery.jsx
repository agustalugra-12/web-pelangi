import { useMemo, useState } from "react";
import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import { galleryCategoriesAll } from "@/data/content";
import SectionHeading from "@/components/site/SectionHeading";

export default function Gallery() {
  const { gallery } = useContent();
  const { t } = useLang();
  const [active, setActive] = useState("Semua");
  const filtered = useMemo(
    () => (active === "Semua" ? gallery : gallery.filter((g) => g.category === active)),
    [active, gallery]
  );
  const label = (cat) => t(`gallery.categories.${cat}`, cat);

  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow={t("gallery.eyebrow")}
          title={t("gallery.title")}
          italicWord={t("gallery.italic")}
          subtitle={t("gallery.subtitle")}
        />

        <div className="mt-10 flex gap-2 overflow-x-auto no-scrollbar pb-2">
          {galleryCategoriesAll.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setActive(c)}
              data-testid={`gallery-filter-${c.toLowerCase().replace(/\s+/g, "-")}`}
              className={`shrink-0 rounded-full px-4 py-2 text-sm font-semibold border-2 transition-colors ${
                active === c
                  ? "bg-mustard text-teal-deep border-mustard"
                  : "bg-transparent text-teal-deep border-teal-deep/20 hover:border-teal-deep/60"
              }`}
            >
              {label(c)}
            </button>
          ))}
        </div>

        <div className="mt-8 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {filtered.map((g, i) => (
            <div key={g.id || `${g.category}-${i}`} className={`overflow-hidden rounded-2xl shadow-paper-sm ${i % 5 === 0 ? "aspect-[3/4]" : "aspect-square"}`}>
              <img src={g.src} alt={label(g.category)} className="w-full h-full object-cover hover:scale-105 transition-transform duration-500" loading="lazy" />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
