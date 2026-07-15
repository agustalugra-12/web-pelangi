"""Backend API tests for CMS content and media endpoints (iteration 3)."""
import io
import os
import struct
import zlib
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "https://pelangi-homestay.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = "admin@pelangihomestay.com"
ADMIN_PASSWORD = "pelangi2026"


@pytest.fixture(scope="module")
def auth_session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text}")
    return s


def _make_png_bytes():
    """Create a minimal valid 1x1 PNG in-memory."""
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = b"\x00\xff\x00\x00"  # filter=0, R=255 G=0 B=0
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ---------- Content: Public GET ----------
def test_get_all_content_public():
    r = requests.get(f"{BASE_URL}/api/content", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    for key in ["rooms", "menu", "gallery", "attractions", "faqs", "testimonials", "site"]:
        assert key in data, f"Missing content key: {key}"


def test_get_content_rooms_public():
    r = requests.get(f"{BASE_URL}/api/content/rooms", timeout=15)
    assert r.status_code == 200
    rooms = r.json()
    assert isinstance(rooms, list)
    assert len(rooms) >= 2
    names = {room["name"] for room in rooms}
    assert "Standard Room" in names
    assert "Cottage" in names


def test_get_content_menu_public():
    r = requests.get(f"{BASE_URL}/api/content/menu", timeout=15)
    assert r.status_code == 200
    menu = r.json()
    assert isinstance(menu, list)
    names = {m["name"] for m in menu}
    for expected in ["Nasi Goreng", "Mie Instan", "Sosis Bakar", "Kentang Goreng", "Kopi Hitam"]:
        assert expected in names


def test_get_content_gallery_public():
    r = requests.get(f"{BASE_URL}/api/content/gallery", timeout=15)
    assert r.status_code == 200
    assert len(r.json()) >= 17


def test_get_content_faqs_public():
    r = requests.get(f"{BASE_URL}/api/content/faqs", timeout=15)
    assert r.status_code == 200
    assert len(r.json()) >= 7


def test_get_content_attractions_public():
    r = requests.get(f"{BASE_URL}/api/content/attractions", timeout=15)
    assert r.status_code == 200
    assert len(r.json()) >= 5


def test_get_content_testimonials_public():
    r = requests.get(f"{BASE_URL}/api/content/testimonials", timeout=15)
    assert r.status_code == 200
    assert len(r.json()) >= 4


def test_get_content_site_public():
    r = requests.get(f"{BASE_URL}/api/content/site", timeout=15)
    assert r.status_code == 200
    site = r.json()
    assert site["brand"] == "Pelangi Homestay"
    assert "promoTitle" in site


def test_get_content_invalid_type():
    r = requests.get(f"{BASE_URL}/api/content/invalid_type", timeout=15)
    assert r.status_code == 400


# ---------- Content: Auth-guarded PUT ----------
def test_put_content_requires_auth():
    r = requests.put(f"{BASE_URL}/api/admin/content/rooms", json={"data": []}, timeout=15)
    assert r.status_code == 401


def test_put_content_invalid_type(auth_session):
    r = auth_session.put(f"{BASE_URL}/api/admin/content/nope", json={"data": []}, timeout=15)
    assert r.status_code == 400


def test_put_content_missing_data(auth_session):
    r = auth_session.put(f"{BASE_URL}/api/admin/content/rooms", json={}, timeout=15)
    assert r.status_code == 400


def test_put_content_roundtrip_rooms(auth_session):
    """Update Standard Room priceFrom and verify GET returns new value; restore original."""
    # Fetch current
    r = requests.get(f"{BASE_URL}/api/content/rooms", timeout=15)
    assert r.status_code == 200
    original = r.json()
    assert isinstance(original, list) and len(original) >= 2

    # Deep-copy modify
    modified = [dict(x) for x in original]
    std_idx = next(i for i, r_ in enumerate(modified) if r_.get("name") == "Standard Room")
    old_price = modified[std_idx]["priceFrom"]
    modified[std_idx] = {**modified[std_idx], "priceFrom": "IDR 180.000"}

    # PUT
    r = auth_session.put(f"{BASE_URL}/api/admin/content/rooms", json={"data": modified}, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    assert body.get("type") == "rooms"

    # Verify via public GET
    r = requests.get(f"{BASE_URL}/api/content/rooms", timeout=15)
    assert r.status_code == 200
    fetched = r.json()
    std = next(x for x in fetched if x["name"] == "Standard Room")
    assert std["priceFrom"] == "IDR 180.000"

    # Restore original
    restore = [dict(x) for x in fetched]
    r_std_idx = next(i for i, r_ in enumerate(restore) if r_.get("name") == "Standard Room")
    restore[r_std_idx]["priceFrom"] = old_price
    r = auth_session.put(f"{BASE_URL}/api/admin/content/rooms", json={"data": restore}, timeout=15)
    assert r.status_code == 200

    # Confirm restored
    r = requests.get(f"{BASE_URL}/api/content/rooms", timeout=15)
    std = next(x for x in r.json() if x["name"] == "Standard Room")
    assert std["priceFrom"] == old_price


def test_put_content_roundtrip_site_promo(auth_session):
    """Update site.promoTitle and verify persistence via public GET."""
    r = requests.get(f"{BASE_URL}/api/content/site", timeout=15)
    assert r.status_code == 200
    original = r.json()
    old_title = original.get("promoTitle")

    new_title = "Menginap 5 malam gratis 1 malam"
    modified = {**original, "promoTitle": new_title}
    r = auth_session.put(f"{BASE_URL}/api/admin/content/site", json={"data": modified}, timeout=15)
    assert r.status_code == 200

    r = requests.get(f"{BASE_URL}/api/content/site", timeout=15)
    assert r.status_code == 200
    assert r.json()["promoTitle"] == new_title

    # Restore
    modified["promoTitle"] = old_title
    r = auth_session.put(f"{BASE_URL}/api/admin/content/site", json={"data": modified}, timeout=15)
    assert r.status_code == 200


# ---------- Media Upload ----------
def test_media_upload_requires_auth():
    png = _make_png_bytes()
    r = requests.post(
        f"{BASE_URL}/api/admin/media",
        files={"file": ("test.png", png, "image/png")},
        timeout=20,
    )
    assert r.status_code == 401


def test_media_upload_and_get(auth_session):
    png = _make_png_bytes()
    # requests session already has cookies + Content-Type: application/json header — remove for multipart
    s = requests.Session()
    s.cookies.update(auth_session.cookies)
    r = s.post(
        f"{BASE_URL}/api/admin/media",
        files={"file": ("TEST_pytest.png", png, "image/png")},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "id" in body and "url" in body
    assert body["content_type"] == "image/png"
    assert body["size"] == len(png)
    file_id = body["id"]

    # Fetch the image
    r2 = requests.get(f"{BASE_URL}{body['url']}", timeout=20)
    assert r2.status_code == 200
    assert r2.headers.get("content-type", "").startswith("image/png")
    assert r2.content == png

    # List media should include it
    r3 = auth_session.get(f"{BASE_URL}/api/admin/media", timeout=15)
    assert r3.status_code == 200
    listed = r3.json()
    assert any(m["id"] == file_id for m in listed)

    # Delete
    r4 = auth_session.delete(f"{BASE_URL}/api/admin/media/{file_id}", timeout=15)
    assert r4.status_code == 200

    # After delete, GET media returns 404
    r5 = requests.get(f"{BASE_URL}{body['url']}", timeout=15)
    assert r5.status_code == 404


def test_media_upload_unsupported_type(auth_session):
    s = requests.Session()
    s.cookies.update(auth_session.cookies)
    r = s.post(
        f"{BASE_URL}/api/admin/media",
        files={"file": ("test.exe", b"MZ\x90\x00", "application/octet-stream")},
        timeout=15,
    )
    assert r.status_code == 400


def test_media_list_requires_auth():
    r = requests.get(f"{BASE_URL}/api/admin/media", timeout=15)
    assert r.status_code == 401
