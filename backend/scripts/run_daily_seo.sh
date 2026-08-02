#!/bin/bash
# Dipanggil cron 10x/hari (2026-08-02, naik dari 7x/hari - permintaan Agus: target
# WAJIB 10 artikel/hari/situs, bukan cuma "dicoba") - lihat crontab -l, jam
# 02/04/06/08/10/12/14/16/18/20 WIB, tiap panggilan generate 1 SLOT per situs
# (pelangi + harmoni), jadi total 10 artikel/hari/situs (20/hari gabungan). "WAJIB
# 10" ditegakkan di dalam seo_agent.py main() sendiri (retry-until-sukses per slot,
# lihat MAX_RETRY_PER_SLOT) - --count di sini tetap berarti 1 SLOT (bisa lebih dari
# 1 percobaan internal kalau ada yang gagal quality gate), bukan 1 percobaan mentah.
# Log ke file terpisah supaya bisa dicek kalau ada kegagalan tanpa perlu masuk
# journalctl.
cd /var/www/web-pelangi/backend || exit 1
set -a
source .env
set +a
venv/bin/python -m scripts.seo_agent --site all --count 1 >> /var/log/seo_agent.log 2>&1
