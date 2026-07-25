import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@/vendor/fontawesome/fontawesome-subset.css";
import "@/index.css";
import App from "@/App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
    },
  },
});

const container = document.getElementById("root");
const tree = (
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);

// Prerender LCP fix (2026-07-26): kalau HTML ini datang dari snapshot statis (lihat
// backend/scripts/prerender_home.py, window.__PRERENDERED__ diinjeksi ke <body> sebelum
// bundle ini jalan), pakai hydrateRoot supaya markup yang SUDAH ada di-reuse (bukan
// dibongkar-bangun ulang dari nol) - itu satu-satunya cara manfaat kecepatan prerender
// benar-benar kepakai. Semua halaman lain (tidak pernah dapat snapshot) tetap pakai
// createRoot seperti sebelumnya, tidak ada perubahan perilaku untuk mereka.
if (window.__PRERENDERED__) {
  ReactDOM.hydrateRoot(container, tree);
} else {
  ReactDOM.createRoot(container).render(tree);
}
