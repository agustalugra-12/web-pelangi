#!/bin/bash
# Dipanggil cron 1x/minggu (lihat crontab -l) - perdalam artikel yang SUDAH TERBUKTI dapat
# impression GSC riil (lihat scripts/expand_top_articles.py). GSC lag pelaporan ~2-3 hari
# dan konten tidak perlu diperdalam tiap hari, mingguan sudah cukup drastis lebih murah
# drpd harian utk dampak yang sama (beda dari SEO Agent artikel baru yang 7x/hari).
cd /var/www/web-pelangi/backend || exit 1
set -a
source .env
set +a
venv/bin/python -m scripts.expand_top_articles --site all >> /var/log/expand_top_articles.log 2>&1
