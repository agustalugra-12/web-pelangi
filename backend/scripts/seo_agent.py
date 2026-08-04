"""AI SEO Growth Agent - versi ramping (2026-07-26, permintaan user setelah diskusi PRD
16-Agent penuh yang dianggap over-engineering untuk 2 properti milik sendiri, bukan SaaS
multi-tenant komersial). Cakupan yang DIBANGUN: Keyword Agent (dari 100 keyword yang
diberi user + generate keyword baru kalau pool habis, prioritas High/Medium/Low lalu
tie-break sinyal demand GSC riil - lihat _cluster_demand_scores), Keyword Cannibalization
Check (2026-07-28, real-time SEBELUM keyword mana pun dipilih ditulis - lihat
_keyword_cannibalizes_existing, cek embedding similarity ke JUDUL artikel yang sudah
terbit, bukan cuma ke sesama keyword generate-baru spt sebelumnya), Writer Agent
(grounded ke data CMS asli - lihat _fetch_site_facts), Competitor Analysis Agent
(2026-07-28, lihat analyze_competitors - awalnya "sengaja tidak dibangun", ditambahkan
belakangan begitu user minta; heading kompetitor yang berbentuk pertanyaan jadi kandidat
FAQ prioritas krn Serper "peopleAlsoAsk" TIDAK tersedia utk keyword long-tail lokal kita -
sudah dites 3 query berbeda, semua kosong), Internal Link Agent (2026-07-28, kandidat
link dikirim SEBELUM menulis supaya anchor text natural tertanam di kalimat, BUKAN
ditempel mekanis "Baca juga: [Judul]" - fallback mekanis tetap ada kalau model tidak
menyelipkan satupun), Fact-Check pass (2026-07-28, satu panggilan API tambahan verifikasi
draft final ke DATA ASLI SEBELUM publish - lihat fact_check, lapis KEDUA setelah instruksi
anti-mengarang di system prompt), Quality Gate (rule-based, BUKAN "AI menilai AI"), Schema
+ Cover Image Agent, Publish (auto, TANPA approval manusia - ini keputusan sadar user
setelah diberi tahu risiko kebijakan "Scaled Content Abuse" Google), Impression-based
Expansion Agent (2026-07-28, script terpisah scripts/expand_top_articles.py - jalan
mingguan, perdalam artikel yang TERBUKTI dapat impression GSC riil).
Cakupan yang SENGAJA TIDAK dibangun: Autopilot penuh 10.000 artikel sekaligus, Analytics
Dashboard penuh (SEBAGIAN sudah ada - lihat GET /admin/gsc/summary di server.py, GSC
Integration 2026-07-28). Volume naik bertahap: 3/hari/situs (2026-07-26) ->
7/hari/situs (2026-07-28, permintaan user) - lihat scripts/run_daily_seo.sh utk
penjadwalan cron aktual.

Jalankan manual: `venv/bin/python -m scripts.seo_agent --site pelangi --count 1`
"""
import argparse
import asyncio
import json
import math
import os
import random
import re
import statistics
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
from typing import Optional, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
import httpx  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from scripts import prerender_home as _prerender  # noqa: E402

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
# Ganti dari gpt-5-mini ke gpt-4.1-mini (2026-08-05, investigasi biaya + insiden nyata:
# sejak 2026-08-04 ~12:36 WIB SEMUA slot cron gagal 4x percobaan lalu MENYERAH tanpa
# publish sama sekali - ditemukan 2 penyebab: (1) banyak panggilan ReadTimeout di 90 detik,
# kemungkinan besar krn gpt-5-mini (model reasoning) punya overhead "thinking" tersembunyi
# yg tidak kelihatan di teks tapi tetap makan waktu & TETAP DITAGIH sbg output token walau
# client sudah menyerah nunggu; (2) gpt-5-mini output token 25% lebih mahal ($2.00/1M) drpd
# gpt-4.1-mini ($1.60/1M), plus overhead reasoning token di atas itu - kombinasi ini bikin
# gpt-5-mini jadi model termahal di seluruh stack (ai-chat-bot pakai gpt-4o-mini/gpt-4.1-mini,
# jauh lebih murah). gpt-4.1-mini BUKAN model reasoning (tidak ada overhead tersembunyi),
# lebih cepat respon (harusnya langsung mengurangi ReadTimeout), lebih murah per token, DAN
# tidak lagi dipaksa temperature=1 (lihat _chat() di bawah - restriksi itu cuma utk model
# gpt-5) - artinya temperature asli tiap call site (0.6 penulisan/0.2 fact-check/0.5 fix)
# yg sengaja di-tuning dari awal otomatis balik berlaku, bukan diseragamkan paksa ke 1 lagi.
CHAT_MODEL = "gpt-4.1-mini"
EMBED_MODEL = "text-embedding-3-small"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

WA_BY_SITE = {
    "pelangi": "https://wa.me/6285119459269?text=Halo%2C%20saya%20ingin%20booking%20kamar%20di%20Pelangi%20Homestay.",
    "harmoni": "https://wa.me/6285168941258?text=Halo%2C%20saya%20ingin%20booking%20kamar%20di%20harmoni.",
}

# Aset foto ASLI yang boleh dipakai per situs - JANGAN PERNAH pinjam foto bangunan/kamar
# milik properti lain (facade/garden/restaurant itu Pelangi asli, tidak boleh dipakai utk
# harmoni). Foto atraksi wisata (tempat publik, sama-sama dekat kedua properti di Bedugul)
# boleh dipakai kedua situs.
SHARED_ASSETS = ["/assets/ulun-danu.webp", "/assets/danau-beratan.webp", "/assets/kebun-raya.webp",
                 "/assets/pasar-candikuning.webp", "/assets/handara-gate.webp"]
SITE_ASSETS = {
    "pelangi": SHARED_ASSETS + ["/assets/facade.webp", "/assets/garden.webp", "/assets/restaurant.webp",
                                 "/assets/std-1.webp", "/assets/std-2.webp", "/assets/std-3.webp",
                                 "/assets/std-4.webp", "/assets/std-5.webp",
                                 "/assets/cot-1.webp", "/assets/cot-2.webp", "/assets/cot-3.webp",
                                 "/assets/cot-4.webp", "/assets/cot-5.webp"],
    "harmoni": SHARED_ASSETS + ["/assets/cot-1.webp", "/assets/cot-2.webp", "/assets/cot-3.webp",
                                 "/assets/cot-4.webp", "/assets/cot-5.webp"],
}

# Brand Voice / Content Differentiation (2026-08-03, permintaan Agus - "AI Blog v3 Content
# Differentiation Engine") - Pelangi & Harmoni berbagi 1 root domain (Harmoni = subdomain
# pelangihomestay.com), jadi kalau keduanya kebetulan menulis keyword yang mirip TANPA sudut
# pandang beda, Google berisiko anggap itu duplicate content lintas situs & bingung mana yang
# lebih relevan - merugikan RANKING KEDUANYA, bukan cuma salah satu. Persona ini SELALU
# disuntik ke Writer Agent (bukan cuma saat tabrakan keyword terdeteksi, lihat
# _cross_brand_collision) supaya nada tulisan tiap situs konsisten dari awal, tapi jadi
# KRITIS terutama saat tabrakan - lihat blok "TABRAKAN KEYWORD LINTAS BRAND" di write_article.
SITE_PERSONA = {
    "pelangi": (
        "Pelangi Homestay - budget-friendly, ramah keluarga, cocok backpacker & long stay/"
        "remote work, dekat Danau Beratan & Handara, value for money. Nada tulisan: hangat, "
        "ramah, membantu wisatawan yang cari penginapan terjangkau & praktis."
    ),
    "harmoni": (
        "Harmoni Hills - villa privat, cocok honeymoon & nature escape, suasana premium "
        "dgn view pegunungan, romantis. Nada tulisan: elegan, eksklusif, lebih emosional/"
        "sensorik dibanding Pelangi."
    ),
}

# Gate 1: Facility Truthfulness Gate (2026-08-04, PRD "AI Blog Engine v2.0") - blacklist
# KERAS, terpisah dari larangan di _fetch_site_facts/_generate_new_keywords brainstorm
# prompt di bawah (yang SIFATNYA instruksi ke model, bisa dilanggar - sudah 3x terbukti di
# sesi ini prompt-only tidak 100% reliable: bug multi-tipe kamar, janji eskalasi, jam
# kesiapan besok/lusa). Gate ini jalan SEBELUM keyword sempat masuk antrian sama sekali -
# lihat pemanggilnya di get_next_keyword()/_pick_from_pool() & _generate_new_keywords().
# Fasilitas di bawah sudah dikonfirmasi TIDAK dimiliki KEDUA properti (audit 2026-08-03,
# lihat FASILITAS/LAYANAN YANG TIDAK KAMI SEDIAKAN di _fetch_site_facts).
#
# "villa" SENGAJA TIDAK masuk daftar walau ada di draft PRD asli - Harmoni Hills memakai
# "villa privat" sbg deskripsi brand-nya sendiri (lihat SITE_PERSONA di atas), blacklist
# kata itu akan salah-tolak keyword legitimate soal Harmoni sendiri. Ambang deteksi tetap
# akurat karena fasilitas spesifik ("private pool", "dapur lengkap") sudah cukup menangkap
# klaim palsu tanpa perlu blok kata generik "villa".
FACILITY_BLACKLIST = [
    "kolam renang", "swimming pool", "private pool", "kolam pribadi",
    "glamping", "tenda camping",
    "dapur lengkap", "full kitchen", "kitchen lengkap", "dengan dapur", "dapur pribadi",
    "ruang meeting", "ruang rapat", "layanan katering", "catering",
    "gym", "fitness center", "spa",
    "sewa mobil", "sewa motor", "rental mobil", "rental motor",
    "jemput bandara", "antar jemput bandara", "airport transfer", "airport pickup",
    "paket trip", "paket tur", "paket wisata", "paket trekking",
    "hewan peliharaan", "pet friendly", "pet-friendly",
]
ACCOMMODATION_SIGNALS = [
    "hotel", "villa", "resort", "penginapan", "homestay", "cottage",
    "guest house", "guesthouse", "akomodasi", "menginap", "sewa", "booking",
]


def _keyword_menjanjikan_fasilitas_tidak_ada(keyword: str) -> Optional[str]:
    """True (return nama fasilitasnya) kalau keyword mengandung fasilitas yang TIDAK kami
    punya DAN menyiratkan ini soal akomodasi/booking (bukan pertanyaan informasional murni,
    mis. "kolam renang umum di Bedugul" boleh lolos - itu bukan klaim Pelangi/Harmoni
    punya kolam)."""
    lower = keyword.lower()
    fasilitas_match = next((f for f in FACILITY_BLACKLIST if f in lower), None)
    if not fasilitas_match:
        return None
    if not any(s in lower for s in ACCOMMODATION_SIGNALS):
        return None
    return fasilitas_match


CLUSTER_CATEGORY = {
    "Utama": "General", "Harga": "Tips", "Lokasi Wisata": "Wisata", "View": "Wisata",
    "Keluarga": "Tips", "Pasangan": "Tips", "Fasilitas": "Tips", "Aktivitas": "Wisata",
    "Booking": "Tips", "Long Tail": "General",
}

# Angle per cluster (2026-07-29, revisi manual user - akar masalah "3 artikel isinya hampir
# identik": SEBELUM ini, SATU system prompt yang SAMA dipakai utk semua cluster, jadi model
# cenderung menjelaskan ULANG semua kebijakan/fasilitas/pembayaran di SETIAP artikel apa pun
# angle-nya - Google anggap ini duplicate content, bisa menurunkan ranking SEMUA artikel
# terkait sekaligus. Fix-nya: tiap cluster dikasih FOKUS BERBEDA & instruksi eksplisit apa
# yang HARUS diringkas/dihindari, supaya tiap artikel benar-benar punya angle sendiri,
# bukan versi lain dari artikel yang sama.
CLUSTER_ANGLE = {
    "Utama": (
        "Fokus GAMBARAN UMUM properti - siapa yang paling cocok menginap di sini & kenapa. "
        "JANGAN uraikan SEMUA kebijakan (parkir/pembayaran/kebijakan anak) panjang lebar - "
        "itu bikin artikel jadi mirip artikel cluster lain. Cukup 1 kalimat singkat per "
        "kebijakan kalau memang perlu disebut, sisanya cukup di FAQ."
    ),
    "Harga": (
        "Fokus RINCIAN HARGA & value-for-money - bandingkan opsi (Day Use vs Menginap, "
        "dengan/tanpa sarapan), estimasi budget total (kamar + perkiraan makan/aktivitas dari "
        "DATA ASLI saja, jangan mengarang harga di luar itu), kenapa harganya sepadan."
    ),
    "Lokasi Wisata": (
        "Fokus LOKASI & JARAK ke destinasi wisata spesifik di keyword - beri estimasi jarak/"
        "waktu tempuh dari properti (kalau ada di DATA ASLI, kalau tidak ada JANGAN mengarang "
        "angka pasti - tulis 'dekat'/'tidak jauh' saja), mini itinerary 1 hari kalau relevan, "
        "tips kunjungi destinasi itu (waktu terbaik, hindari antrean). Deskripsi kamar CUKUP "
        "1-2 kalimat, jangan diuraikan panjang seperti artikel ttg kamar itu sendiri."
    ),
    "View": (
        "Fokus PENGALAMAN VISUAL/SENSORIK - apa yang benar-benar dilihat/dirasakan dari kamar "
        "atau teras (kabut pagi, hijau pegunungan, dst), bukan sekadar daftar fasilitas."
    ),
    "Keluarga": (
        "Fokus LOGISTIK KELUARGA - kebijakan anak/extra bed, keamanan, aktivitas ramah anak. "
        "JANGAN sisipkan konten romantis/honeymoon di sini - beda cluster, beda pembaca."
    ),
    "Pasangan": (
        "Fokus PENGALAMAN ROMANTIS utk PASANGAN - suasana intim, aktivitas berdua, momen "
        "berkesan. JANGAN sebut kebijakan anak/extra bed SAMA SEKALI (tidak relevan utk "
        "honeymoon/pasangan) kecuali keyword eksplisit menyebut anak."
    ),
    "Fasilitas": (
        "Fokus DETAIL FASILITAS spesifik yang disebut keyword - jelaskan KENAPA fasilitas itu "
        "berguna dgn detail konkret/sensorik, bukan cuma menyalin daftar fasilitas mentah."
    ),
    "Aktivitas": (
        "Fokus AKTIVITAS yang bisa dilakukan tamu (di properti atau sekitar) - detail konkret "
        "ttg aktivitas itu sendiri, bukan deskripsi umum penginapan."
    ),
    "Booking": (
        "Fokus PROSES BOOKING & PEMBAYARAN - cara pesan, metode bayar, kebijakan DP/pelunasan, "
        "kebijakan pembatalan. Cluster INI yang wajar menjelaskan detail pembayaran/kebijakan "
        "secara lengkap (cluster lain cukup singkat + rujuk FAQ)."
    ),
    "Long Tail": (
        "Keyword ini sangat spesifik - jawab LANGSUNG ke inti pertanyaannya di paragraf "
        "pembuka, jangan muter-muter dgn info umum properti dulu."
    ),
}

# Query pencarian Pexels (2026-07-28) - Pexels cuma cari bagus dalam Bahasa Inggris, jadi
# dipetakan per cluster (bukan pakai keyword Indonesia mentah) - beberapa varian per cluster
# supaya tidak selalu dapat foto yang sama persis utk cluster yang sama.
# Setiap query WAJIB eksplisit "bali"/"tropical" (2026-07-28, ditemukan lewat uji visual -
# query generik seperti "cozy cottage interior" tanpa kata itu sering nyasar ke hasil kabin
# gaya Eropa/alpine, bukan tropis Bali - tidak sesuai suasana properti sama sekali).
#
# DIROMBAK TOTAL (2026-07-28, permintaan user) - versi sebelumnya banyak query
# "guesthouse/resort/cottage/veranda" yang hasilnya foto KAMAR/KOLAM RENANG/INTERIOR
# penginapan generik (bukan milik Pelangi/Harmoni asli, tapi tetap MENYESATKAN kalau
# terlihat seperti "penginapan" - bisa disangka klaim visual properti yang tidak
# benar). Sekarang SEMUA query murni pemandangan PUBLIK area Bedugul yang nyata &
# bisa diverifikasi (danau/pura Ulun Danu Beratan, Kebun Raya Bali, sawah/kebun
# dataran tinggi, pasar/kebun stroberi Candikuning, jalan pegunungan berkabut) -
# TIDAK ADA lagi kata resort/guesthouse/cottage/veranda/vacation/homestay di query
# manapun, supaya Pexels tidak pernah balikin foto kamar/kolam renang/interior.
CLUSTER_PEXELS_QUERY = {
    "Utama": ["ulun danu temple lake bali", "bali highland mountain lake"],
    "Harga": ["bali highland mountain scenery", "bali lake temple misty morning"],
    "Lokasi Wisata": ["ulun danu beratan temple bali", "bali botanical garden tropical"],
    "View": ["misty lake temple bali mountain", "bali highland lake sunrise"],
    "Keluarga": ["bali botanical garden tropical", "bali rice terrace mountain"],
    "Pasangan": ["misty bali mountain lake sunset", "bali temple lake reflection"],
    "Fasilitas": ["bali highland garden path public", "bali tropical mountain scenery"],
    "Aktivitas": ["bali mountain nature trail", "bali strawberry farm highland"],
    "Booking": ["bali highland lake temple scenery", "bali mountain village travel"],
    "Long Tail": ["bali highland garden mountain", "bali lake temple misty morning"],
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# OpenAI helpers (httpx langsung - repo ini belum punya dependency openai/litellm)
# ---------------------------------------------------------------------------
async def _chat(system: str, user: str, temperature: float = 0.7) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY belum diisi di backend/.env")
    # Keluarga GPT-5 (gpt-5, gpt-5-mini, gpt-5.4-mini, dst) CUMA terima temperature=1 -
    # ditemukan lewat tes live 2026-07-31 (bug yang sama juga ditemukan & diperbaiki di
    # ai-chat-bot) - API OpenAI menolak keras temperature lain utk model ini. Diklem di
    # SINI (bukan di tiap pemanggil _chat) supaya seluruh pipeline (Writer Agent 0.6,
    # fact-check 0.2, expand loop, dst) otomatis aman tanpa perlu ubah tiap call site.
    if CHAT_MODEL.lower().startswith("gpt-5"):
        temperature = 1
    # Timeout dinaikkan 90 -> 150 detik (2026-08-05, jaring pengaman tambahan sesudah
    # ganti model - bukan solusi utama, tapi tetap wajar dikasih margin lebih longgar
    # utk artikel panjang, bukan hanya berharap gpt-4.1-mini selalu cukup cepat).
    async with httpx.AsyncClient(timeout=150) as http:
        resp = await http.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": CHAT_MODEL,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _embed(texts: list) -> list:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY belum diisi di backend/.env")
    async with httpx.AsyncClient(timeout=60) as http:
        resp = await http.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": EMBED_MODEL, "input": texts},
        )
        resp.raise_for_status()
        return [d["embedding"] for d in resp.json()["data"]]


