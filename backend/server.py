from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import asyncio
import logging
import uuid
import re
import tempfile
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Annotated

import bcrypt
import jwt
from bson import ObjectId
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, status, UploadFile, File
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator, EmailStr

from storage import init_storage, put_object, get_object, MIME_TYPES
from seed_content import SEED_CONTENT


# Zona waktu bisnis (Bedugul/Bali = WITA, UTC+8) - dipakai utk batas "hari ini" di
# dashboard CMS (bukan UTC) supaya angka "Dibuat AI hari ini" cocok dgn kalender hari
# yang dialami Agus, bukan reset 8 jam lebih awal (2026-07-31, bug nyata: user lapor
# "7 artikel terbit kemarin tapi dashboard cuma tertulis 5" - root cause: batas UTC
# midnight membuat artikel yg terbit dini hari WITA (00:00-08:00) masih terhitung hari
# SEBELUMNYA di UTC, jadi counter "hari ini" kehilangan beberapa artikel tiap hari).
BALI_TZ = ZoneInfo("Asia/Makassar")

# ---------- MongoDB ----------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]


# ---------- App ----------
app = FastAPI(title="Pelangi Homestay API")
api_router = APIRouter(prefix="/api")


# ---------- Helpers: JSON-safe ObjectId ----------
def _validate_object_id(v):
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str):
        return v
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[str, BeforeValidator(_validate_object_id)]


# ---------- Password / JWT ----------
JWT_ALGORITHM = "HS256"


def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "access",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=3600,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=604800,
        path="/",
    )


def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


def _parse_site_host_map() -> dict:
    """Multi-situs (2026-07-25) - satu backend + satu build React yang sama melayani
    lebih dari satu domain properti (pelangihomestay.com + harmoni.pelangihomestay.com),
    dibedakan dari header Host request. Format env `SITE_HOST_MAP`:
    "harmoni.pelangihomestay.com:harmoni,pelangihomestay.com:pelangi" - domain yang tidak
    ada di map (termasuk bare IP/localhost) jatuh ke DEFAULT_SITE, sama seperti perilaku
    sebelum fitur ini ada."""
    raw = os.environ.get("SITE_HOST_MAP", "")
    mapping = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        host, site = pair.split(":", 1)
        mapping[host.strip().lower()] = site.strip()
    return mapping


SITE_HOST_MAP = _parse_site_host_map()
DEFAULT_SITE = os.environ.get("DEFAULT_SITE", "pelangi")

# Sama seperti SITE_DOMAIN di scripts/gsc_sync.py & scripts/seo_agent.py (2026-07-28) -
# dipakai admin_gsc_summary utk mencocokkan slug artikel ke URL yang disimpan GSC.
GSC_SITE_DOMAIN = {"pelangi": "pelangihomestay.com", "harmoni": "harmoniby.pelangihomestay.com"}


def _resolve_site_from_host(request: Request) -> str:
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return SITE_HOST_MAP.get(host, DEFAULT_SITE)


async def get_current_site_public(request: Request) -> str:
    """Dipakai endpoint publik (content/blog/contact) - tamu tidak login, jadi
    satu-satunya sinyal properti mana yang dimaksud adalah domain yang diakses."""
    return _resolve_site_from_host(request)


async def get_current_site_admin(request: Request) -> str:
    """Dipakai endpoint admin (edit konten) - owner yang sama bisa kelola KEDUA situs
    dari satu login manapun, jadi klien (frontend) mengirim header `X-Site` eksplisit
    (site switcher) - kalau tidak dikirim (build lama/cache), fallback ke domain Host
    supaya tetap masuk akal daripada error."""
    header_site = request.headers.get("x-site")
    if header_site:
        return header_site
    return _resolve_site_from_host(request)


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["id"] = str(user["_id"])
        del user["_id"]
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------- Models ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str


class BlogPostCreate(BaseModel):
    title: str
    excerpt: str = ""
    content: str
    category: str = "General"
    cover_image: str = ""
    tags: List[str] = []
    published: bool = True


class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    cover_image: Optional[str] = None
    tags: Optional[List[str]] = None
    published: Optional[bool] = None


class BlogPostOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    slug: str
    title: str
    excerpt: str
    content: str
    category: str
    cover_image: str
    tags: List[str] = []
    published: bool
    created_at: str
    updated_at: str
    # Ada isinya HANYA kalau artikel ini dibuat AI SEO Agent (scripts/seo_agent.py),
    # kosong untuk artikel yang ditulis manual - dipakai admin CmsBlog.jsx menandai
    # mana yang otomatis (2026-07-26, permintaan user: tidak ada cara lihat aktivitas
    # AI SEO Agent dari dalam CMS sama sekali sebelum ini).
    seo_keyword: Optional[str] = None
    # Data kompetitor yang dibaca AI sebelum menulis artikel ini (2026-07-28, permintaan
    # user - tampil di dashboard CMS). Shape: {keyword, competitors: [{url, word_count,
    # headings}], avg_word_count, analyzed_at}. None kalau analisis di-skip (budget
    # Serper harian habis/API down) atau artikel ditulis manual (bukan AI).
    competitor_analysis: Optional[dict] = None
    # Kapan artikel ini terakhir diperdalam AI krn terbukti dapat impression GSC riil
    # (2026-07-28, lihat scripts/expand_top_articles.py) - None kalau belum pernah.
    expanded_at: Optional[str] = None
    # Intent Coverage Score (2026-07-29) - {skor_persen, tercakup, kurang}. None utk
    # artikel lama sebelum fitur ini ada, atau artikel yang ditulis manual.
    intent_coverage: Optional[dict] = None
    # Author byline (2026-08-02, PRD "AI Blog V2.0" modul 9 EEAT Builder) - "Tim {brand
    # asli}" (lihat seo_agent.py generate_one), BUKAN nama editor/reviewer karangan. Field
    # ini SEMPAT hilang dari response walau sudah ditulis ke DB & dibackfill ke artikel
    # lama (2026-08-02, bug nyata ditemukan lewat verifikasi live: BlogPostOut ini
    # whitelist Pydantic ketat, field baru yang tidak didaftarkan di sini otomatis
    # ke-drop dari response API walau ada di dokumen Mongo-nya) - byline tampil "Tim
    # Kami" generik (fallback frontend) sampai fix ini, bukan nama brand asli.
    author: Optional[str] = None


class ContactMessageCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str = ""
    message: str


class ContactMessageOut(BaseModel):
    id: str
    name: str
    email: str
    subject: str
    message: str
    created_at: str


# ---------- Utils ----------
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or uuid.uuid4().hex[:8]


