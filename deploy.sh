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
cd ..

echo "== restart backend service =="
systemctl restart pelangi-web-backend
sleep 2
systemctl is-active --quiet pelangi-web-backend && echo "backend OK" || { echo "backend GAGAL start, cek: journalctl -u pelangi-web-backend -n 50"; exit 1; }

echo "== nginx sanity check (config tidak diubah, cuma memastikan masih valid) =="
nginx -t

echo "== selesai: https://pelangihomestay.com =="
