# Pelangi Homestay — PRD & Progress

**Status**: MVP live
**Date**: 2026-02

## Original Problem Statement
Website resmi Pelangi Homestay (homestay di Bedugul, Bali). Marketing-only site untuk membangun kepercayaan, meningkatkan SEO, mengarahkan tamu ke Booking Engine di `pelangihomestay.com/book`, dan mengurangi ketergantungan pada OTA. Termasuk Blog CMS dengan admin login. Visual style: torn-paper editorial (teal + mustard yellow) sesuai referensi.

## Architecture
- **Backend**: FastAPI + MongoDB (Motor). JWT (httpOnly cookies, samesite=none, secure=true). Bcrypt password hashing.
- **Frontend**: React 19 + React Router 7 + Tailwind + Sonner + Framer Motion. Fraunces (display) + DM Sans (body) + Caveat (script accents). Font Awesome via kit CDN.
- **Auth**: single admin, seeded from `ADMIN_EMAIL` / `ADMIN_PASSWORD` on startup.
- **CMS**: Blog posts (title, excerpt, content, category, cover_image, tags, published). Auto-generated slugs, unique index.

## Personas
- Wisatawan domestik / mancanegara (utama)
- Pasangan, keluarga, backpacker
- Sekunder: agen perjalanan, komunitas wisata

## Implemented (2026-02)
- Public site pages: Home, Rooms, Facilities, Gallery (filterable), Explore Bedugul, Restaurant, About, Blog list + detail, Contact (form + Google Map embed), FAQ.
- All Book Now CTAs → `https://pelangihomestay.com/book` (new tab).
- Floating WhatsApp button → `wa.me/6285119459269`.
- Admin: Login, Dashboard (list posts), New/Edit post editor, Delete with confirm, Logout.
- Contact form → POST `/api/contact`, persists to MongoDB.
- SEO basics: meta title/description, Open Graph tags, viewport, semantic headings.
- Design: torn-paper SVG dividers, italic display headings, mustard stickers, blob-cropped images, grain overlay, script eyebrow labels.

## Deferred / Backlog

### P1 (next iteration)
- Real photography ingestion (user will provide).
- Rich text editor for blog CMS (currently plain text with paragraph splits).
- Blog cover image upload (currently URL field).
- Structured data (Hotel JSON-LD schema) for stronger SEO.
- Sitemap.xml + robots.txt generation.
- Multi-bahasa (ID/EN) toggle — Phase 2 in PRD.

### P2
- Testimoni dinamis (managed from admin).
- Promo dinamis (managed from admin).
- Analytics dashboard (Google Analytics + Search Console integration).
- Password reset flow for admin.
- Multiple admin roles / staff invitations.

### P3 (Phase 3 in PRD)
- Loyalty & membership landing.
- Landing pages promosi musiman.
- Integrasi event lokal.

## Test Credentials
See `/app/memory/test_credentials.md`.

## Notes
- Backend cookies require HTTPS; only test admin flows via the public ingress URL.
- Photos are SVG landscape placeholders — replace when user delivers real photography.