def _cosine(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


# ---------------------------------------------------------------------------
# 1. Keyword Agent
# ---------------------------------------------------------------------------
CANNIBALIZATION_THRESHOLD = 0.65


async def _keyword_cannibalizes_existing(site: str, keyword: str, cluster: str) -> Optional[str]:
    """Return keyword ASLI (yang sudah dipakai menulis artikel terbit, di CLUSTER YANG
    SAMA) kalau `keyword` baru ini mirip secara semantik (cosine > CANNIBALIZATION_
    THRESHOLD) - None kalau aman ditulis.

    2026-07-28 - sebelumnya cek duplikat semantik cuma jalan di _generate_new_keywords()
    (keyword hasil brainstorm AI saat 100 keyword awal user habis), TIDAK PERNAH jalan
    utk 100 keyword awal itu sendiri. Melalui 2 revisi hari ini, keduanya salah & DITEMUKAN
    LEWAT TES EMPIRIS NYATA (bukan cuma teori), bukan lewat baca kode doang:

    Revisi 1 (dibuang): bandingkan keyword ke JUDUL artikel terbit, ambang 0.88 (disalin
    apa adanya dari _generate_new_keywords). SALAH: keyword pendek vs judul panjang (byk
    kata boilerplate "Pilihan Nyaman dan Terjangkau di Pelangi Homestay") selalu skor
    <0.6 walau topik identik ("hotel bedugul" vs judul "Hotel Murah Bedugul: ..." cuma
    0.594) - cannibalization LOLOS tanpa terdeteksi.

    Revisi 2 (dibuang): ganti perbandingan ke KEYWORD ASLI (bukan judul, struktur teks
    sebanding) TANPA batasi cluster, ambang 0.65. Menangkap kasus asli user dgn benar,
    TAPI dites dampaknya ke SELURUH 81 keyword belum_dibuat pelangi -> 71/81 (88%!)
    ke-skip, termasuk keyword yang SENGAJA dibuat beda angle (mis. "cottage keluarga
    bedugul" vs "cottage bedugul" - cluster Keluarga vs Utama, target audiens beda).
    Niche Bedugul sempit (kosakata "hotel/homestay/cottage" + "bedugul" berulang di
    hampir semua keyword) bikin cosine keyword-vs-keyword secara umum tinggi walau
    angle/intent-nya beda - threshold tunggal tidak bisa membedakan "duplikat asli"
    dari "variasi angle yang disengaja".

    Revisi 3 (dipakai): batasi perbandingan HANYA ke keyword tertulis di CLUSTER YANG
    SAMA (cluster memang sengaja dirancang jadi sinyal "angle berbeda" - Keluarga vs
    Pasangan vs Booking vs Harga, dst - lihat CLUSTER_CATEGORY & seo_keywords.cluster).
    Dites ulang scr empiris: kasus asli user (semua di cluster Booking) tetap tertangkap
    benar di ambang 0.65 (skor 0.69-0.87), TAPI dampak ke seluruh pool turun jadi 20/81
    (25%) - jauh lebih masuk akal, tidak lagi memblokir variasi angle yang disengaja."""
    written = await db.seo_keywords.find(
        {"site": site, "status": "sudah_dibuat", "cluster": cluster}, {"keyword": 1},
    ).to_list(1000)
    if not written:
        return None
    written_kws = [w["keyword"] for w in written]
    embeds = await _embed([keyword] + written_kws)
    kw_emb, written_embs = embeds[0], embeds[1:]
    for w_kw, emb in zip(written_kws, written_embs):
        if _cosine(kw_emb, emb) > CANNIBALIZATION_THRESHOLD:
            return w_kw
    return None


async def _cross_brand_collision(site: str, keyword: str, cluster: str) -> Optional[dict]:
    """Cek tabrakan keyword LINTAS BRAND - Pelangi vs Harmoni (2026-08-03, permintaan Agus,
    PRD "AI Blog v3 Content Differentiation Engine"). BEDA dari _keyword_cannibalizes_
    existing di atas: fungsi itu cuma cek DALAM 1 situs (query `{"site": site, ...}`),
    TIDAK PERNAH membandingkan Pelangi vs Harmoni - dikonfirmasi langsung baca kodenya
    sebelum menambah fungsi ini, supaya tidak menduplikasi cek yang sudah ada.

    Beda perlakuan dari kasus within-site JUGA disengaja: within-site collision -> SKIP
    (topik sama + situs sama = benar-benar duplikat, tidak ada alasan nulis ulang). Cross-
    brand collision -> JANGAN skip, tetap tulis, TAPI beri tahu Writer Agent (lihat
    write_article, blok TABRAKAN KEYWORD LINTAS BRAND) supaya wajib ambil sudut pandang
    beda sesuai SITE_PERSONA masing-masing brand - itu skenario nyata yang diminta Agus
    (keyword sama, angle beda: Pelangi budget/keluarga vs Harmoni honeymoon/private).

    Return dict {"title", "site"} punya brand SEBERANG kalau ketemu tabrakan (skor cosine
    > CANNIBALIZATION_THRESHOLD, threshold SAMA & cluster-scoping SAMA dgn within-site utk
    konsistensi - sudah terbukti pas lewat 3 revisi empiris di fungsi di atas), None kalau
    aman."""
    other_site = "harmoni" if site == "pelangi" else "pelangi"
    written = await db.seo_keywords.find(
        {"site": other_site, "status": "sudah_dibuat", "cluster": cluster}, {"keyword": 1, "artikel_slug": 1},
    ).to_list(1000)
    if not written:
        return None
    written_kws = [w["keyword"] for w in written]
    embeds = await _embed([keyword] + written_kws)
    kw_emb, written_embs = embeds[0], embeds[1:]
    for w_doc, emb in zip(written, written_embs):
        if _cosine(kw_emb, emb) > CANNIBALIZATION_THRESHOLD:
            title = w_doc["keyword"]
            if w_doc.get("artikel_slug"):
                post = await db.blog_posts.find_one(
                    {"site": other_site, "slug": w_doc["artikel_slug"]}, {"title": 1},
                )
                if post and post.get("title"):
                    title = post["title"]
            return {"title": title, "site": other_site}
    return None


async def _cluster_demand_scores(site: str) -> dict:
    """cluster -> total impression GSC (28 hari terakhir) dari artikel yang SUDAH ditulis
    utk cluster itu - sinyal riil "topik ini benar-benar dicari orang", bukan tebakan.

    2026-07-28 - jawaban konkret utk "apakah AI membaca performa Search Console sebelum
    menulis": ya, dipakai get_next_keyword() sbg tie-breaker SEKUNDER (BUKAN menggantikan
    priority High/Medium/Low yang user tentukan manual - itu tetap kunci utama) - di ANTARA
    keyword dgn priority yang sama, cluster yang artikelnya terbukti dapat impression nyata
    dari GSC didahulukan drpd cluster yang belum terbukti diminati. blog_posts sendiri tidak
    simpan field cluster (cuma category, terlalu kasar - 1 category = gabungan bbrp cluster,
    lihat CLUSTER_CATEGORY), jadi join lewat db.seo_keywords (field cluster ADA di sana,
    persis keyword yang dipakai menulis artikel itu) -> bangun URL dari artikel_slug -> cocokkan
    ke db.gsc_page_stats. None/kosong (situs baru/GSC belum sync) - caller HARUS tetap jalan
    normal tanpa sinyal ini (bukan dianggap error)."""
    domain = SITE_DOMAIN.get(site)
    if not domain:
        return {}
    written = await db.seo_keywords.find(
        {"site": site, "status": "sudah_dibuat", "artikel_slug": {"$ne": None}},
        {"cluster": 1, "artikel_slug": 1},
    ).to_list(1000)
    if not written:
        return {}
    url_to_cluster = {f"https://{domain}/blog/{w['artikel_slug']}": w["cluster"] for w in written}
    stats = await db.gsc_page_stats.find(
        {"site": site, "url": {"$in": list(url_to_cluster.keys())}}, {"url": 1, "impressions": 1},
    ).to_list(1000)
    scores: dict = {}
    for row in stats:
        cluster = url_to_cluster.get(row["url"])
        if cluster:
            scores[cluster] = scores.get(cluster, 0) + row.get("impressions", 0)
    return scores


# Seasonal Planner (2026-07-29, permintaan user) - kalender resmi hari libur/cuti bersama
# Indonesia 2026 (dicek via web search ke sumber berita asli tanggal 2026-07-29, BUKAN
# ditebak/dihafal dari training data - libur nasional bisa bergeser tiap tahun krn hilal/
# SKB 3 menteri). PENTING: kalender ini WAJIB diperbarui tiap tahun (angka tahun di nama
# variabel sengaja eksplisit 2026 supaya ketahuan kalau lupa update). Window "boost" =
# 21 hari SEBELUM tanggal mulai musim (bukan selama musimnya) - tujuannya artikel sudah
# terbit & ter-index Google SEBELUM volume pencarian naik, bukan pas musimnya sudah lewat.
SEASONAL_WINDOWS_2026 = [
    (date(2026, 1, 1), date(2026, 1, 1), "Tahun Baru Masehi"),
    (date(2026, 1, 29), date(2026, 1, 29), "Imlek"),
    (date(2026, 3, 20), date(2026, 3, 24), "Nyepi + Lebaran (Idul Fitri 1447H)"),
    (date(2026, 4, 3), date(2026, 4, 3), "Wafat Isa Almasih"),
    (date(2026, 5, 1), date(2026, 5, 1), "Hari Buruh"),
    (date(2026, 5, 14), date(2026, 5, 14), "Kenaikan Isa Almasih"),
    (date(2026, 5, 26), date(2026, 5, 26), "Waisak"),
    (date(2026, 6, 1), date(2026, 6, 1), "Hari Lahir Pancasila"),
    (date(2026, 6, 20), date(2026, 7, 15), "Libur Sekolah Pertengahan Tahun"),
    (date(2026, 7, 7), date(2026, 7, 7), "Idul Adha"),
    (date(2026, 7, 27), date(2026, 7, 27), "Tahun Baru Islam"),
    (date(2026, 8, 17), date(2026, 8, 17), "Hari Kemerdekaan RI"),
    (date(2026, 10, 5), date(2026, 10, 5), "Maulid Nabi"),
    (date(2026, 12, 15), date(2027, 1, 5), "Libur Natal, Tahun Baru & Libur Sekolah Akhir Tahun"),
]
SEASONAL_LEAD_DAYS = 21


def _musim_mendekat(today: Optional[date] = None) -> Optional[str]:
    """Return nama musim kalau HARI INI berada di window boost (21 hari sebelum musim
    mulai, sampai musim itu berakhir) - None kalau sedang tidak mendekati musim apa pun."""
    today = today or datetime.now(timezone.utc).date()
    for start, end, label in SEASONAL_WINDOWS_2026:
        if start - timedelta(days=SEASONAL_LEAD_DAYS) <= today <= end:
            return label
    return None


# Rasio komposisi intent target (2026-08-04, PRD "AI Blog Engine v2.0" §5.1) - 40%
# Informational murni, 40% Commercial (masih informasional, soft-promosi Pelangi sbg
# salah satu opsi - padanan terdekat dari "informational+soft" PRD ke taksonomi intent 3
# kategori yang SUDAH ADA, bukan taksonomi baru), 20% Transactional (fokus Pelangi/niat
# booking). Dipakai get_next_keyword() sbg tie-breaker CONDONG (bukan kuota kaku per
# batch) supaya komposisi keseluruhan korpus perlahan menuju target ini.
INTENT_RATIO_TARGET = {"Informational": 0.40, "Commercial": 0.40, "Transactional": 0.20}


async def _intent_ratio_saat_ini(site: str) -> Dict[str, float]:
    """Komposisi intent artikel yang SUDAH terbit - join blog_posts.seo_keyword ->
    seo_keywords.intent (field intent sudah ada dari Intent Classifier 2026-08-02, tapi
    sebelumnya cuma tersimpan, tidak pernah dipakai apa pun - lihat catatan di
    _generate_new_keywords). {} kalau belum ada artikel terbit sama sekali."""
    posts = await db.blog_posts.find({"site": site, "published": True}, {"seo_keyword": 1}).to_list(2000)
    kw_texts = [p["seo_keyword"] for p in posts if p.get("seo_keyword")]
    if not kw_texts:
        return {}
    kw_docs = await db.seo_keywords.find(
        {"site": site, "keyword": {"$in": kw_texts}}, {"keyword": 1, "intent": 1},
    ).to_list(len(kw_texts))
    intent_by_kw = {d["keyword"]: d.get("intent", "Transactional") for d in kw_docs}
    counts = {"Informational": 0, "Commercial": 0, "Transactional": 0}
    for kw in kw_texts:
        counts[intent_by_kw.get(kw, "Transactional")] = counts.get(intent_by_kw.get(kw, "Transactional"), 0) + 1
    total = len(kw_texts)
    return {k: v / total for k, v in counts.items()}


async def get_next_keyword(site: str, exclude_ids: Optional[set] = None) -> dict:
    """Ambil keyword prioritas tertinggi yang statusnya 'belum_dibuat' DAN belum
    cannibalize topik yang sudah pernah ditulis, DAN bukan janji fasilitas yang tidak
    kami punya (Gate 1, lihat _keyword_menjanjikan_fasilitas_tidak_ada). Di antara
    keyword dgn priority sama, dahulukan (1) keyword musiman kalau lagi mendekati musim
    (lihat _musim_mendekat), (2) cluster yang terbukti dapat impression GSC nyata (lihat
    _cluster_demand_scores), (3) intent yang komposisinya masih di bawah target 40/40/20
    (lihat INTENT_RATIO_TARGET) - condong, bukan kuota kaku, supaya tidak deadlock kalau
    pool suatu intent kebetulan kosong hari itu. Kalau pool habis (atau semua kandidat
    ternyata cannibalizing/fasilitas fiktif), generate keyword baru dulu (cek duplikat
    semantik ke keyword+judul artikel yang sudah ada) sebelum diambil.

    `exclude_ids` (2026-08-05, bug nyata ditemukan lewat tes live - retry-until-sukses di
    main() SEHARUSNYA "otomatis skip yang baru gagal" (lihat komentar main()), tapi pool
    di-sort DETERMINISTIK (priority/cluster-score/intent-ratio) tanpa memandang percobaan
    barusan - keyword yang gagal langsung direset ke "belum_dibuat" & posisi sortirnya
    TIDAK BERUBAH SAMA SEKALI, jadi kepilih lagi persis sama di percobaan berikutnya.
    Terbukti nyata: 1 keyword ("...kebun strawberry...", topik yg fact-check-nya SELALU
    gagal krn tidak didukung data asli) kepilih 8x berturut-turut lintas 2 percobaan
    terpisah, MAX_RETRY_PER_SLOT habis tanpa pernah coba keyword lain. Dipakai main() utk
    mengecualikan keyword yang SUDAH gagal di slot yang SAMA, supaya percobaan berikutnya
    benar-benar coba kandidat berbeda spt yang diniatkan sejak awal."""
    order = {"High": 0, "Medium": 1, "Low": 2}
    cluster_scores = await _cluster_demand_scores(site)
    musim_aktif = _musim_mendekat()
    intent_ratio = await _intent_ratio_saat_ini(site)
    exclude_ids = exclude_ids or set()

    async def _pick_from_pool() -> Optional[dict]:
        pool = await db.seo_keywords.find({"site": site, "status": "belum_dibuat"}).to_list(500)
        pool = [k for k in pool if k["id"] not in exclude_ids]
        pool.sort(key=lambda k: (
            order.get(k["priority"], 9),
            0 if (musim_aktif and k.get("musiman")) else 1,
            -cluster_scores.get(k.get("cluster"), 0),
            -(INTENT_RATIO_TARGET.get(k.get("intent", "Transactional"), 0) - intent_ratio.get(k.get("intent", "Transactional"), 0)),
        ))
        now = datetime.now(timezone.utc).isoformat()
        for kw_doc in pool:
            fasilitas_match = _keyword_menjanjikan_fasilitas_tidak_ada(kw_doc["keyword"])
            if fasilitas_match:
                await db.seo_keywords.update_one(
                    {"id": kw_doc["id"]},
                    {"$set": {
                        "status": "ditolak_fasilitas_tidak_ada", "updated_at": now,
                        "cannibalization_note": f'Gate 1: keyword menjanjikan "{fasilitas_match}" yang tidak dimiliki properti',
                    }},
                )
                continue
            dupe_kw = await _keyword_cannibalizes_existing(site, kw_doc["keyword"], kw_doc["cluster"])
            if dupe_kw is None:
                return kw_doc
            await db.seo_keywords.update_one(
                {"id": kw_doc["id"]},
                {"$set": {
                    "status": "dilewati_mirip", "updated_at": now,
                    "cannibalization_note": f'topik sama dgn keyword yang sudah ditulis: "{dupe_kw}"',
                }},
            )
        return None

    picked = await _pick_from_pool()
    if picked is None:
        await _generate_new_keywords(site, n=10)
        picked = await _pick_from_pool()
    if picked is None:
        raise RuntimeError(
            f"Tidak ada keyword tersedia untuk situs {site} (pool habis/semua kandidat "
            "mirip topik yang sudah ditulis/menjanjikan fasilitas fiktif, generate baru juga gagal)"
        )
    return picked


async def _generate_new_keywords(site: str, n: int = 10) -> None:
    """Dipanggil kalau 100 keyword awal sudah habis dipakai - AI brainstorm keyword baru
    yang MASIH relevan (penginapan/wisata Bedugul), lalu dicek duplikat semantik terhadap
    keyword & judul artikel yang sudah ada sebelum dimasukkan sbg 'belum_dibuat'."""
    existing_kw = await db.seo_keywords.find({"site": site}, {"keyword": 1}).to_list(2000)
    existing_titles = await db.blog_posts.find({"site": site}, {"title": 1}).to_list(500)
    existing_texts = [k["keyword"] for k in existing_kw] + [p["title"] for p in existing_titles]

    # Cluster Generator (2026-08-02, PRD "AI Blog V2.0" modul 6) - SEBELUM ini SEMUA keyword
    # hasil generate baru hardcode cluster="Long Tail" tanpa dianalisis, artinya CLUSTER_ANGLE
    # (10 angle berbeda yang SENGAJA dibuat 2026-07-29 supaya artikel tidak duplicate content -
    # lihat komentarnya) tidak pernah benar-benar dipakai utk keyword baru, SEMUA dapat angle
    # "Long Tail" generik walau topiknya sebenarnya jelas² "Pasangan"/"Keluarga"/dst - bug yang
    # sama persis dgn kelas masalah yang CLUSTER_ANGLE dibuat utk dicegah. Sekarang model WAJIB
    # pilih cluster PALING PAS dari 10 yang sudah ada (bukan bikin cluster baru), dan diminta
    # SEBAR ke cluster berbeda-beda (bukan semua nyasar ke 1-2 cluster saja) - efeknya: 1 sesi
    # generate ini otomatis jadi kumpulan artikel terstruktur lintas angle, bukan varian long-
    # tail generik semua, mendekati semangat "1 topik -> beberapa artikel bersudut beda" tanpa
    # perlu subsistem baru terpisah.
    cluster_list = ", ".join(f'"{c}"' for c in CLUSTER_ANGLE.keys())
    prompt = (
        f"Kamu ahli SEO untuk penginapan di kawasan Bedugul, Bali. Sudah ada {len(existing_kw)} "
        f"keyword yang tercatat. Buat {n} ide keyword BARU (belum ada di daftar), gaya pencarian "
        "orang Indonesia asli (bukan terjemahan kaku), fokus penginapan/wisata Bedugul - variasi "
        "kombinasi tipe akomodasi + lokasi/fasilitas/aktivitas/harga yang BELUM ada polanya. "
        f"SEBARKAN ke cluster yang BERBEDA-BEDA (jangan semua ke cluster yang sama) dari daftar "
        f"ini: {cluster_list}.\n\n"
        # (2026-08-03, permintaan Agus - bug nyata: keyword spt "penginapan pet friendly boleh "
        # bawa anjing" & "akomodasi dgn ruang meeting dan katering" sempat lolos jadi keyword,
        # artikelnya PUBLISH mengasumsikan fasilitas yg TIDAK PERNAH ada) - dicegah dari akar
        # di sini SEBELUM masuk pool sama sekali, bukan cuma mengandalkan Writer Agent/fact-
        # checker menangkapnya belakangan.
        "JANGAN buat keyword yang mengasumsikan/menyiratkan properti punya salah satu dari ini "
        "(properti TIDAK punya semuanya): menerima hewan peliharaan/pet-friendly, ruang meeting/"
        "katering untuk acara/corporate, sewa mobil/motor, jemput/antar bandara, paket trip/tur/"
        "wisata terorganisir (trekking/panen buah/city tour dst yang dijual properti), kolam "
        "renang/swimming pool (Pelangi maupun Harmoni sama-sama tidak punya).\n\n"
        # Intent Classifier (2026-08-02, PRD "AI Blog V2.0" modul 3, extends existing 200
        # seed keywords yang sudah punya klasifikasi asli - lihat catatan di bawah) - SEBELUM
        # ini SEMUA keyword hasil generate baru hardcode "Transactional" tanpa benar-benar
        # dianalisis (bug nyata ditemukan lewat audit: 38/38 keyword ai_generated 100%
        # Transactional, padahal 200 keyword seed awal punya variasi asli
        # 100 Transactional/60 Commercial/40 Informational - generator ini yang tidak pernah
        # ikut mengklasifikasi). Sekarang WAJIB klasifikasi tiap keyword ke SALAH SATU dari 3
        # kategori standar SEO (bukan 4 - "Navigational" tidak relevan utk niche ini, tidak
        # ada yang mencari nama brand spesifik yg belum dikenal): "Informational" (mencari
        # info/panduan, blm niat booking, mis. "itinerary 1 hari bedugul"), "Commercial"
        # (membandingkan pilihan sebelum memutuskan, mis. "cottage vs hotel bedugul mana lebih "
        # bagus"), "Transactional" (niat pesan/booking sekarang, mis. "booking cottage bedugul "
        # murah").\n\n"
        'Balas HARUS JSON valid array of object, format PERSIS: '
        f'[{{"keyword":"...","intent":"Informational"|"Commercial"|"Transactional","cluster":{cluster_list}}}, ...] '
        "- TIDAK ADA teks lain di luar JSON array itu."
    )
    raw = await _chat(
        "Kamu SEO keyword researcher yang teliti, tidak pernah mengarang tempat/fasilitas fiktif. "
        "Balas HANYA JSON valid, tidak ada markdown code fence atau teks pembuka/penutup.",
        prompt,
    )
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
    except json.JSONDecodeError:
        parsed = []
    candidates = [(c.get("keyword", "").strip(),
                   c.get("intent") if c.get("intent") in ("Informational", "Commercial", "Transactional") else "Transactional",
                   c.get("cluster") if c.get("cluster") in CLUSTER_ANGLE else "Long Tail")
                  for c in parsed if isinstance(c, dict) and c.get("keyword", "").strip()]

    if not candidates:
        return
    cand_texts = [c[0] for c in candidates]
    cand_embeds = await _embed(cand_texts)
    existing_embeds = await _embed(existing_texts) if existing_texts else []

    now = datetime.now(timezone.utc).isoformat()
    accepted = 0
    for (cand, cand_intent, cand_cluster), cand_emb in zip(candidates, cand_embeds):
        is_dupe = any(_cosine(cand_emb, e) > 0.88 for e in existing_embeds)
        if is_dupe:
            continue
        await db.seo_keywords.update_one(
            {"site": site, "keyword": cand},
            {"$setOnInsert": {
                "id": str(uuid.uuid4()), "site": site, "keyword": cand, "cluster": cand_cluster,
                "intent": cand_intent, "priority": "Medium", "musiman": False,
                "status": "belum_dibuat", "artikel_slug": None, "source": "ai_generated",
                "created_at": now, "updated_at": now,
            }},
            upsert=True,
        )
        accepted += 1
    print(f"  [keyword agent] {accepted}/{len(candidates)} keyword baru diterima (sisanya duplikat semantik)")


# ---------------------------------------------------------------------------
# 2. Grounding - fakta ASLI dari CMS, supaya Writer Agent tidak mengarang
# ---------------------------------------------------------------------------
# Fakta area Bedugul (2026-07-29, permintaan user via revisi manual - "data spesifik yang
# membuat artikel terasa kredibel") - DIVERIFIKASI via web search 2026-07-29 ke beberapa
# sumber (Wikipedia + situs travel Bali), BUKAN ditebak/dihafal dari training data. Angka
# dibulatkan ke rentang yang konsisten di semua sumber (bukan angka presisi palsu). SAMA
# utk kedua situs (fakta geografis area, bukan klaim spesifik milik properti).
BEDUGUL_FACTS = (
    "Ketinggian kawasan Bedugul: sekitar 1.200-1.500 mdpl. Suhu udara rata-rata: sekitar "
    "17-24°C (lebih sejuk dibanding Bali selatan). Jarak dari Bandara Ngurah Rai: sekitar "
    "63-65 km, kira-kira 1,5-2 jam berkendara tergantung lalu lintas."
)
# Fakta jarak/waktu ANTAR landmark wisata spesifik (2026-07-30, revisi manual user artikel
# Handara Gate - butuh jarak/waktu SPESIFIK dari kawasan Bedugul, bukan cuma "dekat").
# Diverifikasi via web search 2026-07-30, sama disiplinnya dgn BEDUGUL_FACTS di atas - bukan
# ditebak dari training data, angka dibulatkan ke rentang konsisten antar sumber.
LANDMARK_FACTS = (
    "Jarak Handara Gate (Bali Handara Iconic Gate) dari kawasan Danau Beratan/Candikuning "
    "(area yang sama dgn lokasi Pelangi Homestay): sekitar 7 km, kira-kira 20 menit "
    "berkendara. Waktu terbaik kunjungi Handara Gate utk foto tanpa antre panjang: pagi "
    "06.00-09.00 WITA (sebelum jam 8 cahaya masih bagus & belum ramai) ATAU sore "
    "16.00-18.00 WITA - HINDARI sekitar jam 12 siang (paling ramai, banyak antre gantian "
    "foto). Hari kerja jauh lebih sepi drpd akhir pekan. Di Danau Beratan tersedia "
    "penyewaan sampan/perahu dayung & sepeda bebek air utk berkeliling danau (harga "
    "dibayar on-site langsung ke penyedia, BUKAN bagian dari layanan properti - jangan "
    "sebut harga pasti krn bisa berubah)."
)
# Jumlah kamar FISIK total (2026-07-29, dicek manual ke database PMS - CMS web-pelangi
# sendiri cuma simpan jumlah TIPE kamar (2 utk pelangi), bukan jumlah kamar fisik) - update
# manual angka ini kalau jumlah kamar di PMS berubah (jarang, bukan data yang perlu live-sync).
SITE_ROOM_COUNT = {"pelangi": 18, "harmoni": 5}


def _maps_url_from_embed(map_embed: str) -> Optional[str]:
    """External Link Agent (2026-07-31, PRD "AI Blog V2" Agus, modul 12 - sebelumnya TIDAK
    ADA sama sekali, cuma instruksi teks di editorial rule "sertakan link Maps kalau
    relevan" yg mengandalkan LLM menebak/mengingat link dari training data - risiko nyata
    link salah/halusinasi). `db.site_content.type=site.mapEmbed` SUDAH ADA per situs
    (dipakai iframe kontak), diubah di sini jadi link yang bisa diklik tamu & dijamin
    BENAR krn diambil dari data asli, bukan ditulis ulang oleh model. Dukung 2 format
    embed yang ada di data: (a) format "pb=" dgn koordinat+Place ID (Pelangi & Harmoni
    versi baru), (b) format "?q=Nama+Tempat" polos (fallback situs yg belum py koordinat)."""
    if not map_embed:
        return None
    m_lat = re.search(r"!3d(-?[\d.]+)", map_embed)
    m_lng = re.search(r"!2d(-?[\d.]+)", map_embed)
    m_place = re.search(r"!1s(0x[0-9a-f]+%3A0x[0-9a-f]+)", map_embed)
    if m_lat and m_lng:
        url = f"https://www.google.com/maps/search/?api=1&query={m_lat.group(1)},{m_lng.group(1)}"
        if m_place:
            url += f"&query_place_id={m_place.group(1).replace('%3A', ':')}"
        return url
    m_q = re.search(r"[?&]q=([^&]+)", map_embed)
    if m_q:
        return f"https://www.google.com/maps/search/?api=1&query={unquote(m_q.group(1))}"
    return None


async def _maps_url_for_site(site: str) -> Optional[str]:
    site_doc = (await db.site_content.find_one({"site": site, "type": "site"}) or {}).get("data", {})
    return _maps_url_from_embed(site_doc.get("mapEmbed", ""))


LANDMARK_FACT_MAX_AGE_DAYS = 30


async def refresh_landmark_facts(name: str, source_url: Optional[str] = None) -> dict:
    """Freshness check fakta landmark eksternal (2026-08-03, permintaan Agus, Feature 1
    PRD Tahap 2 - "fact-check ke sumber resmi utk data yang mudah berubah: harga tiket,
    jam buka, kontak"). SENGAJA TIDAK auto-cari/tebak URL resmi landmark (mis. Kebun Raya
    Bedugul, Ulun Danu Beratan) - salah pilih sumber (situs tidak resmi/kadaluarsa) lebih
    berbahaya drpd tidak ada data sama sekali, sama prinsipnya dgn "jangan mengarang lebih
    baik dari mengarang salah" yang sudah dipegang di seluruh file ini. `source_url` WAJIB
    diisi eksplisit oleh staf/owner (via endpoint admin, lihat server.py) - fungsi ini
    CUMA crawl url yang SUDAH dikonfirmasi asli, bukan menebak sendiri.

    Pakai scraping yang SUDAH ADA (_fetch_competitor_page - httpx+BeautifulSoup, gratis,
    tanpa API berbayar baru) - BUKAN Firecrawl, krn kapasitas yang sama (ambil teks halaman)
    sudah tercapai tanpa dependency baru, kecuali nanti ketahuan situs tertentu butuh
    render JavaScript yang scraping ini tidak bisa (belum ada bukti itu terjadi)."""
    if source_url is None:
        existing = await db.landmark_sources.find_one({"name": name})
        if not existing or not existing.get("source_url"):
            return {"ok": False, "error": f'Belum ada source_url utk landmark "{name}" - isi dulu via /admin/landmark-sources'}
        source_url = existing["source_url"]
    try:
        page = await _fetch_competitor_page(source_url)
    except Exception as e:
        return {"ok": False, "error": f"Gagal crawl {source_url}: {type(e).__name__}: {e}"}
    raw_text = page.get("headings", [])
    now = datetime.now(timezone.utc).isoformat()
    await db.landmark_facts.update_one(
        {"name": name},
        {"$set": {
            "name": name, "source_url": source_url, "last_crawled": now,
            "headings": raw_text, "word_count": page.get("word_count", 0),
        }},
        upsert=True,
    )
    await db.landmark_sources.update_one(
        {"name": name}, {"$set": {"name": name, "source_url": source_url}}, upsert=True,
    )
    return {"ok": True, "name": name, "last_crawled": now, "headings_sample": raw_text[:10]}


async def _landmark_facts_block() -> str:
    """Dipanggil oleh _fetch_site_facts di bawah - kumpulkan fakta landmark yang SUDAH
    di-crawl (db.landmark_facts, diisi via refresh_landmark_facts di atas) jadi 1 blok
    teks dgn SUMBER & TANGGAL CRAWL eksplisit disebut (2026-08-03, permintaan Agus -
    "Source Citation": tiap fakta wajib source_url + last_crawled + confidence). Kosong
    kalau belum ada landmark yang di-crawl sama sekali (jujur - belum aktif sampai
    staf/owner isi source_url pertama via endpoint admin)."""
    entries = await db.landmark_facts.find({}).to_list(50)
    if not entries:
        return ""
    lines = []
    for e in entries:
        age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(e["last_crawled"])).days
        confidence = "masih segar" if age_days < LANDMARK_FACT_MAX_AGE_DAYS else f"SUDAH {age_days} hari, mungkin basi - verifikasi manual dulu kalau dipakai"
        heading_text = "; ".join(e.get("headings", [])[:8])
        lines.append(
            f"- {e['name']} (sumber: {e['source_url']}, di-crawl {e['last_crawled'][:10]}, "
            f"{confidence}): {heading_text}"
        )
    return (
        "\n\nFAKTA LANDMARK DARI SUMBER EKSTERNAL (di-crawl dari situs asli, BUKAN dari "
        "training data - kalau ada info harga/jam buka spesifik di sini, itu LEBIH "
        "TERPERCAYA drpd asumsi umum, TAPI kalau ditandai 'mungkin basi', WAJIB frasakan "
        "sbg perkiraan/sarankan cek ulang, jangan sebut sbg pasti):\n" + "\n".join(lines)
    )