def post_to_out(doc: dict) -> BlogPostOut:
    return BlogPostOut(
        id=str(doc["_id"]),
        slug=doc.get("slug", ""),
        title=doc.get("title", ""),
        excerpt=doc.get("excerpt", ""),
        content=doc.get("content", ""),
        category=doc.get("category", "General"),
        cover_image=doc.get("cover_image", ""),
        tags=doc.get("tags", []),
        published=doc.get("published", True),
        created_at=doc.get("created_at", ""),
        updated_at=doc.get("updated_at", ""),
        seo_keyword=doc.get("seo_keyword"),
        competitor_analysis=doc.get("competitor_analysis"),
        expanded_at=doc.get("expanded_at"),
        intent_coverage=doc.get("intent_coverage"),
        author=doc.get("author"),
    )


# ---------- Routes: Health ----------
@api_router.get("/")
async def root():
    return {"message": "Pelangi Homestay API", "status": "ok"}


# ---------- Rate limiting (2026-07-27, audit keamanan - /auth/login sebelumnya tidak ada
# penghalang percobaan berulang sama sekali). In-memory sliding window per-proses, pola sama
# persis dengan yang sudah dipakai di PMS/ai-chat-bot - cukup untuk skala 1 proses backend. ----
import time as _time
_rate_limit_buckets: Dict[str, List[float]] = {}


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limiter(max_requests: int, window_seconds: int):
    async def _check(request: Request) -> None:
        key = f"{request.url.path}:{_client_ip(request)}"
        now = _time.time()
        cutoff = now - window_seconds
        bucket = [t for t in _rate_limit_buckets.get(key, []) if t >= cutoff]
        if len(bucket) >= max_requests:
            _rate_limit_buckets[key] = bucket
            raise HTTPException(429, "Terlalu banyak percobaan, coba lagi sebentar lagi")
        bucket.append(now)
        _rate_limit_buckets[key] = bucket
        if len(_rate_limit_buckets) > 20000:
            _rate_limit_buckets.clear()
    return _check


# ---------- Routes: Auth ----------
@api_router.post("/auth/login")
async def login(payload: LoginRequest, response: Response, _rl: None = Depends(rate_limiter(10, 60))):
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)
    return {
        "user": {
            "id": user_id,
            "email": user["email"],
            "name": user.get("name", "Admin"),
            "role": user.get("role", "admin"),
        },
        "access_token": access,
    }


@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    """Ditemukan 2026-07-26 (laporan user 'gagal simpan' di CMS): access_token cuma
    berlaku 60 menit dan TIDAK PERNAH ada cara memperpanjang - refresh_token dibuat &
    disimpan di cookie saat login (7 hari) tapi tidak pernah benar-benar dipakai di
    manapun. Kalau admin buka CMS >60 menit lalu klik Simpan, permintaan pasti gagal
    401 tanpa jalan keluar selain login ulang. Endpoint ini + interceptor axios di
    frontend (lihat lib/api.js) memperbaikinya - refresh token yang masih valid
    otomatis memperpanjang sesi, transparan tanpa perlu login ulang."""
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = create_access_token(str(user["_id"]), user["email"])
    new_refresh = create_refresh_token(str(user["_id"]))
    set_auth_cookies(response, new_access, new_refresh)
    return {"ok": True}


@api_router.post("/auth/logout")
async def logout(response: Response, _: dict = Depends(get_current_user)):
    clear_auth_cookies(response)
    return {"message": "Logged out"}


@api_router.get("/auth/me", response_model=UserOut)
async def me(current: dict = Depends(get_current_user)):
    return UserOut(
        id=current["id"],
        email=current["email"],
        name=current.get("name", "Admin"),
        role=current.get("role", "admin"),
    )


# ---------- Routes: Blog Public ----------
@api_router.get("/blog", response_model=List[BlogPostOut])
async def list_posts(category: Optional[str] = None, limit: int = 50, site: str = Depends(get_current_site_public)):
    """Multi-situs (2026-07-25) - ditemukan lewat pengecekan langsung setelah harmoni
    live: endpoint ini TIDAK di-scope, jadi harmoniby.pelangihomestay.com/blog benar-benar
    menampilkan 3 postingan blog Pelangi ke tamu asli. Diperbaiki dengan filter `site`
    (default "pelangi" untuk post lama, backward compatible)."""
    query = {"published": True, "site": site}
    if category and category.lower() != "all":
        query["category"] = category
    cursor = db.blog_posts.find(query).sort("created_at", -1).limit(limit)
    return [post_to_out(doc) async for doc in cursor]


@api_router.get("/blog/{slug}", response_model=BlogPostOut)
async def get_post(slug: str, site: str = Depends(get_current_site_public)):
    doc = await db.blog_posts.find_one({"slug": slug, "published": True, "site": site})
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_to_out(doc)


# ---------- Routes: Blog Admin ----------
@api_router.get("/admin/seo-agent/stats")
async def admin_seo_agent_stats(_: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin)):
    """Ringkasan aktivitas AI SEO Agent (scripts/seo_agent.py) untuk ditampilkan di
    CmsBlog.jsx (2026-07-26, permintaan user - sebelum ini tidak ada cara lihat aktivitas
    AI SEO Agent dari dalam CMS sama sekali, semua laporan cuma manual). Dihitung
    langsung dari db.blog_posts (field seo_keyword = ditulis AI) & db.seo_keywords,
    bukan log terpisah - satu sumber kebenaran yang sama dipakai scripts/seo_agent.py."""
    # Batas hari pakai WITA lokal (lihat BALI_TZ), lalu dikonversi balik ke UTC utk
    # dibandingkan ke created_at yg disimpan sbg string ISO UTC (format sama persis jadi
    # perbandingan string $gte tetap valid kronologis).
    today_start = (
        datetime.now(BALI_TZ).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).isoformat()
    )

    generated_today = await db.blog_posts.count_documents({
        "site": site, "seo_keyword": {"$ne": None}, "created_at": {"$gte": today_start},
    })
    generated_total = await db.blog_posts.count_documents({"site": site, "seo_keyword": {"$ne": None}})

    # dilewati_mirip (2026-07-28) - keyword yang DILEWATI otomatis krn cek cannibalization
    # (topiknya terlalu mirip artikel yang sudah terbit, lihat _keyword_cannibalizes_existing
    # di seo_agent.py) - ditampilkan biar transparan, bukan diam-diam hilang dari hitungan.
    keyword_counts = {"belum_dibuat": 0, "draft": 0, "sudah_dibuat": 0, "dilewati_mirip": 0}
    async for row in db.seo_keywords.aggregate([
        {"$match": {"site": site}},
        {"$group": {"_id": "$status", "n": {"$sum": 1}}},
    ]):
        if row["_id"] in keyword_counts:
            keyword_counts[row["_id"]] = row["n"]

    last_post = await db.blog_posts.find_one(
        {"site": site, "seo_keyword": {"$ne": None}},
        {"created_at": 1, "title": 1}, sort=[("created_at", -1)],
    )

    return {
        "generated_today": generated_today,
        "generated_total": generated_total,
        "keyword_belum_dibuat": keyword_counts["belum_dibuat"],
        "keyword_draft": keyword_counts["draft"],
        "keyword_sudah_dibuat": keyword_counts["sudah_dibuat"],
        "keyword_dilewati_mirip": keyword_counts["dilewati_mirip"],
        "last_generated_at": (last_post or {}).get("created_at"),
        "last_generated_title": (last_post or {}).get("title"),
    }


