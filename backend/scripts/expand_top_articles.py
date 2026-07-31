"""Impression-based Article Expansion Agent (2026-07-28) - jawaban konkret utk pertanyaan
user "AI memperluas artikel yang mulai mendapat impresi": artikel yang TERBUKTI dapat
pencarian nyata dari Google (impression GSC, bukan tebakan/asumsi) diperdalam kontennya
(tambah 1 sub-judul baru + perpanjang sub-judul lama yang masih ringkas), BUKAN ditulis
ulang dari nol - struktur/FAQ/link internal yang sudah ada dipertahankan apa adanya.

Dipisah dari seo_agent.py (bukan digabung) krn siklusnya beda total: seo_agent nulis
artikel BARU 7x/hari/situs, ini menulis ULANG artikel LAMA yang datanya baru muncul
stlh GSC sync (lag ~2-3 hari) - jalan mingguan sudah lebih dari cukup (lihat
scripts/run_expand_top_articles.sh + crontab).

Kriteria kandidat (per situs), 2 alasan terpisah (2026-07-29, permintaan user - tampilkan
jumlah kata tiap artikel + alert kalau di bawah 1000 kata, perbaharui ke 1100-1200):
1. "impresi_tinggi" (asli) - URL-nya (https://{domain}/blog/{slug}) tercatat di
   db.gsc_page_stats dgn impressions >= IMPRESSION_THRESHOLD dlm 28 hari terakhir (ambang
   RENDAH sengaja - situs masih baru saat fitur ini dibuat) - target 1300-1700 kata.
2. "kurang_1000_kata" (baru) - artikel di bawah 1000 kata TANPA syarat impresi - ini
   kegagalan kualitas nyata (audit 2026-07-28 nemu artikel lama yang lolos di bawah
   ambang lama 850 kata sebelum quality_check() dinaikkan ke 1000) - target 1100-1200 kata.

Keduanya: belum pernah di-expand ATAU sudah lewat COOLDOWN_DAYS sejak expand terakhir,
maks MAX_PER_RUN artikel/situs/run RUTIN mingguan (biaya API + supaya tidak rewrite
massal sekaligus) - override via --limit utk backfill sekali jalan bersihkan backlog.

Jalankan manual: `venv/bin/python -m scripts.expand_top_articles --site all`
Backfill sekali jalan (limit lebih besar): `... --site all --limit 20`
"""
import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.seo_agent import (  # noqa: E402
    db, SITE_DOMAIN, _chat, _parse_json_response, _fetch_site_facts, quality_check, fact_check,
    _normalize_faq_format,
)
from scripts import prerender_home as _prerender  # noqa: E402

IMPRESSION_THRESHOLD = 20
COOLDOWN_DAYS = 30
MAX_PER_RUN = 3
MIN_WORD_COUNT = 1000


