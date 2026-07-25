"""One-time migration (2026-07-25): backfill `site`/`type` onto every pre-existing
`site_content` document (previously keyed only by `_id` = type name, no multi-site
concept at all), plus a `site` field on `blog_posts`/`contact_messages` so nothing
downstream ever has to assume the field exists. Mirrors the exact idempotent pattern
used in Pelangi PMS's `scripts/migrate_multi_property.py`.

Safe to run more than once — every step only touches documents that don't already have
the target field set, so re-running after a partial failure just picks up where it left
off. `_id` is left untouched on existing docs (now vestigial, no longer the lookup key)
to avoid a risky delete+reinsert of the primary key.

Usage: run manually from backend/ with the venv active:
    venv/bin/python -m scripts.migrate_site_scoping
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from server import db  # noqa: E402

DEFAULT_SITE = "pelangi"


async def main():
    # site_content: _id currently IS the type name (e.g. "rooms") - backfill both
    # `type` (copy of _id) and `site` (default "pelangi") per doc, since Mongo can't
    # $set a field FROM _id in a single update_many without aggregation-pipeline
    # update syntax - loop per-doc instead, same idempotent spirit.
    n_updated = 0
    async for doc in db.site_content.find({"$or": [{"site": {"$exists": False}}, {"type": {"$exists": False}}]}):
        await db.site_content.update_one(
            {"_id": doc["_id"]},
            {"$set": {"site": doc.get("site", DEFAULT_SITE), "type": doc.get("type", doc["_id"])}},
        )
        n_updated += 1
    remaining = await db.site_content.count_documents({"$or": [{"site": {"$exists": False}}, {"type": {"$exists": False}}]})
    print(f"site_content: {n_updated} dokumen di-set site/type, sisa tanpa field: {remaining}")

    await db.site_content.create_index([("site", 1), ("type", 1)], unique=True)
    print("site_content: index (site,type) unique dibuat/sudah ada")

    for coll_name in ("blog_posts", "contact_messages"):
        coll = db[coll_name]
        result = await coll.update_many(
            {"site": {"$exists": False}},
            {"$set": {"site": DEFAULT_SITE}},
        )
        remaining = await coll.count_documents({"site": {"$exists": False}})
        print(f"{coll_name}: {result.modified_count} dokumen di-set site, sisa tanpa site: {remaining}")

    print("\nSelesai. Verifikasi manual: pastikan semua baris di atas 'sisa tanpa ...: 0'.")


if __name__ == "__main__":
    asyncio.run(main())
