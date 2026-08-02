import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useLang } from "@/context/LanguageContext";
import { useContent } from "@/context/ContentContext";
import api from "@/lib/api";
import Seo from "@/components/site/Seo";
import { breadcrumbNode, schemaGraph } from "@/lib/schema";

// Sama seperti Blog.jsx (2026-07-28, perluas SSR) - snapshot BlogDetail spesifik utk
// 1 slug tertentu, jadi cocokkan slug URL saat ini dgn slug yang dipakai saat prerender
// (harusnya SELALU sama krn nginx serve snapshot yang benar per-slug, tapi jaga-jaga
// kalau ada mismatch, jangan pakai data slug yang salah - fallback ke fetch normal).
function initialBlogDetail(slug) {
  if (typeof window === "undefined") return null;
  const detail = window.__PRERENDERED_BLOG__?.detail;
  return detail && detail.slug === slug ? detail : null;
}

export default function BlogDetail() {
  const { slug } = useParams();
  const initial = initialBlogDetail(slug);
  const [post, setPost] = useState(initial);
  const [loading, setLoading] = useState(!initial);
  const [notFound, setNotFound] = useState(false);
  const { t, lang, pick } = useLang();
  const { testimonials } = useContent();

  useEffect(() => {
    api
      .get(`/blog/${slug}`)
      .then(({ data }) => setPost(data))
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <div className="min-h-[60vh] flex items-center justify-center text-teal-deep">{t("common.loading")}</div>;
  if (notFound) {
    // noindex (2026-07-28, audit SEO teknis) - slug artikel yang tidak ada TETAP dapat
    // index.html 200 dari nginx (regex /blog/:slug tidak bisa tahu slug asli/palsu tanpa
    // query DB), jadi harus tegas noindex di sini supaya tidak ikut ke-index sbg halaman
    // kosong "Artikel tidak ditemukan" - sebelumnya <Seo> tidak pernah dipasang sama sekali
    // di state ini, jadi tidak ada sinyal apa pun (bukan cuma "tidak noindex", tapi kosong).
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4 px-6 text-center">
        <Seo title={t("blog.notFound")} noindex />
        <p className="font-display italic text-3xl text-teal-deep">{t("blog.notFound")}</p>
        <Link to="/blog" className="rounded-full bg-leaf text-white px-5 py-2 font-semibold">{t("common.backToBlog")}</Link>
      </div>
    );
  }

  const locale = lang === "en" ? "en-GB" : "id-ID";
  const content = pick(post, "content") || post.content;
  const jsonLd = buildArticleSchema(post, content, t("blog.title"), testimonials);

  return (
    <article className="max-w-3xl mx-auto px-5 md:px-8 pt-14 pb-24" data-testid={`blog-detail-${post.slug}`}>
      <Seo title={pick(post, "title")} description={pick(post, "excerpt")} image={post.cover_image || undefined} jsonLd={jsonLd} />
      <Link to="/blog" className="text-sm text-mustard-deep hover:underline">← {t("common.allArticles")}</Link>
      <p className="mt-4 text-[11px] font-semibold uppercase tracking-widest text-mustard-deep">{post.category}</p>
      <h1 className="font-display text-4xl md:text-5xl text-teal-deep leading-tight mt-2">{pick(post, "title")}</h1>
      <p className="mt-3 text-sm text-teal-deep/60">
        {/* Byline (2026-08-02, PRD "AI Blog V2.0" modul 9 EEAT Builder) - identitas TIM ASLI
            di balik artikel, bukan cuma tanggal - sinyal E-E-A-T yang PEMBACA benar-benar
            lihat, bukan cuma tersembunyi di JSON-LD. Fallback ke label brand generik kalau
            artikel lama belum punya field author (dibuat sebelum fix ini). */}
        {(post.author || (lang === "en" ? "Our Team" : "Tim Kami")) + " · "}
        {new Date(post.created_at).toLocaleDateString(locale, { day: "numeric", month: "long", year: "numeric" })}
        {/* "Terakhir diperbarui" (2026-07-29, Editorial Standard v2) - sinyal freshness/EEAT
            nyata utk PEMBACA, sebelumnya updated_at cuma ada di JSON-LD (dateModified) utk
            crawler, manusia tidak pernah lihat. Cuma tampil kalau BENAR-BENAR pernah direvisi
            (selisih >1 hari dari created_at) - artikel yang belum pernah diperbarui punya
            updated_at nyaris sama dgn created_at (beda hitungan detik saat insert), jangan
            tampilkan "diperbarui" yang menyesatkan utk itu. */}
        {post.updated_at && (new Date(post.updated_at) - new Date(post.created_at)) > 86400000 && (
          <span className="text-teal-deep/45">
            {" · "}
            {lang === "en" ? "Updated" : "Diperbarui"} {new Date(post.updated_at).toLocaleDateString(locale, { day: "numeric", month: "long", year: "numeric" })}
          </span>
        )}
      </p>
      {post.cover_image && (
        <img
          src={post.cover_image}
          alt={pick(post, "title")}
          className="mt-6 w-full aspect-[16/9] object-cover rounded-2xl"
        />
      )}
      <p className="mt-6 text-lg text-teal-deep/85 italic font-display">{pick(post, "excerpt")}</p>
      <div className="mt-8 prose-pelangi">
        {content.split(/\n\n+/).map((para, i) => {
          const wholeBoldMatch = para.match(/^\*\*(.+)\*\*$/s);
          if (wholeBoldMatch) {
            return <h3 key={i} className="font-display text-2xl text-teal-deep mt-8 mb-2">{renderInline(wholeBoldMatch[1])}</h3>;
          }

          // Blok berisi baris "- item" (single \n, bukan paragraf terpisah) -
          // tanpa ini, tiap item cuma nempel jadi satu baris panjang karena <p>
          // tidak menampilkan \n biasa sebagai baris baru.
          const lines = para.split("\n");
          const bulletStart = lines.findIndex((l) => l.trim().startsWith("- "));
          if (bulletStart !== -1 && lines.slice(bulletStart).every((l) => l.trim().startsWith("- "))) {
            const intro = lines.slice(0, bulletStart).join(" ").trim();
            const items = lines.slice(bulletStart).map((l) => l.trim().replace(/^- /, ""));
            return (
              <div key={i}>
                {intro && <p>{renderInline(intro)}</p>}
                <ul className="list-disc pl-5 space-y-1 mb-[1.1rem]">
                  {items.map((item, j) => <li key={j}>{renderInline(item)}</li>)}
                </ul>
              </div>
            );
          }

          // Jaring pengaman umum: blok manapun dengan >1 baris (single \n) yang
          // BUKAN pola bullet di atas - render tiap baris dengan <br/> di antaranya,
          // bukan biarkan nempel jadi satu baris panjang. Ditemukan nyata dari
          // artikel auto-generate AI yang menulis pola "**Pertanyaan?**\n*teks*\njawaban"
          // (bukan **teks pertanyaan?** langsung) - parser harus tetap aman meski
          // AI tidak persis ikuti format yang diminta di prompt.
          if (lines.length > 1) {
            return (
              <p key={i}>
                {lines.map((line, j) => (
                  <span key={j}>
                    {j > 0 && <br />}
                    {renderInline(line)}
                  </span>
                ))}
              </p>
            );
          }

          return <p key={i}>{renderInline(para)}</p>;
        })}
      </div>
    </article>
  );
}

// Bangun JSON-LD Article + (kalau ada) FAQPage + BreadcrumbList langsung dari data
// post yang sudah tersedia lewat API - server.py (post_to_out) cuma meneruskan field
// tertentu, jadi field schema terpisah tidak akan pernah sampai ke sini kalau
// disimpan di backend.
function buildArticleSchema(post, content, blogLabel, testimonials) {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  // 2 pola didukung: (a) "**Pertanyaan asli?**" diikuti 1 ATAU 2 baris baru lalu
  // jawaban - AI kadang pakai \n kadang \n\n meski diminta \n\n persis, jadi regex
  // sengaja longgar (\n+) - dipakai artikel manual maupun auto-generate AI yang sudah
  // benar formatnya, (b) "**Pertanyaan?**\n*teks pertanyaan asli*\njawaban" - pola
  // salah yang PERNAH dihasilkan AI sebelum prompt diperbaiki (2026-07-26), tetap
  // didukung supaya artikel lama dgn pola ini juga dapat schema yang benar.
  const faqPairs = [
    ...content.matchAll(/\*\*([^*]+\?)\*\*\n+([^\n]+)/g),
    ...content.matchAll(/\*\*Pertanyaan\?\*\*\n\*([^*]+)\*\n([^\n]+)/g),
  ];
  // publisher/author (2026-07-28, lengkapi Schema Generator; author diperbarui 2026-08-02
  // PRD "AI Blog V2.0" modul 9 EEAT Builder) - Article punya publisher Organization+logo
  // utk rich result, direferensikan lewat @id ke LodgingBusiness yang sama (dirender site-
  // wide di SiteLayout/LodgingSchema.jsx). Author SEKARANG entity Organization bernama
  // TERPISAH ("Tim {brand}", dari post.author - lihat seo_agent.py generate_one) - BUKAN
  // nama editor/reviewer karangan (byline palsu justru berisiko dianggap konten
  // menyesatkan bagi Google), tapi juga bukan lagi cuma nunjuk balik ke publisher generik
  // spt sebelumnya - identitas tim asli yang bisa diverifikasi lebih spesifik drpd cuma
  // nama bisnis. Fallback ke publisherRef kalau artikel lama belum punya post.author.
  const publisherRef = { "@id": `${origin}/#lodgingbusiness` };
  const authorNode = post.author ? { "@type": "Organization", name: post.author } : publisherRef;
  const nodes = [
    {
      "@type": "Article",
      headline: post.title,
      description: post.excerpt,
      image: post.cover_image ? `${origin}${post.cover_image}` : undefined,
      datePublished: post.created_at,
      dateModified: post.updated_at,
      url: `${origin}/blog/${post.slug}`,
      author: authorNode,
      publisher: publisherRef,
    },
    breadcrumbNode([
      { label: blogLabel, to: "/blog" },
      { label: post.title },
    ]),
  ];
  if (faqPairs.length) {
    nodes.push({
      "@type": "FAQPage",
      mainEntity: faqPairs.map(([, q, a]) => ({
        "@type": "Question", name: q,
        acceptedAnswer: { "@type": "Answer", text: a },
      })),
    });
  }
  // Review (2026-07-31, PRD "AI Blog V2" modul 9) - dari testimoni ASLI tamu
  // (site_content.type=testimonials, sama yang dipakai artikel & halaman utama), BUKAN
  // data buatan. SENGAJA TIDAK menyertakan `reviewRating`/`AggregateRating` - tidak ada
  // rating numerik asli yang dikumpulkan sistem ini (cuma kutipan teks), jadi jujur
  // dihilangkan drpd mengarang angka bintang. Rotasi deterministik per-slug (bukan selalu
  // testimoni pertama - pelajaran yang sama dgn bug "Rina & Aldo selalu dikutip" yang
  // sudah diperbaiki di seo_agent.py) supaya tidak semua artikel kutip testimoni yang sama.
  if (Array.isArray(testimonials) && testimonials.length) {
    let hash = 0;
    for (const ch of post.slug || "") hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
    const tm = testimonials[hash % testimonials.length];
    if (tm?.text) {
      nodes.push({
        "@type": "Review",
        itemReviewed: publisherRef,
        author: { "@type": "Person", name: tm.name || "Tamu" },
        reviewBody: tm.text,
      });
    }
  }
  return schemaGraph(...nodes);
}

// Parser ringan untuk markdown dasar di dalam paragraf artikel - **bold** dan
// [teks](url) - konten blog dirender sebagai teks polos (bukan HTML/markdown),
// jadi tanpa ini keduanya cuma tampil sebagai tanda baca mentah (**...**) atau
// teks link yang tidak bisa diklik. Paragraf yang SELURUHNYA berupa **...**
// diperlakukan sebagai sub-judul (lihat wholeBoldMatch di atas), sisanya cuma
// bold inline biasa.
function renderInline(text) {
  const pattern = /\*\*([^*]+)\*\*|\*([^*\n]+)\*|\[([^\]]+)\]\(([^)]+)\)/g;
  const parts = [];
  let lastIndex = 0;
  let match;
  let key = 0;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    if (match[1] !== undefined) {
      parts.push(<strong key={key++}>{match[1]}</strong>);
    } else if (match[2] !== undefined) {
      parts.push(<em key={key++}>{match[2]}</em>);
    } else {
      const label = match[3];
      const href = match[4];
      const isInternal = href.startsWith("/");
      // Whitelist skema URL (2026-07-27, audit keamanan) - konten artikel dibuat AI TANPA
      // review manusia, jadi kalau AI pernah generate href seperti "javascript:..." (sengaja
      // atau tidak), itu TIDAK BOLEH jadi link yang bisa diklik. Cuma internal (/...),
      // http(s), atau mailto yang dirender sebagai link asli - selain itu tampil sbg teks biasa.
      const isSafeExternal = /^(https?:|mailto:)/i.test(href);
      parts.push(
        isInternal ? (
          <Link key={key++} to={href} className="text-mustard-deep underline hover:text-mustard">{label}</Link>
        ) : isSafeExternal ? (
          <a key={key++} href={href} target="_blank" rel="noopener noreferrer" className="text-mustard-deep underline hover:text-mustard">{label}</a>
        ) : (
          <span key={key++}>{label}</span>
        )
      );
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts.length ? parts : text;
}