async def _fetch_site_facts(site: str) -> str:
    site_doc = (await db.site_content.find_one({"site": site, "type": "site"}) or {}).get("data", {})
    rooms_doc = (await db.site_content.find_one({"site": site, "type": "rooms"}) or {}).get("data", [])
    faqs_doc = (await db.site_content.find_one({"site": site, "type": "faqs"}) or {}).get("data", [])
    testimonials_doc = (await db.site_content.find_one({"site": site, "type": "testimonials"}) or {}).get("data", [])

    lines = [
        f"Nama brand: {site_doc.get('brand', '')}",
        f"Alamat: {site_doc.get('address', '')}",
        f"WhatsApp: {site_doc.get('whatsappDisplay', '')}",
        f"Total kamar tersedia: {SITE_ROOM_COUNT.get(site, '-')} kamar",
        f"Fakta area Bedugul (boleh dikutip - ini fakta geografis umum area, BUKAN klaim "
        f"khusus milik properti ini): {BEDUGUL_FACTS}",
        f"Fakta jarak & waktu kunjungan landmark wisata sekitar (boleh dikutip, fakta publik "
        f"area, BUKAN milik properti): {LANDMARK_FACTS}",
        # (2026-08-03, permintaan Agus - bug nyata: artikel terbit yg mengklaim pet-friendly/
        # ruang meeting yg TIDAK PERNAH ada) - fasilitas/layanan yg SERING diasumsikan hotel
        # pada umumnya tapi properti INI TIDAK PUNYA, WAJIB ditegaskan eksplisit di sini (bukan
        # cuma "diam" soal itu) - kalau cuma diam, model/keyword generator bisa menganggap
        # topik itu netral & tetap menulis artikel yang MENGASUMSIKAN properti punya fasilitas
        # itu (spt yg sudah terjadi). fact_check() pakai fungsi yg SAMA (satu sumber kebenaran,
        # lihat komentar di atas), jadi larangan ini otomatis juga jadi jaring pengaman kalau
        # instruksi prompt Writer Agent (lihat write_article) tetap dilanggar.
        "FASILITAS/LAYANAN YANG TIDAK KAMI SEDIAKAN (JANGAN PERNAH tulis artikel yang "
        "mengklaim/mengasumsikan salah satu ini tersedia, walau keyword-nya menyiratkan "
        "begitu - kalau keyword secara eksplisit minta topik ini, jawab jujur TIDAK "
        "tersedia atau alihkan ke sudut pandang lain yang relevan, JANGAN menulis seolah "
        "tersedia): TIDAK menerima hewan peliharaan/pet (anjing/kucing/dst) dalam bentuk "
        "apa pun; TIDAK ada ruang meeting/rapat dan TIDAK ada layanan katering/catering "
        "makanan untuk acara; TIDAK menyewakan mobil maupun motor; TIDAK ada layanan "
        "jemput/antar bandara; TIDAK ada paket trip/tur/wisata (mis. paket trekking, paket "
        "panen buah, city tour) yang dijual/diselenggarakan properti; TIDAK ada kolam "
        "renang (baik Pelangi Homestay maupun Harmoni Hills, kedua properti SAMA-SAMA "
        "tidak punya kolam renang) - properti hanya "
        "menyediakan penginapan, tamu atur sendiri aktivitas wisata di luar.",
        "KAPASITAS ROMBONGAN (fakta ASLI, boleh dikutip): properti BISA menerima rombongan "
        "dengan kapasitas total sekitar 30-50 orang (gabungan beberapa kamar) - boleh "
        "disebutkan sbg fasilitas nyata, TAPI jangan campur dgn klaim ruang meeting/katering "
        "di atas (rombongan menginap biasa, bukan fasilitas acara/venue).",
    ]
    # Link Maps ASLI (2026-07-31, bug nyata ditemukan lewat tes gpt-5-mini) - write_article()
    # sudah dikasih link ini via external_block (lihat _maps_url_for_site), tapi fact_check()
    # SEBELUM ini pakai fungsi INI (_fetch_site_facts) sbg DATA ASLI-nya - tanpa link di sini,
    # model yang BENAR mengutip koordinat/place_id asli dari external_block malah ditolak
    # fact-checker sbg "klaim tidak didukung" (fact-checker tidak tahu data itu ASLI). Satu
    # sumber kebenaran sekarang - baik prompt Writer maupun fact-checker baca dari sini.
    maps_url_site = _maps_url_from_embed(site_doc.get("mapEmbed", ""))
    if maps_url_site:
        lines.append(f"Link Google Maps ASLI properti ini (boleh dikutip persis, termasuk koordinat/place_id di dalamnya): {maps_url_site}")
    landmark_block = await _landmark_facts_block()
    if landmark_block:
        lines.append(landmark_block)
    for r in rooms_doc:
        # Day Use & Menginap SENGAJA dipisah (2026-07-29, revisi manual user menemukan Day
        # Use disebut-sebut di artikel tapi TIDAK PERNAH dijelaskan harga/jamnya krn memang
        # tidak pernah ada di data ini sebelumnya) - priceFromDayUse baru ditambahkan ke CMS.
        lines.append(
            f"Tipe kamar: {r.get('name')} | ukuran {r.get('size')} | kapasitas {r.get('capacity')} | "
            f"harga Menginap mulai {r.get('priceFrom')}/malam | harga Day Use (6 jam) mulai "
            f"{r.get('priceFromDayUse', '-')} | fasilitas: {', '.join(r.get('facilities', []))}"
        )
    for f in faqs_doc:
        lines.append(f"FAQ - {f.get('q')}: {f.get('a')}")
    if testimonials_doc:
        # SEMUA testimoni ASLI disediakan, bukan cuma testimonials_doc[0] (2026-07-30, bug
        # nyata ditemukan: sebelumnya SELALU cuma testimoni pertama yang dikirim ke Writer
        # Agent, jadi SEMUA artikel yang pernah kutip testimoni pasti kutip "Rina & Aldo" yang
        # sama persis - itu sendiri jadi konten berulang di seluruh blog, masalah yang sama
        # dgn duplicate-content yang sedang diperbaiki). Kutip PALING BANYAK 1 yang paling
        # relevan per artikel (lihat instruksi system prompt), JANGAN semua sekaligus.
        quotes = "; ".join(
            f"\"{t.get('text')}\" - {t.get('name')}, {t.get('origin')}" for t in testimonials_doc
        )
        lines.append(
            f"Testimoni tamu asli (pilih SATU yang paling relevan dgn topik artikel ini utk "
            f"dikutip, JANGAN pakai lebih dari satu, JANGAN selalu pilih yang pertama): {quotes}"
        )
    return "\n".join(lines)


# Editorial Knowledge Base (2026-07-29, permintaan user) - aturan editorial permanen yang
# bisa diedit staf via CMS (db.editorial_rules, 1 dokumen shared - bukan per-situs, krn
# standar sama utk Pelangi & Harmoni), BUKAN cuma hardcode di system prompt. Meniru pola
# guardrail_rules yang sudah terbukti jalan di ai-chat-bot (server.py punya endpoint
# GET/PUT-nya jg, seed default SAMA PERSIS - satu sumber kebenaran, jangan diubah salah
# satu tanpa yang lain).
DEFAULT_EDITORIAL_RULES = [
    "Selalu sertakan link Google Maps kalau relevan (lokasi/arah ke tempat)",
    "Selalu tampilkan harga dalam Rupiah kalau datanya tersedia, jangan pernah mengarang angka",
    "Selalu tutup artikel dengan bagian FAQ",
    "Selalu selipkan 1-2 link internal natural ke artikel lain yang relevan",
    "Hindari judul/pembuka clickbait - klaim harus bisa dibuktikan isi artikel",
    "Gunakan tone konsisten: hangat, jujur, seperti penulis travel berpengalaman - bukan iklan",
    # Ditambahkan 2026-07-29 (Editorial Standard v2, permintaan user)
    "Artikel harus menjawab pertanyaan lanjutan yang wajar muncul - pembaca tidak perlu kembali ke Google cari info tambahan",
    "Prioritaskan detail lokal spesifik dari data asli (nama fasilitas, kebijakan, jarak/rute asli) - hindari generalisasi umum yang bisa ditemukan di web manapun",
    "Cuaca/iklim: hanya pola umum sepanjang tahun, JANGAN tulis ramalan cuaca atau kondisi hari ini",
    "Sisipkan itinerary/budget/checklist/waktu terbaik berkunjung HANYA kalau relevan dgn keyword-nya, jangan dipaksakan ke semua artikel",
]


async def _fetch_editorial_rules() -> list:
    doc = await db.editorial_rules.find_one({"_id": "singleton"})
    return doc["rules"] if doc else DEFAULT_EDITORIAL_RULES


# Freshness Check (2026-07-29, roadmap AI Grow item 4) - HANYA cek data KITA SENDIRI
# (harga kamar di CMS site_content, punya field `updated_at` yang bisa dipercaya),
# BUKAN pantau perubahan pihak ketiga (cafe baru buka/objek wisata tutup) - itu butuh
# sumber data eksternal yang tidak reliabel diverifikasi otomatis utk skala 2 properti
# ini (disarankan jadi reminder manual triwulanan ke staf, bukan sistem monitoring
# otomatis - lihat diskusi roadmap 2026-07-29). Artikel yang MENYEBUT harga ("Rp") tapi
# diterbitkan SEBELUM data rooms terakhir diubah = kandidat perlu ditinjau ulang - staf
# yang putuskan, TIDAK auto-update kontennya (beda dari expand_top_articles yang memang
# sengaja auto-rewrite, freshness ini lebih ke deteksi risiko, bukan aksi otomatis).
async def cek_artikel_basi(site: str) -> list:
    rooms_doc = await db.site_content.find_one({"site": site, "type": "rooms"})
    if not rooms_doc or not rooms_doc.get("updated_at"):
        return []
    rooms_updated_at = rooms_doc["updated_at"]
    stale = []
    async for post in db.blog_posts.find(
        {"site": site, "published": True, "created_at": {"$lt": rooms_updated_at}},
        {"slug": 1, "title": 1, "content": 1, "created_at": 1},
    ):
        if "rp" in post["content"].lower():
            stale.append({
                "slug": post["slug"], "title": post["title"], "created_at": post["created_at"],
            })
    return stale


# Cakupan Rencana Keyword per Cluster (2026-07-29, roadmap AI Grow item 5, versi jujur) -
# BUKAN "topical authority" beneran (itu perlu data kompetitif skala besar yang mahal utk
# diukur akurat, dibahas & ditolak di roadmap krn budget Serper mepet) - ini murni %
# keyword per cluster yang SUDAH ditulis dari rencana 100 keyword awal, dihitung dari data
# yang sudah ada tanpa API tambahan. Label sengaja "cakupan rencana keyword", bukan
# "topical authority", supaya tidak mengklaim lebih dari yang sebenarnya diukur.
async def cakupan_keyword_per_cluster(site: str) -> list:
    pipeline = [
        {"$match": {"site": site}},
        {"$group": {
            "_id": "$cluster",
            "total": {"$sum": 1},
            "sudah_dibuat": {"$sum": {"$cond": [{"$eq": ["$status", "sudah_dibuat"]}, 1, 0]}},
        }},
    ]
    result = []
    async for row in db.seo_keywords.aggregate(pipeline):
        total = row["total"]
        sudah = row["sudah_dibuat"]
        result.append({
            "cluster": row["_id"], "total": total, "sudah_dibuat": sudah,
            "persen": round(sudah / total * 100) if total else 0,
        })
    result.sort(key=lambda r: r["persen"])
    return result


# Bobot estimasi internal (2026-08-03, permintaan Agus - "Editorial Intelligence
# Dashboard") - SENGAJA BUKAN data volume pencarian/nilai booking asli (tidak ada API
# berbayar utk itu, sama seperti keterbatasan yang sudah didokumentasikan di seluruh
# file ini) - ini murni bobot kualitatif dari KARAKTER masing-masing cluster (lihat
# CLUSTER_ANGLE) supaya owner dapat SINYAL AWAL cluster mana yang layak diprioritaskan,
# BUKAN angka presisi palsu yang kelihatan meyakinkan padahal karangan (persis jenis
# "AI Slop angka" yang sudah berkali-kali dihindari di proyek ini). Selalu ditimpa oleh
# data GSC ASLI kalau cluster itu sudah punya traffic tercatat (lihat cakupan_editorial_
# lengkap di bawah) - heuristik ini CUMA fallback utk cluster yang belum ada data nyata
# sama sekali (situs baru/cluster baru).
CLUSTER_TRAFFIC_HEURISTIK = {
    "Harga": 4, "Lokasi Wisata": 4, "Aktivitas": 3, "Utama": 3, "Keluarga": 3,
    "Pasangan": 3, "Fasilitas": 3, "View": 2, "Booking": 2, "Long Tail": 2,
}
CLUSTER_BOOKING_HEURISTIK = {
    "Booking": 5, "Harga": 5, "Keluarga": 4, "Pasangan": 4, "Long Tail": 4,
    "Fasilitas": 3, "Utama": 3, "Aktivitas": 2, "Lokasi Wisata": 2, "View": 2,
}


