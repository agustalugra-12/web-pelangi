import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import LegalLayout from "@/components/site/LegalLayout";
import { LEGAL_CONTENT } from "@/i18n/legal";

// Renders inline `**bold**` and `<a href>` markers safely.
// We keep it minimal: bold via ** ** only.
function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) => {
    if (/^\*\*[^*]+\*\*$/.test(p)) return <strong key={i}>{p.slice(2, -2)}</strong>;
    return <span key={i}>{p}</span>;
  });
}

function renderBody(body, site, lang) {
  return body.map((b, i) => {
    if (typeof b === "string") return <p key={i}>{renderInline(b)}</p>;
    if (b && b.list) {
      return (
        <ul key={i}>
          {b.list.map((li, j) => (
            <li key={j}>{renderInline(li)}</li>
          ))}
        </ul>
      );
    }
    if (b && b.contact) {
      // Special contact block for privacy §9
      const emailLabel = lang === "en" ? "Email" : "Email";
      const waLabel = lang === "en" ? "WhatsApp" : "WhatsApp";
      const addrLabel = lang === "en" ? "Address" : "Alamat";
      const intro =
        lang === "en"
          ? "For privacy-related questions, please contact us at:"
          : "Untuk pertanyaan terkait privasi data, silakan hubungi kami di:";
      return (
        <div key={i}>
          <p>{intro}</p>
          <ul>
            <li>
              {emailLabel}: <a href={`mailto:${site.email}`}>{site.email}</a>
            </li>
            <li>
              {waLabel}: <a href={`https://wa.me/${site.whatsapp}`}>{site.whatsappDisplay}</a>
            </li>
            <li>
              {addrLabel}: {site.address}
            </li>
          </ul>
        </div>
      );
    }
    return null;
  });
}

// Generic legal page. Pass slug — one of the keys in LEGAL_CONTENT[lang].
// breadcrumbLabel is optional; falls back to page title.
export default function LegalPage({ slug }) {
  const { lang } = useLang();
  const { site } = useContent();
  const content = LEGAL_CONTENT[lang]?.[slug] || LEGAL_CONTENT.id[slug];

  return (
    <LegalLayout
      title={content.title}
      description={content.description}
      breadcrumb={[{ label: content.title }]}
      hero={content.hero}
    >
      {content.showLastUpdated && (
        <p>
          <em>
            {lang === "en" ? "Last updated" : "Terakhir diperbarui"}:{" "}
            {new Date().toLocaleDateString(lang === "en" ? "en-GB" : "id-ID", {
              year: "numeric",
              month: "long",
            })}
            .
          </em>
        </p>
      )}
      {content.sections.map((s, i) => (
        <div key={i}>
          <h2>{s.h}</h2>
          {renderBody(s.body, site, lang)}
        </div>
      ))}
    </LegalLayout>
  );
}
