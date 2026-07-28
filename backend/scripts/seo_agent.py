"""AI SEO Growth Agent - versi ramping (2026-07-26, permintaan user setelah diskusi PRD
16-Agent penuh yang dianggap over-engineering untuk 2 properti milik sendiri, bukan SaaS
multi-tenant komersial). Cakupan yang DIBANGUN: Keyword Agent (dari 100 keyword yang
diberi user + generate keyword baru kalau pool habis), Writer Agent (grounded ke data
CMS asli - lihat _fetch_site_facts), Competitor Analysis Agent (2026-07-28, lihat
analyze_competitors - awalnya "sengaja tidak dibangun", ditambahkan belakangan begitu
user minta), Quality Gate (rule-based, BUKAN "AI menilai AI"), Internal Link + Schema +
Cover Image Agent, Publish (auto, TANPA approval manusia - ini keputusan sadar user
setelah diberi tahu risiko kebijakan "Scaled Content Abuse" Google).
Cakupan yang SENGAJA TIDAK dibangun: Analytics/Conversion/Learning Agent (SEBAGIAN
sudah ada - lihat GET /admin/gsc/summary di server.py, GSC Integration + Analytics
Dashboard 2026-07-28), Autopilot penuh 10.000 artikel sekaligus. Volume naik bertahap:
3/hari/situs (2026-07-26) -> 7/hari/situs (2026-07-28, permintaan user) - lihat
scripts/run_daily_seo.sh utk penjadwalan cron aktual.

Jalankan manual: `venv/bin/python -m scripts.seo_agent --site pelangi --count 1`
"""
import argparse
import asyncio
import json
import math
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

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

CLUSTER_CATEGORY = {
    "Utama": "General", "Harga": "Tips", "Lokasi Wisata": "Wisata", "View": "Wisata",
    "Keluarga": "Tips", "Pasangan": "Tips", "Fasilitas": "Tips", "Aktivitas": "Wisata",
    "Booking": "Tips", "Long Tail": "General",
}

