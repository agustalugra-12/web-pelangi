// Global JSON-LD LodgingBusiness schema — rendered once in SiteLayout so it
// appears on every public page. Complements per-page BreadcrumbList schema
// from LegalLayout/Seo.
import { useContent } from "@/context/ContentContext";

export default function LodgingSchema() {
  const { site } = useContent();
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const schema = {
    "@context": "https://schema.org",
    "@type": "LodgingBusiness",
    "@id": `${origin}/#lodgingbusiness`,
    name: site.brand,
    description: site.seoDescription,
    url: origin,
    logo: `${origin}/assets/pelangi-logo.png`,
    image: [`${origin}/assets/pelangi-logo.png`, `${origin}/assets/signage.jpg`, `${origin}/assets/facade.jpg`],
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
