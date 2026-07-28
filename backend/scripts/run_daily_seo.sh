#!/bin/bash
# Dipanggil cron 7x/hari (lihat crontab -l, jam 02/05/08/11/14/17/20 WIB) - tiap
# panggilan generate 1 artikel per situs (pelangi + harmoni), jadi total 7
# artikel/hari/situs (14/hari gabungan) sesuai permintaan user 2026-07-28 (naik dari
# 3x/hari sebelumnya). Log ke file terpisah supaya bisa dicek kalau ada kegagalan
# tanpa perlu masuk journalctl.
cd /var/www/web-pelangi/backend || exit 1
set -a
source .env
set +a
venv/bin/python -m scripts.seo_agent --site all --count 1 >> /var/log/seo_agent.log 2>&1
