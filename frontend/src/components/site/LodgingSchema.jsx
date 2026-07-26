// Global JSON-LD LodgingBusiness schema — rendered once in SiteLayout so it
// appears on every public page. Complements per-page BreadcrumbList schema
// from LegalLayout/Seo.
//
// All fields below are derived from real per-site content (site_content /
// rooms) instead of being hardcoded to Pelangi's facts, so this stays correct
// as new sites are added. Only `numberOfRooms` and `geo` fall back to a small
// per-site table, since those aren't derivable from any displayed content —
// new sites simply omit them (never fabricated) until confirmed.
import { useContent } from "@/context/ContentContext";
import { faviconPath, heroImagePath } from "@/lib/siteAssets";

// Confirmed-only facts that can't be derived from site_content/rooms.
// Add an entry here only once the real value has been confirmed for that site.
const CONFIRMED_FACTS = {
  pelangi: {
    numberOfRooms: 18,
    geo: { latitude: -8.276, longitude: 115.164 },
  },
};

// Raw facility strings (as entered in CMS) → schema.org LocationFeatureSpecification name.
const AMENITY_MAP = [
  [/wi-?fi/i, "WiFi"],
  [/air\s*panas|hot\s*water/i, "Hot Water"],
  [/smart\s*tv|tv\s*led|television/i, "Smart TV"],
  [/breakfast|sarapan/i, "Breakfast Included"],
  [/\bac\b|air\s*cond/i, "Air Conditioning"],
  [/kamar\s*mandi\s*dalam|private\s*bathroom/i, "Private Bathroom"],
  [/teras\s*pribadi|private\s*terrace/i, "Private Terrace"],
  [/parkir|parking/i, "Free Parking"],
];

function deriveAmenities(rooms) {
  const found = new Set();
  for (const r of rooms || []) {
    for (const f of r.facilities || []) {
      const match = AMENITY_MAP.find(([re]) => re.test(f));
      if (match) found.add(match[1]);
    }
  }
  return [...found].map((name) => ({
    "@type": "LocationFeatureSpecification",
    name,
    value: true,
  }));
}

function derivePriceRange(rooms) {
  const values = (rooms || [])
    .map((r) => parseInt(String(r.priceFrom || "").replace(/\D/g, ""), 10))
    .filter((n) => !Number.isNaN(n));
  if (!values.length) return undefined;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const fmt = (n) => `IDR ${n.toLocaleString("id-ID")}`;
  return min === max ? fmt(min) : `${fmt(min)} – ${fmt(max)}`;
}

// Parses e.g. "Reception 07:00 – 22:00 WITA" into {opens, closes}. Sites
// without a fixed range (e.g. "Hubungi kami kapan saja lewat WhatsApp") are
// genuinely reachable any time, so they get a 24-hour spec, not a fabricated one.
function deriveOpeningHours(hoursText) {
  const match = String(hoursText || "").match(/(\d{1,2}:\d{2})\D+(\d{1,2}:\d{2})/);
  const [opens, closes] = match ? [match[1], match[2]] : ["00:00", "23:59"];
  return [
    {
      "@type": "OpeningHoursSpecification",
      dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
      opens,
      closes,
    },
  ];
}

export default function LodgingSchema() {
  const { site, rooms, _site } = useContent();
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const confirmed = CONFIRMED_FACTS[_site] || {};

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
    priceRange: derivePriceRange(rooms),
    address: site.address,
    openingHoursSpecification: deriveOpeningHours(site.hours),
    amenityFeature: deriveAmenities(rooms),
    sameAs: [],
    ...(confirmed.numberOfRooms ? { numberOfRooms: confirmed.numberOfRooms } : {}),
    ...(confirmed.geo ? { geo: { "@type": "GeoCoordinates", ...confirmed.geo } } : {}),
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
