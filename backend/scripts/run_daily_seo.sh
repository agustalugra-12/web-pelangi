#!/bin/bash
# Dipanggil cron 3x/hari (lihat crontab -l) - tiap panggilan generate 1 artikel per situs
# (pelangi + harmoni), jadi total 3 artikel/hari/situs sesuai kesepakatan user 2026-07-26.
# Log ke file terpisah supaya bisa dicek kalau ada kegagalan tanpa perlu masuk journalctl.
cd /var/www/web-pelangi/backend || exit 1
set -a
source .env
set +a
venv/bin/python -m scripts.seo_agent --site all --count 1 >> /var/log/seo_agent.log 2>&1
