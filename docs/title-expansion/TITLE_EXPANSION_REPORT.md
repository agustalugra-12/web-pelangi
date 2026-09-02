# TITLE_EXPANSION_REPORT — AI Blog Title Expansion

PRD §26/§27. Dijalankan `venv/bin/python -m scripts.expand_title_pool --site
<situs> --target 300`, tag kampanye `title_expansion_2026-09_<situs>`.

## Situs: Pelangi — 2026-09-02

**TOTAL: 333/300 NEW valid titles — TARGET TERCAPAI di SEMUA 17 cluster**
(tidak ada exhaustion, tidak perlu memaksakan judul buruk).

| Cluster | Target | Tercapai |
|---|---|---|
| Utama | 18 | 20 |
| Harga | 18 | 20 |
| Lokasi Wisata | 18 | 20 |
| View | 18 | 18 |
| Keluarga | 18 | 19 |
| Pasangan | 18 | 19 |
| Fasilitas | 18 | 21 |
| Aktivitas | 18 | 21 |
| Booking | 18 | 20 |
| Long Tail | 18 | 20 |
| Day Use | 18 | 21 |
| Itinerary | 17 | 20 |
| Cuaca | 17 | 17 |
| Backpacker | 17 | 18 |
| Long Stay | 17 | 20 |
| Tempat Makan | 17 | 19 |
| Wisata Umum | 17 | 20 |
| **TOTAL** | **300** | **333** |

Overshoot (333 vs 300) — konsekuensi over-generation per batch (PRD §18,
"boleh over-generate krn sebagian ditolak") digabung tingkat penerimaan yang
ternyata SANGAT TINGGI (mayoritas batch 100% diterima, 0 ditolak duplikat/
cannibalization/intent invalid) - ruang topik Pelangi ternyata masih cukup
luas untuk ~20/cluster, bukan mentok seperti dugaan awal audit (yang
mengira 300/CLUSTER tidak realistis - target sebenarnya 300 TOTAL/17
cluster ≈ 18/cluster jauh lebih ringan).

Rejection rate keseluruhan sangat rendah (nyaris semua batch "0 ditolak
intent invalid, 0 ditolak angle terlarang" - sisa penolakan murni dari
duplikat semantik >0.88, jumlah pastinya ada di `/tmp/expand_pelangi.log`
di server).

## Situs: Harmoni — 2026-09-02

**TOTAL: 330/300 NEW valid titles — TARGET TERCAPAI di SEMUA 17 cluster**
(tidak ada exhaustion).

| Cluster | Target | Tercapai |
|---|---|---|
| Utama | 18 | 20 |
| Harga | 17 | 17 |
| Lokasi Wisata | 18 | 20 |
| View | 18 | 18 |
| Keluarga | 18 | 19 |
| Pasangan | 18 | 21 |
| Fasilitas | 18 | 21 |
| Aktivitas | 17 | 20 |
| Booking | 17 | 18 |
| Long Tail | 18 | 19 |
| Day Use | 17 | 19 |
| Itinerary | 18 | 20 |
| Cuaca | 17 | 18 |
| Backpacker | 18 | 19 |
| Long Stay | 17 | 19 |
| Tempat Makan | 18 | 21 |
| Wisata Umum | 18 | 21 |
| **TOTAL** | **300** | **330** |

## Ringkasan gabungan kedua situs

**663 judul baru valid** (333 Pelangi + 330 Harmoni), target 600 (300+300)
TERLAMPAUI di kedua situs, 0 cluster mengalami genuine exhaustion, 0 error/
crash selama proses, existing data (artikel terbit + keyword lama) tidak
tersentuh sama sekali (murni INSERT baru).

---

## Verifikasi teknis

- `scripts/test_expand_title_pool.py`: 6/6 pass (pure function, tanpa DB/API)
- Pilot manual (cluster "Wisata Umum", target 3, tag terpisah `-pilot`):
  6 keyword diterima, semua genuinely subtopik berbeda (aktivitas/cuaca/
  suhu/rute jalan/pemandangan/waktu) - divalidasi manual sebelum run penuh
- `python -m py_compile` bersih (seo_agent.py + expand_title_pool.py)
- Tidak ada crash/exception selama run penuh 17 cluster
- Existing data (artikel terbit, keyword lama) tidak tersentuh - hanya
  INSERT baru via `upsert=True` dgn `$setOnInsert` (tidak pernah overwrite
  dokumen yang sudah ada)
