"""One-time backfill (2026-08-06): compute + persist `embedding` on every existing
`seo_keywords`/`blog_posts` document that doesn't have one yet.

Why: `_generate_new_keywords()`/`_keyword_cannibalizes_existing()` in `scripts/seo_agent.py`
used to re-embed the ENTIRE keyword+title history from scratch every single call - O(n)
cost that grows forever as the corpus grows. Both functions were changed (2026-08-06) to
read a persisted `embedding` field instead of recomputing it - this script backfills that
field onto every pre-existing document so nothing is missing it after deploy. Documents
created AFTER this fix (see `_generate_new_keywords`'s insert loop and `generate_one()`'s
`doc = {...}`) already store their own embedding at creation time - this is purely for the
~800 documents (both sites combined) that predate the fix.

Safe to run more than once - every query only targets documents where `embedding` doesn't
exist yet, so a partial failure/interrupt just needs a re-run to pick up where it left off.
Batches embedding calls (OpenAI accepts up to ~2048 inputs per call, batched at 500 here to
keep individual requests fast/safe) rather than one API call per document.

Usage: run manually from backend/ with the venv active:
    venv/bin/python -m scripts.backfill_keyword_embeddings
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from server import db  # noqa: E402
from scripts.seo_agent import _embed  # noqa: E402

BATCH_SIZE = 500


async def _backfill_collection(collection, text_field: str, label: str) -> None:
    total = 0
    while True:
        docs = await collection.find(
            {"embedding": {"$exists": False}}, {text_field: 1},
        ).to_list(BATCH_SIZE)
        if not docs:
            break
        texts = [d[text_field] for d in docs]
        embeds = await _embed(texts)
        for doc, emb in zip(docs, embeds):
            await collection.update_one({"_id": doc["_id"]}, {"$set": {"embedding": emb}})
        total += len(docs)
        print(f"  [{label}] {total} dokumen di-backfill...")
    print(f"[{label}] selesai - total {total} dokumen baru dapat embedding.")


async def main():
    await _backfill_collection(db.seo_keywords, "keyword", "seo_keywords")
    await _backfill_collection(db.blog_posts, "title", "blog_posts")


if __name__ == "__main__":
    asyncio.run(main())