@api_router.get("/admin/seo-agent/queue")
async def admin_seo_agent_queue(
    limit: int = 20, _: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin),
):
    """Perencanaan artikel - keyword yang AKAN ditulis AI berikutnya (2026-07-28,
    permintaan user - tampil di dashboard CMS). Urutan PERSIS sama dengan
    get_next_keyword() di scripts/seo_agent.py (priority High > Medium > Low, lalu
    urutan insert/_id sbg tie-breaker) - supaya daftar ini betul-betul mencerminkan
    urutan nyata, bukan tebakan terpisah."""
    order = {"High": 0, "Medium": 1, "Low": 2}
    pool = await db.seo_keywords.find(
        {"site": site, "status": "belum_dibuat"}, {"_id": 0, "keyword": 1, "cluster": 1, "priority": 1, "intent": 1},
    ).to_list(500)
    pool.sort(key=lambda k: order.get(k.get("priority"), 9))
    total_belum_dibuat = len(pool)
    return {"total_belum_dibuat": total_belum_dibuat, "next_up": pool[:limit]}


@api_router.get("/admin/seo-agent/dilewati")
async def admin_seo_agent_dilewati(
    limit: int = 20, _: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin),
):
    """Keyword yang OTOMATIS di-skip krn dianggap cannibalize topik yang sudah ditulis
    (2026-07-29, permintaan user - tampil di dashboard CMS supaya staf bisa review manual,
    bukan diam-diam hilang tanpa jejak). Diurutkan dari yang paling baru di-skip - keyword
    yang lama biasanya sudah pernah ditinjau."""
    docs = await db.seo_keywords.find(
        {"site": site, "status": "dilewati_mirip"},
        {"_id": 0, "keyword": 1, "cluster": 1, "priority": 1, "cannibalization_note": 1, "updated_at": 1},
    ).sort("updated_at", -1).to_list(limit)
    total = await db.seo_keywords.count_documents({"site": site, "status": "dilewati_mirip"})
    return {"total": total, "items": docs}


# Editorial Knowledge Base (2026-07-29, permintaan user - "aturan editorial jadi knowledge
# system, bukan cuma prompt"). Meniru persis pola guardrail_rules yang SUDAH ada & terbukti
# jalan di ai-chat-bot (list string di 1 dokumen, diedit staf via textarea, disuntik ke
# system prompt Writer Agent) - bukan bangun sistem rules-engine baru dari nol. Satu
# dokumen SHARED (bukan per-situs) krn standar editorial memang sama utk Pelangi & Harmoni.
DEFAULT_EDITORIAL_RULES = [
    "Selalu sertakan link Google Maps kalau relevan (lokasi/arah ke tempat)",
    "Selalu tampilkan harga dalam Rupiah kalau datanya tersedia, jangan pernah mengarang angka",
    "Selalu tutup artikel dengan bagian FAQ",
    "Selalu selipkan 1-2 link internal natural ke artikel lain yang relevan",
    "Hindari judul/pembuka clickbait - klaim harus bisa dibuktikan isi artikel",
    "Gunakan tone konsisten: hangat, jujur, seperti penulis travel berpengalaman - bukan iklan",
    # Ditambahkan 2026-07-29 (Editorial Standard v2, permintaan user) - SAMA PERSIS dgn
    # DEFAULT_EDITORIAL_RULES di scripts/seo_agent.py, jangan diubah salah satu tanpa yang lain.
    "Artikel harus menjawab pertanyaan lanjutan yang wajar muncul - pembaca tidak perlu kembali ke Google cari info tambahan",
    "Prioritaskan detail lokal spesifik dari data asli (nama fasilitas, kebijakan, jarak/rute asli) - hindari generalisasi umum yang bisa ditemukan di web manapun",
    "Cuaca/iklim: hanya pola umum sepanjang tahun, JANGAN tulis ramalan cuaca atau kondisi hari ini",
    "Sisipkan itinerary/budget/checklist/waktu terbaik berkunjung HANYA kalau relevan dgn keyword-nya, jangan dipaksakan ke semua artikel",
]


@api_router.get("/admin/editorial-rules")
async def admin_editorial_rules_get(_: dict = Depends(get_current_user)):
    doc = await db.editorial_rules.find_one({"_id": "singleton"})
    return {"rules": doc["rules"] if doc else DEFAULT_EDITORIAL_RULES}


@api_router.put("/admin/editorial-rules")
async def admin_editorial_rules_update(body: dict, _: dict = Depends(get_current_user)):
    rules = [r.strip() for r in (body.get("rules") or []) if r and r.strip()]
    await db.editorial_rules.update_one(
        {"_id": "singleton"}, {"$set": {"rules": rules}}, upsert=True,
    )
    return {"rules": rules}


@api_router.get("/admin/seo-agent/basi")
async def admin_seo_agent_basi(_: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin)):
    """Freshness check (2026-07-29) - artikel yang menyebut harga (Rp) tapi diterbitkan
    SEBELUM data harga kamar terakhir diubah di CMS - kandidat perlu ditinjau ulang staf
    (bukan auto-update). Import lokal (bukan di top-level) supaya scripts.seo_agent (modul
    besar, dipakai cron) tidak ikut ter-load penuh saat server.py start kalau tidak
    dibutuhkan endpoint lain."""
    from scripts.seo_agent import cek_artikel_basi
    stale = await cek_artikel_basi(site)
    return {"total": len(stale), "items": stale[:10]}


