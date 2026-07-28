#!/bin/bash
# Dipanggil cron 1x/hari (lihat crontab -l) - sync data performa (klik/impression/
# CTR/posisi) dari Google Search Console ke db.gsc_page_stats, dipakai Analytics
# Dashboard di admin CMS (GET /admin/gsc/summary). GSC sendiri punya lag pelaporan
# ~2-3 hari, jadi 1x/hari sudah cukup (beda dari SEO Agent artikel yang 3x/hari).
cd /var/www/web-pelangi/backend || exit 1
set -a
source .env
set +a
venv/bin/python -m scripts.gsc_sync --site all >> /var/log/gsc_sync.log 2>&1