# Query pencarian Pexels (2026-07-28) - Pexels cuma cari bagus dalam Bahasa Inggris, jadi
# dipetakan per cluster (bukan pakai keyword Indonesia mentah) - beberapa varian per cluster
# supaya tidak selalu dapat foto yang sama persis utk cluster yang sama.
# Setiap query WAJIB eksplisit "bali"/"tropical" (2026-07-28, ditemukan lewat uji visual -
# query generik seperti "cozy cottage interior" tanpa kata itu sering nyasar ke hasil kabin
# gaya Eropa/alpine, bukan tropis Bali - tidak sesuai suasana properti sama sekali).
CLUSTER_PEXELS_QUERY = {
    "Utama": ["tropical bali garden cottage", "bali mountain homestay"],
    "Harga": ["tropical bali guesthouse", "affordable bali tropical resort"],
    "Lokasi Wisata": ["bali mountain lake", "tropical bali highland scenery"],
    "View": ["misty bali mountain lake", "tropical bali garden view"],
    "Keluarga": ["bali family tropical vacation", "tropical family garden outdoor"],
    "Pasangan": ["romantic bali tropical getaway", "bali couple garden veranda"],
    "Fasilitas": ["tropical bali guesthouse interior", "bali resort veranda"],
    "Aktivitas": ["bali tropical nature walk", "tropical bali garden path"],
    "Booking": ["tropical bali resort relaxing", "bali vacation cottage tropical"],
    "Long Tail": ["tropical bali mountain cottage", "bali highland tropical garden"],
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
    async with httpx.AsyncClient(timeout=90) as http:
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
async def get_next_keyword(site: str) -> dict:
    """Ambil keyword prioritas tertinggi yang statusnya 'belum_dibuat'. Kalau pool habis,
    generate keyword baru dulu (cek duplikat semantik ke keyword+judul artikel yang sudah
    ada) sebelum diambil."""
    order = {"High": 0, "Medium": 1, "Low": 2}
    pool = await db.seo_keywords.find({"site": site, "status": "belum_dibuat"}).to_list(500)
    if not pool:
        await _generate_new_keywords(site, n=10)
        pool = await db.seo_keywords.find({"site": site, "status": "belum_dibuat"}).to_list(500)
    if not pool:
        raise RuntimeError(f"Tidak ada keyword tersedia untuk situs {site} (generate gagal)")
    pool.sort(key=lambda k: order.get(k["priority"], 9))
    return pool[0]


async def _generate_new_keywords(site: str, n: int = 10) -> None:
    """Dipanggil kalau 100 keyword awal sudah habis dipakai - AI brainstorm keyword baru
    yang MASIH relevan (penginapan/wisata Bedugul), lalu dicek duplikat semantik terhadap
    keyword & judul artikel yang sudah ada sebelum dimasukkan sbg 'belum_dibuat'."""
    existing_kw = await db.seo_keywords.find({"site": site}, {"keyword": 1}).to_list(2000)
    existing_titles = await db.blog_posts.find({"site": site}, {"title": 1}).to_list(500)
    existing_texts = [k["keyword"] for k in existing_kw] + [p["title"] for p in existing_titles]

    prompt = (
        f"Kamu ahli SEO untuk penginapan di kawasan Bedugul, Bali. Sudah ada {len(existing_kw)} "
        f"keyword yang tercatat. Buat {n} ide keyword BARU (belum ada di daftar), gaya pencarian "
        "orang Indonesia asli (bukan terjemahan kaku), fokus penginapan/wisata Bedugul - variasi "
        "kombinasi tipe akomodasi + lokasi/fasilitas/aktivitas/harga yang BELUM ada polanya. "
        "Balas HANYA daftar keyword, satu per baris, tanpa nomor/tanda apapun."
    )
    raw = await _chat("Kamu SEO keyword researcher yang teliti, tidak pernah mengarang tempat/fasilitas fiktif.", prompt)
    candidates = [ln.strip("-• \t") for ln in raw.strip().split("\n") if ln.strip()]

    if not candidates:
        return
    cand_embeds = await _embed(candidates)
    existing_embeds = await _embed(existing_texts) if existing_texts else []

    now = datetime.now(timezone.utc).isoformat()
    accepted = 0
    for cand, cand_emb in zip(candidates, cand_embeds):
        is_dupe = any(_cosine(cand_emb, e) > 0.88 for e in existing_embeds)
        if is_dupe:
            continue
        cluster = "Long Tail"
        await db.seo_keywords.update_one(
            {"site": site, "keyword": cand},
            {"$setOnInsert": {
                "id": str(uuid.uuid4()), "site": site, "keyword": cand, "cluster": cluster,
                "intent": "Transactional", "priority": "Medium", "musiman": False,
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
async def _fetch_site_facts(site: str) -> str:
    site_doc = (await db.site_content.find_one({"site": site, "type": "site"}) or {}).get("data", {})
    rooms_doc = (await db.site_content.find_one({"site": site, "type": "rooms"}) or {}).get("data", [])
    faqs_doc = (await db.site_content.find_one({"site": site, "type": "faqs"}) or {}).get("data", [])

    lines = [
        f"Nama brand: {site_doc.get('brand', '')}",
        f"Alamat: {site_doc.get('address', '')}",
        f"WhatsApp: {site_doc.get('whatsappDisplay', '')}",
    ]
    for r in rooms_doc:
        lines.append(
            f"Tipe kamar: {r.get('name')} | ukuran {r.get('size')} | kapasitas {r.get('capacity')} | "
            f"harga mulai {r.get('priceFrom')} | fasilitas: {', '.join(r.get('facilities', []))}"
        )
    for f in faqs_doc:
        lines.append(f"FAQ - {f.get('q')}: {f.get('a')}")
    return "\n".join(lines)


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


async def analyze_competitors(keyword: str) -> Optional[dict]:
    """Return {"prompt_text": ..., "data": {...}} - prompt_text siap disisipkan ke
    Writer Agent, data = hasil mentah (url/word_count/heading per kompetitor) UTK
    DISIMPAN ke blog_posts.competitor_analysis (2026-07-28, permintaan user - tampil
    di dashboard CMS "data kompetitor yang dibaca"). None kalau analisis gagal total
    (search API down/tidak dikonfigurasi/budget harian habis)."""
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
    return {
        "prompt_text": "\n".join(lines),
        "data": {
            "keyword": keyword,
            "competitors": [{"url": p["url"], "word_count": p["word_count"], "headings": p["headings"]} for p in pages],
            "avg_word_count": avg_words,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# 3. Writer Agent
# ---------------------------------------------------------------------------
async def write_article(site: str, keyword_doc: dict) -> dict:
    facts = await _fetch_site_facts(site)
    keyword = keyword_doc["keyword"]
    competitor_result = await analyze_competitors(keyword)

    system = (
        "Kamu content writer SEO Bahasa Indonesia untuk penginapan di Bedugul, Bali. "
        "ATURAN KERAS: HANYA gunakan fakta yang diberikan di 'DATA ASLI' - JANGAN PERNAH mengarang "
        "fasilitas, harga, kebijakan, atau nama tempat yang tidak disebutkan di sana atau tidak "
        "umum diketahui publik (mis. nama tempat wisata terkenal boleh, tapi jangan mengarang "
        "klaim spesifik soal tempat itu). Kalau ragu suatu fakta, jangan disebutkan sama sekali "
        "daripada mengarang. Tulis natural, tidak keyword stuffing, gaya sapaan 'Kakak'."
    )
    competitor_block = (
        f"\n\nANALISIS KOMPETITOR (dari hasil pencarian Google nyata):\n{competitor_result['prompt_text']}"
        if competitor_result else ""
    )
    user = f"""DATA ASLI ({site}):
{facts}
{competitor_block}

Tulis artikel SEO untuk target keyword: "{keyword}"

Format balasan HARUS JSON valid dengan struktur persis ini (tanpa markdown code fence):
{{
  "title": "judul menarik & mengandung keyword, maks 70 karakter",
  "excerpt": "ringkasan 1-2 kalimat, maks 160 karakter",
  "content": "isi artikel WAJIB 900-1300 kata (ini batas keras, hitung sendiri sebelum menjawab - kalau draftmu kurang dari 900 kata, perpanjang tiap bagian dengan detail/contoh lebih dulu sebelum dikirim). Struktur WAJIB: 1 paragraf pembuka (~80-120 kata), lalu PERSIS 6 sub-judul **Sub Judul** (masing-masing paragraf tersendiri, tiap sub-judul diikuti isi 100-150 kata - JANGAN ada sub-judul dengan isi di bawah 100 kata), lalu WAJIB 4 FAQ di bagian akhir, ditutup 1 paragraf penutup singkat. Paragraf dipisah \\n\\n. ATURAN FORMAT FAQ (WAJIB DIIKUTI PERSIS, JANGAN pakai kata literal 'Pertanyaan' sebagai label, JANGAN pakai *tanda-bintang-tunggal* untuk pertanyaan): tulis TEKS PERTANYAAN ASLI langsung di dalam **dua bintang**, contoh PERSIS begini -> **Apakah sarapan sudah termasuk di kamar ini?**\\n\\nYa, sarapan sudah termasuk untuk 2 orang di semua tipe kamar. <- lihat, pertanyaan aslinya ADA di dalam ** **, bukan diganti kata 'Pertanyaan' lalu pertanyaan aslinya ditaruh terpisah.",
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
async def pick_internal_links(site: str, cluster: str, exclude_slug: str = "") -> list:
    candidates = await db.blog_posts.find(
        {"site": site, "published": True, "slug": {"$ne": exclude_slug}},
        {"slug": 1, "title": 1, "category": 1},
    ).sort("created_at", -1).to_list(50)
    same_category = [c for c in candidates if c["category"] == CLUSTER_CATEGORY.get(cluster)]
    pool = same_category if len(same_category) >= 2 else candidates
    return pool[:3]


def _inject_links(content: str, links: list, wa_url: str) -> str:
    """Selipkan link internal (2-3 artikel terkait, kalau ada) + link booking WA (SELALU,
    bahkan kalau belum ada artikel lain utk disarankan - mis. situs baru) SEBELUM SELURUH
    bagian FAQ, bukan ditempel asal di akhir. Kerja di level daftar paragraf (bukan potong
    string mentah dgn regex posisi).

    2 bug nyata ditemukan & diperbaiki (2026-07-26) sebelum sempat live:
    (1) versi awal cuma cari pertanyaan **...?** PERTAMA - salah masuk DI TENGAH FAQ
    (antara pertanyaan 1 & 2). (2) versi kedua (whole-bold berakhir '?') malah kena
    subjudul H2 yang ditulis gaya pertanyaan (mis. "**Kenapa Memilih X?**" - gaya
    subjudul yang wajar & umum, BUKAN bagian FAQ) - salah deteksi sebagai awal FAQ.
    Sekarang: prioritaskan label eksplisit "**FAQ**" (case-insensitive) sebagai jangkar;
    kalau model tidak menulis label itu, fallback ke deteksi RUN minimal 2 paragraf
    **...?** BERTURUT-TURUT (satu subjudul-gaya-tanya yang berdiri sendiri, diikuti body
    text biasa, tidak akan pernah cocok - FAQ asli selalu berupa beberapa Q&A beruntun)."""
    baca_juga = ""
    if links:
        link_lines = " ".join(f"[{l['title']}](/blog/{l['slug']})" for l in links)
        baca_juga = f"Baca juga: {link_lines}.\n\n"
    insert_para = f"{baca_juga}Siap booking? [Chat sekarang lewat WhatsApp]({wa_url})."

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


# ---------------------------------------------------------------------------
# 8. Orkestrasi + publish
# ---------------------------------------------------------------------------
SITE_DOMAIN = {"pelangi": "pelangihomestay.com", "harmoni": "harmoniby.pelangihomestay.com"}


async def generate_one(site: str) -> dict:
    keyword_doc = await get_next_keyword(site)
    await db.seo_keywords.update_one({"id": keyword_doc["id"]}, {"$set": {"status": "draft", "updated_at": datetime.now(timezone.utc).isoformat()}})

    article = await write_article(site, keyword_doc)
    links = await pick_internal_links(site, keyword_doc["cluster"])
    content_final = _inject_links(article["content"], links, WA_BY_SITE[site])

    problems = quality_check(article, content_final)
    if problems:
        await db.seo_keywords.update_one({"id": keyword_doc["id"]}, {"$set": {"status": "belum_dibuat"}})
        return {"ok": False, "keyword": keyword_doc["keyword"], "problems": problems}

    slug_base = slugify(article["title"])
    slug = slug_base
    counter = 1
    while await db.blog_posts.find_one({"slug": slug}):
        counter += 1
        slug = f"{slug_base}-{counter}"

    cover = await pick_cover_image(site, keyword_doc["keyword"], keyword_doc["cluster"], slug)
    now = datetime.now(timezone.utc).isoformat()

    doc = {
        "title": article["title"], "excerpt": article["excerpt"], "content": content_final,
        "category": CLUSTER_CATEGORY.get(keyword_doc["cluster"], "General"),
        "cover_image": cover, "tags": article.get("tags", []), "published": True,
        "slug": slug, "site": site, "created_at": now, "updated_at": now,
        "seo_keyword": keyword_doc["keyword"],
        # Data kompetitor yang dibaca AI sebelum menulis (2026-07-28, permintaan user -
        # tampil di dashboard CMS) - None kalau analisis di-skip (budget Serper habis
        # hari itu/API down) - lihat analyze_competitors().
        "competitor_analysis": article.get("_competitor_data"),
    }
    await db.blog_posts.insert_one(doc)
    await db.seo_keywords.update_one({"id": keyword_doc["id"]}, {"$set": {
        "status": "sudah_dibuat", "artikel_slug": slug, "updated_at": now,
    }})

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
    for site in sites:
        for i in range(args.count):
            try:
                result = await generate_one(site)
                print(f"[{site}] {i+1}/{args.count}: {json.dumps(result, ensure_ascii=False)}")
            except Exception as e:
                print(f"[{site}] {i+1}/{args.count}: GAGAL - {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
