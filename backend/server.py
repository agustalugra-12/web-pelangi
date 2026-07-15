from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import logging
import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Annotated

import bcrypt
import jwt
from bson import ObjectId
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, status
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator, EmailStr


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
    )


# ---------- Routes: Health ----------
@api_router.get("/")
async def root():
    return {"message": "Pelangi Homestay API", "status": "ok"}


# ---------- Routes: Auth ----------
@api_router.post("/auth/login")
async def login(payload: LoginRequest, response: Response):
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
async def list_posts(category: Optional[str] = None, limit: int = 50):
    query = {"published": True}
    if category and category.lower() != "all":
        query["category"] = category
    cursor = db.blog_posts.find(query).sort("created_at", -1).limit(limit)
    return [post_to_out(doc) async for doc in cursor]


@api_router.get("/blog/{slug}", response_model=BlogPostOut)
async def get_post(slug: str):
    doc = await db.blog_posts.find_one({"slug": slug, "published": True})
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_to_out(doc)


# ---------- Routes: Blog Admin ----------
@api_router.get("/admin/blog", response_model=List[BlogPostOut])
async def admin_list_posts(_: dict = Depends(get_current_user)):
    cursor = db.blog_posts.find({}).sort("created_at", -1)
    return [post_to_out(doc) async for doc in cursor]


@api_router.get("/admin/blog/{post_id}", response_model=BlogPostOut)
async def admin_get_post(post_id: str, _: dict = Depends(get_current_user)):
    try:
        doc = await db.blog_posts.find_one({"_id": ObjectId(post_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_to_out(doc)


@api_router.post("/admin/blog", response_model=BlogPostOut)
async def admin_create_post(payload: BlogPostCreate, _: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    slug_base = slugify(payload.title)
    slug = slug_base
    counter = 1
    while await db.blog_posts.find_one({"slug": slug}):
        counter += 1
        slug = f"{slug_base}-{counter}"

    doc = {
        "title": payload.title,
        "excerpt": payload.excerpt,
        "content": payload.content,
        "category": payload.category,
        "cover_image": payload.cover_image,
        "tags": payload.tags,
        "published": payload.published,
        "slug": slug,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.blog_posts.insert_one(doc)
    doc["_id"] = result.inserted_id
    return post_to_out(doc)


@api_router.put("/admin/blog/{post_id}", response_model=BlogPostOut)
async def admin_update_post(
    post_id: str, payload: BlogPostUpdate, _: dict = Depends(get_current_user)
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
    result = await db.blog_posts.update_one({"_id": oid}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    doc = await db.blog_posts.find_one({"_id": oid})
    return post_to_out(doc)


@api_router.delete("/admin/blog/{post_id}")
async def admin_delete_post(post_id: str, _: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")
    result = await db.blog_posts.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Deleted"}


# ---------- Routes: Contact ----------
@api_router.post("/contact")
async def submit_contact(payload: ContactMessageCreate):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "name": payload.name,
        "email": payload.email,
        "subject": payload.subject,
        "message": payload.message,
        "created_at": now,
    }
    result = await db.contact_messages.insert_one(doc)
    return {"id": str(result.inserted_id), "message": "Thank you, we'll contact you soon."}


@api_router.get("/admin/contact", response_model=List[ContactMessageOut])
async def admin_list_contact(_: dict = Depends(get_current_user)):
    cursor = db.contact_messages.find({}).sort("created_at", -1).limit(200)
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


# ---------- App wiring ----------
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
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


@app.on_event("startup")
async def on_startup():
    await db.users.create_index("email", unique=True)
    await db.blog_posts.create_index("slug", unique=True)
    await db.blog_posts.create_index("category")
    await seed_admin()
    await seed_blog_posts()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
