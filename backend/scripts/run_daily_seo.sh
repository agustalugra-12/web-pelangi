#!/bin/bash
# Dipanggil cron 15x/hari (2026-08-03, naik dari 10x/hari supaya cukup slot utk target
# kampanye Pelangi 15/hari - lihat crontab -l, jam 02/04/.../20 WIB tiap 2 jam + tambahan
# jam 04:30/08:30/12:30/16:30/20:30 WIB). Target harian AKTUAL per situs TIDAK di-hardcode
# di sini/crontab - dihitung dinamis di seo_agent.py (_target_harian(), berbasis tanggal
# hari ini) & di-cek per site SEBELUM generate (_artikel_sukses_hari_ini()), jadi tiap
# situs otomatis STOP begitu kuota hari itu tercapai walau cron masih fire lagi (self-
# limit, bukan overshoot) - kalau target berubah lagi nanti (kampanye baru/berakhir),
# cukup ubah tanggal/angka di seo_agent.py, TIDAK PERNAH perlu ubah crontab ini lagi.
# "WAJIB tercapai" (bukan cuma "dicoba") ditegakkan di seo_agent.py main() sendiri
# (retry-until-sukses per slot, lihat MAX_RETRY_PER_SLOT) - --count di sini tetap
# berarti 1 SLOT (bisa lebih dari 1 percobaan internal kalau ada yang gagal quality
# gate), bukan 1 percobaan mentah. Log ke file terpisah supaya bisa dicek kalau ada
# kegagalan tanpa perlu masuk journalctl.
cd /var/www/web-pelangi/backend || exit 1
set -a
source .env
set +a
venv/bin/python -m scripts.seo_agent --site all --count 1 >> /var/log/seo_agent.log 2>&1
