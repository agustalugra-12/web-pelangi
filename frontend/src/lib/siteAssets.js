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

// Ikon KHUSUS tab browser/search-engine favicon (2026-07-28, laporan user - logo lengkap
// dari faviconPath() di atas ada teks brand kecil ("PELANGI HOMESTAY"/"HARMONI HILLS
// Village") yang jadi buram/tidak terbaca sama sekali begitu di-scale ke ukuran favicon
// asli (16-32px) - dites nyata via ImageMagick, hasilnya cuma blur warna tanpa bentuk
// jelas. faviconPath() SENGAJA TIDAK diubah krn dipakai jg utk logo header (BrandLogo.jsx),
// JSON-LD LodgingBusiness (LodgingSchema.jsx), & preview admin (CmsSettings.jsx) - semua
// itu memang harus tampilkan logo LENGKAP dgn teks, beda kebutuhan dari ikon tab kecil.
// Aset ini di-crop manual ke bagian grafis paling ikonik saja (swoosh warna Pelangi /
// pohon-di-gapura Harmoni), tanpa teks - tetap jelas di ukuran 16px sekalipun.
export function tabIconPath(site) {
  return site && site !== "pelangi"
    ? `/assets/pelangi-favicon-icon-${site}.png`
    : "/assets/pelangi-favicon-icon.png";
}
