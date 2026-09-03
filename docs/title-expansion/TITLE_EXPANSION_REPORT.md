# TITLE_EXPANSION_REPORT — AI Blog Title Expansion

PRD §26/§27. Dijalankan `venv/bin/python -m scripts.expand_title_pool --site
<situs> --target 300`, tag kampanye `title_expansion_2026-09_<situs>`.

## Situs: Pelangi — 2026-09-02 (angka awal run pertama, LIHAT KOREKSI di bawah)

**TOTAL run pertama: 333/300 NEW valid titles — TARGET TERCAPAI di SEMUA 17
cluster** (tidak ada exhaustion). **Angka final SETELAH koreksi bug "villa"
(lihat bagian "Bug ditemukan pasca-run" di bawah): 330/300**, tetap tercapai
di semua cluster, tabel per-cluster di bawah adalah angka run pertama
(sebelum 41 keyword salah dihapus + top-up ulang).

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

## Bug ditemukan pasca-run + diperbaiki (2026-09-03, permintaan Agus "cek apakah judulnya masuk akal")

Audit manual Agus menemukan **38 keyword baru Pelangi salah sebut "villa"**
(Pelangi Homestay = Cottage/Standard, BUKAN villa — Harmoni yang villa).
Root cause: Gate 6 (`_keyword_properti_salah_tipe`, sudah ada sejak
2026-08-06) TIDAK PERNAH dipanggil di `_generate_new_keywords()` — cuma
dipasang di `get_next_keyword()` dan `generate_keyword_cluster()`, celah
yang sama kelasnya dgn Angle-Entity Gate (gate ada, tidak dipasang di
SEMUA jalur generation). Karena campaign ini pakai `_generate_new_keywords`
sbg mesin utamanya, celah ini akhirnya kena skala penuh.

**Diperbaiki**: Gate 6 dipasang di `_generate_new_keywords()` (permanen,
bukan cuma utk campaign ini — berlaku jg utk cron auto-refill harian ke
depannya). 41 keyword salah (38 "villa" + 3 "vila", regex awal cuma
tangkap 1 varian ejaan) dihapus (masih `status="belum_dibuat"`, belum
pernah jadi artikel — aman, bukan protected inventory). 10 cluster
terdampak di-top-up ulang pakai gate yang sudah diperbaiki — **terbukti
langsung memblokir 7 percobaan "villa"/"vila" baru** selama top-up.

**Verifikasi akhir**: 0 "villa"/"vila" tersisa di 330 keyword campaign
Pelangi, 0 entitas non-akomodasi salah konteks (kantor polisi/puskesmas/
rumah sakit/dst) di 662 keyword gabungan kedua situs — dicek manual
seluruh daftar, bukan sampling.

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