def _status_prioritas(persen: int) -> tuple:
    """Badge status per cluster (2026-08-03, permintaan Agus) - ambang SAMA dgn contoh
    yang diminta langsung: 0-20 Sangat Kurang, 20-40 Perlu Ditingkatkan, 40-70 Cukup,
    70-90 Hampir Lengkap, 100 Selesai."""
    if persen >= 100:
        return ("✅", "Selesai")
    if persen >= 70:
        return ("🟢", "Hampir Lengkap")
    if persen >= 40:
        return ("🟡", "Cukup")
    if persen >= 20:
        return ("🟠", "Perlu Ditingkatkan")
    return ("🔴", "Sangat Kurang")


_BLOG_LINK_RE = re.compile(r"\[([^\]]+)\]\(/blog/([a-z0-9-]+)\)")


async def cakupan_editorial_lengkap(site: str) -> dict:
    """Editorial Coverage Dashboard (2026-08-03, permintaan Agus - versi lengkap dari
    cakupan_keyword_per_cluster di atas, TIDAK menggantikannya krn fungsi lama masih
    dipakai tempat lain). Sengaja dinamai "Cakupan Editorial/Keyword", BUKAN "Topical
    Authority" (sudah jadi prinsip proyek ini sejak awal - lihat catatan di fungsi lama)
    - owner sempat minta ini ditegaskan lagi, jadi label di sini & di frontend
    konsisten hindari istilah itu.

    Tujuan: dashboard ini harus bisa jawab 5 pertanyaan (persis permintaan owner):
    1) sudah berapa artikel -> `sudah_dibuat`/`total_sudah`
    2) masih kurang berapa -> `sisa`/`total_sisa`
    3) keyword berikutnya -> `belum_ditulis` (list) & `rekomendasi_hari_ini`
    4) kenapa dipilih -> `alasan` per item rekomendasi (dihitung dari sinyal ASLI:
       priority manual, musim, demand GSC - SAMA PERSIS logika get_next_keyword,
       bukan penjelasan karangan setelah fakta)
    5) kapan cluster dianggap selesai -> "selesai" didefinisikan jujur sbg 100% dari
       keyword yang MASIH BISA ditulis di cluster itu (`total_efektif` = sudah_dibuat +
       belum_dibuat + draft, SENGAJA TIDAK menghitung `dilewati_mirip` - ditemukan lewat
       audit data nyata: cluster "Harga" Harmoni 14/16 keyword-nya ternyata sudah
       di-skip permanen krn dianggap duplikat topik yang sama, cuma 2 yang genuinely
       ditulis/bisa ditulis - kalau dihitung dari 16, persennya kelihatan "Sangat Kurang"
       padahal SEBENARNYA cluster itu nyaris tuntas dari keyword yang memang layak
       ditulis. Menghitung skip permanen sbg "belum dikerjakan" itu sendiri bentuk
       ketidakjujuran angka yang coba dihindari proyek ini).
    """
    demand = await _cluster_demand_scores(site)  # {cluster: impression GSC ASLI}

    # Breakdown status PER cluster (2026-08-03, ganti dari cakupan_keyword_per_cluster
    # yang cuma tahu total & sudah_dibuat - lihat catatan "selesai" di atas kenapa
    # dilewati_mirip WAJIB dipisah, bukan ikut dihitung sbg "belum").
    status_rows: Dict[str, Dict[str, int]] = {}
    async for row in db.seo_keywords.aggregate([
        {"$match": {"site": site}},
        {"$group": {"_id": {"cluster": "$cluster", "status": "$status"}, "n": {"$sum": 1}}},
    ]):
        cluster = row["_id"]["cluster"]
        status_rows.setdefault(cluster, {}).update({row["_id"]["status"]: row["n"]})

    # Keyword "belum_dibuat" per cluster, sekalian ambil priority utk sortir & bahan
    # rekomendasi - 1 query, dikelompokkan di Python (jumlah row kecil, <1000).
    belum_docs = await db.seo_keywords.find(
        {"site": site, "status": "belum_dibuat"},
        {"_id": 0, "keyword": 1, "cluster": 1, "priority": 1, "musiman": 1},
    ).to_list(2000)
    order_prio = {"High": 0, "Medium": 1, "Low": 2}
    belum_by_cluster: Dict[str, list] = {}
    for k in belum_docs:
        belum_by_cluster.setdefault(k["cluster"], []).append(k)
    for lst in belum_by_cluster.values():
        lst.sort(key=lambda k: order_prio.get(k.get("priority"), 9))

    # Internal link network per cluster (2026-08-03) - link internal TIDAK disimpan
    # terstruktur (cuma markdown di dalam content), jadi diekstrak di sini dgn regex
    # yang SAMA persis pola yang dipakai _inject_links/_internal_links_valid (format
    # link internal SELALU "[label](/blog/slug)") - bukan data baru, cuma dibaca ulang
    # dari yang sudah ada, supaya owner lihat jaringan artikel per cluster tanpa perlu
    # sistem pelacakan baru. Cluster tiap artikel di-JOIN lewat `seo_keyword` (keyword
    # ASLI yang dipakai menulis, tersimpan apa adanya di blog_posts) -> db.seo_keywords -
    # BUKAN reverse-lookup dari `category` (dicoba dulu, TERBUKTI salah: CLUSTER_CATEGORY
    # itu many-to-one, mis. Harga/Keluarga/Pasangan/Booking/Fasilitas SEMUA sama-sama
    # "Tips", reverse-lookup asal ambil cluster PERTAMA yg cocok kategori - hasil ditemukan
    # salah atribusi lewat tes langsung sebelum kode ini dikirim).
    keyword_to_cluster = {
        k["keyword"]: k["cluster"] for k in await db.seo_keywords.find(
            {"site": site}, {"_id": 0, "keyword": 1, "cluster": 1},
        ).to_list(3000)
    }
    posts = await db.blog_posts.find(
        {"site": site, "published": True}, {"_id": 0, "slug": 1, "title": 1, "seo_keyword": 1, "content": 1},
    ).to_list(1000)
    slug_to_title = {p["slug"]: p["title"] for p in posts}
    links_by_cluster: Dict[str, list] = {}
    for p in posts:
        cluster_match = keyword_to_cluster.get(p.get("seo_keyword"))
        found = _BLOG_LINK_RE.findall(p.get("content") or "")
        if found:
            targets = [{"slug": slug, "title": slug_to_title.get(slug, label)} for label, slug in found if slug in slug_to_title]
            if targets:
                links_by_cluster.setdefault(cluster_match or "Lainnya", []).append({
                    "from_title": p["title"], "from_slug": p["slug"], "targets": targets,
                })

    clusters_out = []
    for cluster, statuses in status_rows.items():
        sudah = statuses.get("sudah_dibuat", 0)
        belum = statuses.get("belum_dibuat", 0)
        draft = statuses.get("draft", 0)
        dilewati = statuses.get("dilewati_mirip", 0)
        total_efektif = sudah + belum + draft
        persen = round(sudah / total_efektif * 100) if total_efektif else (100 if dilewati else 0)
        emoji, label_status = _status_prioritas(persen)
        gsc_impressions = demand.get(cluster)
        clusters_out.append({
            "cluster": cluster,
            "total": total_efektif,
            "sudah_dibuat": sudah,
            "sisa": belum + draft,
            "dilewati_mirip": dilewati,
            "persen": persen,
            "status_emoji": emoji,
            "status_label": label_status,
            "belum_ditulis": [
                {"keyword": k["keyword"], "priority": k.get("priority"), "musiman": bool(k.get("musiman"))}
                for k in belum_by_cluster.get(cluster, [])[:10]
            ],
            "traffic_level": None if gsc_impressions else CLUSTER_TRAFFIC_HEURISTIK.get(cluster, 3),
            "traffic_gsc_impressions": gsc_impressions,
            "booking_level": CLUSTER_BOOKING_HEURISTIK.get(cluster, 3),
            "internal_links": links_by_cluster.get(cluster, [])[:8],
        })
    clusters_out.sort(key=lambda c: c["persen"])

    total_sudah = sum(c["sudah_dibuat"] for c in clusters_out)
    total_all = sum(c["total"] for c in clusters_out)
    berdata = [c for c in clusters_out if c["total"] > 0]
    terlemah = min(berdata, key=lambda c: c["persen"])["cluster"] if berdata else None
    terkuat = max(berdata, key=lambda c: c["persen"])["cluster"] if berdata else None

    # Rekomendasi hari ini (2026-08-03) - REUSE persis logika get_next_keyword (priority
    # -> musim -> demand GSC), bukan aturan terpisah/kedua yang bisa menyimpang dari
    # urutan nyata yang benar-benar dipakai AI menulis. Diambil 3 kandidat teratas dari
    # SEMUA cluster gabungan (bukan cuma 1 cluster) - alasan per item ditentukan dari
    # sinyal MANA yang sebenarnya paling menentukan skor kandidat itu.
    musim_aktif = _musim_mendekat()
    semua_belum = sorted(
        belum_docs,
        key=lambda k: (
            order_prio.get(k.get("priority"), 9),
            0 if (musim_aktif and k.get("musiman")) else 1,
            -demand.get(k.get("cluster"), 0),
        ),
    )
    rekomendasi = []
    for k in semua_belum[:3]:
        cluster = k["cluster"]
        cluster_row = next((c for c in clusters_out if c["cluster"] == cluster), None)
        if k.get("priority") == "High":
            alasan = f"Prioritas High (ditandai manual) & cluster {cluster} baru {cluster_row['persen'] if cluster_row else '?'}%."
        elif musim_aktif and k.get("musiman"):
            alasan = f"Musiman - sedang mendekati \"{musim_aktif}\"."
        elif demand.get(cluster):
            alasan = f"Cluster {cluster} terbukti dapat {demand[cluster]} impression nyata dari Google Search Console."
        elif cluster_row and cluster_row["persen"] < 40:
            alasan = f"Cluster {cluster} masih {cluster_row['persen']}% - termasuk yang paling lemah."
        else:
            alasan = f"Berikutnya dalam antrian cluster {cluster}."
        rekomendasi.append({"keyword": k["keyword"], "cluster": cluster, "alasan": alasan})

    insight = []
    if terlemah:
        lemah_row = next(c for c in clusters_out if c["cluster"] == terlemah)
        insight.append(f"Cluster {terlemah} masih paling lemah ({lemah_row['persen']}%, sisa {lemah_row['sisa']} artikel).")
    if terkuat and terkuat != terlemah:
        kuat_row = next(c for c in clusters_out if c["cluster"] == terkuat)
        insight.append(f"Cluster {terkuat} paling lengkap ({kuat_row['persen']}%).")
    hampir_selesai = [c["cluster"] for c in clusters_out if 70 <= c["persen"] < 100]
    if hampir_selesai:
        insight.append(f"{', '.join(hampir_selesai)} sudah hampir lengkap (70-90%).")
    if terlemah:
        insight.append(f"Disarankan fokus ke cluster {terlemah} selama beberapa hari ke depan.")

    return {
        "clusters": clusters_out,
        "total_sudah": total_sudah,
        "total_sisa": total_all - total_sudah,
        "total_target": total_all,
        "persen_keseluruhan": round(total_sudah / total_all * 100) if total_all else 0,
        "cluster_terlemah": terlemah,
        "cluster_terkuat": terkuat,
        "insight": insight,
        "rekomendasi_hari_ini": rekomendasi,
    }


# ---------------------------------------------------------------------------
# 2.5 Competitor Analysis Agent (2026-07-28) - cari artikel top-ranking Google utk
# keyword yang sama, analisis panjang/struktur heading/FAQ, supaya Writer Agent
# bisa menulis artikel yang LEBIH LENGKAP daripada kompetitor (bukan cuma sama
# panjang). Best-effort penuh: kalau search API/fetch kompetitor gagal (quota
# habis, situs kompetitor block scraping, dll), fungsi ini return None dan
# write_article() lanjut TANPA analisis kompetitor - tidak pernah menggagalkan
# generate artikel gara-gara langkah tambahan ini.
#
# Pakai Serper (serper.dev), BUKAN Google Custom Search JSON API - dicoba lebih
# dulu tapi ternyata Google sudah menutup akses API itu utk project/customer baru
# (dikonfirmasi via web search, ada rencana deprecation penuh 2027), gagal terus
# walau enable API + billing sudah benar. Serper reseller hasil Google Search asli
# dgn API sederhana, jauh lebih murah & tanpa syarat billing GCP.
#
# Budget kredit (2026-07-28, permintaan user) - user cuma punya 2400 kredit Serper
# SEKALI PAKAI (bukan kuota bulanan yang reset), diminta dijaga bertahan 2 tahun,
# TERLEPAS dari berapa pun volume artikel (naik dari 6/hari ke 14/hari - 7 situs x
# 2 - per permintaan user 2026-07-28, kemungkinan naik lagi ke depan). Cap 3
# kredit/hari (BUKAN 3 dari total artikel per hari, tapi hard limit harian yang
# SAMA berapa pun jumlah artikel) cukup utk 730 hari (2190 dari 2400 kredit, sisa
# buffer 210) - di volume 14/hari, ~21% artikel dapat analisis kompetitor; kalau
# naik ke 20+/hari, proporsinya makin kecil tapi kredit tetap bertahan 2 tahun sama
# persis (lihat perhitungan yg sudah dijelaskan ke user). Artikel yang tidak
# kebagian slot TETAP ditulis normal TANPA analisis kompetitor (bukan gagal, cuma
# skip - graceful degradation yang sama seperti kalau API down).
SERPER_TOTAL_CREDITS = 2400
SERPER_TARGET_DAYS = 2 * 365
SERPER_DAILY_CAP = SERPER_TOTAL_CREDITS // SERPER_TARGET_DAYS  # = 3/hari


async def _serper_budget_ok() -> bool:
    """Cek & catat pemakaian kredit Serper hari ini - return False (skip search,
    HEMAT kredit) kalau cap harian ATAU total kredit sudah tercapai. Disimpan di
    db.serper_usage (1 dokumen per situs+tanggal via upsert $inc, atomic)."""
    today = datetime.now(timezone.utc).date().isoformat()
    total_used = 0
    async for doc in db.serper_usage.find({}, {"_id": 0, "count": 1}):
        total_used += doc.get("count", 0)
    if total_used >= SERPER_TOTAL_CREDITS:
        return False
    today_doc = await db.serper_usage.find_one({"date": today})
    if today_doc and today_doc.get("count", 0) >= SERPER_DAILY_CAP:
        return False
    await db.serper_usage.update_one(
        {"date": today}, {"$inc": {"count": 1}}, upsert=True,
    )
    return True


async def _search_competitors(keyword: str) -> list:
    if not SERPER_API_KEY:
        return []
    if not await _serper_budget_ok():
        return []
    async with httpx.AsyncClient(timeout=15) as http:
        resp = await http.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": keyword, "num": 5, "gl": "id", "hl": "id"},
        )
        resp.raise_for_status()
        return resp.json().get("organic", [])


async def _fetch_competitor_page(url: str) -> dict:
    # Timeout pendek (10s) & User-Agent browser biasa - banyak situs block request
    # tanpa User-Agent yang wajar. Kegagalan per-URL (timeout/403/dll) DIBIARKAN
    # naik ke caller supaya bisa di-skip satu-satu (bukan menggagalkan semua).
    async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (compatible; PelangiSeoAgent/1.0)"
    }) as http:
        resp = await http.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        word_count = len(text.split())
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]
        return {"url": url, "word_count": word_count, "headings": headings[:15]}


# OTA/booking besar yang beroperasi di Indonesia (2026-07-29, permintaan user - "tingkat
# persaingan kata kunci") - dipakai sbg sinyal proxy, BUKAN skor "Keyword Difficulty"
# presisi ala Ahrefs/SEMrush (itu butuh data backlink/domain authority berbayar yang tidak
# kita punya aksesnya). Kalau salah satu domain besar ini muncul di hasil pencarian nyata
# utk sebuah keyword, itu sinyal kuat situs kecil kita akan sulit menembus halaman 1.
MAJOR_OTA_DOMAINS = {
    "booking.com", "traveloka.com", "agoda.com", "tripadvisor.com", "tripadvisor.co.id",
    "trivago.co.id", "trivago.com", "airbnb.com", "tiket.com", "pegipegi.com",
    "expedia.com", "hotels.com", "klook.com", "nusatrip.com", "oyorooms.com", "oyo.com",
    "reddoorz.com",
}


def _klasifikasi_persaingan(urls: list) -> str:
    """"Tinggi" kalau ada OTA besar (lihat MAJOR_OTA_DOMAINS) di hasil pencarian nyata utk
    keyword ini - sinyal kuat sulit ditembus. "Rendah" kalau kompetitor yang ditemukan
    SANGAT SEDIKIT (<=1) - sinyal keyword yang jarang dibahas siapa pun. Selain itu
    "Sedang" (bukan default diam-diam tanpa dasar - murni krn tidak terdeteksi sinyal
    tinggi maupun rendah dari data yang ada)."""
    if len(urls) <= 1:
        return "Rendah"
    for url in urls:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        if any(ota in domain for ota in MAJOR_OTA_DOMAINS):
            return "Tinggi"
    return "Sedang"


COMPETITOR_CACHE_MAX_AGE_DAYS = 30


async def analyze_competitors(keyword: str, site: Optional[str] = None) -> Optional[dict]:
    """Cache-first wrapper (2026-08-03, permintaan Agus - "jangan crawl tiap kali, simpan
    ke database, refresh cuma kalau kedaluwarsa >30 hari atau owner minta refresh") -
    SEBELUM ini analisis kompetitor SELALU live tiap generate_one() dipanggil (dibatasi
    jatah Serper harian, tapi tetap konsumsi kredit tiap kali walau keyword yang sama
    baru saja dianalisis kemarin). Sekarang dicek db.competitor_cache dulu - kalau ada
    entri utk keyword ini & umurnya < 30 hari, dipakai ulang TANPA panggil Serper/fetch
    sama sekali (hemat kredit, bukan cuma hemat waktu). `site` opsional (utk content gap
    detection di bawah - lihat _content_gap_topics) - kalau tidak diisi, gap detection
    dilewati (tetap kompatibel dgn caller lama yang belum kirim `site`).
    Return TETAP sama persis shape-nya spt sebelumnya (prompt_text + data) supaya semua
    caller existing (write_article, CmsBlog "competitor_analysis" tersimpan) tidak perlu
    berubah - field baru (`from_cache`, `content_gap`) cuma tambahan di `data`, bukan
    breaking change."""
    cached = await db.competitor_cache.find_one({"keyword": keyword})
    if cached:
        cached_at = datetime.fromisoformat(cached["data"]["analyzed_at"])
        age_days = (datetime.now(timezone.utc) - cached_at).days
        if age_days < COMPETITOR_CACHE_MAX_AGE_DAYS:
            data = dict(cached["data"])
            data["from_cache"] = True
            data["cache_age_days"] = age_days
            if site:
                data["content_gap"] = await _content_gap_topics(site, data)
            return {"prompt_text": cached["prompt_text"], "data": data}

    result = await _analyze_competitors_live(keyword)
    if result is None:
        return result
    await db.competitor_cache.update_one(
        {"keyword": keyword},
        {"$set": {"keyword": keyword, "prompt_text": result["prompt_text"], "data": result["data"]}},
        upsert=True,
    )
    result["data"]["from_cache"] = False
    if site:
        result["data"]["content_gap"] = await _content_gap_topics(site, result["data"])
    return result


async def refresh_competitor_cache(keyword: str) -> Optional[dict]:
    """Refresh manual (2026-08-03) - permintaan Agus "owner bisa minta refresh" - buang
    entri lama, panggil live lagi, timpa cache. Dipakai endpoint admin (lihat server.py)."""
    await db.competitor_cache.delete_one({"keyword": keyword})
    return await analyze_competitors(keyword)


async def _content_gap_topics(site: str, competitor_data: dict) -> list:
    """Content Gap Detection (2026-08-03, permintaan Agus, Feature 1 PRD Tahap 2) -
    bandingkan heading/topik kompetitor (data yang SUDAH di-crawl, bukan panggilan baru)
    terhadap JUDUL semua artikel kita sendiri di situs ini - heading kompetitor yang tidak
    ada kata kuncinya di judul artikel manapun milik kita ditandai sbg "belum dibahas".
    SENGAJA heuristik sederhana (cocok kata kunci signifikan, bukan NLP topic-modeling
    berat) - cukup utk sinyal awal "ini mungkin lubang konten", staf/AI yang menilai
    relevansinya, BUKAN klaim pasti "topik ini pasti harus ditulis"."""
    headings = competitor_data.get("competitors", [])
    all_headings = [h for c in headings for h in c.get("headings", [])]
    if not all_headings:
        return []
    our_titles = " ".join(
        p["title"].lower() for p in await db.blog_posts.find(
            {"site": site, "published": True}, {"_id": 0, "title": 1},
        ).to_list(1000)
    )
    STOPWORDS = {
        "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "atau", "ini", "itu", "apa",
        "bagaimana", "kenapa", "kapan", "adalah", "saja", "juga", "bisa", "tidak", "ada",
        "bedugul", "hotel", "penginapan", "villa", "cottage", "homestay",
    }
    gap = []
    seen = set()
    for h in all_headings:
        words = [w for w in re.findall(r"[a-z]+", h.lower()) if w not in STOPWORDS and len(w) > 3]
        if len(words) < 2:
            continue
        # Heading dianggap "sudah dibahas" kalau MAYORITAS kata signifikannya muncul di
        # judul artikel kita manapun (bukan wajib semua kata - beda urutan/imbuhan wajar).
        hits = sum(1 for w in words if w in our_titles)
        if hits / len(words) < 0.5 and h.strip().lower() not in seen:
            seen.add(h.strip().lower())
            gap.append(h.strip())
    return gap[:8]