@api_router.get("/admin/landmark-sources")
async def admin_landmark_sources_list(_: dict = Depends(get_current_user)):
    """Daftar landmark & URL sumber resmi yang sudah dikonfigurasi (2026-08-03,
    permintaan Agus, Feature 1 PRD Tahap 2 - "Source Citation"). Kosong sampai staf/owner
    isi source_url pertama - fungsi crawl (refresh_landmark_facts) SENGAJA tidak
    menebak URL sendiri, lihat catatan lengkap di scripts/seo_agent.py."""
    sources = await db.landmark_sources.find({}, {"_id": 0}).to_list(100)
    facts = {f["name"]: f for f in await db.landmark_facts.find({}, {"_id": 0}).to_list(100)}
    for s in sources:
        f = facts.get(s["name"])
        s["last_crawled"] = f.get("last_crawled") if f else None
    return {"sources": sources}


class LandmarkSourceIn(BaseModel):
    name: str
    source_url: str


@api_router.post("/admin/landmark-sources")
async def admin_landmark_sources_add(body: LandmarkSourceIn, _: dict = Depends(get_current_user)):
    """Tambah/update 1 landmark + URL sumber resminya, LANGSUNG crawl sekali saat
    disimpan (staf/owner yang menjamin URL ini benar-benar resmi - sistem tidak
    memverifikasi keaslian sumber, cuma mengambil isinya)."""
    from scripts.seo_agent import refresh_landmark_facts
    result = await refresh_landmark_facts(body.name, body.source_url)
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "Gagal crawl"))
    return result


@api_router.post("/admin/landmark-sources/{name}/refresh")
async def admin_landmark_sources_refresh(name: str, _: dict = Depends(get_current_user)):
    """Refresh manual (2026-08-03, permintaan Agus - "owner bisa minta refresh") - crawl
    ulang landmark yang source_url-nya sudah tersimpan, timpa data lama."""
    from scripts.seo_agent import refresh_landmark_facts
    result = await refresh_landmark_facts(name)
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "Gagal crawl"))
    return result


@api_router.get("/admin/seo-agent/cakupan")
async def admin_seo_agent_cakupan(_: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin)):
    """Cakupan Editorial per cluster (2026-08-03, upgrade dari versi progress-bar polos
    2026-07-29 - permintaan Agus jadi "Editorial Intelligence Dashboard"). Sengaja
    "Cakupan Editorial/Keyword", BUKAN "Topical Authority" (itu perlu data kompetitif
    berbayar yang tidak dimiliki proyek ini - lihat catatan lengkap di
    cakupan_editorial_lengkap/cakupan_keyword_per_cluster)."""
    from scripts.seo_agent import cakupan_editorial_lengkap
    return await cakupan_editorial_lengkap(site)


@api_router.get("/admin/gsc/summary")
async def admin_gsc_summary(_: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin)):
    """Analytics Dashboard (2026-07-28) - performa artikel dari Google Search Console
    (klik, impression, CTR, posisi rata-rata). Data ditarik scripts/gsc_sync.py (cron
    harian) ke db.gsc_page_stats - endpoint ini CUMA baca & gabungkan dengan
    db.blog_posts by URL (bukan panggil GSC API langsung tiap admin buka halaman -
    lebih cepat & tidak kena rate limit)."""
    domain = GSC_SITE_DOMAIN.get(site)
    posts = await db.blog_posts.find(
        {"site": site, "published": True}, {"_id": 0, "slug": 1, "title": 1},
    ).to_list(500)
    stats_by_url = {
        row["url"]: row async for row in db.gsc_page_stats.find({"site": site}, {"_id": 0})
    }

    articles = []
    for p in posts:
        url = f"https://{domain}/blog/{p['slug']}"
        s = stats_by_url.get(url)
        articles.append({
            "slug": p["slug"], "title": p["title"],
            "clicks": s["clicks"] if s else 0,
            "impressions": s["impressions"] if s else 0,
            "ctr": s["ctr"] if s else 0,
            "position": s["position"] if s else None,
        })
    articles.sort(key=lambda a: (-a["clicks"], -a["impressions"]))
    synced_ats = [s["synced_at"] for s in stats_by_url.values() if s.get("synced_at")]

    return {
        "articles": articles,
        "total_clicks": sum(a["clicks"] for a in articles),
        "total_impressions": sum(a["impressions"] for a in articles),
        "best_article": articles[0] if articles and articles[0]["clicks"] > 0 else None,
        "last_synced_at": max(synced_ats) if synced_ats else None,
    }


@api_router.get("/admin/blog", response_model=List[BlogPostOut])
async def admin_list_posts(_: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin)):
    cursor = db.blog_posts.find({"site": site}).sort("created_at", -1)
    return [post_to_out(doc) async for doc in cursor]


@api_router.get("/admin/blog/{post_id}", response_model=BlogPostOut)
async def admin_get_post(post_id: str, _: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin)):
    try:
        # site di-filter langsung di query (2026-07-27, audit keamanan) - sebelumnya admin
        # situs manapun bisa lihat/edit/hapus post situs LAIN cukup tahu post_id.
        doc = await db.blog_posts.find_one({"_id": ObjectId(post_id), "site": site})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_to_out(doc)


@api_router.post("/admin/blog", response_model=BlogPostOut)
async def admin_create_post(payload: BlogPostCreate, _: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin)):
    now = datetime.now(timezone.utc).isoformat()
    slug_base = slugify(payload.title)
    slug = slug_base
    counter = 1
    while await db.blog_posts.find_one({"slug": slug}):
        counter += 1
        slug = f"{slug_base}-{counter}"

    # Author byline (2026-08-02, sama pola dgn scripts/seo_agent.py generate_one) - artikel
    # yang ditulis manual staf via CMS ini JUGA butuh byline (bukan cuma artikel AI SEO
    # Agent), tanpa ini fallback frontend "Tim Kami" generik selamanya. Tetap "Tim {brand}",
    # bukan nama staf individu - staf yang login CMS memang bagian dari tim itu, jujur.
    site_brand_doc = (await db.site_content.find_one({"site": site, "type": "site"}) or {}).get("data", {})
    author_name = f"Tim {site_brand_doc.get('brand') or ('Pelangi Homestay' if site == 'pelangi' else 'Harmoni Hills')}"

    doc = {
        "title": payload.title,
        "excerpt": payload.excerpt,
        "content": payload.content,
        "category": payload.category,
        "cover_image": payload.cover_image,
        "tags": payload.tags,
        "published": payload.published,
        "slug": slug,
        "site": site,
        "created_at": now,
        "updated_at": now,
        "author": author_name,
    }
    result = await db.blog_posts.insert_one(doc)
    doc["_id"] = result.inserted_id
    if doc["published"]:
        _trigger_prerender_blog(site, slug)
    return post_to_out(doc)


