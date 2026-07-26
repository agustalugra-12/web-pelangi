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

// Perpanjang sesi otomatis (2026-07-26, laporan user "gagal simpan" di CMS) -
// access_token cuma berlaku 60 menit, sebelumnya TIDAK ADA cara memperpanjang sama
// sekali walau refresh_token (7 hari) sudah ada di cookie sejak login - begitu admin
// buka CMS >60 menit lalu klik Simpan, request langsung gagal 401 permanen sampai
// login ulang. Sekarang: begitu ada respons 401, coba /auth/refresh SEKALI, kalau
// berhasil ulangi request aslinya secara transparan - admin tidak perlu tahu/lakukan
// apapun. Kalau refresh JUGA gagal (refresh_token juga sudah kedaluwarsa/tidak ada),
// baru redirect ke halaman login - itu satu-satunya kasus yang genuinely perlu login
// ulang.
let refreshingPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const isAuthRoute = original?.url?.includes("/auth/login") || original?.url?.includes("/auth/refresh");
    if (status === 401 && !original._retried && !isAuthRoute) {
      original._retried = true;
      try {
        if (!refreshingPromise) {
          refreshingPromise = api.post("/auth/refresh").finally(() => {
            refreshingPromise = null;
          });
        }
        await refreshingPromise;
        return api(original);
      } catch (refreshErr) {
        if (typeof window !== "undefined") window.location.href = "/admin/login";
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

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
