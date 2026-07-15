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

export function ContentProvider({ children }) {
  const [content, setContent] = useState(DEFAULT_CONTENT);
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
