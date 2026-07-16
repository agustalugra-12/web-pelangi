import { useLang } from "@/context/LanguageContext";

// Compact ID / EN toggle. Sits in navbar (desktop) and mobile menu.
export default function LanguageSwitcher({ variant = "default" }) {
  const { lang, setLang } = useLang();
  const isDark = variant === "dark";

  const baseBtn =
    "px-2.5 py-1 text-xs font-semibold uppercase tracking-widest rounded-full transition-colors";
  const activeCls = isDark
    ? "bg-mustard-soft text-teal-deep"
    : "bg-teal-deep text-cream";
  const idleCls = isDark
    ? "text-cream/70 hover:text-cream"
    : "text-teal-deep/60 hover:text-teal-deep";

  return (
    <div
      data-testid="language-switcher"
      className={`inline-flex items-center gap-0.5 rounded-full border ${
        isDark ? "border-cream/30" : "border-ink/15"
      } p-0.5`}
    >
      <button
        type="button"
        onClick={() => setLang("id")}
        data-testid="lang-id"
        aria-pressed={lang === "id"}
        className={`${baseBtn} ${lang === "id" ? activeCls : idleCls}`}
      >
        ID
      </button>
      <button
        type="button"
        onClick={() => setLang("en")}
        data-testid="lang-en"
        aria-pressed={lang === "en"}
        className={`${baseBtn} ${lang === "en" ? activeCls : idleCls}`}
      >
        EN
      </button>
    </div>
  );
}
