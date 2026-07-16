import { Link } from "react-router-dom";
import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import Seo from "@/components/site/Seo";
import Breadcrumb from "@/components/site/Breadcrumb";
import RainbowAccent from "@/components/site/RainbowAccent";

// Wrapper for legal / info pages. Provides:
//  - SEO metadata (title, description, JSON-LD BreadcrumbList)
//  - Breadcrumb nav
//  - Hero with eyebrow + H1 (single H1 per page)
//  - Book Now CTA + supporting text at the bottom
export default function LegalLayout({
  title,
  eyebrow,
  hero,
  description,
  breadcrumb = [],
  children,
}) {
  const { site } = useContent();
  const { t } = useLang();
  const bcJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: (typeof window !== "undefined" ? window.location.origin : "") + "/" },
      ...breadcrumb.map((b, i) => ({
        "@type": "ListItem",
        position: i + 2,
        name: b.label,
        ...(b.to ? { item: (typeof window !== "undefined" ? window.location.origin : "") + b.to } : {}),
      })),
    ],
  };

  return (
    <div className="pt-14 pb-24">
      <Seo title={title} description={description} jsonLd={bcJsonLd} />
      <section className="max-w-4xl mx-auto px-5 md:px-8">
        <Breadcrumb items={breadcrumb} />
        <p className="font-script text-2xl text-mustard-deep">{eyebrow || t("legal.eyebrow")}</p>
        <h1 className="font-display font-semibold text-teal-deep text-4xl md:text-5xl lg:text-6xl leading-tight">
          {title}
        </h1>
        <div className="mt-5"><RainbowAccent width="w-20" /></div>
        {hero && <p className="mt-6 text-lg text-teal-deep/85 leading-relaxed">{hero}</p>}

        <div className="mt-10 bg-paper rounded-3xl border border-ink/10 shadow-paper-sm p-6 md:p-10 prose-pelangi">
          {children}
        </div>

        {/* CTA */}
        <div className="mt-12 bg-teal-deep text-cream rounded-3xl p-8 md:p-10">
          <p className="font-script text-2xl text-mustard-soft">{t("legal.ctaScript")}</p>
          <h3 className="font-display italic text-3xl md:text-4xl mt-1">{t("legal.ctaTitle")}</h3>
          <p className="mt-3 text-cream/85 max-w-2xl">{t("legal.ctaBody")}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a href={site.bookingUrl} target="_blank" rel="noopener noreferrer"
              className="btn-lift inline-flex items-center gap-2 rounded-full bg-leaf text-white px-6 py-3 font-semibold shadow-paper-sm">
              {t("common.bookNow")}
              <i className="fa-solid fa-arrow-right text-xs" aria-hidden="true"></i>
            </a>
            <Link to="/contact" className="btn-lift inline-flex items-center gap-2 rounded-full border-2 border-mustard-soft text-mustard-soft px-6 py-3 font-semibold hover:bg-mustard-soft hover:text-teal-deep">
              {t("common.contactUs")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
