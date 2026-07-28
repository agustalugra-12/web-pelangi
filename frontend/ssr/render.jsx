// Real SSR entry (2026-07-26, extended 2026-07-28 to accept any `path` - was Home-only)
// - renders any route via ReactDOMServer.renderToString, which never runs effects, so
// its output always matches a fresh client's first render pass. This replaces the
// earlier headless-browser (Playwright) capture approach, which captured the DOM AFTER
// mount effects fired (networkidle) - a different point in the lifecycle than what
// hydrateRoot compares against, causing production-only hydration mismatches (Minified
// React error #418). See /root/.claude/plans/buzzing-bouncing-lark.md.
//
// Not bundled by CRA/craco - built separately via ssr/build.mjs (esbuild, Node target).
// NODE_ENV is baked to "production" at build time via esbuild's `define` (selects
// react/react-dom's production internals) - no runtime assignment needed here.

import React from "react";
import { renderToPipeableStream } from "react-dom/server";
import { PassThrough } from "stream";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StaticRouter } from "react-router";
import { AuthProvider } from "@/context/AuthContext";
import { ContentProvider } from "@/context/ContentContext";
import { LanguageProvider } from "@/context/LanguageContext";
import { AppRoutes } from "@/App";

// renderToString (versi lama fungsi ini) cuma cocok utk Home, yang di-import EAGER
// di App.js (import Home from "@/pages/Home") - semua halaman lain (Rooms, Facilities,
// dst) di-lazy-load (React.lazy), dan renderToString TIDAK BISA menunggu dynamic
// import() lazy component selesai - hasilnya cuma fallback Suspense kosong
// ("<!--$!--><template></template><!--/$-->"), ditemukan 2026-07-28 saat coba
// perluas prerender ke /rooms. renderToPipeableStream + onAllReady (bukan
// onShellReady) menunggu SEMUA Suspense boundary - termasuk lazy-loaded page
// component - selesai resolve dulu sebelum di-pipe, baru benar2 lengkap.
export function renderHome({ content, lang, origin, path = "/" }) {
  // Minimal window/localStorage shim - only what the tree actually touches
  // synchronously during render (confirmed via source audit):
  //   - AuthContext.jsx reads bare `localStorage.getItem(...)` synchronously in useState
  //   - LodgingSchema.jsx reads `window.location.origin` for JSON-LD @id/url
  //   - LanguageContext.jsx falls back to `window.navigator.language` if no stored/
  //     prerendered lang matches (shouldn't happen given our inputs, cheap insurance)
  // Deliberately NOT shimming `document` - axios/@radix-ui/@tanstack query-core all
  // safely no-op or short-circuit without it (confirmed), and adding a fake `document`
  // risks fooling a library into thinking it's in a real browser.
  const fakeStorage = { getItem: () => null, setItem() {} };
  global.localStorage = fakeStorage;
  global.window = {
    localStorage: fakeStorage,
    location: {
      origin,
      hostname: origin.replace(/^https?:\/\//, ""),
      href: origin + path,
    },
    navigator: { language: lang },
    // ContentContext/LanguageContext read this exact shape for their initial state -
    // must match what prerender_home.py later embeds as the literal <script> tag, or
    // the client's hydration pass would mismatch against THIS render's output.
    __PRERENDERED__: { content, lang },
  };

  const queryClient = new QueryClient({
    defaultOptions: { queries: { staleTime: 60_000 } },
  });

  // Reconstructs the SAME provider tree App.js uses client-side, just with StaticRouter
  // instead of BrowserRouter - kept as a separate tree (not by passing a prop to App)
  // specifically so StaticRouter/react-router core is never imported by App.js itself,
  // keeping it out of the client bundle entirely.
  const element = (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ContentProvider>
          <LanguageProvider>
            <StaticRouter location={path}>
              <AppRoutes />
            </StaticRouter>
          </LanguageProvider>
        </ContentProvider>
      </AuthProvider>
    </QueryClientProvider>
  );

  return new Promise((resolve, reject) => {
    let html = "";
    const passthrough = new PassThrough();
    passthrough.on("data", (chunk) => { html += chunk; });
    passthrough.on("end", () => resolve(html));
    passthrough.on("error", reject);

    const { pipe } = renderToPipeableStream(element, {
      onAllReady() {
        pipe(passthrough);
      },
      onError(err) {
        reject(err);
      },
    });
  });
}
