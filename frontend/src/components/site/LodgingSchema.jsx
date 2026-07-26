// Global JSON-LD LodgingBusiness schema — rendered once in SiteLayout so it
// appears on every public page. Complements per-page BreadcrumbList schema
// from LegalLayout/Seo.
import { useContent } from "@/context/ContentContext";
import { faviconPath, heroImagePath } from "@/lib/siteAssets";

export default function LodgingSchema() {
  const { site, _site } = useContent();
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  // NOTE (2026-07-26): sisa field di bawah (address/priceRange/numberOfRooms/
  // amenityFeature/openingHoursSpecification) MASIH HARDCODE data Pelangi apa pun
  // situsnya - ditemukan sekaligus saat perbaikan bug foto hero, TAPI belum diperbaiki
  // di sini krn butuh fakta asli harmoni (alamat lengkap, lat/long, jumlah kamar) yang
  // belum dikonfirmasi user, dan breakfast harmoni SUDAH dikonfirmasi TIDAK termasuk
  // (beda dari amenityFeature "Breakfast Included" di bawah). Ini schema.org JSON-LD yang
  // dibaca Google, jadi field yang salah bisa muncul di hasil pencarian - perlu tindak
  // lanjut terpisah, jangan anggap sudah benar untuk harmoni.
  const schema = {
    "@context": "https://schema.org",
    "@type": "LodgingBusiness",
    "@id": `${origin}/#lodgingbusiness`,
    name: site.brand,
    description: site.seoDescription,
    url: origin,
    logo: `${origin}${faviconPath(_site)}`,
    image: [`${origin}${faviconPath(_site)}`, `${origin}${heroImagePath(_site)}`],
    telephone: `+${site.whatsapp}`,
    email: site.email,
    priceRange: "IDR 175.000 – IDR 225.000",
    numberOfRooms: 18,
    address: {
      "@type": "PostalAddress",
      streetAddress: "Jl. Kebun Raya Bedugul",
      addressLocality: "Baturiti",
      addressRegion: "Bali",
      postalCode: "82191",
      addressCountry: "ID",
    },
    geo: {
      "@type": "GeoCoordinates",
      latitude: -8.276,
      longitude: 115.164,
    },
    openingHoursSpecification: [
      {
        "@type": "OpeningHoursSpecification",
        dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        opens: "07:00",
        closes: "22:00",
      },
    ],
    amenityFeature: [
      { "@type": "LocationFeatureSpecification", name: "WiFi", value: true },
      { "@type": "LocationFeatureSpecification", name: "Free Parking", value: true },
      { "@type": "LocationFeatureSpecification", name: "Breakfast Included", value: true },
      { "@type": "LocationFeatureSpecification", name: "Hot Water", value: true },
      { "@type": "LocationFeatureSpecification", name: "Smart TV", value: true },
    ],
    sameAs: [],
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
