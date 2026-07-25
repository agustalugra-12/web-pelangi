// Central React context holding site content editable via admin CMS.
// Fetches /api/content once on mount, merges with defaults so pages
// always have data (even before API returns).
import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { DEFAULT_CONTENT } from "@/data/content";

const ContentContext = createContext(null);

function mergeContent(base, override) {
  const merged = { ...base };
  if (override && typeof override === "object") {
    for (const key of Object.keys(override)) {
      if (override[key] !== undefined && override[key] !== null) {
        merged[key] = override[key];
      }
    }
  }
  return merged;
}

// Kalau halaman ini datang dari snapshot prerender (2026-07-26, LCP fix), pakai data yang
// SAMA PERSIS dipakai saat snapshot itu dirender - supaya hydrateRoot tidak lihat mismatch
// antara markup yang sudah ada dengan render pertama client (yang defaultnya DEFAULT_CONTENT
// sebelum fetch selesai). Halaman non-Home (tanpa snapshot) tetap mulai dari DEFAULT_CONTENT
// seperti sebelumnya - window.__PRERENDERED__ cuma ada di HTML hasil prerender.
function initialContent() {
  if (typeof window === "undefined" || !window.__PRERENDERED__?.content) return DEFAULT_CONTENT;
  return mergeContent(DEFAULT_CONTENT, window.__PRERENDERED__.content);
}

export function ContentProvider({ children }) {
  const [content, setContent] = useState(initialContent);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/content");
      setContent(mergeContent(DEFAULT_CONTENT, data));
    } catch (_) {
      // fall back to defaults silently
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <ContentContext.Provider value={{ content, loaded, refresh }}>
      {children}
    </ContentContext.Provider>
  );
}

export function useContent() {
  const ctx = useContext(ContentContext);
  if (!ctx) throw new Error("useContent must be used within ContentProvider");
  return ctx.content;
}

export function useRefreshContent() {
  const ctx = useContext(ContentContext);
  return ctx?.refresh;
}
