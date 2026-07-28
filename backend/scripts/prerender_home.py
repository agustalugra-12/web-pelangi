"""Content-driven homepage prerendering (2026-07-26) - fixes a real, Lighthouse-measured
LCP problem: web-pelangi is a plain CRA SPA (no SSR), so the hero image can't paint until
the JS bundle downloads+parses+executes+React renders the DOM.

v1 (headless-browser/Playwright DOM capture after networkidle) shipped, passed every
loopback test, then caused a MEASURED LIVE REGRESSION (React hydration mismatch,
`Minified React error #418`) once actually served - root cause: capturing a browser's
DOM after networkidle reflects the page AFTER mount effects have already fired, which is
a different point in the lifecycle than what hydrateRoot compares against on a fresh
client (its own pre-effects first render). See /root/.claude/plans/buzzing-bouncing-lark.md.

v2 (this version): real SSR via `frontend/ssr/dist/render.cjs` (ReactDOMServer.
renderToString, built separately with esbuild - see frontend/ssr/build.mjs). Real SSR
never runs effects, so its output always matches a fresh client's first render by
construction - architecturally avoids the v1 failure mode entirely. `window.__PRERENDERED__`
embedded exactly as before so the client can hydrate over it instead of throwing it away
and rebuilding from scratch (see src/index.js/ContentContext.jsx/LanguageContext.jsx for
the client-side half of this - unchanged from v1).

Auto-triggered by PUT /admin/content/{type} (server.py) as a fire-and-forget subprocess
whenever an admin saves content - so uploading a new photo never needs a manual rebuild.
Can also be run by hand: `venv/bin/python -m scripts.prerender_home <pelangi|harmoni>`.

Ships Bahasa Indonesia only for v1 (confirmed with Agus 2026-07-26) - matches the site's
own default `lang="id"`. English-first-time visitors keep today's CSR behavior unchanged,
just without this LCP boost.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import httpx  # noqa: E402

FRONTEND_DIR = Path("/var/www/web-pelangi/frontend")
SSR_BIN = FRONTEND_DIR / "ssr" / "dist" / "render.cjs"
BUILD_INDEX = FRONTEND_DIR / "build" / "index.html"
NODE_BIN = "/root/.nvm/versions/node/v20.20.2/bin/node"
OUTPUT_DIR = Path("/var/www/web-pelangi/prerendered")


def _site_domains() -> dict:
    """Balikkan SITE_HOST_MAP (host->site) jadi site->host, satu sumber kebenaran yang
    sama dipakai server.py - ambil host PERTAMA yang cocok per situs (skip alias www.)."""
    raw = os.environ.get("SITE_HOST_MAP", "")
    out: dict = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        host, site = pair.split(":", 1)
        host, site = host.strip(), site.strip()
        if site not in out:
            out[site] = host
    return out


async def _fetch_content(domain: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"https://{domain}/api/content")
        r.raise_for_status()
        return r.json()


async def _render_ssr(content: dict, lang: str, origin: str) -> str:
    """Panggil bundle Node SSR (renderToString) - lihat frontend/ssr/render.jsx untuk
    shim window/localStorage minimal yang dipakai. stdin = payload, stdout = HTML."""
    stdin_payload = json.dumps({"content": content, "lang": lang, "origin": origin}).encode()
    proc = await asyncio.create_subprocess_exec(
        NODE_BIN, str(SSR_BIN),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate(stdin_payload)
    if proc.returncode != 0:
        raise RuntimeError(f"SSR render gagal (exit {proc.returncode}): {err.decode(errors='replace')[:1000]}")
    return out.decode("utf-8")


async def prerender_site(site: str, domain: str) -> None:
    content = await _fetch_content(domain)
    lang = "id"
    origin = f"https://{domain}"
    ssr_html = await _render_ssr(content, lang, origin)

    payload = json.dumps({"content": content, "lang": lang})
    # Jaga-jaga kalau ada teks CMS yang kebetulan mengandung "</script>" literal - bisa
    # menutup tag lebih awal dan merusak halaman kalau tidak di-escape.
    payload_safe = payload.replace("</script>", "<\\/script>")
    script_tag = f"<script>window.__PRERENDERED__={payload_safe}</script>"

    # Baca build/index.html SEGAR tiap kali - selalu cocok dengan build yang sedang live
    # (hash JS/CSS berubah tiap deploy), bukan template lama yang bisa basi.
    html = BUILD_INDEX.read_text(encoding="utf-8")
    html = html.replace('<div id="root"></div>', f'<div id="root">{ssr_html}</div>', 1)
    html = html.replace("<body>", f"<body>{script_tag}", 1)

    # Preload hint hero image (2026-07-26) - build/index.html HARDCODE signage.webp (foto
    # pelangi) krn dipakai bersama utk semua situs. Sejak hero photo jadi per-situs (lihat
    # _site_asset_filename di server.py, bug: upload harmoni dulu menimpa punya pelangi),
    # snapshot situs lain harus preload FILE MILIKNYA SENDIRI, bukan preload foto pelangi
    # yang tidak relevan (buang budget LCP percuma, sekaligus tidak preload yang benar).
    if site != "pelangi":
        html = html.replace(
            '<link rel="preload" as="image" href="/assets/signage.webp" fetchpriority="high"/>',
            f'<link rel="preload" as="image" href="/assets/signage-{site}.webp" fetchpriority="high"/>',
            1,
        )

    # Canonical STATIS di HTML mentah (2026-07-28, audit SEO teknis - ditemukan lewat
    # laporan user 57rb+ URL sampah ter-index GSC, salah satu penyebabnya: crawler yang
    # baca HTML mentah/belum-render-JS sama sekali tidak lihat sinyal canonical apa pun di
    # homepage, jadi variasi query string acak di "/" (mis. "/?m=123456") berisiko dianggap
    # URL terpisah. Seo.jsx SUDAH pasang canonical dinamis lewat JS utk semua halaman lain,
    # ini khusus tambahan utk homepage yang di-prerender (satu-satunya yang perlu versi
    # statis - hanya path "/" persis yang dapat perlakuan prerender ini).
    html = html.replace("</head>", f'<link rel="canonical" href="{origin}/"/></head>', 1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_path = OUTPUT_DIR / f"{site}.html"
    tmp_path = OUTPUT_DIR / f".{site}.html.tmp"
    tmp_path.write_text(html, encoding="utf-8")
    os.rename(tmp_path, final_path)  # atomic - nginx never sees a partial write
    print(f"{site}: snapshot ditulis ke {final_path} ({len(html)} bytes)")


async def main():
    if len(sys.argv) < 2:
        print("Usage: venv/bin/python -m scripts.prerender_home <site>")
        sys.exit(1)
    site = sys.argv[1]
    domains = _site_domains()
    if site not in domains:
        print(f"Situs '{site}' tidak dikenal di SITE_HOST_MAP. Pilihan: {list(domains)}")
        sys.exit(1)
    await prerender_site(site, domains[site])


if __name__ == "__main__":
    asyncio.run(main())