async def _find_candidates(site: str, limit: int) -> list:
    domain = SITE_DOMAIN[site]
    # seo_keyword != None (2026-07-29, bug nyata ditemukan sebelum sempat jalan ke
    # produksi): tanpa filter ini, artikel MANUAL (mis. blurb tips 45 kata yang memang
    # sengaja pendek, ditulis staf sebelum AI SEO Agent ada, seo_keyword=None) ikut
    # kena "expand" jadi 1100-1200 kata AI - salah total, itu bukan kegagalan kualitas,
    # itu memang gaya kontennya sengaja singkat. Fitur "kurang dari 1000 kata" HANYA
    # utk artikel yang DITULIS AI SEO Agent (selalu punya seo_keyword).
    posts = await db.blog_posts.find(
        {"site": site, "published": True, "seo_keyword": {"$ne": None}},
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

    def _cooldown_ok(post: dict) -> bool:
        expanded_at = post.get("expanded_at")
        return not (expanded_at and (now - datetime.fromisoformat(expanded_at)) < timedelta(days=COOLDOWN_DAYS))

    # Prioritas 1: kurang dari 1000 kata (kegagalan kualitas nyata, bukan "kesempatan
    # tumbuh" spt impresi - lihat catatan di atas) - dicek DULUAN & lolos limit sendiri
    # dari impresi, supaya backlog kualitas tidak kalah saing sama artikel impresi tinggi.
    kurang_kata = [
        {"post": p, "reason": "kurang_1000_kata", "word_count": len(p["content"].split())}
        for p in posts
        if len(p["content"].split()) < MIN_WORD_COUNT and _cooldown_ok(p)
    ]
    kurang_kata.sort(key=lambda c: c["word_count"])  # yang paling pendek duluan

    slugs_terpakai = {c["post"]["slug"] for c in kurang_kata}
    impresi_tinggi = []
    for row in stats:
        post = url_to_post.get(row["url"])
        if not post or post["slug"] in slugs_terpakai or not _cooldown_ok(post):
            continue
        impresi_tinggi.append({"post": post, "reason": "impresi_tinggi", "impressions": row["impressions"]})
    impresi_tinggi.sort(key=lambda c: -c["impressions"])

    return (kurang_kata + impresi_tinggi)[:limit]


async def _expand_article(site: str, post: dict, reason: str) -> dict:
    facts = await _fetch_site_facts(site)
    if reason == "kurang_1000_kata":
        alasan_line = (
            "Artikel ini MASIH DI BAWAH 1000 KATA (standar kualitas minimum kita) - "
            "bukan soal populer/tidaknya, ini kegagalan kualitas yang harus diperbaiki."
        )
        target_line = "Total artikel akhir 1100-1200 kata (JANGAN kurang dari 1100, JANGAN lebih dari 1200)."
    else:
        alasan_line = (
            "Artikel ini SUDAH TERBUKTI mendapat pencarian nyata di Google (impression GSC) - "
            "topik ini terbukti diminati, jadi layak dibuat lebih lengkap & otoritatif."
        )
        target_line = "Total artikel akhir 1300-1700 kata."
    system = (
        "Kamu editor konten profesional Bahasa Indonesia untuk penginapan di Bedugul, "
        "Bali. Tugasmu memperdalam (BUKAN menulis ulang dari nol) artikel yang sudah "
        f"terbit. {alasan_line} JANGAN mengarang fakta baru (harga/fasilitas/lokasi) di "
        "luar DATA ASLI yang diberikan - kalau perlu detail yang tidak tersedia di data, "
        "tulis jujur secara umum, jangan angka pasti yang belum tentu benar."
    )
    user = f"""DATA ASLI ({site}):
{facts}

ARTIKEL YANG SUDAH TERBIT (perlu diperdalam):
{post['content']}

Perdalam artikel ini:
- Pertahankan SEMUA sub-judul, FAQ, dan link markdown yang sudah ada PERSIS apa adanya
  (termasuk teks link "Baca juga"/WhatsApp kalau ada - JANGAN dihapus/diubah path-nya).
- Tambah SATU sub-judul **Sub Judul** baru yang relevan (topik terkait keyword utama
  artikel ini yang belum dibahas), isi 120-180 kata, disisipkan SEBELUM bagian FAQ.
- Perpanjang 1-2 sub-judul yang sudah ada dengan detail/contoh lebih konkret dari DATA
  ASLI kalau memang masih ringkas (di bawah ~150 kata).
- {target_line} Paragraf dipisah \\n\\n. Judul & excerpt boleh tetap sama kalau masih akurat.
- Hitung sendiri jumlah kata draftmu SEBELUM menjawab - kalau belum masuk target,
  perpanjang lagi dulu sebelum dikirim.

Balas HARUS JSON valid (tanpa markdown code fence): {{"title": "...", "excerpt": "...", "content": "..."}}"""

    raw = await _chat(system, user, temperature=0.6)
    return _parse_json_response(raw)


async def run(site: str, limit: int = MAX_PER_RUN) -> None:
    candidates = await _find_candidates(site, limit)
    if not candidates:
        print(f"[{site}] tidak ada kandidat expand (< {MIN_WORD_COUNT} kata / impression >= {IMPRESSION_THRESHOLD}, cooldown {COOLDOWN_DAYS} hari)")
        return
    domain = SITE_DOMAIN[site]
    for c in candidates:
        post = c["post"]
        reason = c["reason"]
        old_count = len(post["content"].split())
        try:
            expanded = await _expand_article(site, post, reason)
        except Exception as e:
            print(f"[{site}] GAGAL expand {post['slug']}: {type(e).__name__}: {e}")
            continue

        if expanded.get("content"):
            expanded["content"] = _normalize_faq_format(expanded["content"])
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
        label = f"kurang dari {MIN_WORD_COUNT} kata" if reason == "kurang_1000_kata" else f"impression {c.get('impressions')}"
        print(f"[{site}] expanded {post['slug']}: {old_count} -> {new_count} kata ({label})")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, choices=["pelangi", "harmoni", "all"])
    ap.add_argument("--limit", type=int, default=MAX_PER_RUN, help="Override limit/situs (dipakai utk backfill sekali jalan)")
    args = ap.parse_args()
    sites = ["pelangi", "harmoni"] if args.site == "all" else [args.site]

    # try/except per situs (konsisten dgn seo_agent.py/gsc_sync.py) - gagal di satu situs
    # tidak menghalangi situs lain.
    for site in sites:
        try:
            await run(site, limit=args.limit)
        except Exception as e:
            print(f"[{site}] GAGAL total: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
