# CHANGE_MAP — AI Blog Title Expansion

Dibuat 2026-09-02 (PRD §29, dokumen ke-3 dari 5). Diff nyata.

## File diubah

### `backend/scripts/seo_agent.py`

1. `existing_kw` query (`_generate_new_keywords`) — tambah `"cluster": 1` ke
   projection (sebelumnya cuma `keyword`/`embedding`). Perlu untuk content-gap
   mapping per cluster. **0 perubahan perilaku lain** — field tambahan di hasil
   query, tidak dipakai di jalur lama.
2. `_generate_new_keywords(site, n=10)` → `_generate_new_keywords(site, n=10,
   target_cluster=None, expansion_campaign=None)`:
   - Prompt: kalau `target_cluster` diisi, paksa SEMUA kandidat ke 1 cluster
     itu + kasih daftar keyword existing di cluster itu (content gap). Kalau
     `None` (default), teks prompt PERSIS SAMA seperti sebelumnya.
   - Parsing kandidat: `target_cluster if target_cluster else (cluster dari
     model / fallback "Long Tail")` — override level-kode, bukan cuma prompt.
   - Dedup loop: `existing_embeds.append(cand_emb)` setelah diterima (within-
     batch pairwise dedup, sebelumnya tidak ada di fungsi ini).
   - Insert: tambah field `expansion_campaign` HANYA kalau param diisi
     (dict spread kondisional, dokumen lama/caller lama tidak dapat field ini
     sama sekali, bukan `None` eksplisit — MongoDB schemaless, aman).
   - Return: `None` → `int` (jumlah accepted). Satu-satunya caller lama
     (`get_next_keyword()`, line ~1129) mengabaikan return value — non-breaking.

**Baris yang TIDAK diubah**: seluruh logic intent validation, angle-entity
gate, embedding computation, `_chat()` call — 100% sama.

### `backend/scripts/expand_title_pool.py` (baru)

Orkestrasi: `split_target_evenly()`, `campaign_tag()`, `cluster_progress()`,
`expand_cluster()`, `main()` (CLI `--site`/`--target`). ~115 baris, tidak ada
logic generation/dedup baru di sini — semua delegasi ke `_generate_new_keywords`.

### `backend/scripts/test_expand_title_pool.py` (baru)

6 test pure-function (tanpa DB/API) untuk `split_target_evenly`/`campaign_tag`.

## Tidak ada file lain yang diubah

Tidak ada perubahan ke: `server.py`, model artikel/CMS, frontend, publishing,
scheduler, brand/situs lain (kode ini generik site-parametrized, dipakai
Pelangi DAN Harmoni tanpa percabangan khusus brand).

## Statistik

- 1 file diubah (`seo_agent.py`): ~20 baris berubah/ditambah dari total
  4400+ baris file.
- 2 file baru (~150 baris total).
- 0 baris dihapus dari logic existing.
- 0 field/kolom existing di-overwrite semantiknya.
