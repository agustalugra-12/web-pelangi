import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api, { formatApiError } from "@/lib/api";

const AuthContext = createContext(null);

// Multi-situs (2026-07-25) - satu build React yang sama melayani pelangihomestay.com
// DAN harmoni.pelangihomestay.com. Situs aktif default mengikuti domain yang sedang
// dibuka (lihat inferDefaultSite), tapi owner bisa pindah lewat SiteSwitcher untuk
// mengelola situs LAIN tanpa perlu login ulang dari domain itu - dipersist di
// localStorage sama seperti pola X-Property-Id di PMS.
export const ACTIVE_SITE_KEY = "web_active_site";
export const KNOWN_SITES = [
  { id: "pelangi", label: "Pelangi Homestay" },
  { id: "harmoni", label: "harmoni" },
];

function inferDefaultSite() {
  if (typeof window === "undefined") return "pelangi";
  return window.location.hostname.toLowerCase().includes("harmoni") ? "harmoni" : "pelangi";
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null = checking, false = anonymous, object = logged in
  const [loading, setLoading] = useState(true);
  const [activeSite, setActiveSiteState] = useState(
    () => localStorage.getItem(ACTIVE_SITE_KEY) || inferDefaultSite()
  );

  const setActiveSite = (site) => {
    localStorage.setItem(ACTIVE_SITE_KEY, site);
    // Reload penuh - cara paling sederhana supaya SEMUA halaman admin ikut fetch ulang
    // di bawah konteks situs baru tanpa perlu audit tiap halaman satu-satu (sama pola
    // dengan property switcher di PMS).
    window.location.reload();
    setActiveSiteState(site);
  };

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch (e) {
      setUser(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (email, password) => {
    try {
      const { data } = await api.post("/auth/login", { email, password });
      setUser(data.user);
      return { ok: true };
    } catch (e) {
      return { ok: false, error: formatApiError(e.response?.data?.detail) || e.message };
    }
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch (_) {}
    setUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh, activeSite, setActiveSite }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