async def _analyze_competitors_live(keyword: str) -> Optional[dict]:
    """Isi asli analyze_competitors (2026-07-28) - dipisah jadi fungsi privat 2026-08-03
    supaya bisa dibungkus cache di atas tanpa mengubah logika analisis itu sendiri."""
    try:
        results = await _search_competitors(keyword)
    except Exception as e:
        print(f"[competitor-analysis] search gagal: {type(e).__name__}: {e}")
        return None
    if not results:
        return None

    pages = []
    for item in results[:5]:
        link = item.get("link")
        if not link:
            continue
        try:
            pages.append(await _fetch_competitor_page(link))
        except Exception:
            continue  # 1 kompetitor gagal di-fetch bukan masalah, lanjut yang lain

    if not pages:
        return None

    avg_words = round(sum(p["word_count"] for p in pages) / len(pages))
    all_headings = [h for p in pages for h in p["headings"]]
    sample_headings = all_headings[:20]

    # Pertanyaan nyata dari kompetitor (2026-07-28) - dicoba dulu Serper "peopleAlsoAsk"
    # utk sumber FAQ berbasis pertanyaan yang benar-benar sering dicari, tapi dites 3
    # query berbeda (semua terkait Bedugul/hotel lokal) dan field itu TIDAK PERNAH ada di
    # respons - kemungkinan krn Google cuma munculkan kotak "People Also Ask" utk query
    # bervolume tinggi, sedangkan keyword long-tail lokal kita rata-rata tidak memicunya.
    # Ganti sumber: heading H2/H3 kompetitor yang sudah di-scrape di atas SERINGKALI
    # sudah berbentuk pertanyaan (pola umum blog travel Indonesia) - itu tetap data nyata
    # (bukan karangan AI), jadi dipakai sbg kandidat FAQ prioritas di prompt Writer Agent.
    question_headings = []
    seen_q = set()
    for h in all_headings:
        h_stripped = h.strip()
        if h_stripped.endswith("?") and h_stripped.lower() not in seen_q:
            seen_q.add(h_stripped.lower())
            question_headings.append(h_stripped)
    question_headings = question_headings[:8]

    lines = [
        f"{len(pages)} artikel kompetitor teratas ditemukan untuk keyword ini, rata-rata "
        f"panjang {avg_words} kata.",
        "Contoh sub-judul/topik yang mereka bahas (jangan ditiru kata-per-kata, tapi "
        "pastikan artikelmu MENCAKUP topik senada + tambahkan yang belum mereka bahas):",
    ]
    for h in sample_headings:
        lines.append(f"- {h}")
    lines.append(
        f"Tulis artikel MINIMAL sepanjang rata-rata kompetitor ({avg_words} kata) dan "
        "usahakan lebih lengkap (bahas 1-2 topik relevan yang tidak ada di daftar di atas)."
    )
    if question_headings:
        lines.append(
            "\nPERTANYAAN NYATA dari kompetitor (dipakai orang lain sbg sub-judul, bukan "
            "karangan) - prioritaskan ini utk bagian FAQ kalau relevan & bisa dijawab jujur "
            "dari DATA ASLI di atas, boleh diparafrase agar natural, JANGAN dipaksakan kalau "
            "tidak relevan/tidak bisa dijawab akurat untuk properti ini:"
        )
        for q in question_headings:
            lines.append(f"- {q}")

    return {
        "prompt_text": "\n".join(lines),
        "data": {
            "keyword": keyword,
            "competitors": [{"url": p["url"], "word_count": p["word_count"], "headings": p["headings"]} for p in pages],
            "avg_word_count": avg_words,
            "question_headings": question_headings,
            "tingkat_persaingan": _klasifikasi_persaingan([p["url"] for p in pages]),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# 3. Writer Agent
# ---------------------------------------------------------------------------
async def write_article(site: str, keyword_doc: dict, link_candidates: Optional[list] = None,
                         sibling_collision: Optional[dict] = None) -> dict:
    facts = await _fetch_site_facts(site)
    keyword = keyword_doc["keyword"]
    competitor_result = await analyze_competitors(keyword, site=site)
    maps_url = await _maps_url_for_site(site)

    # Editorial Writing Standard (2026-07-28, permintaan user, diringkas dari pedoman
    # panjang yang diberikan) - target BUKAN "supaya tidak terdeteksi AI detector"
    # (tidak pernah jadi tujuan di sistem ini sejak awal), tapi standar editorial
    # riil: akurat, dapat diverifikasi, jujur soal ketidakpastian, enak dibaca manusia.
    # Prinsip anti-mengarang di paragraf 2 SUDAH ada sejak awal - bagian BARU murni
    # soal gaya tulisan (variasi kalimat, hindari frasa generik AI, direct/aktif).
    system = (
        "Kamu editor konten profesional Bahasa Indonesia untuk penginapan di Bedugul, Bali - "
        "bukan sekadar 'menulis artikel', tapi menghasilkan konten yang akurat, jujur, dan "
        "enak dibaca seperti ditulis penulis berpengalaman.\n\n"
        "ATURAN KERAS SOAL FAKTA: HANYA gunakan fakta yang diberikan di 'DATA ASLI' - JANGAN PERNAH "
        "mengarang fasilitas, harga, kebijakan, statistik, atau nama tempat yang tidak disebutkan di "
        "sana atau tidak umum diketahui publik (mis. nama tempat wisata terkenal boleh, tapi jangan "
        "mengarang klaim spesifik soal tempat itu - jam buka, harga tiket, dll kalau tidak yakin). "
        "Kalau ragu suatu fakta, jangan disebutkan sama sekali daripada mengarang. Jangan mengarang "
        "pengalaman pribadi/kunjungan yang tidak pernah terjadi.\n\n"
        "GAYA TULISAN: Tulis natural, variasikan panjang kalimat & struktur paragraf (jangan semua "
        "paragraf polanya sama), gunakan kalimat aktif, bahasa yang mudah dipahami. Sapaan 'Kakak' "
        "MAKSIMAL 5-7 kali di SELURUH artikel (2026-07-29, revisi manual user - sebelumnya muncul "
        ">15 kali/artikel, terasa dipaksakan) - variasikan dgn 'kamu'/'tamu'/langsung tanpa sapaan "
        "di kalimat lain (2026-08-04, revisi PRD AI Blog v2.0 - 'kamu' bukan 'Anda', target pembaca "
        "traveler 25-40 tahun yang cari info santai, bukan korespondensi formal). Paragraf pendek "
        "(2-5 kalimat), setiap paragraf punya tujuan jelas - jangan "
        "bertele-tele atau mengulang poin yang sama. HINDARI frasa generik/klise seperti 'di era "
        "digital ini', 'tidak dapat dipungkiri', 'perlu diketahui bahwa', 'pada dasarnya', "
        "'kesimpulannya', 'udara sejuk yang menyegarkan', 'nyaman dan menyenangkan', 'kenyamanan "
        "maksimal', 'tanpa harus khawatir', atau daftar 'pertama...kedua...selain itu...oleh karena "
        "itu' yang kaku - pakai transisi yang mengalir sesuai konteks. GANTI pujian generik dgn "
        "detail SPESIFIK: alih-alih 'udara sejuk yang menyegarkan', tulis mis. 'suhu 17-24°C yang "
        "bikin selimut terasa pas di malam hari' (pakai angka dari DATA ASLI/fakta area kalau ada). "
        "Tidak keyword stuffing - keyword masuk natural, prioritaskan kenyamanan baca. BATASI kata "
        "'menghadirkan', 'memberikan', 'menawarkan', 'memanjakan' MAKSIMAL 2 kali TOTAL di seluruh "
        "artikel (2026-07-31, ditemukan lewat pengecekan otomatis - kata ini sering dipakai berulang "
        "jadi terasa seperti template AI generik) - ganti dgn kata kerja/kalimat aktif yang lebih "
        "spesifik, mis. bukan 'kamar ini menawarkan pemandangan gunung' tapi 'dari jendela kamar, "
        "pegunungan terlihat jelas setiap pagi'.\n\n"
        "SEBELUM MENJAWAB, cek draftmu sendiri: apakah ada kalimat yang berulang-ulang? Apakah "
        "pembuka menarik & penutup memberi nilai tambah (bukan cuma ringkasan)? Apakah tiap sub-judul "
        "benar-benar menjawab pertanyaan yang relevan? WAJIB HITUNG LITERAL: berapa kali kata "
        "'menghadirkan', 'memberikan', 'menawarkan', 'memanjakan' masing-masing muncul di draftmu "
        "(hitung satu-satu, jangan menebak) - kalau ADA yang lebih dari 2 kali, ganti kelebihannya "
        "sebelum kirim (2026-08-01, ditemukan lewat data nyata: instruksi batas 2x di atas SERING "
        "dilanggar tanpa penghitungan eksplisit ini, artikel jadi tertolak sistem quality gate). "
        "Kalau ada yang kurang dari semua pengecekan ini, revisi dulu sebelum kirim. "
        "TAMBAHAN (2026-08-04, PRD AI Blog v2.0): apakah paragraf pembuka BENAR-BENAR tidak "
        "menyebut nama properti? Apakah dari 6 sub-judul, MAYORITAS (4-5) benar-benar tentang "
        "topik/destinasi, bukan tentang properti? Apakah properti hanya disebut di 1-2 sub-judul "
        "saja (bukan di semua)? Apakah ada harga/suhu/jarak/kapasitas yang kamu tulis LEBIH dari "
        "sekali dgn angka yang sama? Kalau ADA salah satu yang jawabannya tidak sesuai target, "
        "revisi dulu.\n\n"
        # Editorial Standard v2 (2026-07-29, permintaan user) - target artikel jadi "halaman
        # referensi terbaik utk topik ini", bukan sekadar berhasil masuk index Google. Ditulis
        # sbg MENU pilihan (bukan wajib semua di tiap artikel) krn tidak semua elemen relevan
        # utk tiap keyword - mis. keyword "harga kamar cottage" tidak butuh itinerary, tapi
        # keyword "liburan ke bedugul" cocok. Model yang menilai relevansi per keyword, bukan
        # dipaksa checklist kaku (konsisten dgn ALUR yg sudah ada: PERSIS 6 sub-judul, topiknya
        # model yang pilih - menu ini cuma memperluas PILIHAN topik yg tersedia).
        "NILAI UNIK (pilih yang RELEVAN dgn keyword ini, isi ke 1-2 dari 6 sub-judul, JANGAN "
        "paksakan semua ke satu artikel): itinerary/contoh rencana kunjungan singkat, estimasi "
        "budget total (kamar + makan + aktivitas, dari DATA ASLI - jangan mengarang harga "
        "makanan/aktivitas yang tidak ada di data), checklist barang bawaan, waktu terbaik "
        "berkunjung (musim/jam/hari), perbandingan (mis. tipe kamar) KALAU keyword memang "
        "membandingkan sesuatu. Soal CUACA: HANYA pola iklim UMUM yang selalu benar sepanjang "
        "tahun (mis. \"Bedugul dataran tinggi, umumnya sejuk & kadang berkabut\") - JANGAN "
        "PERNAH menulis cuaca/suhu HARI INI atau ramalan cuaca, itu akan langsung basi & bisa "
        "salah total begitu dibaca kapan pun setelah ditulis.\n\n"
        "PENGALAMAN LOKAL SPESIFIK: hindari generalisasi yang bisa ditemukan di web mana pun "
        "(\"Bali terkenal dengan keindahan alamnya\") - prioritaskan detail SPESIFIK dari DATA "
        "ASLI (nama fasilitas asli, kebijakan asli, jarak/rute asli) yang membuat artikel ini "
        "beda dari kompetitor, bukan cuma versi lain dari artikel yang sama.\n\n"
        # Anti-duplicate-content (2026-07-29, revisi manual user - masalah TERBESAR yang
        # ditemukan: 3 artikel isinya hampir identik krn semua menjelaskan ulang SEMUA
        # kebijakan/fasilitas/pembayaran dgn kalimat beda tipis - Google anggap ini duplicate
        # content, bisa menurunkan ranking SEMUA artikel terkait sekaligus). ANGLE_BLOCK di
        # bawah (diisi per cluster keyword ini) memberi FOKUS BERBEDA tiap cluster - WAJIB
        # diikuti, bukan cuma saran.
        # Brand Voice (2026-08-03, PRD "AI Blog v3 Content Differentiation Engine") - SELALU
        # disuntik (bukan cuma saat tabrakan) supaya nada tiap situs konsisten sejak awal.
        f"KARAKTER BRAND (WAJIB, situs \"{site}\"): {SITE_PERSONA.get(site, '')}\n\n"
        # Cross-brand collision (2026-08-03) - HANYA muncul kalau _cross_brand_collision di
        # generate_one() menemukan brand seberang sudah menulis topik mirip di cluster yang
        # sama. Beri tahu Writer Agent SECARA EKSPLISIT judul artikel seberang supaya bisa
        # benar-benar menghindarinya, bukan cuma diminta "beda" secara abstrak.
        + (
            f"TABRAKAN KEYWORD LINTAS BRAND (WAJIB DIPERHATIKAN): situs \"{sibling_collision['site']}\" "
            f"sudah menulis artikel dgn topik SANGAT MIRIP keyword ini, judulnya: "
            f"\"{sibling_collision['title']}\". JANGAN tulis artikel dgn sudut pandang/fokus yang "
            f"sama seperti itu - WAJIB ambil angle BERBEDA sesuai KARAKTER BRAND situs \"{site}\" di "
            "atas (kalau situs ini Pelangi, fokus budget/keluarga/backpacker/value; kalau Harmoni, "
            "fokus honeymoon/private/romantis/premium) supaya kedua artikel benar-benar melayani "
            "pembaca dgn kebutuhan berbeda, bukan 2 versi dari artikel yang sama.\n\n"
            if sibling_collision else ""
        ) +
        f"FOKUS ARTIKEL INI (WAJIB diikuti, cluster \"{keyword_doc['cluster']}\"): "
        f"{CLUSTER_ANGLE.get(keyword_doc['cluster'], '')}\n\n"
        + ("" if keyword_doc["cluster"] in ("Booking", "Keluarga") else (
            "ATURAN TAMBAHAN krn cluster ini BUKAN Booking/Keluarga: JANGAN buat sub-judul apa "
            "pun yang isinya kebijakan/fasilitas umum (contoh judul yang DILARANG: 'Kemudahan "
            "Akses dan Fasilitas Pendukung Lainnya', 'Kebijakan Menginap', 'Fasilitas Pendukung', "
            "atau sejenisnya yang membahas parkir/jam check-in/check-out/kebijakan anak/metode "
            "pembayaran). Kalau salah satu topik itu MEMANG perlu disebut, selipkan sebagai "
            "MAKSIMAL 1 kalimat pendek di DALAM salah satu sub-judul FOKUS ARTIKEL (bukan "
            "sub-judul terpisah) - keenam sub-judul WAJIB seluruhnya tentang FOKUS ARTIKEL di "
            "atas, BUKAN kebijakan/fasilitas umum. Ini krn menjelaskan ulang kebijakan yang sama "
            "persis di SETIAP artikel adalah akar masalah duplicate content nyata yang harus "
            "dihindari.\n\n"
        )) +
        "CTA: tutup artikel dengan ajakan SPESIFIK & natural (mis. \"Tanya langsung ketersediaan "
        "kamar untuk tanggal liburan Kakak\"), BUKAN kalimat generik seperti \"Chat sekarang lewat "
        "WhatsApp\" saja. Muncul SATU KALI saja di penutup, jangan diulang di tengah artikel.\n\n"
        "TESTIMONI: kalau ada \"Testimoni tamu asli\" di DATA ASLI DAN relevan dgn topik artikel "
        "ini, boleh dikutip singkat sbg social proof - JANGAN PERNAH mengarang testimoni baru yang "
        "tidak ada di DATA ASLI. Kalau tidak ada testimoni yang benar-benar relevan dgn topik "
        "artikel ini, JANGAN dipaksakan masuk - lewati saja bagian ini.\n\n"
        # Rasio 70/30 & hook (2026-08-04, PRD "AI Blog Engine v2.0" §4.1 - permintaan Agus,
        # digabung dgn draft revisi prompt yang dikirim langsung) - instruksi di sini SELALU
        # dipasangkan dgn enforcement KODE (Gate 3 template intro, Gate 4 dominasi brand di
        # editor_review) krn sesi ini sudah 3x buktikan instruksi prompt saja tidak reliable
        # (bug multi-tipe kamar, janji eskalasi, jam kesiapan besok/lusa) - prompt di sini
        # bukan satu-satunya jaring pengaman, tapi tetap penting supaya draft PERTAMA sudah
        # cenderung benar (kurangi reject-&-retry, hemat biaya API).
        "PEMBACA DULU, PROPERTI BELAKANGAN: target ~70% isi artikel tentang TOPIK/DESTINASI "
        "(Bedugul, aktivitas, tempat wisata) dan ~30% tentang properti sbg opsi menginap - "
        f"pembaca yang TIDAK jadi booking {'Pelangi' if site == 'pelangi' else 'Harmoni'} tetap "
        "harus dapat nilai dari artikel ini. JANGAN sebut nama properti di paragraf pembuka - "
        "mulai dengan cerita/skenario pendek, pertanyaan yang bikin penasaran, fakta spesifik "
        "ttg Bedugul/destinasi, atau detail sensorik (suara, suhu, pemandangan, aroma) - BUKAN "
        "deskripsi properti/lokasi/\"Jika kata kunci Anda...\"/\"Artikel ini membahas...\". "
        "Properti baru boleh disebut mulai sub-judul kedua/ketiga dst, idealnya di 1 sub-judul "
        "khusus (\"X sbg opsi menginap\") yang ringkas, bukan disebut berulang di semua sub-judul.\n\n"
        # Penegasan angka pasti (2026-08-05, ditemukan lewat tes live sesudah ganti model
        # gpt-5-mini ke gpt-4.1-mini) - gate dominasi brand (ambang 35% paragraf utk intent
        # Informational/Commercial) jauh lebih sering menolak dgn model baru ini, terukur
        # 44-71% padahal instruksi target 70/30 di atas sudah ada sejak awal - gpt-4.1-mini
        # terbukti nyata cenderung menyebut nama properti jauh lebih sering per paragraf
        # drpd gpt-5-mini walau instruksinya sama persis. Angka pasti + peringatan "ditolak
        # otomatis" di bawah SENGAJA lebih tegas drpd instruksi "target 70/30" di atas,
        # supaya model menghitung sendiri sbg batas keras, bukan sekadar arahan gaya.
        "PENTING - BATAS KERAS PENYEBUTAN NAMA PROPERTI: draft ini akan DITOLAK OTOMATIS kalau "
        f"nama \"{'Pelangi' if site == 'pelangi' else 'Harmoni'}\"/\"{'Pelangi Homestay' if site == 'pelangi' else 'Harmoni Hills'}\" "
        "muncul di LEBIH DARI 1 dari SETIAP 3 paragraf (maks ~33%, target aman ~25% biar ada "
        "ruang). Sebelum menulis tiap paragraf baru selain bagian \"X sbg opsi menginap\", "
        "TANYA KE DIRI SENDIRI: paragraf ini WAJIB menyebut nama properti, atau bisa tetap "
        "membahas destinasi/aktivitas/tips tanpa menyebut nama sama sekali? Kalau bisa tanpa, "
        "JANGAN sebut nama - pakai kata ganti umum (\"penginapan ini\", \"tempat menginap\") "
        "HANYA kalau benar-benar perlu, atau lebih baik lanjut bahas topik tanpa referensi "
        "properti sama sekali di paragraf itu."
    )
    editorial_rules = await _fetch_editorial_rules()
    if editorial_rules:
        system += "\n\nATURAN EDITORIAL TAMBAHAN (wajib dipatuhi):\n" + "\n".join(f"- {r}" for r in editorial_rules)
    competitor_block = (
        f"\n\nANALISIS KOMPETITOR (dari hasil pencarian Google nyata):\n{competitor_result['prompt_text']}"
        if competitor_result else ""
    )
    # Content Gap (2026-08-03, permintaan Agus) - topik yang kompetitor bahas tapi BELUM
    # ada di artikel kita manapun (situs ini) - SARAN opsional, bukan wajib (model yang
    # nilai relevansi ke keyword spesifik ini, jangan dipaksa masuk kalau tidak nyambung).
    gap_topics = (competitor_result or {}).get("data", {}).get("content_gap") or []
    if gap_topics:
        competitor_block += (
            "\n\nCONTENT GAP (topik yang dibahas kompetitor tapi BELUM PERNAH ada di artikel "
            "kita manapun) - kalau RELEVAN dengan keyword ini, boleh disinggung singkat "
            "(bukan wajib, jangan dipaksakan kalau tidak nyambung/tidak bisa dijawab jujur "
            "dari DATA ASLI): " + "; ".join(gap_topics)
        )
    # Internal link SEBAGAI KONTEKS PENULISAN, bukan ditempel di akhir (2026-07-28,
    # perbaikan anchor text natural) - sebelumnya pick_internal_links() dipanggil SETELAH
    # write_article() lalu ditempel mekanis sbg "Baca juga: [Judul Asli] [Judul Asli]."
    # sebelum FAQ - anchor text-nya selalu judul mentah, bukan ditulis natural mengikuti
    # konteks kalimat. Sekarang kandidat link dikirim SEBELUM menulis supaya model bisa
    # menyelipkan 1-2 link itu sendiri di kalimat yang relevan dgn anchor text wajar.
    # _inject_links() di generate_one() tetap jadi JARING PENGAMAN (fallback list mekanis)
    # kalau ternyata model tidak menyelipkan satupun - linking tidak pernah 0.
    links_block = ""
    if link_candidates:
        cand_lines = "\n".join(f"- [{l['title']}](/blog/{l['slug']})" for l in link_candidates)
        links_block = (
            "\n\nARTIKEL LAIN YANG BISA DI-LINK (opsional, dari situs yang sama):\n"
            f"{cand_lines}\n"
            "Kalau ada kalimat di isi artikel yang relevan secara alami dengan salah satu "
            "artikel di atas, selipkan SEBAGAI LINK MARKDOWN di dalam kalimat itu sendiri "
            "(bukan daftar terpisah), pakai anchor text natural yang cocok dgn konteks "
            "kalimat (boleh beda dari judul asli di atas, tapi harus jujur mewakili isi "
            "tujuan link, contoh: '...seperti dibahas di [tips memilih kamar keluarga]"
            "(/blog/slug-asli)...'). Maksimal 1-2 link total, JANGAN dipaksakan kalau "
            "tidak ada kalimat yang cocok secara alami, JANGAN ubah path slug-nya."
        )
    external_block = ""
    if maps_url:
        external_block = (
            f"\n\nLINK GOOGLE MAPS ASLI properti ini (kalau artikel menyebut lokasi/arah/"
            f"rute ke properti, WAJIB pakai link INI - JANGAN menebak/mengingat link lain "
            f"dari pengetahuanmu sendiri, itu bisa salah): {maps_url}\n"
            "Selipkan sbg link markdown natural kalau relevan, mis. '...lokasinya bisa "
            "langsung dicek lewat [Google Maps](URL)...'. Tidak wajib dipakai kalau "
            "artikel ini memang tidak membahas lokasi/arah sama sekali."
        )
    user = f"""DATA ASLI ({site}):
{facts}
{competitor_block}
{links_block}
{external_block}

Tulis artikel SEO untuk target keyword: "{keyword}"

Format balasan HARUS JSON valid dengan struktur persis ini (tanpa markdown code fence):
{{
  "title": "judul menarik & natural, maks 60 karakter, keyword masuk alami (JANGAN sekadar deret kata kunci ditempel - itu keyword stuffing di judul)",
  "excerpt": "ringkasan 1-2 kalimat, maks 160 karakter",
  "content": "isi artikel WAJIB 900-1300 kata (ini batas keras, hitung sendiri sebelum menjawab - kalau draftmu kurang dari 900 kata, perpanjang tiap bagian dengan detail/contoh lebih dulu sebelum dikirim). Struktur WAJIB: 1 paragraf pembuka (~80-120 kata), lalu PERSIS 6 sub-judul **Sub Judul** (masing-masing paragraf tersendiri, tiap sub-judul diikuti isi 100-150 kata - JANGAN ada sub-judul dengan isi di bawah 100 kata), lalu WAJIB 4 FAQ di bagian akhir, ditutup 1 paragraf penutup singkat. Paragraf dipisah \\n\\n. UNTUK FAQ: kalau di atas ada daftar 'PERTANYAAN NYATA dari kompetitor', UTAMAKAN pertanyaan itu (boleh diparafrase, wajib tetap bisa dijawab jujur dari DATA ASLI) - baru tambahkan pertanyaan relevan lain kalau kurang dari 4 atau tidak ada yang cocok. KHUSUS kalau cluster keyword ini BUKAN Booking/Keluarga: dari 4 FAQ, MAKSIMAL 1 boleh soal kebijakan umum (check-in/check-out/parkir/anak/pembayaran) - MINIMAL 3 FAQ WAJIB pertanyaan yang relevan dgn FOKUS ARTIKEL INI (lihat instruksi FOKUS ARTIKEL di atas), supaya bagian FAQ tidak jadi salinan generik yang sama persis di semua artikel - ini kelanjutan aturan anti-duplicate-content yang sama. ATURAN FORMAT FAQ (WAJIB DIIKUTI PERSIS - HANYA SATU pola di bawah yang diterima sistem, format lain akan DITOLAK otomatis): tulis TEKS PERTANYAAN ASLI langsung di dalam **dua bintang**, TANPA prefix/label apa pun sebelum atau sesudahnya, lalu jawabannya di baris baru. Contoh PERSIS yang BENAR -> **Apakah sarapan sudah termasuk di kamar ini?**\\n\\nYa, sarapan sudah termasuk untuk 2 orang di semua tipe kamar. DILARANG KERAS semua pola berikut (SERING salah dipakai, WAJIB dihindari): (a) label 'Pertanyaan:'/'Q:'/'Question:' sebelum pertanyaan, mis. 'Q: Apakah ada parkir? A: Ya' - INI SALAH, (b) pertanyaan cuma pakai *tanda-bintang-tunggal* atau tanpa bintang sama sekali, (c) menjawab pertanyaan secara alami di dalam paragraf isi/sub-judul TANPA membuat blok FAQ terpisah di akhir artikel - itu TIDAK dihitung sebagai FAQ oleh sistem meski isinya relevan. WAJIB ada persis 4 blok terpisah di BAGIAN AKHIR artikel (setelah semua sub-judul, sebelum paragraf penutup) yang PERSIS mengikuti pola **pertanyaan?**\\n\\njawaban - JANGAN ada 'FAQ' sbg judul section terpisah, JANGAN duplikasi pertanyaan yang sudah dijawab natural di paragraf isi.",
  "tags": ["tag1", "tag2", "tag3"]
}}"""

    raw = await _chat(system, user, temperature=0.6)
    data = _parse_json_response(raw)

    # gpt-4.1-mini konsisten menulis lebih pendek dari target (~500-600 kata) apapun
    # instruksi jumlah kata di prompt awal - daripada terus-menerus gagal quality gate
    # & buang keyword, coba panggilan tambahan minta perpanjang tiap bagian (cuma kalau
    # memang masih kurang, supaya tidak selalu 2-3x biaya API per artikel).
    #
    # Threshold trigger dinaikkan dari <850 ke <1000 (2026-07-28, ditemukan lewat
    # laporan user - audit 19 artikel AI live menunjukkan banyak draft mendarat persis
    # di 850-988 kata, LOLOS trigger lama tanpa pernah diperpanjang, padahal masih di
    # bawah target riil user "di atas 1000 kata"). Target expand juga dinaikkan ke
    # 1050+ (bukan cuma "900-1300" yang sudah terbukti under-deliver sekali) supaya ada
    # buffer setelah _inject_links nambah sedikit kata link internal/WA nanti.
    #
    # Loop, BUKAN sekali (2026-07-28, ditemukan lewat tes live: 1 dari 3 percobaan
    # SETELAH fix di atas MASIH mendarat di bawah 1000 walau sudah 1x expand - LLM
    # tidak selalu tepat sasaran walau diminta eksplisit). Maks 2x percobaan expand
    # (3 panggilan API total per artikel di kasus terburuk) - berhenti lebih awal
    # begitu >=1000, supaya tidak selalu 3x biaya kalau expand pertama sudah cukup.
    word_count = len(data["content"].split())
    attempts = 0
    while word_count < 1000 and attempts < 2:
        attempts += 1
        expand_user = f"""Artikel ini masih terlalu pendek ({word_count} kata, target MINIMAL 1050 kata,
idealnya 1100-1300).
Tulis ULANG dengan struktur & fakta yang SAMA PERSIS, tapi perpanjang tiap sub-judul jadi
180-220 kata (tambah detail/contoh konkret dari DATA ASLI, JANGAN mengarang fakta baru).
Hitung sendiri jumlah kata draftmu sebelum menjawab - kalau masih di bawah 1050, perpanjang
lagi sebelum dikirim.
JSON artikel sebelumnya:
{json.dumps(data, ensure_ascii=False)}

Balas HARUS JSON valid struktur sama seperti sebelumnya (title, excerpt, content, tags)."""
        raw2 = await _chat(system, expand_user, temperature=0.6)
        try:
            data2 = _parse_json_response(raw2)
            new_count = len(data2["content"].split())
            if new_count > word_count:
                data = data2
                word_count = new_count
        except (json.JSONDecodeError, KeyError):
            break  # gagal expand - tetap pakai draft terbaik sejauh ini, hentikan loop
    # Disisipkan ke doc artikel oleh generate_one() (2026-07-28, permintaan user - tampil
    # di dashboard CMS "data kompetitor yang dibaca") - None kalau analisis di-skip/gagal.
    data["_competitor_data"] = competitor_result["data"] if competitor_result else None
    data["_maps_url"] = maps_url
    return data


def _parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


# ---------------------------------------------------------------------------
# 4. Internal Link Agent
# ---------------------------------------------------------------------------
# Entity Map ringan (2026-07-29, roadmap AI Grow item 2) - dievaluasi dulu: graph database
# (Neo4j dkk) itu solusi utk ribuan node dgn query multi-hop kompleks. Area Bedugul cuma
# ada ~15 entity nyata (danau, pura, kebun raya, dst) - graph DB jauh lebih rumit drpd
# masalahnya. Cukup dict statis kecil {entity: [entity terkait]}, dicocokkan ke KEYWORD
# (bukan cuma cluster) supaya internal-link candidate lebih tepat topical-nya - mis.
# keyword ttg "ulun danu" akan disarankan link ke artikel ttg "danau beratan" (kompleks
# yang sama), bukan cuma "artikel lain di cluster yang sama" spt sebelumnya.
ENTITY_MAP = {
    "danau beratan": ["ulun danu", "kebun raya", "candikuning"],
    "ulun danu": ["danau beratan", "candikuning"],
    "kebun raya": ["danau beratan", "candikuning", "strawberry"],
    "handara": ["kebun raya", "danau beratan"],
    "candikuning": ["danau beratan", "ulun danu", "kebun raya", "strawberry"],
    "strawberry": ["kebun raya", "candikuning"],
    "bedugul": ["danau beratan", "ulun danu", "kebun raya", "candikuning", "handara"],
}


def _entity_terkait(keyword: str) -> list:
    lower = keyword.lower()
    terkait = set()
    for entity, related in ENTITY_MAP.items():
        if entity in lower:
            terkait.update(related)
    return list(terkait)


async def pick_internal_links(site: str, cluster: str, keyword: str = "", exclude_slug: str = "") -> list:
    candidates = await db.blog_posts.find(
        {"site": site, "published": True, "slug": {"$ne": exclude_slug}},
        {"slug": 1, "title": 1, "category": 1, "seo_keyword": 1},
    ).sort("created_at", -1).to_list(50)

    # Entity match diprioritaskan DULUAN (lebih tepat topical drpd sekadar sesama cluster) -
    # cek apakah judul/keyword artikel lain menyebut entity yang TERKAIT dgn keyword ini.
    entity_pool = []
    if keyword:
        terkait = _entity_terkait(keyword)
        if terkait:
            entity_pool = [
                c for c in candidates
                if any(e in (c.get("title", "") + " " + (c.get("seo_keyword") or "")).lower() for e in terkait)
            ]

    same_category = [c for c in candidates if c["category"] == CLUSTER_CATEGORY.get(cluster)]
    # Gabung: entity match dulu, lalu isi sisanya dari same_category (dedup by slug),
    # fallback ke seluruh candidates kalau keduanya kurang dari 2.
    pool = entity_pool + [c for c in same_category if c["slug"] not in {e["slug"] for e in entity_pool}]
    if len(pool) < 2:
        pool = candidates
    # Rotasi (2026-08-04, PRD "AI Blog Engine v2.0" - "internal link selalu ke 1 artikel
    # sama") - SEBELUM ini `pool[:3]` deterministik, urutan ditentukan created_at DESC
    # yang dibawa dari query awal, jadi artikel PALING BARU di kategori/entity yang sama
    # selalu jadi target link untuk BERBULAN-BULAN sampai ada artikel lebih baru lagi -
    # link equity tidak tersebar. Entity match (paling relevan topical) tetap DIUTAMAKAN
    # (selalu masuk kalau ada, tidak ikut diacak keluar), tapi urutan PENGAMBILAN di dalam
    # tiap grup diacak tiap generate - dari banyak artikel, target link jadi bervariasi
    # alami tanpa perlu tracking counter/state baru.
    entity_slugs = {e["slug"] for e in entity_pool}
    entity_shuffled = entity_pool.copy()
    random.shuffle(entity_shuffled)
    sisa_shuffled = [c for c in pool if c["slug"] not in entity_slugs]
    random.shuffle(sisa_shuffled)
    return (entity_shuffled + sisa_shuffled)[:3]


def _normalize_faq_format(content: str) -> str:
    """Normalisasi format FAQ (2026-07-31, ditemukan lewat tes live gpt-5-mini) - model ini
    KONSISTEN menulis pertanyaan FAQ sbg baris polos tanpa **tebal** sama sekali (beda dari
    gpt-4.1-mini/gpt-4.1 yg patuh instruksi prompt aslinya), MESKIPUN instruksi format sudah
    dibuat sangat eksplisit + contoh negatif jelas di prompt - 3x percobaan nyata beda
    keyword/cluster semua gagal 0% patuh. Daripada terus memperkuat prompt yang terbukti
    tidak didengar model reasoning ini, normalisasi terjadi di SINI (post-process
    deterministik) - jauh lebih andal drpd berharap ke kepatuhan model.

    Deteksi: paragraf yang BARIS PERTAMANYA diakhiri '?' (ciri khas soal FAQ ditulis sbg
    baris tersendiri diikuti jawaban di baris berikutnya dlm paragraf yg sama) - dibungkus
    **tebal** kalau belum. Cukup aman diterapkan ke SELURUH artikel (bukan cuma bagian FAQ)
    krn paragraf prosa biasa nyaris tidak pernah berupa SATU baris pertanyaan berdiri
    sendiri diikuti baris baru dalam paragraf yg sama - itu pola KHAS Q&A, bukan kalimat
    retoris di tengah paragraf naratif (yg menyatu dgn kalimat lain di baris yg sama)."""
    paras = re.split(r"(\n\n+)", content)
    out = []
    for p in paras:
        lines = p.split("\n")
        first = lines[0].strip()
        if first.endswith("?") and not first.startswith("**") and not first.startswith("#") and 10 <= len(first) <= 200:
            lines[0] = f"**{first}**"
            p = "\n".join(lines)
        out.append(p)
    return "".join(out)


def _inject_links(content: str, links: list, wa_url: str, maps_url: Optional[str] = None) -> str:
    """Selipkan link booking WA (SELALU, bahkan kalau belum ada artikel lain utk
    disarankan - mis. situs baru) SEBELUM SELURUH bagian FAQ, bukan ditempel asal di
    akhir. Kerja di level daftar paragraf (bukan potong string mentah dgn regex posisi).

    2 bug nyata ditemukan & diperbaiki (2026-07-26) sebelum sempat live:
    (1) versi awal cuma cari pertanyaan **...?** PERTAMA - salah masuk DI TENGAH FAQ
    (antara pertanyaan 1 & 2). (2) versi kedua (whole-bold berakhir '?') malah kena
    subjudul H2 yang ditulis gaya pertanyaan (mis. "**Kenapa Memilih X?**" - gaya
    subjudul yang wajar & umum, BUKAN bagian FAQ) - salah deteksi sebagai awal FAQ.
    Sekarang: prioritaskan label eksplisit "**FAQ**" (case-insensitive) sebagai jangkar;
    kalau model tidak menulis label itu, fallback ke deteksi RUN minimal 2 paragraf
    **...?** BERTURUT-TURUT (satu subjudul-gaya-tanya yang berdiri sendiri, diikuti body
    text biasa, tidak akan pernah cocok - FAQ asli selalu berupa beberapa Q&A beruntun).

    Baca-juga mekanis DIHAPUS sbg jalur utama (2026-07-28, perbaikan anchor text natural)
    - write_article() sekarang dikasih kandidat link SEBELUM menulis supaya bisa
    menyelipkan link natural sendiri di dalam isi (lihat links_block di write_article).
    Fallback JARING PENGAMAN di bawah: kalau TIDAK SATUPUN slug kandidat ternyata muncul
    di isi (model mengabaikan instruksi), baru tempel daftar mekanis spt sebelumnya -
    supaya internal linking tidak pernah nol, cuma tidak jadi jalur utama lagi.

    `maps_url` (2026-07-31, External Link Agent) - jaring pengaman yang sama utk link Maps
    ASLI: kalau model tidak menyelipkan link itu sendiri (lihat external_block di
    write_article), tempel 1 baris di sini juga - supaya artikel yang membahas lokasi tidak
    pernah kehilangan link Maps yang benar sama sekali."""
    baca_juga = ""
    if links and not any(f"/blog/{l['slug']}" in content for l in links):
        link_lines = " ".join(f"[{l['title']}](/blog/{l['slug']})" for l in links)
        baca_juga = f"Baca juga: {link_lines}.\n\n"
    maps_line = ""
    if maps_url and maps_url not in content:
        maps_line = f"Lihat lokasi lengkap di [Google Maps]({maps_url}).\n\n"
    insert_para = f"{baca_juga}{maps_line}Siap booking? [Chat sekarang lewat WhatsApp]({wa_url})."

    paras = re.split(r"\n\n+", content)
    faq_label_idx = next((i for i, p in enumerate(paras) if p.strip().lower() == "**faq**"), None)

    if faq_label_idx is not None:
        faq_start = faq_label_idx
    else:
        is_question_para = [bool(re.match(r"^\*\*[^*]+\?\*\*\s*$", p.strip())) or bool(re.match(r"^\*\*[^*]+\?\*\*\n", p.strip())) for p in paras]
        faq_start = None
        for i in range(len(paras) - 1):
            if is_question_para[i] and is_question_para[i + 1]:
                faq_start = i
                break

    if faq_start is not None:
        paras.insert(faq_start, insert_para)
    else:
        paras.append(insert_para)
    return "\n\n".join(paras)


# ---------------------------------------------------------------------------
# 5. Schema Agent - SENGAJA TIDAK disimpan di sini. post_to_out() di server.py
# cuma meneruskan field tertentu (bukan passthrough dokumen mentah), jadi field
# baru di sini tidak akan pernah sampai ke API publik/frontend. Schema JSON-LD
# dibangun di BlogDetail.jsx langsung dari title/excerpt/content/slug/cover_image
# yang SUDAH tersedia lewat API yang ada - lihat perubahan BlogDetail.jsx.
# ---------------------------------------------------------------------------
# 6. Cover Image Agent
# ---------------------------------------------------------------------------
# Tempat wisata NYATA - foto ASLI yang sudah ada tetap dipakai (akurat & gratis),
# TIDAK di-generate ulang pakai AI biar tidak mengganti foto asli tempat publik yang
# sudah benar dengan versi buatan AI yang belum tentu mirip.
REAL_PLACE_ASSETS = {
    "ulun danu": "/assets/ulun-danu.webp", "pura": "/assets/ulun-danu.webp",
    "danau": "/assets/danau-beratan.webp", "beratan": "/assets/danau-beratan.webp",
    "kebun raya": "/assets/kebun-raya.webp", "handara": "/assets/handara-gate.webp",
    "candikuning": "/assets/pasar-candikuning.webp", "pasar": "/assets/pasar-candikuning.webp",
}

PEXELS_DIR = Path("/var/www/web-pelangi/frontend/public/assets/pexels")
PEXELS_DIR_BUILD = Path("/var/www/web-pelangi/frontend/build/assets/pexels")


async def _fetch_pexels_photo(cluster: str, keyword: str) -> bytes:
    """Ambil 1 foto stok GRATIS dari Pexels (2026-07-28, permintaan user - ganti generate AI
    berbayar dengan foto stok gratis utk artikel Pelangi). Query dipilih dari CLUSTER_PEXELS_QUERY
    (bukan keyword Indonesia mentah - Pexels cuma bagus dicari Bahasa Inggris), foto dipilih dari
    15 hasil teratas pakai hash keyword supaya variatif tapi tetap deterministik per keyword yang
    sama. Lisensi Pexels bebas pakai tanpa atribusi wajib (pexels.com/license)."""
    if not PEXELS_API_KEY:
        raise RuntimeError("PEXELS_API_KEY belum diisi di backend/.env")
    queries = CLUSTER_PEXELS_QUERY.get(cluster, CLUSTER_PEXELS_QUERY["Utama"])
    query = queries[hash(keyword) % len(queries)]
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 15, "orientation": "landscape"},
        )
        resp.raise_for_status()
        photos = resp.json().get("photos") or []
        if not photos:
            raise RuntimeError(f"Tidak ada hasil Pexels untuk query '{query}'")
        photo = photos[hash(keyword + cluster) % len(photos)]
        img_resp = await http.get(photo["src"]["large"])
        img_resp.raise_for_status()
        return img_resp.content