@api_router.put("/admin/blog/{post_id}", response_model=BlogPostOut)
async def admin_update_post(
    post_id: str, payload: BlogPostUpdate, _: dict = Depends(get_current_user),
    site: str = Depends(get_current_site_admin),
):
    try:
        oid = ObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "title" in updates:
        new_slug_base = slugify(updates["title"])
        existing = await db.blog_posts.find_one({"slug": new_slug_base, "_id": {"$ne": oid}})
        if existing:
            updates["slug"] = f"{new_slug_base}-{uuid.uuid4().hex[:4]}"
        else:
            updates["slug"] = new_slug_base
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    # site di-filter langsung di query (2026-07-27, audit keamanan) - cegah admin situs lain
    # edit post situs ini cukup tahu post_id.
    result = await db.blog_posts.update_one({"_id": oid, "site": site}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    doc = await db.blog_posts.find_one({"_id": oid})
    if doc.get("published"):
        _trigger_prerender_blog(site, doc["slug"])
    return post_to_out(doc)


@api_router.delete("/admin/blog/{post_id}")
async def admin_delete_post(post_id: str, _: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin)):
    try:
        oid = ObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")
    # site di-filter langsung di query (2026-07-27, audit keamanan) - cegah admin situs lain
    # hapus post situs ini cukup tahu post_id.
    result = await db.blog_posts.delete_one({"_id": oid, "site": site})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    _trigger_prerender_blog(site)  # regenerasi listing (artikel yg dihapus hilang dari daftar)
    return {"message": "Deleted"}


# ---------- Routes: Contact ----------
@api_router.post("/contact")
async def submit_contact(payload: ContactMessageCreate, site: str = Depends(get_current_site_public)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "name": payload.name,
        "email": payload.email,
        "subject": payload.subject,
        "message": payload.message,
        "site": site,
        "created_at": now,
    }
    result = await db.contact_messages.insert_one(doc)
    return {"id": str(result.inserted_id), "message": "Thank you, we'll contact you soon."}


@api_router.get("/admin/contact", response_model=List[ContactMessageOut])
async def admin_list_contact(_: dict = Depends(get_current_user), site: str = Depends(get_current_site_admin)):
    cursor = db.contact_messages.find({"site": site}).sort("created_at", -1).limit(200)
    out = []
    async for doc in cursor:
        out.append(ContactMessageOut(
            id=str(doc["_id"]),
            name=doc.get("name", ""),
            email=doc.get("email", ""),
            subject=doc.get("subject", ""),
            message=doc.get("message", ""),
            created_at=doc.get("created_at", ""),
        ))
    return out


# ---------- Routes: Site Config ----------
@api_router.get("/site/config")
async def site_config():
    return {
        "booking_url": os.environ.get("BOOKING_ENGINE_URL", "https://pelangihomestay.com/book"),
        "whatsapp": os.environ.get("WHATSAPP_NUMBER", "6285119459269"),
        "brand": "Pelangi Homestay",
    }


# ---------- Routes: CMS Content ----------
ALLOWED_CONTENT_TYPES = {"rooms", "menu", "gallery", "attractions", "faqs", "testimonials", "site"}


@api_router.get("/content")
async def get_all_content(site: str = Depends(get_current_site_public)):
    """Public endpoint that returns all site content (used by frontend to hydrate).
    Multi-situs: di-scope ke `site` yang di-resolve dari domain (Host header) yang
    diakses tamu - lihat get_current_site_public."""
    out = {}
    async for doc in db.site_content.find({"site": site}):
        out[doc["type"]] = doc.get("data")
    # `_site` (2026-07-26, bug nyata: hero pelangi & harmoni ternyata berbagi SATU file
    # "signage.webp" krn frontend hardcode path tanpa tahu situs mana yang aktif - upload
    # foto harmoni menimpa punya pelangi juga). Slug ini dipakai komponen frontend
    # (Home.jsx, BrandLogo.jsx, dst) memilih nama file aset yang benar per situs.
    out["_site"] = site
    return out


# Halaman statis (harus disamakan manual dengan <Route> di App.js kalau ada rute publik
# baru ditambahkan/dihapus - tidak ada cara introspeksi otomatis dari sisi backend).
STATIC_SITEMAP_PATHS = [
    "/", "/rooms", "/facilities", "/gallery", "/explore-bedugul", "/restaurant", "/about",
    "/blog", "/contact", "/faq", "/privacy-policy", "/terms-and-conditions",
    "/cancellation-policy", "/refund-policy", "/house-rules", "/payment-information",
]


