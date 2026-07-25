"""One-time seed (2026-07-25): minimal, structurally-valid `site_content` docs for the
NEW second property "harmoni" (site="harmoni") - separate from `seed_content.py`'s
Pelangi auto-seed so it's never accidentally re-triggered on startup.

Deliberately does NOT invent marketing copy (no lorem ipsum, no made-up descriptions/
testimonials/FAQs/photos). Only fields independently confirmed true (from the live PMS
`properties`/`rooms-catalog` data for the "harmoni" property, checked 2026-07-25) are
filled in; everything else is left blank/empty so the owner fills it in via the real
admin CMS (/admin) afterward. Idempotent - safe to re-run, only inserts docs that don't
already exist for site="harmoni".

Usage: run manually from backend/ with the venv active:
    venv/bin/python -m scripts.seed_harmoni_content
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from server import db  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

SITE = "harmoni"

# Hanya fakta yang sudah dikonfirmasi nyata (dari data PMS live untuk properti "harmoni",
# dicek 2026-07-25 lewat /api/public/rooms-catalog?properti=harmoni) - BUKAN karangan.
DOCS = {
    "site": {
        "brand": "harmoni",
        "address": "jalan denpasar - singaraja",
        # Field lain (tagline, whatsapp, email, hours, bookingUrl, hero/promo copy, seo)
        # SENGAJA dikosongkan - belum ada info nyata, isi lewat /admin/settings.
        "tagline": "", "whatsappDisplay": "", "whatsapp": "", "email": "", "hours": "",
        "bookingUrl": "", "mapEmbed": "",
        "restaurantIntro": "", "restaurantHours": "",
        "heroEyebrow": "", "heroTitle": "", "heroSubtitle": "", "heroBody": "",
        "promoEyebrow": "", "promoTitle": "", "promoBody": "",
        "seoTitle": "", "seoDescription": "",
    },
    "rooms": [
        {
            "id": "cottage",
            "slug": "cottage",
            "name": "Cottage",
            "capacity": "2 Dewasa + 1 Anak",
            "size": "5 x 3,5 m",
            "priceFrom": "IDR 145.000",
            "image": "",
            "gallery": [],
            "facilities": ["AC", "Wi-Fi gratis", "TV LED", "Kamar mandi dalam", "Air panas", "Handuk & toiletries", "Cottage Style", "Area Outdoor"],
            "description": "",
        }
    ],
    "menu": [],
    "gallery": [],
    "attractions": [],
    "faqs": [],
    "testimonials": [],
}


async def main():
    now = datetime.now(timezone.utc).isoformat()
    for content_type, data in DOCS.items():
        existing = await db.site_content.find_one({"site": SITE, "type": content_type})
        if existing:
            print(f"{content_type}: sudah ada untuk site={SITE}, dilewati")
            continue
        await db.site_content.insert_one({
            "site": SITE, "type": content_type, "data": data, "updated_at": now,
        })
        print(f"{content_type}: dibuat untuk site={SITE}")

    print("\nSelesai. Isi konten asli (foto, deskripsi, kontak, dst) lewat /admin "
          "setelah login, pilih situs 'harmoni' di site switcher.")


if __name__ == "__main__":
    asyncio.run(main())
