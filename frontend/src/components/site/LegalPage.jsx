import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";
import LegalLayout from "@/components/site/LegalLayout";
import { LEGAL_CONTENT } from "@/i18n/legal";

// 2026-08-13, bug nyata ditemukan Agus ("harmonihillsvillage.com yang tampil web
// pelangi") - LEGAL_CONTENT (i18n/legal.js) awalnya ditulis HARDCODE "Pelangi Homestay"
// di puluhan tempat (privacy/terms/cancellation/refund/house-rules/payment-info x2
// bahasa), halaman legal Harmoni jadi salah sebut brand di sepanjang isi.
//
// Perbaikan v1 (string-match "Pelangi Homestay" literal) SEMPAT dipakai tapi rapuh -
// permintaan Agus lanjutan "pisahkan kedua brand agar tidak tercampur": kalau suatu saat
// wording brand berubah/typo, match literal itu diam-diam berhenti berfungsi tanpa
// error apa pun. Sekarang legal.js TIDAK PERNAH lagi menulis nama brand tertentu sama
// sekali - SEMUA teks memakai token eksplisit `{{BRAND}}` (lihat i18n/legal.js), jadi
// pemisahan brand terlihat jelas di source (bukan implisit lewat kecocokan string) &
// mustahil "kelewat nyambung" ke brand yang salah - token yang tidak tersubstitusi akan
// terlihat JELAS di halaman (literal "{{BRAND}}" tampil ke tamu), bukan gagal diam-diam.
function withBrand(text, brand) {
  if (typeof text !== "string" || !brand) return text;
  return text.replaceAll("{{BRAND}}", brand);
}

// Renders inline `**bold**` and `<a href>` markers safely.
// We keep it minimal: bold via ** ** only.
function renderInline(text, brand) {
  const parts = withBrand(text, brand).split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) => {
    if (/^\*\*[^*]+\*\*$/.test(p)) return <strong key={i}>{p.slice(2, -2)}</strong>;
    return <span key={i}>{p}</span>;
  });
}

function renderBody(body, site, lang) {
  return body.map((b, i) => {
    if (typeof b === "string") return <p key={i}>{renderInline(b, site.brand)}</p>;
    if (b && b.list) {
      return (
        <ul key={i}>
          {b.list.map((li, j) => (
            <li key={j}>{renderInline(li, site.brand)}</li>
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
  const title = withBrand(content.title, site.brand);

  return (
    <LegalLayout
      title={title}
      description={withBrand(content.description, site.brand)}
      breadcrumb={[{ label: title }]}
      hero={withBrand(content.hero, site.brand)}
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
          <h2>{withBrand(s.h, site.brand)}</h2>
          {renderBody(s.body, site, lang)}
        </div>
      ))}
    </LegalLayout>
  );
}