@api_router.get("/sitemap.xml")
async def sitemap_xml(request: Request, site: str = Depends(get_current_site_public)):
    """sitemap.xml (2026-07-26, permintaan user - butuh utk Google Search Console).
    Dinamis per-situs (BUKAN file statis) supaya artikel blog baru - termasuk yang
    di-auto-publish AI SEO Agent tiap hari - otomatis ikut tanpa perlu regenerasi
    terpisah. Origin dibangun dari Host header request ITU SENDIRI (bukan reverse-lookup
    SITE_HOST_MAP) supaya otomatis benar apa pun domain yang sedang diakses. Nginx
    proxy /sitemap.xml (root domain) -> endpoint ini, lihat sites-available/*."""
    host = request.headers.get("host", "").split(":")[0]
    origin = f"https://{host}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    urls = [(f"{origin}{p}", now) for p in STATIC_SITEMAP_PATHS]
    async for post in db.blog_posts.find({"site": site, "published": True}, {"slug": 1, "updated_at": 1}):
        lastmod = (post.get("updated_at") or now)[:10]
        urls.append((f"{origin}/blog/{post['slug']}", lastmod))

    entries = "".join(
        f"<url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>" for loc, lastmod in urls
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</urlset>'
    return StarletteResponse(content=xml, media_type="application/xml", headers={"Content-Type": "application/xml; charset=utf-8"})


@api_router.get("/content/{type}")
async def get_content_type(type: str, site: str = Depends(get_current_site_admin)):
    """SATU-SATUNYA pemakai endpoint ini adalah halaman admin (CmsList.jsx/
    CmsSettings.jsx) untuk memuat data yang akan diedit - situs publik pakai
    `GET /content` (semua tipe sekaligus). Karena itu resolusi situsnya HARUS ikut
    switcher admin (X-Site), BUKAN cuma domain - kalau tidak, form edit akan selalu
    menampilkan data situs sesuai domain (mis. pelangi) walau switcher sudah
    dipindah ke situs lain, dan simpan bisa menimpa data situs yang salah."""
    if type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid content type")
    doc = await db.site_content.find_one({"site": site, "type": type})
    return doc.get("data") if doc else None


# Prerender LCP fix (2026-07-26) - regen dipicu di sini, bukan endpoint media upload,
# karena upload foto sendiri belum mengubah field manapun di site_content sampai admin
# benar-benar PUT konten yang menunjuk ke foto barunya (lihat catatan di
# scripts/prerender_home.py). "menu" sengaja dilewati - Home.jsx tidak konsumsi tipe itu.
_PRERENDER_RUNNING: set = set()


# Halaman yang diprerender per situs (2026-07-28, perluas Priority 3 audit produksi) -
# "" = homepage, sisanya cocok dgn EXTRA_PAGES di scripts/prerender_home.py. Statis murni
# (Rooms/Facilities) - aman diregenerasi tiap ada perubahan konten apa pun, sama seperti
# homepage sebelumnya.
_PRERENDER_PAGES = ["", "rooms", "facilities"]


def _trigger_prerender(site: str):
    """Fire-and-forget, subprocess terpisah (BUKAN asyncio.create_task import Playwright
    langsung ke proses ini) - proses backend ini single-process, tanpa --workers,
    Restart=always, dan melayani SEMUA trafik API booking/admin kedua situs. Chromium
    yang macet/crash TIDAK BOLEH bisa mengganggu/me-restart proses API. Guard sederhana:
    kalau situs ini sedang diproses, lewati saja - simpanan berikutnya akan menyusul."""
    if site in _PRERENDER_RUNNING:
        return
    _PRERENDER_RUNNING.add(site)

    async def _run():
        try:
            for page in _PRERENDER_PAGES:
                args = ["-m", "scripts.prerender_home", site] + ([page] if page else [])
                proc = await asyncio.create_subprocess_exec(
                    str(ROOT_DIR / "venv" / "bin" / "python"), *args,
                    cwd=str(ROOT_DIR),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
                )
                try:
                    out, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
                except asyncio.TimeoutError:
                    proc.kill()
                    logging.getLogger("prerender").error(f"Prerender {site} [{page or 'home'}] timeout, di-kill")
                    continue
                if proc.returncode != 0:
                    logging.getLogger("prerender").error(
                        f"Prerender {site} [{page or 'home'}] gagal (exit {proc.returncode}): {out.decode(errors='replace')[:500]}"
                    )
        except Exception as e:
            logging.getLogger("prerender").error(f"Prerender {site} error: {e}")
        finally:
            _PRERENDER_RUNNING.discard(site)

    asyncio.create_task(_run())


# Blog listing/detail (2026-07-28, perluas Priority 3 - prerender Blog) - trigger
# TERPISAH dari _trigger_prerender di atas krn beda sumber data sepenuhnya: Rooms/
# Facilities baca dari db.site_content (via update_content_type), Blog baca dari
# db.blog_posts (endpoint CRUD sendiri, admin_create_post/admin_update_post/
# admin_delete_post) - tidak pernah lewat update_content_type sama sekali.
_PRERENDER_BLOG_RUNNING: set = set()


def _trigger_prerender_blog(site: str, slug: str = None):
    """Selalu regenerasi listing "/blog" (daftar artikel berubah tiap create/update/
    delete). Kalau `slug` diberikan (create/update, BUKAN delete - artikel yang dihapus
    tidak perlu snapshot baru), regenerasi juga detail artikel itu. Guard per-situs sama
    seperti _trigger_prerender - key terpisah (_PRERENDER_BLOG_RUNNING) supaya tidak
    saling tunggu/skip dengan trigger Rooms/Facilities/Home yang independen."""
    key = site
    if key in _PRERENDER_BLOG_RUNNING:
        return
    _PRERENDER_BLOG_RUNNING.add(key)

    async def _run():
        try:
            targets = [["-m", "scripts.prerender_home", site, "blog"]]
            if slug:
                targets.append(["-m", "scripts.prerender_home", site, "blog-detail", slug])
            for args in targets:
                proc = await asyncio.create_subprocess_exec(
                    str(ROOT_DIR / "venv" / "bin" / "python"), *args,
                    cwd=str(ROOT_DIR),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
                )
                try:
                    out, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
                except asyncio.TimeoutError:
                    proc.kill()
                    logging.getLogger("prerender").error(f"Prerender blog {site} {args[-1]} timeout, di-kill")
                    continue
                if proc.returncode != 0:
                    logging.getLogger("prerender").error(
                        f"Prerender blog {site} {args[-1]} gagal (exit {proc.returncode}): {out.decode(errors='replace')[:500]}"
                    )
        except Exception as e:
            logging.getLogger("prerender").error(f"Prerender blog {site} error: {e}")
        finally:
            _PRERENDER_BLOG_RUNNING.discard(key)

    asyncio.create_task(_run())


@api_router.put("/admin/content/{type}")
async def update_content_type(
    type: str,
    payload: dict,
    _: dict = Depends(get_current_user),
    site: str = Depends(get_current_site_admin),
):
    if type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid content type")
    data = payload.get("data")
    if data is None:
        raise HTTPException(status_code=400, detail="Missing 'data' field")
    now = datetime.now(timezone.utc).isoformat()
    await db.site_content.update_one(
        {"site": site, "type": type},
        {"$set": {"data": data, "updated_at": now, "site": site, "type": type}},
        upsert=True,
    )
    if type != "menu":
        _trigger_prerender(site)
    return {"ok": True, "type": type, "site": site, "updated_at": now}


# ---------- Routes: Media Upload ----------
APP_NAME = os.environ.get("APP_NAME", "pelangi-homestay")
MAX_UPLOAD_BYTES = 6 * 1024 * 1024  # 6 MB


@api_router.post("/admin/media")
async def upload_media(
    file: UploadFile = File(...),
    current: dict = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    if ext not in MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 6 MB)")
    file_id = uuid.uuid4().hex
    storage_path = f"{APP_NAME}/media/{file_id}.{ext}"
    content_type = MIME_TYPES.get(ext, file.content_type or "application/octet-stream")
    try:
        result = put_object(storage_path, data, content_type)
    except Exception as e:
        logger.exception("Storage upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    now = datetime.now(timezone.utc).isoformat()
    await db.media_files.insert_one({
        "file_id": file_id,
        "storage_path": result.get("path", storage_path),
        "original_filename": file.filename,
        "content_type": content_type,
        "size": len(data),
        "uploader": current.get("email"),
        "is_deleted": False,
        "created_at": now,
    })
    return {
        "id": file_id,
        "url": f"/api/media/{file_id}",
        "content_type": content_type,
        "size": len(data),
    }


# ---------- Routes: Site Asset Upload (hero photo, favicon/logo) ----------
# Beda dari upload_media di atas (2026-07-26) - hero photo & favicon TIDAK lewat
# Cloudinary/media_files dengan URL baru tiap upload. Path-nya SENGAJA tetap
# (/assets/signage.webp, /assets/pelangi-logo.png) - dipertahankan supaya optimasi LCP
# (preload hint di index.html, hardcoded di Home.jsx) & favicon/logo Navbar (BrandLogo.jsx)
# tidak perlu ikut diubah tiap admin ganti foto. Upload di sini cuma MENGGANTI ISI file di
# path yang sama (resize/kompresi otomatis, sama teknik yang dipakai manual sepanjang sesi
# optimasi performa 2026-07-26), baik di build/ (langsung live) maupun public/ (source,
# supaya deploy/build berikutnya tidak menimpanya balik ke foto lama).
#
# Catatan cache: nginx cache gambar override jadi 5 menit khusus utk file ini (lihat
# nginx sites-available/*, location = /assets/signage*.webp) - dipersingkat 2026-07-26
# stlh laporan user foto masih tampak lama walau server sudah benar (30 hari kelamaan
# utk aset yang bisa berubah isi kapan saja lewat CMS).
#
# Bug nyata ditemukan & diperbaiki 2026-07-26: filename di sini dulu SELALU "signage.webp"
# / "pelangi-logo.png" apa pun situsnya - desain awal cuma mikirin pelangi, belum
# mengantisipasi harmoni PAKAI FITUR YANG SAMA. Akibatnya upload foto hero harmoni diam-diam
# MENIMPA foto hero pelangi juga (satu file fisik yang sama). Sekarang nama file per-situs
# (pelangi tetap pakai nama asli spy tidak perlu migrasi, situs lain dapat suffix) - lihat
# `_site_asset_filename`. Frontend (Home.jsx dst) baca `_site` dari /api/content utk pilih
# file yang benar - lihat ContentContext.jsx.
SITE_ASSET_SLOTS = {
    "hero": {"filename": "signage.webp", "max_width": 900, "strip_alpha": True, "quality": 78},
    "favicon": {"filename": "pelangi-logo.png", "size": 128, "strip_alpha": False, "quality": None},
}
FRONTEND_BUILD_ASSETS = Path("/var/www/web-pelangi/frontend/build/assets")
FRONTEND_PUBLIC_ASSETS = Path("/var/www/web-pelangi/frontend/public/assets")
SITE_ASSET_UPLOAD_EXTS = {"jpg", "jpeg", "png", "gif", "webp"}


def _site_asset_filename(slot: str, site: str) -> str:
    base = SITE_ASSET_SLOTS[slot]["filename"]
    if site == DEFAULT_SITE:
        return base
    stem, _, ext = base.rpartition(".")
    return f"{stem}-{site}.{ext}"


async def _process_site_asset(slot: str, data: bytes, ext: str) -> bytes:
    """Resize/kompresi file yang di-upload admin jadi format final sesuai slot (hero:
    WebP lebar maks 900px; favicon: PNG persegi 128x128) - subprocess ke cwebp/convert,
    sama tool & teknik yang dipakai manual sepanjang optimasi performa sesi ini."""
    spec = SITE_ASSET_SLOTS[slot]
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"src.{ext}"
        src.write_bytes(data)
        if slot == "hero":
            flat = Path(tmp) / "flat.png"
            # -auto-orient WAJIB sebelum -resize (ditemukan 2026-07-26, laporan user foto
            # hero jadi rotate setelah diganti): foto dari kamera HP menyimpan orientasi
            # asli sensor + tag EXIF "Orientation" terpisah, bukan piksel yang sudah
            # diputar. Tanpa -auto-orient, convert resize apa adanya (salah arah), lalu
            # webp/strip metadata di bawah menghilangkan tag EXIF itu selamanya - hasil
            # akhir permanen miring/terbalik, tidak bisa "dibetulkan" cuma dgn EXIF viewer.
            cmd_flat = ["convert", str(src), "-auto-orient", "-resize", f"{spec['max_width']}x10000>",
                        "-background", "white", "-alpha", "remove", "-alpha", "off", str(flat)]
            proc = await asyncio.create_subprocess_exec(*cmd_flat, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            _, err = await proc.communicate()
            if proc.returncode != 0:
                raise HTTPException(400, f"Gagal memproses gambar: {err.decode(errors='replace')[:300]}")
            out = Path(tmp) / "out.webp"
            proc2 = await asyncio.create_subprocess_exec(
                "cwebp", "-q", str(spec["quality"]), str(flat), "-o", str(out),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            _, err2 = await proc2.communicate()
            if proc2.returncode != 0:
                raise HTTPException(400, f"Gagal kompresi WebP: {err2.decode(errors='replace')[:300]}")
            return out.read_bytes()
        else:  # favicon
            out = Path(tmp) / "out.png"
            cmd = ["convert", str(src), "-auto-orient", "-resize", f"{spec['size']}x{spec['size']}",
                   "-background", "none", "-gravity", "center", "-extent", f"{spec['size']}x{spec['size']}", str(out)]
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            _, err = await proc.communicate()
            if proc.returncode != 0:
                raise HTTPException(400, f"Gagal memproses gambar: {err.decode(errors='replace')[:300]}")
            return out.read_bytes()


@api_router.post("/admin/site-asset/{slot}")
async def upload_site_asset(
    slot: str,
    file: UploadFile = File(...),
    current: dict = Depends(get_current_user),
    site: str = Depends(get_current_site_admin),
):
    if slot not in SITE_ASSET_SLOTS:
        raise HTTPException(400, f"Slot tidak dikenal: {slot}")
    if not file.filename:
        raise HTTPException(400, "Missing filename")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in SITE_ASSET_UPLOAD_EXTS:
        raise HTTPException(400, f"Format tidak didukung: .{ext} (pakai jpg/jpeg/png/gif/webp)")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "File terlalu besar (maks 6 MB)")

    processed = await _process_site_asset(slot, data, ext)

    filename = _site_asset_filename(slot, site)
    for target_dir in (FRONTEND_BUILD_ASSETS, FRONTEND_PUBLIC_ASSETS):
        target_dir.mkdir(parents=True, exist_ok=True)
        final_path = target_dir / filename
        tmp_path = target_dir / f".{filename}.tmp"
        tmp_path.write_bytes(processed)
        os.rename(tmp_path, final_path)  # atomic - nginx tidak pernah baca file setengah tertulis

    logger.info(f"Site asset '{slot}' diganti oleh {current.get('email')} (site={site}, {len(processed)} bytes)")
    return {"ok": True, "slot": slot, "url": f"/assets/{filename}", "size": len(processed)}


@api_router.get("/media/{file_id}")
async def get_media(file_id: str):
    record = await db.media_files.find_one({"file_id": file_id, "is_deleted": False})
    if not record:
        raise HTTPException(status_code=404, detail="Media not found")
    try:
        # get_object pakai requests.get sync (timeout 60s) ke Cloudinary - to_thread
        # supaya tidak blokir event loop tunggal sampai 60 detik (2026-07-28, audit performa).
        data, ct = await asyncio.to_thread(get_object, record["storage_path"])
    except Exception as e:
        logger.exception("Storage fetch failed")
        raise HTTPException(status_code=500, detail=f"Fetch failed: {e}")
    return StarletteResponse(
        content=data,
        media_type=record.get("content_type", ct),
        headers={"Cache-Control": "public, max-age=31536000"},
    )


@api_router.get("/admin/media")
async def list_media(_: dict = Depends(get_current_user), limit: int = 100):
    cursor = db.media_files.find({"is_deleted": False}).sort("created_at", -1).limit(limit)
    out = []
    async for r in cursor:
        out.append({
            "id": r["file_id"],
            "url": f"/api/media/{r['file_id']}",
            "original_filename": r.get("original_filename"),
            "content_type": r.get("content_type"),
            "size": r.get("size"),
            "created_at": r.get("created_at"),
        })
    return out


@api_router.delete("/admin/media/{file_id}")
async def delete_media(file_id: str, _: dict = Depends(get_current_user)):
    result = await db.media_files.update_one(
        {"file_id": file_id},
        {"$set": {"is_deleted": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Media not found")
    return {"ok": True}


# ---------- App wiring ----------
app.include_router(api_router)

_cors_origins = [o.strip() for o in os.environ.get(
    "FRONTEND_URLS", os.environ.get("FRONTEND_URL", "http://localhost:3000")
).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------- Startup: seed admin + indexes + seed initial blog ----------
async def seed_admin():
    email = os.environ.get("ADMIN_EMAIL", "admin@pelangihomestay.com").lower().strip()
    password = os.environ.get("ADMIN_PASSWORD", "pelangi2026")
    existing = await db.users.find_one({"email": email})
    if existing is None:
        await db.users.insert_one({
            "email": email,
            "password_hash": hash_password(password),
            "name": "Admin",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Seeded admin user {email}")
    else:
        if not verify_password(password, existing["password_hash"]):
            await db.users.update_one(
                {"email": email},
                {"$set": {"password_hash": hash_password(password)}},
            )
            logger.info(f"Updated admin password for {email}")


async def seed_blog_posts():
    count = await db.blog_posts.count_documents({})
    if count > 0:
        return
    now = datetime.now(timezone.utc).isoformat()
    posts = [
        {
            "title": "5 Tempat Wajib Dikunjungi di Bedugul",
            "excerpt": "Dari danau kembar hingga pasar tradisional Candikuning, inilah destinasi favorit tamu Pelangi Homestay.",
            "content": "Bedugul menyimpan panorama pegunungan yang selalu menyejukkan. Mulailah pagi Anda dengan menyeruput kopi di teras cottage, lalu berkendara singkat menuju Pura Ulun Danu Beratan. Setelah itu, jelajahi Kebun Raya Bali yang luas, singgah di Pasar Candikuning untuk berburu strawberry segar, dan tutup hari dengan panorama sunset di Danau Buyan.\n\nSetiap sudut Bedugul menawarkan pengalaman berbeda. Jangan lupa membawa jaket tipis karena suhu bisa turun hingga 16°C di malam hari.",
            "category": "Wisata",
            "cover_image": "",
            "tags": ["bedugul", "wisata", "itinerary"],
            "published": True,
            "slug": "5-tempat-wajib-dikunjungi-di-bedugul",
            "created_at": now,
            "updated_at": now,
        },
        {
            "title": "Itinerary 2 Hari 1 Malam di Bedugul",
            "excerpt": "Rencana perjalanan singkat namun berkesan untuk pasangan maupun keluarga.",
            "content": "Hari pertama: check-in di Pelangi Homestay, lanjut ke Pura Ulun Danu untuk sesi foto ikonik, makan siang seafood danau, lalu Kebun Raya sore. Malam: dinner di restoran homestay dengan menu khas lokal.\n\nHari kedua: sunrise di Danau Beratan, sarapan pancake hangat di taman, singgah di Handara Gate untuk foto, lalu pulang lewat jalur Munduk untuk melihat air terjun.",
            "category": "Itinerary",
            "cover_image": "",
            "tags": ["itinerary", "keluarga", "pasangan"],
            "published": True,
            "slug": "itinerary-2-hari-1-malam-di-bedugul",
            "created_at": now,
            "updated_at": now,
        },
        {
            "title": "Tips Menginap Nyaman di Dataran Tinggi",
            "excerpt": "Beberapa hal kecil yang membuat liburan gunung Anda lebih menyenangkan.",
            "content": "Bawa jaket tipis, kaus kaki hangat, dan minyak angin. Manfaatkan air panas di kamar untuk teh sore. Selalu bawa botol air — udara pegunungan lebih kering dari dugaan Anda.\n\nPelangi Homestay menyediakan selimut tebal, breakfast lokal, dan sudut baca di taman untuk pagi yang tenang.",
            "category": "Tips",
            "cover_image": "",
            "tags": ["tips", "liburan"],
            "published": True,
            "slug": "tips-menginap-nyaman-di-dataran-tinggi",
            "created_at": now,
            "updated_at": now,
        },
    ]
    await db.blog_posts.insert_many(posts)
    logger.info(f"Seeded {len(posts)} blog posts")


async def seed_site_content():
    for type_key, data in SEED_CONTENT.items():
        existing = await db.site_content.find_one({"_id": type_key})
        if existing:
            continue
        now = datetime.now(timezone.utc).isoformat()
        await db.site_content.insert_one({
            "_id": type_key,
            "data": data,
            "updated_at": now,
        })
        logger.info(f"Seeded site_content type={type_key}")


@app.on_event("startup")
async def on_startup():
    await db.users.create_index("email", unique=True)
    await db.blog_posts.create_index("slug", unique=True)
    await db.blog_posts.create_index("category")
    await db.media_files.create_index("file_id", unique=True)
    await seed_admin()
    await seed_blog_posts()
    await seed_site_content()
    try:
        init_storage()
    except Exception as e:
        logger.warning(f"Storage init deferred: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
