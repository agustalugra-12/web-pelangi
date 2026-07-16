// Lightweight i18n provider — no external dep, works with SSR-safe defaults.
// Persists selection in localStorage and updates <html lang="…"> on change.
// Exposes { lang, setLang, t(key), pick(item, field) } via useLang().
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { DICTIONARY, tGet } from "@/i18n/dictionary";

const ContextObj = createContext(null);
const STORAGE_KEY = "pelangi.lang";
const DEFAULT_LANG = "id";
const SUPPORTED = ["id", "en"];

function initialLang() {
  if (typeof window === "undefined") return DEFAULT_LANG;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored && SUPPORTED.includes(stored)) return stored;
  // First visit: try browser preference
  const browser = (window.navigator.language || "").slice(0, 2).toLowerCase();
  if (SUPPORTED.includes(browser)) return browser;
  return DEFAULT_LANG;
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(initialLang);

  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("lang", lang);
    }
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, lang);
    }
  }, [lang]);

  const setLang = useCallback((next) => {
    if (SUPPORTED.includes(next)) setLangState(next);
  }, []);

  const t = useCallback(
    (key, fallback) => {
      const active = DICTIONARY[lang] || DICTIONARY[DEFAULT_LANG];
      const value = tGet(active, key);
      if (value !== undefined) return value;
      const def = tGet(DICTIONARY[DEFAULT_LANG], key);
      return def !== undefined ? def : fallback ?? key;
    },
    [lang]
  );

  // Pick a translated CMS field. Convention: field foo has optional foo_en.
  // pick(room, "name") returns room.name_en when lang==="en" and non-empty,
  // otherwise room.name.
  const pick = useCallback(
    (item, field) => {
      if (!item) return "";
      if (lang === "en") {
        const en = item[`${field}_en`];
        if (en !== undefined && en !== null && en !== "") return en;
      }
      return item[field];
    },
    [lang]
  );

  const value = useMemo(
    () => ({ lang, setLang, t, pick, supported: SUPPORTED }),
    [lang, setLang, t, pick]
  );

  return <ContextObj.Provider value={value}>{children}</ContextObj.Provider>;
}

export function useLang() {
  const ctx = useContext(ContextObj);
  if (!ctx) throw new Error("useLang must be used within LanguageProvider");
  return ctx;
}
