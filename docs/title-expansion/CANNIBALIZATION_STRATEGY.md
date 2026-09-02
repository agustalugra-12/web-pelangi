# CANNIBALIZATION_STRATEGY — AI Blog Title Expansion

Dibuat 2026-09-02 (PRD §29, dokumen ke-4 dari 5).

## 4 level anti-duplicate (PRD §13) → mekanisme nyata

| Level | PRD | Mekanisme | Threshold |
|---|---|---|---|
| 1. Exact | Judul identik | `db.seo_keywords.update_one({site, keyword: cand}, ..., upsert=True)` — MongoDB unique-by-value alami, keyword identik tidak pernah dobel-insert | exact string match |
| 2. Near duplicate | Beda beberapa kata | Cosine similarity embedding | > 0.88 (global) |
| 3. Semantic duplicate | Beda kalimat, substansi sama | Cosine similarity embedding (SAMA mekanisme dgn Level 2 — dalam praktik keduanya diukur 1 angka similarity, tidak ada garis tegas "near" vs "semantic", threshold 0.88 menutup keduanya sekaligus) | > 0.88 |
| 4. Search intent duplicate | Keyword beda, jawaban sama | `_validasi_intent_keyword()` (regex/dict) + `intent` classification (Informational/Commercial/Transactional) — kandidat dgn intent tidak konsisten/tidak valid ditolak sebelum masuk pool | rule-based, bukan similarity |

## Cannibalization (beda dari sekadar duplicate — PRD §14/§15)

**Within-cluster** (`_keyword_cannibalizes_existing`, sudah ada sejak revisi
ke-3 empiris): dibandingkan HANYA ke keyword di CLUSTER YANG SAMA yang
SUDAH JADI ARTIKEL TERBIT (bukan ke seluruh pool "belum_dibuat") — cluster
memang didesain sebagai sinyal "angle berbeda", jadi 2 keyword beda cluster
boleh terdengar mirip (itu tujuannya).

**Cross-cluster** (PRD §15): TIDAK ADA pengecekan literal "band pisah cluster
X vs Y" yang eksplisit di campaign ini — mitigasi TIDAK LANGSUNG via:
1. `target_cluster` memaksa 1 cluster per panggilan generation, jadi model
   tidak pernah diminta membuat 2 keyword lintas-cluster dalam 1 prompt yang
   bisa saling tumpang tindih secara sengaja.
2. Global embedding dedup (0.88, lintas SEMUA keyword+judul site, tidak
   dibatasi cluster) tetap menangkap kasus keyword di cluster BERBEDA yang
   ternyata semantically identik (mis. "cottage bedugul untuk keluarga"
   cluster Keluarga vs "penginapan bedugul cocok keluarga" cluster Aktivitas)
   — akan ke-block di similarity check meski cluster-nya beda.

**Keterbatasan yang diterima sadar**: PRD §15 contoh spesifik (2 cluster BEDA
membahas topik yang secara INTENT sama tapi kalimatnya cukup beda utk lolos
threshold 0.88) tidak 100% tertangkap oleh mekanisme di atas — ini
keterbatasan yang SUDAH ADA di sistem lama juga (bukan regresi baru dari
campaign ini), dan memperbaikinya butuh classifier intent-matching lintas
cluster yang lebih mahal (panggilan LLM tambahan per pasangan kandidat) -
di luar scope PRD §28 "jangan refactor besar yang tidak diperlukan".
Mitigasi realistis: audit manual berkala oleh Agus di laporan
TITLE_EXPANSION_REPORT.md, bukan otomatisasi penuh.

**Cross-brand** (Pelangi ⟷ Harmoni): `_cross_brand_collision()` sudah ada
(threshold sama, cluster-scoped) — dipakai jalur `generate_keyword_cluster`,
BELUM diintegrasikan ke `_generate_new_keywords`/campaign ini. Risiko rendah
karena kedua situs punya karakter cukup beda (Pelangi budget vs Harmoni
villa) dan cluster-nya sendiri-sendiri secara data, tapi dicatat sbg
keterbatasan yang sama, bukan disembunyikan.

## Re-run & idempotency (PRD §23/§24)

`expansion_campaign` tag unik per situs (`title_expansion_2026-09_<site>`).
Re-run apa pun menghitung ulang progress dari DB — keyword yang sudah
tersimpan (dgn tag ini) TIDAK PERNAH digenerate ulang karena mereka otomatis
masuk `existing_kw`/`existing_embeds` di setiap panggilan berikutnya
(pool bertambah monotonic, bukan direset).
