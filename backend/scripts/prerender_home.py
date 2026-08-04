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
import html as html_lib
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

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


async def _fetch_blog_list(domain: str, limit: Optional[int] = None) -> list:
    # `limit` param (2026-08-03, bug nyata ditemukan Agus - beberapa artikel lama TIDAK
    # PERNAH ter-regenerasi lewat blog-detail-all/deploy.sh) - GET /api/blog default
    # limit=50 (lihat server.py list_posts), diurutkan created_at terbaru dulu. Blog
    # sekarang >100 artikel (produksi ~14/hari), jadi artikel LEBIH LAMA dari 50 artikel
    # terbaru selalu kelewat tiap kali blog-detail-all dipanggil pakai limit default -
    # snapshot-nya jadi basi PERMANEN (tidak pernah ikut deploy fix kode apa pun, mis.
    # perbaikan link Maps yang tidak bisa diklik). Caller blog-detail-all (di bawah)
    # WAJIB isi limit tinggi eksplisit - caller listing halaman "blog" TETAP tidak isi
    # (None -> pakai default backend 50), krn itu memang benar 50 artikel terbaru yang
    # dimaksud tampil ke pengunjung, bukan bug yang sama.
    params = {"limit": limit} if limit else {}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"https://{domain}/api/blog", params=params)
        r.raise_for_status()
        return r.json()


async def _fetch_blog_detail(domain: str, slug: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"https://{domain}/api/blog/{slug}")
        r.raise_for_status()
        return r.json()


# Halaman non-homepage yang didukung prerender (2026-07-28, perluas Priority 3 audit
# produksi - "Rendering ~27%" krn cuma homepage yang SSR). name -> path. Rooms/
# Facilities dipilih dulu krn konten statis murni (sama utk semua pengunjung, tidak
# ada rute dinamis per-item) - paling aman & bernilai tinggi. Blog listing juga statis
# murni (path tetap "/blog"). Blog DETAIL per-artikel ("/blog/{slug}") beda arsitektur
# sepenuhnya - lihat prerender_blog_detail(), BUKAN bagian dari dict ini krn pathnya
# dinamis per-slug, bukan 1 path tetap.
EXTRA_PAGES = {
    "rooms": "/rooms",
    "facilities": "/facilities",
    "blog": "/blog",
}


async def _render_ssr(content: dict, lang: str, origin: str, path: str = "/",
                       blog_list: list = None, blog_detail: dict = None) -> str:
    """Panggil bundle Node SSR (renderToPipeableStream + onAllReady - lihat
    frontend/ssr/render.jsx, WAJIB nunggu lazy-loaded page component selesai resolve,
    renderToString sinkron biasa tidak bisa) - shim window/localStorage minimal yang
    dipakai. stdin = payload, stdout = HTML."""
    stdin_payload = json.dumps({
        "content": content, "lang": lang, "origin": origin, "path": path,
        "blogList": blog_list, "blogDetail": blog_detail,
    }).encode()
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


def _assemble_html(ssr_html: str, content: dict, lang: str, path: str, origin: str, site: str,
                    blog_list: list = None, blog_detail: dict = None) -> str:
    """Splice hasil SSR + data prerendered ke dalam build/index.html segar - dipakai
    SEMUA jenis halaman (home/rooms/facilities/blog/blog-detail), bukan cuma ditulis
    ulang tiap fungsi. __PRERENDERED_BLOG__ selalu disuntik (None/None kalau halaman
    ini tidak butuh) - Blog.jsx/BlogDetail.jsx cuma baca field ini di halamannya
    sendiri, tidak mengganggu halaman lain."""
    payload = json.dumps({"content": content, "lang": lang})
    blog_payload = json.dumps({"list": blog_list, "detail": blog_detail})
    # Jaga-jaga kalau ada teks CMS/artikel yang kebetulan mengandung "</script>" literal
    # - bisa menutup tag lebih awal dan merusak halaman kalau tidak di-escape.
    payload_safe = payload.replace("</script>", "<\\/script>")
    blog_payload_safe = blog_payload.replace("</script>", "<\\/script>")
    script_tag = (
        f"<script>window.__PRERENDERED__={payload_safe};"
        f"window.__PRERENDERED_BLOG__={blog_payload_safe}</script>"
    )

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
    # URL terpisah. Seo.jsx SUDAH pasang canonical dinamis lewat JS utk semua halaman lain -
    # halaman yang di-prerender (statis, HTML mentah dibaca crawler sebelum JS jalan) butuh
    # versi statisnya juga, path yang benar sesuai halaman (bukan selalu "/").
    html = html.replace("</head>", f'<link rel="canonical" href="{origin}{path}"/></head>', 1)

    # Meta tag PER-ARTIKEL di snapshot statis (2026-08-04, PRD "AI Blog Engine v2.0" §7.2 -
    # bug nyata diverifikasi live: curl artikel mana pun selalu balikin <title>/<meta
    # description> DEFAULT SITUS yang sama, bukan punya artikel itu sendiri). Root cause:
    # Seo.jsx SUDAH benar set title/description per-artikel, TAPI itu client-side
    # (useEffect, jalan SETELAH JS hydrate) - crawler/social-media-scraper yang baca HTML
    # MENTAH (snapshot ini, sebelum JS jalan) selalu lihat default situs, bukan konten
    # artikel yang sebenarnya. Excerpt (`excerpt` field, sudah ada per-artikel sejak awal
    # tapi TIDAK PERNAH dirender ke sini) jadi meta description; noindex (field baru,
    # lihat BlogPostOut) inject <meta name="robots"> kalau artikel ditandai bermasalah.
    if blog_detail:
        judul = html_lib.escape((blog_detail.get("title") or "").strip())
        excerpt = html_lib.escape((blog_detail.get("excerpt") or "").strip())
        brand = html_lib.escape((content.get("site") or {}).get("brand") or "")
        if judul:
            page_title = f"{judul} — {brand}" if brand else judul
            html = re.sub(r"<title>.*?</title>", f"<title>{page_title}</title>", html, count=1, flags=re.DOTALL)
            html = re.sub(
                r'<meta property="og:title" content="[^"]*"\s*/>',
                f'<meta property="og:title" content="{page_title}"/>', html, count=1,
            )
        if excerpt:
            html = re.sub(
                r'<meta name="description" content="[^"]*"\s*/>',
                f'<meta name="description" content="{excerpt}"/>', html, count=1,
            )
            html = re.sub(
                r'<meta property="og:description" content="[^"]*"\s*/>',
                f'<meta property="og:description" content="{excerpt}"/>', html, count=1,
            )
        if blog_detail.get("noindex"):
            html = html.replace("</head>", '<meta name="robots" content="noindex,nofollow"/></head>', 1)

    return html


