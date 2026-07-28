"""Impression-based Article Expansion Agent (2026-07-28) - jawaban konkret utk pertanyaan
user "AI memperluas artikel yang mulai mendapat impresi": artikel yang TERBUKTI dapat
pencarian nyata dari Google (impression GSC, bukan tebakan/asumsi) diperdalam kontennya
(tambah 1 sub-judul baru + perpanjang sub-judul lama yang masih ringkas), BUKAN ditulis
ulang dari nol - struktur/FAQ/link internal yang sudah ada dipertahankan apa adanya.

Dipisah dari seo_agent.py (bukan digabung) krn siklusnya beda total: seo_agent nulis
artikel BARU 7x/hari/situs, ini menulis ULANG artikel LAMA yang datanya baru muncul
stlh GSC sync (lag ~2-3 hari) - jalan mingguan sudah lebih dari cukup (lihat
scripts/run_expand_top_articles.sh + crontab).

Kriteria kandidat (per situs):
- published=True, URL-nya (https://{domain}/blog/{slug}) tercatat di db.gsc_page_stats
  dgn impressions >= IMPRESSION_THRESHOLD dlm 28 hari terakhir (ambang RENDAH sengaja -
  situs masih baru saat fitur ini dibuat, akan dinaikkan manual nanti kalau trafik naik)
- belum pernah di-expand ATAU sudah lewat COOLDOWN_DAYS sejak expand terakhir (supaya
  tidak diperpanjang berulang-ulang tanpa henti tiap minggu - panjang artikel akan
  membengkak tak terkendali kalau tidak dibatasi)
- maks 3 artikel/situs/run (biaya API + supaya tidak rewrite massal sekaligus)

Jalankan manual: `venv/bin/python -m scripts.expand_top_articles --site all`
"""
import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.seo_agent import (  # noqa: E402
    db, SITE_DOMAIN, _chat, _parse_json_response, _fetch_site_facts, quality_check, fact_check,
)
from scripts import prerender_home as _prerender  # noqa: E402

IMPRESSION_THRESHOLD = 20
COOLDOWN_DAYS = 30
MAX_PER_RUN = 3


async def _find_candidates(site: str) -> list:
    domain = SITE_DOMAIN[site]
    posts = await db.blog_posts.find(
        {"site": site, "published": True},
        {"slug": 1, "title": 1, "excerpt": 1, "content": 1, "expanded_at": 1},
    ).to_list(500)
    if not posts:
        return []
    url_to_post = {f"https://{domain}/blog/{p['slug']}": p for p in posts}
    stats = await db.gsc_page_stats.find(
        {"site": site, "url": {"$in": list(url_to_post.keys())}, "impressions": {"$gte": IMPRESSION_THRESHOLD}},
        {"url": 1, "impressions": 1},
    ).to_list(500)

    now = datetime.now(timezone.utc)
    candidates = []
    for row in stats:
        post = url_to_post.get(row["url"])
        if not post:
            continue
        expanded_at = post.get("expanded_at")
        if expanded_at and (now - datetime.fromisoformat(expanded_at)) < timedelta(days=COOLDOWN_DAYS):
            continue
        candidates.append({"post": post, "impressions": row["impressions"]})
    candidates.sort(key=lambda c: -c["impressions"])
    return candidates[:MAX_PER_RUN]


async def _expand_article(site: str, post: dict) -> dict:
    facts = await _fetch_site_facts(site)
    system = (
        "Kamu editor konten profesional Bahasa Indonesia untuk penginapan di Bedugul, "
        "Bali. Tugasmu memperdalam (BUKAN menulis ulang dari nol) artikel yang SUDAH "
        "TERBUKTI mendapat pencarian nyata di Google (impression GSC) - topik ini terbukti "
        "diminati, jadi layak dibuat lebih lengkap & otoritatif. JANGAN mengarang fakta "
        "baru (harga/fasilitas/lokasi) di luar DATA ASLI yang diberikan - kalau perlu "
        "detail yang tidak tersedia di data, tulis jujur secara umum, jangan angka pasti "
        "yang belum tentu benar."
    )
    user = f"""DATA ASLI ({site}):
{facts}

ARTIKEL YANG SUDAH TERBIT (mendapat impression GSC riil, layak diperdalam):
{post['content']}

Perdalam artikel ini:
- Pertahankan SEMUA sub-judul, FAQ, dan link markdown yang sudah ada PERSIS apa adanya
  (termasuk teks link "Baca juga"/WhatsApp kalau ada - JANGAN dihapus/diubah path-nya).
- Tambah SATU sub-judul **Sub Judul** baru yang relevan (topik terkait keyword utama
  artikel ini yang belum dibahas), isi 120-180 kata, disisipkan SEBELUM bagian FAQ.
- Perpanjang 1-2 sub-judul yang sudah ada dengan detail/contoh lebih konkret dari DATA
  ASLI kalau memang masih ringkas (di bawah ~150 kata).
- Total artikel akhir 1300-1700 kata. Paragraf dipisah \\n\\n. Judul & excerpt boleh
  tetap sama kalau masih akurat.

Balas HARUS JSON valid (tanpa markdown code fence): {{"title": "...", "excerpt": "...", "content": "..."}}"""

    raw = await _chat(system, user, temperature=0.6)
    return _parse_json_response(raw)


async def run(site: str) -> None:
    candidates = await _find_candidates(site)
    if not candidates:
        print(f"[{site}] tidak ada kandidat expand (impression >= {IMPRESSION_THRESHOLD}, cooldown {COOLDOWN_DAYS} hari)")
        return
    domain = SITE_DOMAIN[site]
    for c in candidates:
        post = c["post"]
        old_count = len(post["content"].split())
        try:
            expanded = await _expand_article(site, post)
        except Exception as e:
            print(f"[{site}] GAGAL expand {post['slug']}: {type(e).__name__}: {e}")
            continue

        new_count = len(expanded.get("content", "").split())
        problems = quality_check(expanded, expanded.get("content", ""))
        fact_issues = await fact_check(site, expanded.get("content", ""))
        if fact_issues:
            problems.append("fact-check: " + "; ".join(fact_issues))
        if problems:
            print(f"[{site}] skip {post['slug']}: hasil expand gagal quality/fact check ({problems})")
            continue
        if new_count <= old_count:
            print(f"[{site}] skip {post['slug']}: hasil expand tidak lebih panjang ({new_count} vs {old_count} kata)")
            continue

        now = datetime.now(timezone.utc).isoformat()
        await db.blog_posts.update_one(
            {"slug": post["slug"], "site": site},
            {"$set": {
                "content": expanded["content"],
                "excerpt": expanded.get("excerpt", post.get("excerpt")),
                "expanded_at": now, "updated_at": now,
            }},
        )
        try:
            await _prerender.prerender_site(site, domain, "blog")
            await _prerender.prerender_blog_detail(site, domain, post["slug"])
        except Exception as e:
            print(f"[{site}] prerender gagal utk {post['slug']}: {type(e).__name__}: {e}")
        print(f"[{site}] expanded {post['slug']}: {old_count} -> {new_count} kata (impression {c['impressions']})")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, choices=["pelangi", "harmoni", "all"])
    args = ap.parse_args()
    sites = ["pelangi", "harmoni"] if args.site == "all" else [args.site]

    # try/except per situs (konsisten dgn seo_agent.py/gsc_sync.py) - gagal di satu situs
    # tidak menghalangi situs lain.
    for site in sites:
        try:
            await run(site)
        except Exception as e:
            print(f"[{site}] GAGAL total: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
