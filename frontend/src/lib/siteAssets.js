// Path aset (hero photo, favicon/logo) yang bisa diganti admin lewat CMS - path file
// per-situs (2026-07-26, bug nyata: upload foto hero harmoni dulu diam-diam menimpa foto
// pelangi krn keduanya pakai 1 nama file yang sama). Pelangi (DEFAULT_SITE di backend)
// tetap pakai nama file asli tanpa suffix supaya tidak perlu migrasi data lama; situs lain
// dapat suffix `-{site}`. Satu sumber kebenaran yang sama dengan `_site_asset_filename` di
// backend/server.py - ubah salah satu, ubah juga yang lain.
export function heroImagePath(site) {
  return site && site !== "pelangi" ? `/assets/signage-${site}.webp` : "/assets/signage.webp";
}

export function faviconPath(site) {
  return site && site !== "pelangi" ? `/assets/pelangi-logo-${site}.png` : "/assets/pelangi-logo.png";
}