async def pick_cover_image(site: str, keyword: str, cluster: str, slug: str) -> str:
    """Foto tempat wisata nyata pakai aset asli (akurat, gratis). Selain itu, DIROTASI
    2:1 kebalikan dari sebelumnya (2026-07-28, permintaan user) - SEKARANG 2 dari 3
    artikel pakai foto stok GRATIS dari Pexels API (variasi lebih banyak, tetap gratis),
    1 dari 3 pakai foto aset asli properti yang sudah ada. Foto Pexels generik suasana
    tropis/pegunungan (bukan properti spesifik), jadi tidak diklaim sbg foto kamar/
    bangunan asli - sama alasannya dengan gaya ilustrasi AI yang dipakai sebelumnya."""
    kw = keyword.lower()
    for needle, path in REAL_PLACE_ASSETS.items():
        if needle in kw:
            return path

    generated_so_far = await db.blog_posts.count_documents({"site": site, "seo_keyword": {"$ne": None}})
    if generated_so_far % 3 == 2:  # 1 dari 3 -> aset asli
        pool = SITE_ASSETS.get(site, SHARED_ASSETS)
        return pool[hash(keyword) % len(pool)]

    try:
        img_bytes = await _fetch_pexels_photo(cluster, keyword)
    except Exception as e:
        print(f"  [image agent] gagal ambil foto Pexels, fallback ke aset asli: {e}")
        pool = SITE_ASSETS.get(site, SHARED_ASSETS)
        return pool[hash(keyword) % len(pool)]
    filename = f"{slug}.webp"
    PEXELS_DIR.mkdir(parents=True, exist_ok=True)
    webp_bytes = await _resize_to_webp(img_bytes)
    (PEXELS_DIR / filename).write_bytes(webp_bytes)
    if PEXELS_DIR_BUILD.parent.exists():
        PEXELS_DIR_BUILD.mkdir(parents=True, exist_ok=True)
        (PEXELS_DIR_BUILD / filename).write_bytes(webp_bytes)
    return f"/assets/pexels/{filename}"


