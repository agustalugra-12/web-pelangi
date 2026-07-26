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
// apapun.
//
// BUG SERIUS ditemukan & diperbaiki (2026-07-26, langsung setelah deploy sebelumnya) -
// versi awal me-redirect paksa ke /admin/login (window.location.href) kalau refresh
// JUGA gagal. Ternyata AuthContext.refresh() memanggil GET /auth/me di SEMUA halaman
// termasuk HALAMAN PUBLIK (cek status login, wajar 401 utk pengunjung anonim yang
// belum login) - jadi pengunjung publik biasa pun ikut kena redirect paksa ke
// /admin/login, yang lalu memuat AuthProvider lagi -> /auth/me 401 lagi -> redirect
// lagi -> LOOP REDIRECT TAK TERBATAS di seluruh situs publik. Perbaikan: HAPUS redirect
// paksa sepenuhnya - cukup reject promise seperti biasa kalau refresh gagal.
// ProtectedRoute.jsx SUDAH benar menangani ini sendiri lewat <Navigate> React (bukan
// full-page reload) berdasarkan state `user` dari AuthContext - tidak perlu interceptor
// ini ikut campur redirect sama sekali.
let refreshingPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    // /auth/me sengaja ikut dikecualikan - 401 di situ WAJAR berarti "belum login"
    // (dipanggil di semua halaman termasuk publik), bukan sesi kedaluwarsa di tengah
    // aksi - AuthContext.refresh() sudah benar menangani via try/catch sendiri.
    const isAuthRoute = ["/auth/login", "/auth/refresh", "/auth/me"].some((p) => original?.url?.includes(p));
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
