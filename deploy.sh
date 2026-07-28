#!/bin/bash
# Update deploy untuk web-pelangi: git pull, rebuild frontend, reinstall backend deps, restart service.
set -e

cd "$(dirname "$0")"

echo "== git pull =="
git pull origin main

echo "== backend: install deps =="
cd backend
./venv/bin/pip install -r requirements.txt -q
cd ..

echo "== frontend: install & build =="
cd frontend
npm install --legacy-peer-deps
CI=false npm run build
npm run build:ssr
cd ..

echo "== restart backend service =="
systemctl restart pelangi-web-backend
sleep 2
systemctl is-active --quiet pelangi-web-backend && echo "backend OK" || { echo "backend GAGAL start, cek: journalctl -u pelangi-web-backend -n 50"; exit 1; }

echo "== regenerate prerendered snapshots (SSR: home + rooms + facilities + blog) =="
# Deploy kode baru = hash JS/CSS baru di build/index.html - snapshot lama (baik hash
# maupun bundle SSR-nya) jadi basi kalau tidak diregenerasi sekarang. PUT admin/content
# cuma trigger regen kalau ADA edit konten - deploy kode murni (tanpa edit konten) tidak
# pernah menyentuh endpoint itu, jadi harus di sini juga. Rooms & Facilities (2026-07-28,
# Priority 3 audit produksi) ikut di sini juga - sinkron dengan _PRERENDER_PAGES di
# server.py (kalau nambah halaman baru ke situ, tambahkan juga di list di bawah). Blog
# listing + SEMUA artikel (blog-detail-all) juga di sini - jumlah artikel terus bertambah
# (14/hari sejak 2026-07-28), butuh waktu lebih lama tiap deploy tapi tetap wajar
# (~11 detik/situs per 17 artikel, linear terhadap jumlah artikel).
cd backend
set -a; source .env 2>/dev/null; set +a
for site in pelangi harmoni; do
  for page in "" rooms facilities blog; do
    ./venv/bin/python -m scripts.prerender_home "$site" $page || echo "WARNING: prerender $site [${page:-home}] gagal, snapshot lama tetap dipakai (lihat log di atas)"
  done
  ./venv/bin/python -m scripts.prerender_home "$site" blog-detail-all || echo "WARNING: prerender $site blog-detail-all gagal sebagian, snapshot lama tetap dipakai utk yang gagal"
done
cd ..

echo "== nginx sanity check (config tidak diubah, cuma memastikan masih valid) =="
nginx -t

echo "== selesai: https://pelangihomestay.com =="