async def _resize_to_webp(png_bytes: bytes, max_width: int = 1200, quality: int = 78) -> bytes:
    """gpt-image-2 balikin PNG ~3MB per gambar - jauh lebih besar dari aset situs lain
    (semua .webp) dan bisa rusak LCP/performa yang sudah dioptimasi (lihat kerja SSR
    sebelumnya). Resize + convert ke webp sama seperti alur upload SiteAssetInput.jsx."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png") as src, tempfile.NamedTemporaryFile(suffix=".webp") as dst:
        src.write(png_bytes)
        src.flush()
        proc = await asyncio.create_subprocess_exec(
            "convert", src.name, "-resize", f"{max_width}x", "-strip", f"{src.name}.resized.png",
        )
        await proc.wait()
        resized_path = f"{src.name}.resized.png"
        proc2 = await asyncio.create_subprocess_exec(
            "cwebp", "-q", str(quality), resized_path, "-o", dst.name,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await proc2.wait()
        os.remove(resized_path)
        return Path(dst.name).read_bytes()


# ---------------------------------------------------------------------------
# 7. Quality Gate - rule-based, BUKAN AI menilai AI
# ---------------------------------------------------------------------------
def quality_check(article: dict, content_with_links: str) -> list:
    problems = []
    word_count = len(content_with_links.split())
    if word_count < 600:
        problems.append(f"kurang dari 600 kata (dapat {word_count})")
    # Bug nyata ditemukan (2026-07-26): model kadang menulis placeholder literal
    # "**Pertanyaan?**" lalu pertanyaan aslinya di baris *italic* terpisah, bukan
    # pertanyaan asli LANGSUNG di dalam **...** seperti diminta prompt - regex ini
    # PERSIS menolak pola salah itu, bukan cuma cek "ada **...?**" secara longgar.
    if re.search(r"\*\*Pertanyaan\?\*\*", content_with_links):
        problems.append("format FAQ salah (pakai placeholder '**Pertanyaan?**' bukan pertanyaan asli di dalam **)")
    elif not re.search(r"\*\*[^*]+\?\*\*", content_with_links):
        problems.append("tidak ada FAQ (pola **pertanyaan asli?**)")
    if "](/blog/" not in content_with_links and "](https://wa.me" not in content_with_links:
        problems.append("tidak ada internal link/link booking")
    if not article.get("title") or len(article["title"]) > 100:
        problems.append("judul kosong/terlalu panjang")
    if not article.get("excerpt"):
        problems.append("excerpt kosong")
    return problems


async def _internal_links_valid(site: str, content: str) -> list:
    """Validasi DETERMINISTIK (2026-08-02, permintaan Agus - laporan link internal yang
    tidak bisa diklik): cek tiap link "[label](/blog/slug)" di konten benar-benar menunjuk
    ke artikel yang ASLI ADA & PUBLISHED di SITUS YANG SAMA. Bug nyata ditemukan lewat
    audit: 3 dari 112 link internal di seluruh blog ternyata mati - akar masalahnya model
    kadang menuliskan slug candidat link (dikasih via pick_internal_links) SEDIKIT beda
    dari string asli (typo/salah salin, atau ke variasi slug situs LAIN yang mirip - mis.
    artikel Harmoni menunjuk ke slug gaya Pelangi). Link itu SECARA TEKNIS tetap bisa
    diklik (elemen <a> asli, JANGAN disamakan dgn masalah rendering) - tapi mendarat di
    404, dari sudut pandang tamu awam terasa sama saja dgn "tidak bisa diklik". Sekarang
    dicek sebelum publish, sama seperti fact_check/editor_review - reject & requeue kalau
    ada link mati, JANGAN publish artikel dgn link 404 di dalamnya."""
    targets = set(re.findall(r"\]\(/blog/([^)]+)\)", content))
    if not targets:
        return []
    existing = await db.blog_posts.find(
        {"site": site, "slug": {"$in": list(targets)}}, {"slug": 1},
    ).to_list(len(targets))
    existing_slugs = {e["slug"] for e in existing}
    mati = sorted(targets - existing_slugs)
    return [f'link internal mati: /blog/{slug} (situs "{site}") tidak ditemukan/belum publish' for slug in mati]


# Intent Coverage Score (2026-07-29, roadmap AI Grow item 3) - checklist DETERMINISTIK
# (regex/keyword), BUKAN minta LLM menilai draftnya sendiri 0-100% - itu pola "AI menilai
# AI" yang sengaja DIHINDARI di Quality Gate sejak awal (lihat quality_check() - rule-
# based, bukan kebetulan). LLM yang diminta menilai tulisannya sendiri cenderung selalu
# bilang "sudah lengkap" walau sebenarnya belum, sama tidak reliable-nya dgn hallucination.
# Skor ini INFORMASIONAL (tampil di dashboard CMS utk staf), TIDAK memblokir publish -
# beda dari duplicate/stuffing di bawah yang memang genuine tanda kualitas buruk.
INTENT_PATTERNS = {
    "harga": r"rp\s?[\d.,]+|harga",
    "jam/check-in": r"jam\s?\d|check-?in|check-?out|wita|buka\s",
    "parkir": r"parkir",
    "maps/lokasi": r"google\.com/maps|maps\.app|peta\b|lokasi",
    "tips": r"\btips\b",
    "faq": r"\*\*[^*]+\?\*\*",
    "sekitar/nearby": r"dekat\b|sekitar\b|berjarak",
    "kontak/booking": r"wa\.me|whatsapp",
}


def intent_coverage_score(content: str) -> dict:
    lower = content.lower()
    tercakup, kurang = [], []
    for label, pattern in INTENT_PATTERNS.items():
        (tercakup if re.search(pattern, lower) else kurang).append(label)
    skor = round(len(tercakup) / len(INTENT_PATTERNS) * 100)
    return {"skor_persen": skor, "tercakup": tercakup, "kurang": kurang}


# AI Slop Detector (2026-07-31, PRD "AI Blog V2" Agus - modul 4/6) - SEBELUM ini, larangan
# frasa klise & instruksi variasi kalimat HANYA ada sbg teks di system prompt (lihat
# `write_article` di atas) - TIDAK ADA kode apa pun yang memverifikasi model benar-benar
# mematuhinya. Ini implementasi kode nyata pertama, dijadikan hard-block yg sama spt
# keyword-stuffing/duplicate-section di bawah (bukan cuma informasional) - kalau model
# mengabaikan instruksi prompt, publish sekarang DITOLAK, bukan lolos diam-diam.
SLOP_PHRASES_DILARANG = [
    "di era digital ini", "tidak dapat dipungkiri", "perlu diketahui bahwa", "pada dasarnya",
    "kesimpulannya", "udara sejuk yang menyegarkan", "nyaman dan menyenangkan",
    "kenyamanan maksimal", "tanpa harus khawatir",
]
# Kata generik/hampa yg BOLEH muncul sesekali (bukan klise terlarang spt di atas), tapi
# kalau berulang jadi ciri khas "AI slop" - ambang 3x per artikel (sama spt cap "Kakak"
# maks 5-7x yg sudah ada di prompt, prinsip yg sama: kata netral jadi mencolok kalau
# dipaksakan berulang-ulang).
SLOP_WORDS_MAX_3X = ["menghadirkan", "memberikan", "menawarkan", "memanjakan"]


def _slop_word_counts(content: str) -> dict:
    """Hitung mentah tiap kata di SLOP_WORDS_MAX_3X - dipisah dari fungsi deteksi supaya
    angkanya (bukan cuma lolos/tidak) bisa disimpan di blog_posts utk Content Health
    scorecard di CMS (lihat generate_one), termasuk artikel yang LOLOS gate (mis. 2x,
    masih di bawah ambang blokir 3x tapi tetap informatif ditampilkan ke staf)."""
    lower = content.lower()
    return {kata: len(re.findall(rf"\b{re.escape(kata)}\b", lower)) for kata in SLOP_WORDS_MAX_3X}


def _slop_phrases_terdeteksi(content: str) -> list:
    lower = content.lower()
    hits = [frasa for frasa in SLOP_PHRASES_DILARANG if frasa in lower]
    hits += [f"{kata} ({count}x)" for kata, count in _slop_word_counts(content).items() if count >= 3]
    return hits


def _sentence_cv(content: str) -> Optional[float]:
    """Coefficient of variation (stdev/mean) panjang kalimat (kata) - dipisah dari fungsi
    deteksi supaya angkanya sendiri (bukan cuma lolos/tidak) bisa disimpan utk Content
    Health scorecard. None kalau kalimat terlalu sedikit utk statistik yang berarti."""
    paras = [
        p.strip() for p in re.split(r"\n\n+", content)
        if len(p.strip()) > 80 and not p.strip().startswith("**")
    ]
    panjang_kalimat = []
    for p in paras:
        for kalimat in re.split(r"(?<=[.!?])\s+", p):
            n_kata = len(kalimat.split())
            if n_kata >= 4:
                panjang_kalimat.append(n_kata)
    if len(panjang_kalimat) < 8:
        return None
    mean = statistics.mean(panjang_kalimat)
    if mean <= 0:
        return None
    return statistics.pstdev(panjang_kalimat) / mean


def _variasi_kalimat_kurang(content: str) -> bool:
    """Deteksi NYATA (bukan cuma instruksi prompt "variasikan panjang kalimat") kalau
    kalimat artikel seragam panjangnya - ciri khas tulisan AI generik (mis. semua kalimat
    ~35-40 kata). Threshold 0.25 dipilih konservatif (tulisan manusia natural biasanya CV
    jauh di atas ini) supaya tidak banyak false positive - bisa disesuaikan lagi setelah
    lihat data artikel nyata pasca-deploy."""
    cv = _sentence_cv(content)
    if cv is None:
        return False  # kurang data utk statistik yang berarti, jangan menebak
    return cv < 0.25


def _keyword_stuffing_terdeteksi(content: str, keyword: str) -> bool:
    """Kepadatan keyword >3% (per 100 kata) - ambang umum industri SEO utk "over-
    optimization", di atas ini justru dianggap Google sbg sinyal spam bukan relevansi."""
    words = content.lower().split()
    if len(words) < 50:
        return False
    kw_words = keyword.lower().split()
    n = len(kw_words)
    count = sum(1 for i in range(len(words) - n + 1) if words[i:i + n] == kw_words)
    density = count / len(words) * 100
    return density > 3.0


async def _duplicate_section_terdeteksi(content: str) -> bool:
    """Reuse embedding yang SAMA dipakai cannibalization check (_embed/_cosine) - cek
    antar SUB-JUDUL dalam 1 artikel yang sama (bukan lintas artikel), tangkap kasus model
    menulis ulang poin yang sama dgn kata beda di 2 sub-judul berbeda (nyata pernah
    disinggung di prompt "jangan mengulang poin yang sama" - ini verifikasi otomatisnya,
    bukan cuma andalkan instruksi prompt)."""
    paras = [p.strip() for p in re.split(r"\n\n+", content) if len(p.strip()) > 80]
    if len(paras) < 2:
        return False
    try:
        embeds = await _embed(paras)
    except Exception:
        return False  # gagal embed (mis. rate limit) - jangan blokir publish krn ini
    for i in range(len(embeds)):
        for j in range(i + 1, len(embeds)):
            if _cosine(embeds[i], embeds[j]) > 0.92:
                return True
    return False


# Gate 3: Template Intro Detection (2026-08-04, PRD "AI Blog Engine v2.0") - regex pada
# paragraf PERTAMA artikel, pola pembuka generik yang membuat pembaca langsung sadar ini
# tulisan AI-generated (audit nyata: hampir semua artikel dimulai "Pelangi Homestay
# berada di Bedugul, Baturiti, Tabanan..." atau "Jika kata kunci Anda adalah...").
INTRO_TEMPLATE_PATTERNS = [
    r"^(pelangi homestay|harmoni hills)\s+(berada|terletak|berlokasi)",
    r"^jika\s+(kata kunci|keyword)",
    r"^artikel ini\s+(membahas|menjelaskan|fokus)",
    r"^mencari\s+(resort|villa|hotel|penginapan|homestay)",
    r"^bagi\s+(anda|tamu|wisatawan|kamu)\s+yang",
]


def _intro_template_terdeteksi(content: str) -> bool:
    paras = [p.strip() for p in re.split(r"\n\n+", content) if p.strip()]
    if not paras:
        return False
    intro = paras[0].lower()
    return any(re.search(pat, intro) for pat in INTRO_TEMPLATE_PATTERNS)


# Gate 2: Information Repetition Check (2026-08-04, PRD "AI Blog Engine v2.0") - fakta
# SPESIFIK (harga, suhu, jarak, kapasitas) yang disebut berulang bikin artikel terasa
# "berputar-putar" (audit nyata: harga kamar disebut 3x, "tidak menyediakan transport"
# 4x). SENGAJA regex GENERIK per KATEGORI fakta (angka+satuan), BUKAN hardcode angka
# tertentu spt draft PRD asli ("175.000"/"225.000") - hardcode rapuh & basi begitu harga
# berubah, melanggar prinsip satu-sumber-kebenaran yang dipakai di seluruh file ini
# (tarif SELALU dibaca live dari DB, bukan ditulis ulang di kode). Harga diberi ambang
# lebih longgar (>2x, bukan >1x) krn struktur artikel yang SUDAH ADA (intro ringkas +
# FAQ "berapa harga?" + info praktis) secara wajar menyebut harga 2x tanpa terasa
# repetitif - baru dianggap masalah kalau muncul PERSIS angka yang sama 3x+.
_FAKTA_REPETISI_PATTERNS = {
    "suhu (°C)": (r"\d{1,2}\s?[-–]\s?\d{1,2}\s?°?c\b", 1),
    "jarak (km)": (r"\d+(?:[.,]\d+)?\s?km\b", 1),
    "kapasitas rombongan (orang)": (r"\d+\s?[-–]\s?\d+\s?orang\b", 1),
    "harga (Rp)": (r"rp\s?\d[\d.,]*\d|rp\s?\d", 2),
}


def _fakta_berulang_terdeteksi(content: str) -> list:
    lower = content.lower()
    problems = []
    for label, (pattern, max_ok) in _FAKTA_REPETISI_PATTERNS.items():
        counts: Dict[str, int] = {}
        for m in re.findall(pattern, lower):
            counts[m] = counts.get(m, 0) + 1
        berulang = [f'"{v}" {c}x' for v, c in counts.items() if c > max_ok]
        if berulang:
            problems.append(f"{label} disebut berulang: {', '.join(berulang)}")
    return problems


# Gate 4: Pelangi/Harmoni Dominance Check (2026-08-04, PRD "AI Blog Engine v2.0") - hitung
# % paragraf yang menyebut nama brand, artikel yang HAMPIR SEMUA paragrafnya menyebut
# properti terasa seperti brosur produk, bukan konten blog (target PRD: 70% isi soal
# TOPIK, 30% soal properti). Ambang beda per intent (2026-08-04, mitigasi risiko yang
# SUDAH diantisipasi PRD sendiri §10 "Dominance check terlalu ketat"): keyword ber-intent
# Transactional (fokus Pelangi/Harmoni, mis. "Review Pelangi Homestay") WAJAR dominasi
# tinggi, dikasih ambang lebih longgar drpd Informational/Commercial.
DOMINANCE_THRESHOLD_BY_INTENT = {"Informational": 0.35, "Commercial": 0.35, "Transactional": 0.60}


def _dominasi_brand_terdeteksi(content: str, site: str, intent: str) -> Optional[str]:
    paras = [p.strip() for p in re.split(r"\n\n+", content) if p.strip()]
    if len(paras) < 3:
        return None  # terlalu pendek utk statistik rasio yang berarti
    nama = "pelangi" if site == "pelangi" else "harmoni"
    n_match = sum(1 for p in paras if nama in p.lower())
    rasio = n_match / len(paras)
    ambang = DOMINANCE_THRESHOLD_BY_INTENT.get(intent, 0.35)
    if rasio > ambang:
        return f"{round(rasio * 100)}% paragraf menyebut brand (ambang {round(ambang * 100)}% utk intent {intent})"
    return None


# Gate 5: Cross-Article FAQ Dedup (2026-08-04, PRD "AI Blog Engine v2.0") - FAQ hampir
# identik antar artikel ("Berapa harga kamar?"/"Jam check-in?" berulang di puluhan
# artikel) jadi sinyal duplicate content ke Google. Reuse pipeline embedding yang SAMA
# dgn cannibalization/duplicate-section (_embed/_cosine), BUKAN infrastruktur baru.
# db.faq_index di-cache incremental (diisi tiap artikel publish di generate_one) drpd
# re-embed SELURUH korpus FAQ tiap kali generate - jauh lebih hemat API call.
# Dinaikkan 0.7 -> 0.85 (2026-08-05, investigasi biaya - ditemukan penyebab utama gagal-
# terus-menerus sejak 2026-08-04: korpus FAQ sudah 143 artikel, topik universal (metode
# pembayaran, kebijakan pembatalan, jam check-in/out, sarapan) SECARA WAJAR mirip satu
# sama lain krn memang menjawab hal yang sama - pada 0.7 nyaris SEMUA draft baru gagal di
# gate ini walau kalimatnya beda, bukan cuma yang benar-benar copy-paste. 0.85 tetap
# menangkap duplikat nyaris identik, tapi tidak lagi menolak sekadar rephrasing wajar utk
# topik yang memang berulang di semua artikel hotel manapun.
FAQ_DEDUP_THRESHOLD = 0.85
_FAQ_PATTERN = re.compile(r"\*\*([^*]+\?)\*\*")


def _extract_faqs(content: str) -> list:
    return [q.strip() for q in _FAQ_PATTERN.findall(content) if q.strip()]


async def _faq_duplikat_terdeteksi(site: str, content: str, exclude_slug: str = "") -> list:
    faqs_baru = _extract_faqs(content)
    if not faqs_baru:
        return []
    existing = await db.faq_index.find(
        {"site": site, "slug": {"$ne": exclude_slug}}, {"text": 1, "embedding": 1},
    ).to_list(3000)
    if not existing:
        return []
    try:
        new_embeds = await _embed(faqs_baru)
    except Exception:
        return []  # gagal embed (mis. rate limit) - jangan blokir publish krn ini, sama pola dgn _duplicate_section_terdeteksi
    problems = []
    for faq, emb in zip(faqs_baru, new_embeds):
        mirip = next((e["text"] for e in existing if _cosine(emb, e["embedding"]) > FAQ_DEDUP_THRESHOLD), None)
        if mirip:
            problems.append(f'FAQ mirip yang sudah ada di artikel lain: "{faq}" ~ "{mirip}"')
    return problems


async def _simpan_faq_index(site: str, slug: str, content: str) -> None:
    """Dipanggil SEKALI saat artikel benar-benar publish (generate_one) - simpan FAQ +
    embedding-nya ke db.faq_index supaya artikel BERIKUTNYA bisa dicek dedup terhadap ini
    tanpa perlu re-embed seluruh korpus."""
    faqs = _extract_faqs(content)
    if not faqs:
        return
    try:
        embeds = await _embed(faqs)
    except Exception:
        return  # gagal embed - FAQ artikel ini cuma tidak masuk index dedup, tidak fatal
    now = datetime.now(timezone.utc).isoformat()
    docs = [
        {"id": str(uuid.uuid4()), "site": site, "slug": slug, "text": faq, "embedding": emb, "created_at": now}
        for faq, emb in zip(faqs, embeds)
    ]
    if docs:
        await db.faq_index.insert_many(docs)


async def editor_review(content: str, keyword: str, site: str = "", intent: str = "Transactional") -> list:
    """AI Editor (2026-07-29, roadmap AI Grow item 6) - bagian yang genuinely BISA
    dijadikan pemeriksaan deterministik (duplicate section via embedding yang sudah ada,
    keyword stuffing via hitung frekuensi) DIJADIKAN jaring pengaman keras (masuk
    `problems`, reject-&-requeue spt quality_check). "Trust"/"helpfulness"/"originality"
    dari daftar asli user SENGAJA tidak dibuatkan pemeriksaan terpisah - itu subjektif,
    sudah tercakup instruksi Editorial Writing Standard di system prompt, membuat
    "AI menilai trust-nya sendiri" cuma nambah lapis "AI menilai AI" yang sudah dihindari."""
    problems = []
    if _keyword_stuffing_terdeteksi(content, keyword):
        problems.append("kepadatan keyword berlebihan (>3%, terindikasi keyword stuffing)")
    if await _duplicate_section_terdeteksi(content):
        problems.append("ada 2 sub-judul yang isinya terlalu mirip (kemungkinan mengulang poin yang sama)")
    slop = _slop_phrases_terdeteksi(content)
    if slop:
        problems.append(f"AI slop terdeteksi (frasa klise/kata berulang): {', '.join(slop)}")
    if _variasi_kalimat_kurang(content):
        problems.append("variasi panjang kalimat terlalu rendah (kalimat cenderung seragam, ciri khas AI generik)")
    if _intro_template_terdeteksi(content):
        problems.append("intro pakai pola template generik (mis. 'X berada di...'/'Jika kata kunci Anda...') - tulis ulang dgn hook yang menarik")
    fakta_berulang = _fakta_berulang_terdeteksi(content)
    if fakta_berulang:
        problems.append("informasi berulang: " + "; ".join(fakta_berulang))
    if site:
        dominasi = _dominasi_brand_terdeteksi(content, site, intent)
        if dominasi:
            problems.append(f"artikel terlalu dominan membahas properti ({dominasi}) - perbanyak isi soal topik/destinasi")
    return problems


