import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import SectionHeading from "@/components/site/SectionHeading";

export default function ExploreBedugul() {
  const { attractions } = useContent();
  const { t, pick } = useLang();
  return (
    <div className="pt-14 pb-24">
      <section className="max-w-7xl mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow={t("explore.eyebrow")}
          title={t("explore.title")}
          italicWord={t("explore.italic")}
          subtitle={t("explore.subtitle")}
        />

        <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {attractions.map((a, i) => (
            <article key={a.id || a.title} className="group rounded-3xl overflow-hidden bg-paper shadow-paper-sm border border-ink/5 reveal" style={{ animationDelay: `${i * 90}ms` }} data-testid={`attraction-${i}`}>
              <div className="relative overflow-hidden">
                <img src={a.image} alt={pick(a, "title")} className="w-full h-56 object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy" />
                <span className="absolute top-4 left-4 bg-mustard text-teal-deep text-xs font-semibold rounded-full px-2.5 py-1">{pick(a, "distance")}</span>
              </div>
              <div className="p-5">
                <h3 className="font-display text-xl text-teal-deep">{pick(a, "title")}</h3>
                <p className="mt-2 text-sm text-teal-deep/75 leading-relaxed">{pick(a, "desc")}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
