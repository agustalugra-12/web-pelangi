import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

// Multi-situs (2026-07-25) - situs aktif yang dipilih owner lewat SiteSwitcher admin
// (lihat AuthContext.jsx) dikirim sebagai X-Site di setiap request. Endpoint publik
// tidak butuh ini (backend resolve dari domain/Host sendiri), tapi mengirimnya selalu
// tidak masalah - endpoint publik cukup mengabaikannya.
api.interceptors.request.use((config) => {
  const site = localStorage.getItem("web_active_site");
  if (site) config.headers["X-Site"] = site;
  return config;
});

export function formatApiError(detail) {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail
      .map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e)))
      .filter(Boolean)
      .join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export default api;