async def fact_check(site: str, content: str) -> list:
    """Verifikasi draft FINAL terhadap DATA ASLI SEBELUM publish (2026-07-28, jawaban
    konkret utk "AI melakukan fact-check sebelum publikasi") - lapis KEDUA, lapis
    PERTAMA (instruksi anti-mengarang di system prompt Writer Agent) sudah ada sejak
    awal tapi cuma preventif, tidak ada verifikasi terpisah stlh draft jadi.

    SENGAJA cuma SATU panggilan API tambahan yang bandingkan draft ke DATA ASLI &
    laporkan klaim SPESIFIK yang tidak didukung - BUKAN agent "Fact Checker" penuh
    terpisah bergaya PRD 16-Agent yang sudah ditolak user (over-engineering utk 2
    properti milik sendiri). Reuse mekanisme reject-&-requeue quality_check() yang
    sudah ada di generate_one() - problem list digabung jadi satu, bukan status/plumbing
    baru. temperature rendah (0.2, beda dari Writer Agent 0.6) krn ini tugas verifikasi
    presisi, bukan tugas kreatif - variasi jawaban tidak diinginkan di sini.

    Gagal parse/API dari fact-checker sendiri SEKARANG JUGA memblokir publish (2026-07-31,
    bug nyata ditemukan lewat audit PRD "AI Blog V2" - sebelumnya return [] diam-diam kalau
    error, artinya "fact-checker error" dan "fact-checker jalan & tidak temukan masalah"
    TIDAK BISA DIBEDAKAN di artikel yang terbit - outage diam-diam berarti nol verifikasi
    fakta tanpa jejak sama sekali. Sekarang error menghasilkan 1 issue sintetis yang
    memblokir publish (sama spt kalau fact-checker beneran menemukan klaim tak didukung) -
    lebih aman menunda publish drpd terbit tanpa verifikasi."""
    facts = await _fetch_site_facts(site)
    system = (
        "Kamu fact-checker konten editorial yang teliti & skeptis. Tugasmu HANYA "
        "membandingkan draft artikel dengan DATA ASLI yang diberikan, cari klaim "
        "SPESIFIK (harga, ukuran kamar, nama fasilitas, kapasitas, jarak/lokasi) yang "
        "TIDAK ADA di DATA ASLI atau BERTENTANGAN dengannya. Klaim umum yang wajar "
        "(mis. 'pemandangan indah', 'suasana tenang', 'udara sejuk') BUKAN masalah - "
        "fokus HANYA pada angka/nama spesifik yang bisa saja salah/dikarang."
    )
    user = f"""DATA ASLI ({site}):
{facts}

DRAFT ARTIKEL (final, siap terbit):
{content}

Balas HARUS JSON valid (tanpa markdown code fence):
{{"issues": ["klaim spesifik yang TIDAK didukung DATA ASLI, kalau ada", "..."]}}
Array "issues" KOSONG kalau semua klaim spesifik di draft sudah sesuai/didukung DATA ASLI."""
    try:
        raw = await _chat(system, user, temperature=0.2)
        result = _parse_json_response(raw)
        return [i for i in result.get("issues", []) if i]
    except Exception as e:
        print(f"[fact-check] gagal, publish DITUNDA demi keamanan: {type(e).__name__}: {e}")
        return ["fact-check gagal dijalankan (error API/parse) - publish ditunda demi keamanan"]


# ---------------------------------------------------------------------------
# 8. Orkestrasi + publish
# ---------------------------------------------------------------------------
SITE_DOMAIN = {"pelangi": "pelangihomestay.com", "harmoni": "harmoniby.pelangihomestay.com"}


async def generate_one(site: str, exclude_ids: Optional[set] = None) -> dict:
    keyword_doc = await get_next_keyword(site, exclude_ids=exclude_ids)
    await db.seo_keywords.update_one({"id": keyword_doc["id"]}, {"$set": {"status": "draft", "updated_at": datetime.now(timezone.utc).isoformat()}})

    try:
        links = await pick_internal_links(site, keyword_doc["cluster"], keyword=keyword_doc["keyword"])
        # Cross-brand collision (2026-08-03, permintaan Agus) - Pelangi & Harmoni dicek
        # SEBELUM menulis (bukan skip spt within-site, lihat _cross_brand_collision) supaya
        # Writer Agent tahu kalau brand seberang sudah pernah menulis topik mirip & wajib
        # ambil sudut pandang beda sesuai persona masing-masing brand.
        sibling = await _cross_brand_collision(site, keyword_doc["keyword"], keyword_doc["cluster"])
        article = await write_article(site, keyword_doc, link_candidates=links, sibling_collision=sibling)
        article["content"] = _normalize_faq_format(article["content"])
        content_final = _inject_links(article["content"], links, WA_BY_SITE[site], article.get("_maps_url"))

        problems = quality_check(article, content_final)
        fact_issues = await fact_check(site, content_final)
        if fact_issues:
            problems.append("fact-check: " + "; ".join(fact_issues))
        link_issues = await _internal_links_valid(site, content_final)
        if link_issues:
            problems.extend(link_issues)
        editor_issues = await editor_review(content_final, keyword_doc["keyword"], site=site, intent=keyword_doc.get("intent", "Transactional"))

        # Auto-fix kata AI-slop berulang (2026-08-01, permintaan user: kurangi tingkat
        # gagal - audit nyata menunjukkan ~2 dari 3 kegagalan hari itu MURNI karena kata
        # 'menghadirkan'/'memberikan'/'menawarkan'/'memanjakan' terhitung >=3x, padahal ini
        # masalah MEKANIS (hitung kata), bukan soal fakta/kualitas substansi - sayang kalau
        # seluruh artikel dibuang & keyword harus nunggu jadwal cron berikutnya cuma gara-
        # gara ini. SATU percobaan revisi bertarget (minta model ganti HANYA kalimat yang
        # memakai kata berlebih, bukan tulis ulang semua - beda dari loop expand kata di
        # write_article yang menulis ulang total), lalu validasi ULANG PENUH (bukan cuma
        # slop check - revisi bisa saja tidak sengaja pengaruhi hal lain) sebelum diterima.
        # Fact-check TIDAK disentuh di sini - itu butuh koreksi substansi yang lebih
        # berisiko kalau diperbaiki otomatis, tetap reject-&-requeue seperti biasa.
        counts = _slop_word_counts(content_final)
        berlebih = {k: v for k, v in counts.items() if v >= 3}
        # Guard: hanya coba auto-fix kalau penyebabnya MURNI kata berulang (berlebih terisi) -
        # kalau _slop_phrases_terdeteksi nangkap frasa klise terlarang (SLOP_PHRASES_DILARANG,
        # bukan hitungan kata), berlebih tetap kosong dan instruksi fix di bawah jadi tidak
        # berguna ("kata tertentu terlalu sering: {}") - biarkan quality gate normal yang reject.
        if berlebih and not fact_issues:
            fix_user = f"""Draft artikel ini (JSON) memakai kata tertentu terlalu sering: {berlebih}
(target MAKSIMAL 2x per kata di SELURUH artikel).

Tulis ULANG HANYA kalimat-kalimat yang memakai kata berlebih itu, ganti dengan kalimat aktif/kata
lain yang lebih spesifik (JANGAN sekadar sinonim generik). JANGAN ubah kalimat/paragraf lain yang
tidak bermasalah, JANGAN ubah/tambah/kurangi fakta apa pun, JANGAN ubah struktur/urutan sub-judul.

JSON artikel:
{json.dumps({"title": article["title"], "excerpt": article["excerpt"], "content": article["content"], "tags": article.get("tags", [])}, ensure_ascii=False)}

Balas HARUS JSON valid struktur sama seperti sebelumnya (title, excerpt, content, tags)."""
            fix_system = (
                "Kamu editor konten profesional Bahasa Indonesia untuk penginapan di Bedugul, Bali. "
                "Tugasmu HANYA revisi kata berlebih yang diminta - JANGAN mengarang fakta baru, "
                "JANGAN mengubah fakta/harga/fasilitas yang sudah ada di draft, JANGAN mengubah "
                "struktur/urutan sub-judul atau bagian yang tidak diminta."
            )
            try:
                raw_fix = await _chat(fix_system, fix_user, temperature=0.5)
            except Exception:
                raw_fix = None
            if raw_fix:
                try:
                    fixed = _parse_json_response(raw_fix)
                    fixed_content_norm = _normalize_faq_format(fixed["content"])
                    fixed_final = _inject_links(fixed_content_norm, links, WA_BY_SITE[site], article.get("_maps_url"))
                    if not _slop_phrases_terdeteksi(fixed_final):
                        article["title"], article["excerpt"], article["content"] = fixed["title"], fixed["excerpt"], fixed_content_norm
                        content_final = fixed_final
                        problems = quality_check(article, content_final)
                        fact_issues = await fact_check(site, content_final)
                        if fact_issues:
                            problems.append("fact-check: " + "; ".join(fact_issues))
                        link_issues = await _internal_links_valid(site, content_final)
                        if link_issues:
                            problems.extend(link_issues)
                        editor_issues = await editor_review(content_final, keyword_doc["keyword"], site=site, intent=keyword_doc.get("intent", "Transactional"))
                except (json.JSONDecodeError, KeyError):
                    pass  # gagal parse hasil revisi - lanjut pakai draft asli, biar quality gate normal yang menolak

        if editor_issues:
            problems.append("editor: " + "; ".join(editor_issues))
        faq_dedup_issues = await _faq_duplikat_terdeteksi(site, content_final)
        if faq_dedup_issues:
            problems.append("FAQ duplikat: " + "; ".join(faq_dedup_issues))
    except Exception:
        # Reset ke "belum_dibuat" - JANGAN biarkan macet permanen di "draft" kalau ada
        # error TAK TERDUGA (2026-07-28, ditemukan nyata: httpx.ReadTimeout dari OpenAI
        # saat cron jalan bikin keyword "hotel bedugul" macet selamanya di status "draft" -
        # main() cuma catat "GAGAL" ke log tanpa pernah reset status keyword-nya, jadi
        # get_next_keyword() TIDAK PERNAH memilihnya lagi krn query-nya cuma status=
        # "belum_dibuat"). Re-raise supaya try/except per-situs di main() tetap mencatat
        # kegagalannya spt biasa (perilaku log tidak berubah, cuma DB tidak lagi macet).
        await db.seo_keywords.update_one({"id": keyword_doc["id"]}, {"$set": {"status": "belum_dibuat"}})
        raise

    if problems:
        await db.seo_keywords.update_one({"id": keyword_doc["id"]}, {"$set": {"status": "belum_dibuat"}})
        return {"ok": False, "keyword": keyword_doc["keyword"], "keyword_id": keyword_doc["id"], "problems": problems}

    slug_base = slugify(article["title"])
    slug = slug_base
    counter = 1
    while await db.blog_posts.find_one({"slug": slug}):
        counter += 1
        slug = f"{slug_base}-{counter}"

    cover = await pick_cover_image(site, keyword_doc["keyword"], keyword_doc["cluster"], slug)
    now = datetime.now(timezone.utc).isoformat()

    # Author byline (2026-08-02, PRD "AI Blog V2.0" modul 9 EEAT Builder, permintaan Agus) -
    # SENGAJA nama TIM ASLI ("Tim {brand asli}"), BUKAN nama editor/reviewer karangan - Google
    # menilai E-E-A-T dari identitas yang bisa diverifikasi nyata, byline palsu justru
    # berisiko dianggap konten menyesatkan. `brand` diambil dari db.site_content (sumber
    # kebenaran yang sama dipakai _fetch_site_facts di atas), bukan hardcode per-situs -
    # otomatis benar kalau brand berubah tanpa perlu ubah kode ini.
    site_brand_doc = (await db.site_content.find_one({"site": site, "type": "site"}) or {}).get("data", {})
    author_name = f"Tim {site_brand_doc.get('brand') or ('Pelangi Homestay' if site == 'pelangi' else 'Harmoni Hills')}"

    doc = {
        "title": article["title"], "excerpt": article["excerpt"], "content": content_final,
        "category": CLUSTER_CATEGORY.get(keyword_doc["cluster"], "General"),
        "cover_image": cover, "tags": article.get("tags", []), "published": True,
        "slug": slug, "site": site, "created_at": now, "updated_at": now,
        "seo_keyword": keyword_doc["keyword"], "author": author_name,
        # Data kompetitor yang dibaca AI sebelum menulis (2026-07-28, permintaan user -
        # tampil di dashboard CMS) - None kalau analisis di-skip (budget Serper habis
        # hari itu/API down) - lihat analyze_competitors().
        "competitor_analysis": article.get("_competitor_data"),
        # Intent Coverage Score (2026-07-29, roadmap AI Grow item 3) - informasional,
        # TIDAK memblokir publish (lihat catatan di intent_coverage_score) - tampil di
        # dashboard CMS supaya staf tahu artikel mana yang masih kurang lengkap intent-nya.
        "intent_coverage": intent_coverage_score(content_final),
        # Content Health (2026-07-31, PRD "AI Blog V2" modul 15) - SENGAJA BUKAN skor
        # "AI Detection %" (tidak ada metode AI-detection yang reliable, apalagi utk
        # Bahasa Indonesia - lihat catatan di write_article). Angka REAL & bisa
        # diverifikasi: berapa kali kata hampa (menghadirkan/memberikan/menawarkan/
        # memanjakan) muncul (0-2, krn >=3 sudah diblokir editor_review), dan coefficient
        # of variation panjang kalimat (makin tinggi = makin bervariasi/manusiawi,
        # None kalau artikel terlalu pendek utk dihitung).
        "content_health": {
            "slop_word_max_count": max(_slop_word_counts(content_final).values(), default=0),
            "sentence_variance_cv": _sentence_cv(content_final),
        },
    }
    await db.blog_posts.insert_one(doc)
    await db.seo_keywords.update_one({"id": keyword_doc["id"]}, {"$set": {
        "status": "sudah_dibuat", "artikel_slug": slug, "updated_at": now,
    }})
    # Gate 5 (2026-08-04) - index FAQ artikel ini SEKARANG (setelah benar2 publish, bukan
    # sebelumnya) supaya artikel BERIKUTNYA bisa dicek dedup terhadap FAQ ini.
    await _simpan_faq_index(site, slug, content_final)

    # Prerender listing + detail artikel baru ini (2026-07-28, perluas SSR ke Blog) -
    # jalur INI beda dari admin_create_post di server.py (insert langsung ke DB, bukan
    # lewat endpoint HTTP), jadi trigger-nya dipanggil terpisah di sini juga. Best-effort
    # (try/except) - kegagalan prerender TIDAK BOLEH menggagalkan publish artikel yang
    # sudah berhasil (artikel tetap live via CSR biasa sampai prerender berhasil lain kali).
    try:
        domain = SITE_DOMAIN[site]
        await _prerender.prerender_site(site, domain, "blog")
        await _prerender.prerender_blog_detail(site, domain, slug)
    except Exception as e:
        print(f"[prerender] gagal utk artikel baru {slug}: {type(e).__name__}: {e}")

    return {"ok": True, "keyword": keyword_doc["keyword"], "slug": slug, "word_count": len(content_final.split())}


MAX_RETRY_PER_SLOT = 4  # lihat catatan retry-until-sukses di main() di bawah

# Target produksi harian per situs (2026-08-03, permintaan Agus - kampanye sementara:
# Pelangi naik 10->15/hari, Harmoni turun 10->5/hari, berlaku 2026-08-01 s.d. 2026-09-30,
# otomatis kembali ke 10/10 mulai 2026-10-01 TANPA perlu ubah cron/deploy lagi - lihat
# _artikel_sukses_hari_ini() & pengecekan kuota di main(). Kalau ada kampanye serupa lagi
# nanti, cukup ubah tanggal/angka di sini, bukan crontab.
_TARGET_HARIAN_DEFAULT = 10
_TARGET_HARIAN_KAMPANYE = {"pelangi": 15, "harmoni": 5}
_KAMPANYE_MULAI = date(2026, 8, 1)
_KAMPANYE_SELESAI = date(2026, 9, 30)


def _target_harian(site: str, hari_ini: Optional[date] = None) -> int:
    hari_ini = hari_ini or datetime.now(timezone.utc).date()
    if _KAMPANYE_MULAI <= hari_ini <= _KAMPANYE_SELESAI:
        return _TARGET_HARIAN_KAMPANYE.get(site, _TARGET_HARIAN_DEFAULT)
    return _TARGET_HARIAN_DEFAULT


async def _artikel_sukses_hari_ini(site: str) -> int:
    """Hitung artikel situs ini yang SUDAH terbit hari ini (UTC) - dipakai main() untuk
    berhenti begitu target harian tercapai, supaya cron yang fire lebih sering dari target
    (lihat crontab) otomatis self-limit tanpa perlu hitung manual per run."""
    mulai_hari = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time()).replace(tzinfo=timezone.utc)
    return await db.blog_posts.count_documents({"site": site, "created_at": {"$gte": mulai_hari.isoformat()}})


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, choices=["pelangi", "harmoni", "all"])
    ap.add_argument("--count", type=int, default=1)
    args = ap.parse_args()
    sites = ["pelangi", "harmoni"] if args.site == "all" else [args.site]

    # try/except per situs (2026-07-28) - sebelumnya satu error (mis. OpenAI ReadTimeout,
    # sudah pernah kejadian nyata di log) di pelangi bikin harmoni IKUT SKIP di run yang
    # sama (loop crash total, --site all cuma 1 proses Python) - artikel harmoni jadi
    # ketinggalan 1 siklus cron tanpa error yang kelihatan jelas (silent, cuma keliatan
    # dari created_at terakhir yang beda 4 jam). Sekarang tiap situs independen: gagal di
    # satu situs tidak menghalangi situs lain tetap dapat jatahnya di run yang sama.
    #
    # Retry-until-sukses per slot (2026-08-02, permintaan Agus - target harian WAJIB
    # tercapai, bukan cuma "dicoba"): SEBELUMNYA `--count N` = N PERCOBAAN, bukan N
    # ARTIKEL SUKSES - kalau generate_one() gagal quality gate (fact-check/editor/slop,
    # lihat problems di hasil {"ok": false}), slot itu hilang begitu saja tanpa diganti,
    # jadi target harian bisa meleset (audit log nyata: ~1 dari 6-7 percobaan gagal
    # quality gate, murni krn model kadang menghalusinasi 1 klaim kecil/kata berlebih -
    # BUKAN kegagalan sistemik). Sekarang tiap slot di-retry pakai keyword BERIKUTNYA
    # (get_next_keyword otomatis skip yang baru gagal, requeue balik ke "belum_dibuat")
    # sampai benar-benar sukses, dibatasi MAX_RETRY_PER_SLOT supaya tidak infinite-loop
    # kalau memang ada kegagalan sistemik asli (mis. OpenAI API down total hari itu).
    for site in sites:
        target = _target_harian(site)
        sudah_terbit = await _artikel_sukses_hari_ini(site)
        if sudah_terbit >= target:
            print(f"[{site}] target harian ({target}) sudah tercapai ({sudah_terbit} artikel hari ini) - skip run ini.")
            continue
        sukses = 0
        for i in range(args.count):
            sudah_terbit = await _artikel_sukses_hari_ini(site)
            if sudah_terbit >= target:
                print(f"[{site}] target harian ({target}) tercapai di tengah run ini ({sudah_terbit} artikel) - stop, tidak lanjut slot berikutnya.")
                break
            # exclude_ids terkumpul PER SLOT (2026-08-05, fix bug nyata - lihat catatan
            # exclude_ids di get_next_keyword) - keyword yang baru gagal quality gate di
            # percobaan sebelumnya TIDAK dipilih lagi di percobaan berikutnya slot yang
            # sama, supaya 4x retry benar-benar coba 4 keyword berbeda (spt yang sudah
            # dimaksud sejak awal), bukan keyword cursed yang sama berulang-ulang.
            sudah_dicoba_slot_ini: set = set()
            for attempt in range(1, MAX_RETRY_PER_SLOT + 1):
                try:
                    result = await generate_one(site, exclude_ids=sudah_dicoba_slot_ini)
                    print(f"[{site}] slot {i+1}/{args.count} percobaan {attempt}: {json.dumps(result, ensure_ascii=False)}")
                    if result.get("ok"):
                        sukses += 1
                        break
                    if result.get("keyword_id"):
                        sudah_dicoba_slot_ini.add(result["keyword_id"])
                except Exception as e:
                    print(f"[{site}] slot {i+1}/{args.count} percobaan {attempt}: GAGAL - {type(e).__name__}: {e}")
            else:
                print(f"[{site}] slot {i+1}/{args.count}: MENYERAH setelah {MAX_RETRY_PER_SLOT}x percobaan - kemungkinan kegagalan sistemik (cek log/API), bukan sekadar 1 artikel jelek.")
        print(f"[{site}] ringkasan run ini: {sukses}/{args.count} artikel benar-benar terbit (target harian: {target}).")


if __name__ == "__main__":
    asyncio.run(main())
