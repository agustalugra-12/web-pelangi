# ARCHITECTURE_MAP — AI Blog Title Expansion

Dibuat 2026-09-02 (PRD §29, dokumen ke-2 dari 5). Alur nyata, bukan rencana.

## Alur kampanye (`expand_title_pool.py --site <situs> --target 300`)

```
CLI: --site pelangi --target 300
       │
       ▼
split_target_evenly(300, 17 cluster, demand_scores)
  → 300 // 17 = 17 base, sisa 11 dibagi ke 11 cluster demand TERTINGGI
    (reuse _cluster_demand_scores() - GSC impression riil)
       │
       ▼
untuk setiap cluster (looping 17x):
  │
  ├─ cluster_progress(site, cluster, tag)
  │    = count_documents({site, cluster, expansion_campaign: tag})
  │    (RESUME - kalau sudah 18/18 dari run sebelumnya, SKIP)
  │
  └─ while belum capai target DAN belum 3x batch kosong berturut:
       │
       ▼
     _generate_new_keywords(site, n=batch, target_cluster=cluster,
                             expansion_campaign=tag)
       │
       │  1. Fetch existing_kw (site, dgn embedding) + existing_titles
       │     (blog_posts, dgn embedding) - SEMUA existing, bukan cuma
       │     cluster ini (PRD §6 "compare with ALL existing")
       │  2. Prompt: paksa 1 cluster + kasih tahu keyword yg SUDAH ADA
       │     di cluster itu (content gap mapping, PRD §9/§10) - cari
       │     SUDUT PANDANG BARU, bukan variasi
       │  3. Parse JSON, PAKSA cluster = target_cluster di level kode
       │     (jangan percaya kepatuhan model thd instruksi prompt)
       │  4. Per kandidat:
       │     a. _validasi_intent_keyword() - regex, gratis (Level 4
       │        search-intent check, PRD §13)
       │     b. _angle_terlarang_untuk_entity_type() - cegah angle
       │        salah nempel ke entitas non-akomodasi (PRD §16)
       │     c. cosine similarity > 0.88 vs existing_embeds (Level 1-3
       │        exact/near/semantic duplicate, PRD §13) - existing_embeds
       │        BERTAMBAH tiap kandidat diterima (within-batch pairwise,
       │        PRD §13 penutup gap, baru ditambah hari ini)
       │  5. Diterima → upsert ke seo_keywords, status="belum_dibuat",
       │     expansion_campaign=tag (idempotency marker)
       ▼
     return jumlah accepted
       │
       ▼
     ulangi sampai target tercapai ATAU exhaustion (PRD §19)
       │
       ▼
GLOBAL REPORT (per cluster + total, lihat TITLE_EXPANSION_REPORT.md)
```

## Kenapa progress tracking TIDAK butuh tabel/state baru

`expansion_campaign` adalah field text nullable baru di `seo_keywords`
(migrasi implisit - MongoDB schemaless, dokumen lama otomatis tidak
punya field ini = `None`). Progress = `count_documents({cluster,
expansion_campaign: tag})`. Resume otomatis: jalankan ulang command yang
sama, cluster yang sudah capai target di-skip, sisanya lanjut dari angka
riil di DB — TIDAK ADA state file terpisah yang bisa desync dari DB asli.

## File yang TIDAK disentuh (dan kenapa)

- `generate_one()`/`write_article()` (article writer) — di luar scope,
  title expansion cuma isi POOL, tidak pernah menulis artikel.
- `get_next_keyword()` (cron auto-pick) — tetap baca `status="belum_dibuat"`
  apa adanya, tidak peduli asal keyword dari cron lama atau campaign baru.
- `generate_keyword_cluster()` (single-seed angle expansion) — TIDAK diubah,
  primitif berbeda (butuh 1 seed spesifik), campaign ini pakai
  `_generate_new_keywords` yang brainstorm bebas dari nol.
- Publishing/scheduler/CMS/frontend — nol perubahan (PRD §3).
