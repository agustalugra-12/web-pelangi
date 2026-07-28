import { Link } from "react-router-dom";
import { useLang } from "@/context/LanguageContext";
import { DICTIONARY } from "@/i18n/dictionary";
import Seo from "@/components/site/Seo";

// Catch-all React Router (2026-07-28, audit SEO teknis) - lapis pengaman KEDUA. Lapis
// pertama (utama) ada di nginx: try_files sekarang cuma serve index.html utk pola path
// yang benar-benar terdaftar, path lain dapat 404 asli dari nginx SEBELUM React Router
// sempat jalan sama sekali. Route ini jaga-jaga kalau suatu saat ada path yang lolos
// filter nginx (mis. sub-path dari route yang valid) - React Router sendiri sekarang juga
// tidak diam-diam render blank/apa pun, tapi halaman 404 sungguhan ber-status noindex.
export default function NotFound() {
  const { lang } = useLang();
  const t = DICTIONARY[lang]?.notFoundPage || DICTIONARY.id.notFoundPage;

  return (
    <div className="pt-24 pb-32 min-h-[60vh] flex items-center justify-center">
      <Seo title={t.title} noindex />
      <div className="text-center max-w-md mx-auto px-5">
        <p className="font-script text-2xl text-mustard-deep">{t.eyebrow}</p>
        <h1 className="font-display font-semibold text-teal-deep text-4xl md:text-5xl leading-tight mt-2">
          {t.title}
        </h1>
        <p className="mt-4 text-teal-deep/70">{t.body}</p>
        <Link
          to="/"
          className="btn-lift inline-flex mt-8 items-center gap-2 rounded-full bg-leaf text-white px-6 py-3 font-semibold shadow-paper-sm"
        >
          {t.cta}
        </Link>
      </div>
    </div>
  );
}
