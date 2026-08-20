"""Perbandingan gpt-4.1-mini vs gemini-3.1-flash-lite utk penulisan artikel SEO.

Jalankan: `venv/bin/python -m scripts.compare_models --site pelangi --keyword "tips menginap di bedugul"`

Bandingkan:
- Kualitas artikel (word count, slop check, FAQ diversity)
- Biaya per artikel
- Waktu generate
- Quality gate pass/fail

NOTE: Script ini generate 2 artikel DARI KEYWORD YG SAMA (bukan publish) -
artikel pertama (gpt-4.1-mini) TIDAK di-publish (status "draft" lalu di-revert),
artikel kedua (gemini) juga tidak di-publish. Tujuannya CUMA perbandingan kualitas.
"""
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Load .env BEFORE importing seo_agent
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.seo_agent import (
    _chat, _slop_phrases_terdeteksi, _slop_word_counts, _extract_faqs,
    _keyword_stuffing_terdeteksi, _variasi_kalimat_kurang, _intro_template_terdeteksi,
    _fakta_berulang_terdeteksi, _faq_duplikat_terdeteksi, _faq_overused_check,
    write_article, fact_check, quality_check, editor_review,
    _fetch_site_facts, _klasifikasi_entity_type, _normalize_faq_format,
    _inject_links, pick_internal_links, _cross_brand_collision,
    _internal_links_valid, analyze_competitors, _maps_url_for_site,
    SLOP_WORDS_MAX_3X, SLOP_WORD_MAX_OK,
    db, CHAT_MODEL,
)
from scripts.seo_agent import ENTITY_TYPE_ACCOMMODATION


async def quick_quality_check(content: str, keyword: str, site: str) -> dict:
    """Run quality checks TANPA LLM (deterministic) utk perbandingan cepat."""
    results = {
        "word_count": len(content.split()),
        "slop_words": _slop_word_counts(content),
        "slop_phrases": _slop_phrases_terdeteksi(content),
        "keyword_stuffing": _keyword_stuffing_terdeteksi(content, keyword),
        "low_sentence_variety": _variasi_kalimat_kurang(content),
        "template_intro": _intro_template_terdeteksi(content),
        "repeated_facts": _fakta_berulang_terdeteksi(content),
        "faq_count": len(_extract_faqs(content)),
        "faq_overused": _faq_overused_check(_extract_faqs(content)),
    }
    # FAQ dedup via embedding (butuh API call)
    try:
        faq_issues = await _faq_duplikat_terdeteksi(site, content)
        results["faq_duplicate"] = faq_issues
    except Exception:
        results["faq_duplicate"] = ["gagal cek"]

    return results


async def compare_one_keyword(site: str, keyword: str) -> dict:
    """Generate 1 artikel dgn 2 model, bandingkan."""
    print(f"\n{'='*60}")
    print(f"KEYWORD: {keyword}")
    print(f"SITE: {site}")
    print(f"{'='*60}\n")

    # Shared context
    facts = await _fetch_site_facts(site)
    keyword_doc = {
        "keyword": keyword,
        "cluster": "General",
        "cluster_group_id": None,
        "intent": "Informational",
    }

    links = await pick_internal_links(site, "General", keyword=keyword)
    sibling = await _cross_brand_collision(site, keyword, "General")
    competitor_result = await analyze_competitors(keyword, site=site)
    maps_url = await _maps_url_for_site(site)

    results = {}

    for model_name in [CHAT_MODEL, "gemini-3.1-flash-lite"]:
        print(f"\n--- Generating with {model_name} ---")
        start = time.time()
        try:
            article = await write_article(
                site, keyword_doc,
                link_candidates=links,
                sibling_collision=sibling,
                model=model_name,
            )
            article["content"] = _normalize_faq_format(article["content"])
            content_final = _inject_links(article["content"], links, f"https://wa.me/6285119459269?text=Halo", maps_url)

            elapsed = time.time() - start

            # Quality check (deterministic)
            qc = await quick_quality_check(content_final, keyword, site)

            # Fact-check (butuh LLM call)
            fact_issues = []
            try:
                fact_issues, unverified = await fact_check(site, content_final)
            except Exception as e:
                fact_issues = [f"fact-check error: {e}"]

            results[model_name] = {
                "title": article.get("title", ""),
                "word_count": qc["word_count"],
                "elapsed_seconds": round(elapsed, 1),
                "quality": qc,
                "fact_issues": fact_issues,
                "content_preview": content_final[:500] + "...",
            }

            print(f"  Title: {article.get('title', 'N/A')}")
            print(f"  Words: {qc['word_count']}")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Slop: {qc['slop_phrases']}")
            print(f"  FAQ count: {qc['faq_count']}")
            print(f"  FAQ overused: {qc['faq_overused']}")
            print(f"  FAQ duplicate: {qc['faq_duplicate']}")
            print(f"  Fact issues: {fact_issues}")
            print(f"  Template intro: {qc['template_intro']}")

        except Exception as e:
            elapsed = time.time() - start
            results[model_name] = {
                "error": str(e),
                "elapsed_seconds": round(elapsed, 1),
            }
            print(f"  ERROR: {e}")

    return results


async def main():
    ap = argparse.ArgumentParser(description="Compare gpt-4.1-mini vs gemini-3.1-flash-lite")
    ap.add_argument("--site", required=True, choices=["pelangi", "harmoni"])
    ap.add_argument("--keyword", required=True, help="Keyword untuk diuji")
    args = ap.parse_args()

    results = await compare_one_keyword(args.site, args.keyword)

    # Summary
    print(f"\n{'='*60}")
    print("RINGKASAN PERBANDINGAN")
    print(f"{'='*60}")

    for model, data in results.items():
        if "error" in data:
            print(f"\n{model}: ERROR - {data['error']}")
            continue
        print(f"\n{model}:")
        print(f"  Judul: {data['title']}")
        print(f"  Kata: {data['word_count']}")
        print(f"  Waktu: {data['elapsed_seconds']}s")
        print(f"  Slop words: {data['quality']['slop_words']}")
        print(f"  Slop phrases: {len(data['quality']['slop_phrases'])} issues")
        print(f"  FAQ: {data['quality']['faq_count']} total, {len(data['quality']['faq_overused'])} overused, {len(data['quality']['faq_duplicate'])} duplikat")
        print(f"  Fact-check: {len(data['fact_issues'])} issues")
        print(f"  Template intro: {data['quality']['template_intro']}")

    # Cost estimate
    print(f"\n--- Estimasi Biaya ---")
    gpt = results.get(CHAT_MODEL, {})
    gem = results.get("gemini-3.1-flash-lite", {})
    if "word_count" in gpt and "word_count" in gem:
        # Rough estimate: ~1.3x word count = completion tokens, ~6x = prompt tokens
        gpt_pt = gpt["word_count"] * 6
        gpt_ct = gpt["word_count"] * 1.3
        gem_pt = gem["word_count"] * 6
        gem_ct = gem["word_count"] * 1.3
        gpt_cost = (gpt_pt / 1_000_000) * 0.40 + (gpt_ct / 1_000_000) * 1.60
        gem_cost = (gem_pt / 1_000_000) * 0.075 + (gem_ct / 1_000_000) * 0.30
        print(f"  {CHAT_MODEL}: ~${gpt_cost:.4f} (estimasi)")
        print(f"  gemini-3.1-flash-lite: ~${gem_cost:.4f} (estimasi)")
        print(f"  Selisih: {CHAT_MODEL} {gpt_cost/gem_cost:.1f}x lebih mahal" if gem_cost > 0 else "")


if __name__ == "__main__":
    asyncio.run(main())
