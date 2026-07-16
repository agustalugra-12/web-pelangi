// Lightweight SEO helper — updates document.title + meta tags per page.
// Works on any React version by mutating document.head via useEffect.
import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useContent } from "@/context/ContentContext";
import { useLang } from "@/context/LanguageContext";

function upsertMeta(selector, attrs) {
  let el = document.head.querySelector(selector);
  if (!el) {
    el = document.createElement("meta");
    for (const k in attrs) {
      if (k !== "content") el.setAttribute(k, attrs[k]);
    }
    document.head.appendChild(el);
  }
  el.setAttribute("content", attrs.content || "");
}

function upsertLink(rel, href) {
  let el = document.head.querySelector(`link[rel="${rel}"]`);
  if (!el) {
    el = document.createElement("link");
    el.setAttribute("rel", rel);
    document.head.appendChild(el);
  }
  el.setAttribute("href", href);
}

export default function Seo({ title, description, image, jsonLd }) {
  const location = useLocation();
  const { site } = useContent();
  const { lang, pick } = useLang();

  useEffect(() => {
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const url = origin + location.pathname;
    const brand = site.brand;
    const siteSeoTitle = pick(site, "seoTitle") || brand;
    const siteSeoDesc = pick(site, "seoDescription") || "";
    const t = title ? `${title} — ${brand}` : siteSeoTitle;
    const d = description || siteSeoDesc;
    const img = image || `${origin}/assets/pelangi-logo.png`;

    document.title = t;
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("lang", lang);
    }
    upsertMeta('meta[name="description"]', { name: "description", content: d });
    upsertMeta('meta[property="og:title"]', { property: "og:title", content: t });
    upsertMeta('meta[property="og:description"]', { property: "og:description", content: d });
    upsertMeta('meta[property="og:type"]', { property: "og:type", content: "website" });
    upsertMeta('meta[property="og:url"]', { property: "og:url", content: url });
    upsertMeta('meta[property="og:image"]', { property: "og:image", content: img });
    upsertMeta('meta[property="og:site_name"]', { property: "og:site_name", content: site.brand });
    upsertMeta('meta[name="twitter:card"]', { name: "twitter:card", content: "summary_large_image" });
    upsertMeta('meta[name="twitter:title"]', { name: "twitter:title", content: t });
    upsertMeta('meta[name="twitter:description"]', { name: "twitter:description", content: d });
    upsertMeta('meta[name="twitter:image"]', { name: "twitter:image", content: img });
    upsertMeta('meta[name="robots"]', { name: "robots", content: "index,follow" });
    upsertLink("canonical", url);

    // JSON-LD structured data (breadcrumbs / LodgingBusiness / etc.)
    const scriptId = "page-jsonld";
    let script = document.getElementById(scriptId);
    if (script) script.remove();
    if (jsonLd) {
      script = document.createElement("script");
      script.type = "application/ld+json";
      script.id = scriptId;
      script.textContent = JSON.stringify(jsonLd);
      document.head.appendChild(script);
    }
  }, [title, description, image, jsonLd, location.pathname, site, lang, pick]);

  return null;
}
