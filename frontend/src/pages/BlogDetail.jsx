import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useLang } from "@/context/LanguageContext";
import api from "@/lib/api";

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
      <Link to="/blog" className="text-sm text-mustard-deep hover:underline">← {t("common.allArticles")}</Link>
      <p className="mt-4 text-[11px] font-semibold uppercase tracking-widest text-mustard-deep">{post.category}</p>
      <h1 className="font-display text-4xl md:text-5xl text-teal-deep leading-tight mt-2">{pick(post, "title")}</h1>
      <p className="mt-3 text-sm text-teal-deep/60">
        {new Date(post.created_at).toLocaleDateString(locale, { day: "numeric", month: "long", year: "numeric" })}
      </p>
      <p className="mt-6 text-lg text-teal-deep/85 italic font-display">{pick(post, "excerpt")}</p>
      <div className="mt-8 prose-pelangi">
        {content.split(/\n\n+/).map((para, i) => (
          <p key={i}>{para}</p>
        ))}
      </div>
    </article>
  );
}
