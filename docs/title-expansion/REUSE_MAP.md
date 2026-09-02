# REUSE_MAP — AI Blog Title Expansion, Clustering & Anti-Cannibalization

Dibuat 2026-09-02 sesuai PRD §29 (audit wajib sebelum coding). Target final
(direvisi Agus): **300 judul baru per situs (Pelangi & Harmoni), dibagi rata ke
semua cluster** — bukan 300/cluster.

## Ringkasan

Hampir semua infrastruktur yang PRD minta **sudah ada dan matang** di
`backend/scripts/seo_agent.py`. Genuinely baru: 1 fungsi generation kecil
(cluster-targeted, bukan sistem baru) + 1 script orkestrasi tipis.

| Kebutuhan PRD | Status | Evidence |
|---|---|---|
| Cluster model | ✅ REUSE | `CLUSTER_CATEGORY`/`CLUSTER_ANGLE` (17 cluster/situs, sejak 2026-07-29) |
| Cluster ↔ keyword | ✅ REUSE | `seo_keywords.cluster` field |
| Existing content inventory | ✅ REUSE | `db.seo_keywords` + `db.blog_posts` |
| Primary keyword/intent/slug | ✅ REUSE | `seo_keywords.keyword/intent`, `blog_posts.slug` |
| Semantic similarity | ✅ REUSE | `_embed()`/`_cosine()`, embedding persisten sejak 2026-08-06 |
| Exact/near/semantic duplicate | ✅ REUSE | Threshold 0.88 (global, `_generate_new_keywords`) + 0.65/0.92 (cluster-scoped, `generate_keyword_cluster`) |
| Keyword cannibalization (within-site) | ✅ REUSE | `_keyword_cannibalizes_existing()` (cluster-scoped vs artikel TERBIT) |
| Cross-cluster/cross-brand cannibalization | ✅ REUSE | `_cross_brand_collision()` (Pelangi vs Harmoni) |
| Cluster assignment (bukan cuma keyword) | ✅ REUSE | `_klasifikasi_entity_type()` + `_angle_terlarang_untuk_entity_type()` |
| AI provider/prompt/structured output | ✅ REUSE | `_chat()`, JSON-mode prompt pattern sudah dipakai di semua fungsi generate |
| Batch generation | ✅ REUSE | `_generate_new_keywords(n=...)` sudah batch-based |
| Within-batch pairwise dedup | 🟡 EXTEND | Sudah ada di `generate_keyword_cluster` (Module 6 lama), **TIDAK ada** di `_generate_new_keywords` — ditambahkan hari ini (`existing_embeds.append` per-acceptance) |
| Target per-cluster terarah (bukan sebar bebas) | 🔴 BUILD NEW (kecil) | `_generate_new_keywords` tidak punya mode "1 cluster saja" — ditambah param `target_cluster` |
| Idempotency/resume tracking | 🔴 BUILD NEW (kecil) | Tidak ada state-tracking sebelumnya — direuse via field baru `expansion_campaign` di `seo_keywords` (bukan tabel/state file baru), progress dihitung dari `count_documents` |
| Orkestrasi "300 dibagi rata ke N cluster" | 🔴 BUILD NEW | Genuinely tidak ada — script baru `expand_title_pool.py`, TIPIS, murni memanggil primitif di atas berulang |

## Yang SENGAJA tidak dibangun

- **Cluster management UI baru** — AI Blog tidak punya halaman manajemen
  cluster sama sekali (dicek `CmsBlog.jsx` — tidak ada). PRD §22 bilang "kalau
  ada, extend" — karena tidak ada, dan bikin UI baru di luar scope PRD ini
  (§3 tidak sebut UI), dilewati. Progress dilaporkan via console/log +
  `TITLE_EXPANSION_REPORT.md`.
- **Entity Registry/scoring engine generik** — PRD "Entity Intelligence &
  Dynamic Topic Engine" dan "16-Agent" pernah diajukan Agus sebelumnya dan
  **sengaja ditolak** (komentar `seo_agent.py`: "sistem paralel baru,
  redundan, over-engineering utk 2 properti sendiri"). PRD title-expansion
  ini TIDAK butuh entity registry baru — `ENTITY_TYPE_MARKERS` yang sudah ada
  cukup.

## Data nyata (audit langsung ke DB, bukan tebakan)

Per 2026-09-02, situs Pelangi: 17 cluster, keyword pernah dicoba per cluster
9-104 (rata-rata ~63), artikel terbit per cluster 1-35. Situs Harmoni: juga
17 cluster (belum diaudit detail per-cluster, sama taxonomy).
