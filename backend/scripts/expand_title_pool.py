"""AI Blog Title Expansion (PRD "AI Blog Title Expansion, Clustering &
Anti-Cannibalization", 2026-09-02, revisi Agus: 300 judul baru dibagi RATA ke semua
cluster PER SITUS - bukan 300/cluster). REUSE PENUH mesin existing (audit lengkap ada
di ARCHITECTURE_MAP.md/REUSE_MAP.md di direktori yang sama) - orkestrasi TIPIS di atas
`_generate_new_keywords(site, n, target_cluster, expansion_campaign)` (seo_agent.py,
di-extend hari ini dgn 2 parameter baru, default None = perilaku lama 100% tidak
berubah utk caller existing di get_next_keyword()).

Idempotent/resumable (PRD §23/§24) - progress DIHITUNG dari DB (count dokumen
`expansion_campaign` ber-tag campaign ini per cluster), BUKAN state file terpisah.
Jalankan ulang kapan saja, otomatis lanjut dari yang sudah ada, tidak generate ulang
dari nol.

Jalankan:
  venv/bin/python -m scripts.expand_title_pool --site pelangi --target 300
  venv/bin/python -m scripts.expand_title_pool --site harmoni --target 300
"""
import argparse
import asyncio

from scripts.seo_agent import (
    CLUSTER_ANGLE,
    _generate_new_keywords,
    _cluster_demand_scores,
    db,
)

BATCH_SIZE = 8
# Berhenti lebih awal per cluster kalau N batch BERTURUT-TURUT 0 diterima - tanda
# genuine exhaustion (PRD §19: "247/300 lebih baik drpd paksa 53 duplikat"), bukan
# infinite-retry membakar biaya tanpa hasil.
MAX_CONSECUTIVE_EMPTY_BATCHES = 3


def campaign_tag(site: str) -> str:
    return f"title_expansion_2026-09_{site}"


async def cluster_progress(site: str, cluster: str, tag: str) -> int:
    return await db.seo_keywords.count_documents({"site": site, "cluster": cluster, "expansion_campaign": tag})


def split_target_evenly(total: int, clusters: list[str], demand_scores: dict) -> dict:
    """300 dibagi rata ke N cluster (bukan 300/cluster) - sisa pembagian (remainder)
    diberikan ke cluster ber-demand GSC tertinggi dulu (reuse _cluster_demand_scores
    existing, sinyal riil bukan tebakan) - alasan: cluster yang terbukti diminati
    audiens lebih layak dapat 1 slot ekstra drpd dibagi rata buta."""
    n = len(clusters)
    base = total // n
    remainder = total % n
    ranked = sorted(clusters, key=lambda c: demand_scores.get(c, 0), reverse=True)
    targets = {c: base for c in clusters}
    for c in ranked[:remainder]:
        targets[c] += 1
    return targets


async def expand_cluster(site: str, cluster: str, target: int, tag: str) -> dict:
    already = await cluster_progress(site, cluster, tag)
    print(f"\n--- Cluster: {cluster} | target baru: {target} | sudah ada (resume): {already} ---")
    if already >= target:
        print(f"  SKIP - target sudah tercapai sebelumnya ({already}/{target})")
        return {"cluster": cluster, "target": target, "achieved": already, "batches": 0}

    consecutive_empty = 0
    batches = 0
    while already < target and consecutive_empty < MAX_CONSECUTIVE_EMPTY_BATCHES:
        remaining = target - already
        n = min(BATCH_SIZE, remaining + 3)  # over-generate sedikit (PRD §18) - sebagian pasti ditolak
        accepted = await _generate_new_keywords(site, n=n, target_cluster=cluster, expansion_campaign=tag)
        batches += 1
        already = await cluster_progress(site, cluster, tag)
        print(f"  batch {batches}: +{accepted} diterima, progress {already}/{target}")
        if accepted == 0:
            consecutive_empty += 1
        else:
            consecutive_empty = 0

    if already < target:
        print(
            f"  TARGET NOT FULLY REACHED - {already}/{target} "
            f"(kemungkinan genuine exhaustion, {consecutive_empty} batch kosong berturut)"
        )
    else:
        print(f"  TARGET TERCAPAI - {already}/{target}")
    return {"cluster": cluster, "target": target, "achieved": already, "batches": batches}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True, choices=["pelangi", "harmoni"])
    parser.add_argument("--target", type=int, default=300)
    args = parser.parse_args()

    tag = campaign_tag(args.site)
    clusters = list(CLUSTER_ANGLE.keys())
    demand = await _cluster_demand_scores(args.site)
    targets = split_target_evenly(args.target, clusters, demand)

    print(f"=== AI BLOG TITLE EXPANSION - situs: {args.site} | target total: {args.target} | {len(clusters)} cluster ===")
    print("Pembagian per cluster:", targets)

    results = []
    for cluster in clusters:
        result = await expand_cluster(args.site, cluster, targets[cluster], tag)
        results.append(result)

    total_target = sum(r["target"] for r in results)
    total_achieved = sum(r["achieved"] for r in results)
    print(f"\n=== GLOBAL REPORT - situs: {args.site} ===")
    for r in results:
        print(f"  {r['cluster']}: {r['achieved']}/{r['target']}")
    print(f"\nTOTAL: {total_achieved}/{total_target}")
    if total_achieved < total_target:
        print(
            f"CATATAN: {total_target - total_achieved} slot tidak tercapai - genuine content-gap "
            "exhaustion di beberapa cluster (PRD §19, bukan bug)."
        )


if __name__ == "__main__":
    asyncio.run(main())