def _write_snapshot(html: str, out_name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_path = OUTPUT_DIR / out_name
    tmp_path = OUTPUT_DIR / f".{out_name}.tmp"
    tmp_path.write_text(html, encoding="utf-8")
    os.rename(tmp_path, final_path)  # atomic - nginx never sees a partial write
    return final_path


async def prerender_site(site: str, domain: str, page: str = "") -> None:
    """page="" -> homepage ("/", output {site}.html). page="rooms"/"facilities"/"blog"
    (lihat EXTRA_PAGES) -> path terkait, output {site}__{page}.html."""
    path = EXTRA_PAGES[page] if page else "/"
    content = await _fetch_content(domain)
    lang = "id"
    origin = f"https://{domain}"

    blog_list = await _fetch_blog_list(domain) if page == "blog" else None
    ssr_html = await _render_ssr(content, lang, origin, path, blog_list=blog_list)
    html = _assemble_html(ssr_html, content, lang, path, origin, site, blog_list=blog_list)

    out_name = f"{site}.html" if not page else f"{site}__{page}.html"
    final_path = _write_snapshot(html, out_name)
    print(f"{site} [{page or 'home'}]: snapshot ditulis ke {final_path} ({len(html)} bytes)")


async def prerender_blog_detail(site: str, domain: str, slug: str) -> None:
    """Snapshot PER-ARTIKEL ("/blog/{slug}") - beda dari prerender_site krn path & data
    dinamis per-slug, bukan 1 path tetap. Dipanggil: (a) seo_agent.py tiap kali artikel
    baru publish, (b) server.py tiap admin buat/edit artikel manual, (c) bulk utk semua
    artikel existing (lihat main() --blog-detail-all, backfill/deploy)."""
    path = f"/blog/{slug}"
    content = await _fetch_content(domain)
    lang = "id"
    origin = f"https://{domain}"
    blog_detail = await _fetch_blog_detail(domain, slug)

    ssr_html = await _render_ssr(content, lang, origin, path, blog_detail=blog_detail)
    html = _assemble_html(ssr_html, content, lang, path, origin, site, blog_detail=blog_detail)

    out_name = f"{site}__blog__{slug}.html"
    final_path = _write_snapshot(html, out_name)
    print(f"{site} [blog-detail:{slug}]: snapshot ditulis ke {final_path} ({len(html)} bytes)")


async def main():
    if len(sys.argv) < 2:
        print("Usage: venv/bin/python -m scripts.prerender_home <site> [page]")
        print(f"  page pilihan: {list(EXTRA_PAGES)} (kosong = homepage)")
        print("  venv/bin/python -m scripts.prerender_home <site> blog-detail <slug>")
        print("  venv/bin/python -m scripts.prerender_home <site> blog-detail-all")
        sys.exit(1)
    site = sys.argv[1]
    page = sys.argv[2] if len(sys.argv) > 2 else ""

    domains = _site_domains()
    if site not in domains:
        print(f"Situs '{site}' tidak dikenal di SITE_HOST_MAP. Pilihan: {list(domains)}")
        sys.exit(1)
    domain = domains[site]

    if page == "blog-detail":
        if len(sys.argv) < 4:
            print("Usage: venv/bin/python -m scripts.prerender_home <site> blog-detail <slug>")
            sys.exit(1)
        await prerender_blog_detail(site, domain, sys.argv[3])
        return

    if page == "blog-detail-all":
        # Bulk regenerate SEMUA artikel existing utk situs ini - dipakai backfill awal
        # & deploy.sh (kode baru = hash bundle baru, semua snapshot artikel jadi basi).
        # limit=1000 WAJIB eksplisit di sini (lihat catatan _fetch_blog_list) - tanpa ini
        # cuma 50 artikel TERBARU yang ke-regenerasi, artikel lebih lama snapshot-nya
        # basi permanen tiap deploy.
        posts = await _fetch_blog_list(domain, limit=1000)
        for p in posts:
            try:
                await prerender_blog_detail(site, domain, p["slug"])
            except Exception as e:
                print(f"{site} [blog-detail:{p['slug']}]: GAGAL - {type(e).__name__}: {e}")
        return

    if page and page not in EXTRA_PAGES:
        print(f"Page '{page}' tidak dikenal. Pilihan: {list(EXTRA_PAGES)}, blog-detail, blog-detail-all")
        sys.exit(1)
    await prerender_site(site, domain, page)


if __name__ == "__main__":
    asyncio.run(main())
