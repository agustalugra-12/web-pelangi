"""Backend API tests for Pelangi Homestay."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or "https://pelangi-homestay.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")

ADMIN_EMAIL = "admin@pelangihomestay.com"
ADMIN_PASSWORD = "pelangi2026"


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def auth_session():
    """Session logged in as admin with httpOnly cookies persisted."""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text}")
    return s


# ---------- Health ----------
def test_root(api):
    r = api.get(f"{BASE_URL}/api/", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"


# ---------- Site Config ----------
def test_site_config(api):
    r = api.get(f"{BASE_URL}/api/site/config", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["booking_url"] == "https://pelangihomestay.com/book"
    assert d["whatsapp"] == "6285119459269"
    assert d["brand"] == "Pelangi Homestay"


# ---------- Public Blog ----------
def test_public_blog_list(api):
    r = api.get(f"{BASE_URL}/api/blog", timeout=15)
    assert r.status_code == 200
    posts = r.json()
    assert isinstance(posts, list)
    assert len(posts) >= 3
    slugs = {p["slug"] for p in posts}
    for expected in [
        "5-tempat-wajib-dikunjungi-di-bedugul",
        "itinerary-2-hari-1-malam-di-bedugul",
        "tips-menginap-nyaman-di-dataran-tinggi",
    ]:
        assert expected in slugs, f"Missing seeded slug {expected}"


def test_public_blog_detail(api):
    slug = "5-tempat-wajib-dikunjungi-di-bedugul"
    r = api.get(f"{BASE_URL}/api/blog/{slug}", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["slug"] == slug
    assert d["title"]
    assert d["content"]


def test_public_blog_detail_404(api):
    r = api.get(f"{BASE_URL}/api/blog/does-not-exist-xyz", timeout=15)
    assert r.status_code == 404


# ---------- Auth ----------
def test_auth_me_anonymous_401(api):
    r = requests.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code == 401


def test_login_invalid(api):
    r = api.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": "wrongwrong"},
        timeout=15,
    )
    assert r.status_code == 401


def test_login_success_sets_cookies(api):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["email"] == ADMIN_EMAIL
    # Verify Set-Cookie contains access_token and refresh_token
    set_cookie = r.headers.get("set-cookie", "") + " " + r.headers.get("Set-Cookie", "")
    all_cookies = "; ".join(r.raw.headers.get_all("Set-Cookie") if hasattr(r.raw.headers, "get_all") else [])
    combined = set_cookie + " " + all_cookies
    assert "access_token" in combined
    assert "refresh_token" in combined
    assert "HttpOnly" in combined
    # Session cookies exist for follow-up requests
    assert "access_token" in s.cookies

    # /auth/me should now work
    r2 = s.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r2.status_code == 200
    me = r2.json()
    assert me["email"] == ADMIN_EMAIL
    assert me["role"] == "admin"


def test_logout_clears_cookies():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200
    r2 = s.post(f"{BASE_URL}/api/auth/logout", timeout=15)
    assert r2.status_code == 200
    # After logout, /auth/me must be 401
    r3 = s.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r3.status_code == 401


# ---------- Admin Blog CRUD ----------
def test_admin_list_blog(auth_session):
    r = auth_session.get(f"{BASE_URL}/api/admin/blog", timeout=15)
    assert r.status_code == 200
    posts = r.json()
    assert isinstance(posts, list)
    assert len(posts) >= 3


def test_admin_blog_requires_auth():
    r = requests.get(f"{BASE_URL}/api/admin/blog", timeout=15)
    assert r.status_code == 401


def test_admin_blog_crud_flow(auth_session):
    unique = uuid.uuid4().hex[:6]
    title = f"TEST Artikel {unique}"
    payload = {
        "title": title,
        "excerpt": "Test excerpt",
        "content": "Paragraph one.\n\nParagraph two.",
        "category": "Tips",
        "tags": ["test", "pytest"],
        "published": True,
    }
    # CREATE
    r = auth_session.post(f"{BASE_URL}/api/admin/blog", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["title"] == title
    assert created["slug"].startswith("test-artikel-")
    assert created["category"] == "Tips"
    post_id = created["id"]

    # GET single
    r = auth_session.get(f"{BASE_URL}/api/admin/blog/{post_id}", timeout=15)
    assert r.status_code == 200
    assert r.json()["title"] == title

    # Public GET by slug (should be published)
    r = requests.get(f"{BASE_URL}/api/blog/{created['slug']}", timeout=15)
    assert r.status_code == 200

    # UPDATE
    new_title = f"TEST Updated {unique}"
    r = auth_session.put(
        f"{BASE_URL}/api/admin/blog/{post_id}",
        json={"title": new_title, "excerpt": "Updated excerpt"},
        timeout=15,
    )
    assert r.status_code == 200
    upd = r.json()
    assert upd["title"] == new_title
    assert upd["excerpt"] == "Updated excerpt"

    # Verify update persisted
    r = auth_session.get(f"{BASE_URL}/api/admin/blog/{post_id}", timeout=15)
    assert r.json()["title"] == new_title

    # DELETE
    r = auth_session.delete(f"{BASE_URL}/api/admin/blog/{post_id}", timeout=15)
    assert r.status_code == 200
    r = auth_session.get(f"{BASE_URL}/api/admin/blog/{post_id}", timeout=15)
    assert r.status_code == 404


def test_admin_get_invalid_id(auth_session):
    r = auth_session.get(f"{BASE_URL}/api/admin/blog/not-an-object-id", timeout=15)
    assert r.status_code == 400


# ---------- Contact ----------
def test_contact_submit(api):
    unique = uuid.uuid4().hex[:6]
    payload = {
        "name": f"TEST User {unique}",
        "email": f"test_{unique}@example.com",
        "subject": "TEST subject",
        "message": "TEST message from pytest",
    }
    r = api.post(f"{BASE_URL}/api/contact", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "id" in d
    assert d["id"]


def test_contact_stored_visible_via_admin(auth_session, api):
    unique = uuid.uuid4().hex[:6]
    payload = {
        "name": f"TEST ContactPersist {unique}",
        "email": f"persist_{unique}@example.com",
        "subject": "TEST persist",
        "message": "Persistence check message.",
    }
    r = api.post(f"{BASE_URL}/api/contact", json=payload, timeout=15)
    assert r.status_code == 200
    r2 = auth_session.get(f"{BASE_URL}/api/admin/contact", timeout=15)
    assert r2.status_code == 200
    msgs = r2.json()
    assert any(m["email"] == payload["email"] for m in msgs), "Contact message not persisted"


def test_contact_invalid_email(api):
    r = api.post(
        f"{BASE_URL}/api/contact",
        json={"name": "X", "email": "not-an-email", "message": "hi"},
        timeout=15,
    )
    assert r.status_code == 422
