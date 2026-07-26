import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useLang } from "@/context/LanguageContext";
import api from "@/lib/api";
import Seo from "@/components/site/Seo";

export default function BlogDetail() {
  const { slug } = useParams();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const { t, lang, pick } = useLang();

  useEffect(() => {
    api
      .get(`/blog/${slug}`)
      .then(({ data }) => setPost(data))
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <div className="min-h-[60vh] flex items-center justify-center text-teal-deep">{t("common.loading")}</div>;
  if (notFound) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="font-display italic text-3xl text-teal-deep">{t("blog.notFound")}</p>
        <Link to="/blog" className="rounded-full bg-leaf text-white px-5 py-2 font-semibold">{t("common.backToBlog")}</Link>
      </div>
    );
  }

  const locale = lang === "en" ? "en-GB" : "id-ID";
  const content = pick(post, "content") || post.content;

  return (
    <article className="max-w-3xl mx-auto px-5 md:px-8 pt-14 pb-24" data-testid={`blog-detail-${post.slug}`}>
      <Seo title={pick(post, "title")} description={pick(post, "excerpt")} image={post.cover_image || undefined} />
      <Link to="/blog" className="text-sm text-mustard-deep hover:underline">← {t("common.allArticles")}</Link>
      <p className="mt-4 text-[11px] font-semibold uppercase tracking-widest text-mustard-deep">{post.category}</p>
      <h1 className="font-display text-4xl md:text-5xl text-teal-deep leading-tight mt-2">{pick(post, "title")}</h1>
      <p className="mt-3 text-sm text-teal-deep/60">
        {new Date(post.created_at).toLocaleDateString(locale, { day: "numeric", month: "long", year: "numeric" })}
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

          return <p key={i}>{renderInline(para)}</p>;
        })}
      </div>
    </article>
  );
}

// Parser ringan untuk markdown dasar di dalam paragraf artikel - **bold** dan
// [teks](url) - konten blog dirender sebagai teks polos (bukan HTML/markdown),
// jadi tanpa ini keduanya cuma tampil sebagai tanda baca mentah (**...**) atau
// teks link yang tidak bisa diklik. Paragraf yang SELURUHNYA berupa **...**
// diperlakukan sebagai sub-judul (lihat wholeBoldMatch di atas), sisanya cuma
// bold inline biasa.
function renderInline(text) {
  const pattern = /\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)]+)\)/g;
  const parts = [];
  let lastIndex = 0;
  let match;
  let key = 0;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    if (match[1] !== undefined) {
      parts.push(<strong key={key++}>{match[1]}</strong>);
    } else {
      const label = match[2];
      const href = match[3];
      const isInternal = href.startsWith("/");
      parts.push(
        isInternal ? (
          <Link key={key++} to={href} className="text-mustard-deep underline hover:text-mustard">{label}</Link>
        ) : (
          <a key={key++} href={href} target="_blank" rel="noopener noreferrer" className="text-mustard-deep underline hover:text-mustard">{label}</a>
        )
      );
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts.length ? parts : text;
}
