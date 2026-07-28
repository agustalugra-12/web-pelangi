// Helper JSON-LD bersama (2026-07-28, lengkapi Schema Generator) - dipakai di semua
// halaman yang butuh BreadcrumbList, supaya tidak duplikasi logic yang sebelumnya
// cuma ada inline di LegalLayout.jsx (dan cuma berlaku utk halaman Legal).
export function breadcrumbNode(items) {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  return {
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: `${origin}/` },
      ...items.map((b, i) => ({
        "@type": "ListItem",
        position: i + 2,
        name: b.label,
        ...(b.to ? { item: `${origin}${b.to}` } : {}),
      })),
    ],
  };
}

// Gabungkan beberapa node schema (mis. BreadcrumbList + FAQPage) jadi satu @graph -
// Seo.jsx cuma menerima 1 prop jsonLd, @graph adalah cara resmi schema.org utk
// menaruh >1 entitas pada satu blok JSON-LD yang sama.
export function schemaGraph(...nodes) {
  return { "@context": "https://schema.org", "@graph": nodes.filter(Boolean) };
}
