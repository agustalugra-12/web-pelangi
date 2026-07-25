// Real SSR entry (2026-07-26) - renders Home via ReactDOMServer.renderToString, which
// never runs effects, so its output always matches a fresh client's first render pass.
// This replaces the earlier headless-browser (Playwright) capture approach, which
// captured the DOM AFTER mount effects fired (networkidle) - a different point in the
// lifecycle than what hydrateRoot compares against, causing production-only hydration
// mismatches (Minified React error #418). See /root/.claude/plans/buzzing-bouncing-lark.md.
//
// Not bundled by CRA/craco - built separately via ssr/build.mjs (esbuild, Node target).
// NODE_ENV is baked to "production" at build time via esbuild's `define` (selects
// react/react-dom's production internals) - no runtime assignment needed here.

import React from "react";
import { renderToString } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "@/App";

export function renderHome({ content, lang, origin }) {
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
      href: origin + "/",
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

  return renderToString(
    <QueryClientProvider client={queryClient}>
      <App ssrPath="/" />
    </QueryClientProvider>
  );
}
