"""Content-driven homepage prerendering (2026-07-26) - fixes a real, Lighthouse-measured
LCP problem: web-pelangi is a plain CRA SPA (no SSR), so the hero image can't paint until
the JS bundle downloads+parses+executes+React renders the DOM. This captures a REAL
browser render of the live homepage (via Playwright, not Node SSR - avoids "window is not
defined" entirely since the page genuinely runs in a browser during capture) and saves it
as static HTML, with `window.__PRERENDERED__` embedded so the client can hydrate over it
instead of throwing it away and rebuilding from scratch (see src/index.js/ContentContext.jsx/
LanguageContext.jsx for the client-side half of this).

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
from playwright.async_api import async_playwright  # noqa: E402

BACKEND_ORIGIN = "http://127.0.0.1:8001"
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


async def prerender_site(site: str, domain: str) -> None:
    content = await _fetch_content(domain)
    payload = json.dumps({"content": content, "lang": "id"})
    # Jaga-jaga kalau ada teks CMS yang kebetulan mengandung "</script>" literal - bisa
    # menutup tag lebih awal dan merusak halaman kalau tidak di-escape.
    payload_safe = payload.replace("</script>", "<\\/script>")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Context BARU (tanpa localStorage/cookie) - meniru pengunjung pertama kali,
        # locale id-ID supaya konsisten dengan DEFAULT_LANG di LanguageContext.jsx.
        context = await browser.new_context(locale="id-ID")
        page = await context.new_page()
        await page.goto(f"https://{domain}/", wait_until="networkidle", timeout=20000)
        html = await page.evaluate("document.documentElement.outerHTML")
        await browser.close()

    # add_init_script/page context TIDAK meninggalkan <script> literal di outerHTML -
    # harus disisipkan manual, tepat setelah <body> supaya jalan SEBELUM bundle JS
    # (yang ditaruh CRA di akhir <body>).
    script_tag = f"<script>window.__PRERENDERED__={payload_safe}</script>"
    html = html.replace("<body>", f"<body>{script_tag}", 1)

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
