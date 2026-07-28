"""GSC Analytics Sync (2026-07-28) - tarik data performa (klik/impression/CTR/posisi)
per halaman dari Google Search Console API, disimpan ke db.gsc_page_stats untuk
Analytics Dashboard di admin CMS (CmsBlog.jsx, endpoint GET /admin/gsc/summary di
server.py). Dijalankan cron 1x/hari (lihat scripts/run_gsc_sync.sh) - data GSC sendiri
punya lag pelaporan ~2-3 hari, jadi beda dari SEO Agent generate artikel yang 3x/hari,
sinkron 1x/hari sudah lebih dari cukup.

Auth: service account (backend/secrets/gsc_credentials.json, TIDAK di-commit - lihat
.gitignore backend/secrets/), ditambahkan sebagai user permission "Full" di kedua
property GSC (pelangihomestay.com, harmoniby.pelangihomestay.com) langsung dari GSC UI
oleh owner - service account TIDAK bisa self-provision akses ini, harus ditambahkan
manual sekali oleh pemilik property.

Jalankan manual: `venv/bin/python -m scripts.gsc_sync --site all`
"""
import argparse
import asyncio
import json
import os
import sys
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import httpx  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from google.oauth2 import service_account  # noqa: E402
from google.auth.transport.requests import Request as GRequest  # noqa: E402

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
CREDS_PATH = Path(__file__).parent.parent / "secrets" / "gsc_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Sama seperti SITE_DOMAIN di seo_agent.py - situs baru wajib ditambahkan di kedua
# tempat (tidak di-share lewat import supaya 2 script ini tetap independen satu sama
# lain, konsisten dgn pola yang sudah ada di proyek ini).
SITE_DOMAIN = {"pelangi": "pelangihomestay.com", "harmoni": "harmoniby.pelangihomestay.com"}

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def _get_token() -> str:
    creds = service_account.Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    creds.refresh(GRequest())
    return creds.token


async def _fetch_site_rows(site: str, token: str) -> list:
    domain = SITE_DOMAIN[site]
    site_url = f"https://{domain}/"
    encoded = urllib.parse.quote(site_url, safe="")
    # end mundur 3 hari dari hari ini - data GSC utk 1-2 hari terakhir sering belum
    # final/lengkap (bisa berubah kalau ditarik terlalu awal), window 28 hari kebelakang
    # dari situ (sama seperti rentang default laporan Performance di GSC UI).
    end = date.today() - timedelta(days=3)
    start = end - timedelta(days=28)
    body = {
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "dimensions": ["page"], "rowLimit": 1000,
    }
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            f"https://www.googleapis.com/webmasters/v3/sites/{encoded}/searchAnalytics/query",
            headers={"Authorization": f"Bearer {token}"}, json=body,
        )
        resp.raise_for_status()
        return resp.json().get("rows", [])


async def sync_site(site: str, token: str) -> dict:
    rows = await _fetch_site_rows(site, token)
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        url = row["keys"][0]
        await db.gsc_page_stats.update_one(
            {"site": site, "url": url},
            {"$set": {
                "site": site, "url": url,
                "clicks": row.get("clicks", 0), "impressions": row.get("impressions", 0),
                "ctr": row.get("ctr", 0), "position": row.get("position", 0),
                "synced_at": now,
            }},
            upsert=True,
        )
    return {"pages": len(rows)}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, choices=["pelangi", "harmoni", "all"])
    args = ap.parse_args()
    sites = ["pelangi", "harmoni"] if args.site == "all" else [args.site]
    token = _get_token()

    # try/except per situs (2026-07-28, konsisten dgn perbaikan seo_agent.py) - gagal
    # di satu situs (mis. property GSC belum di-setup benar) tidak menghalangi situs lain.
    for site in sites:
        try:
            result = await sync_site(site, token)
            print(f"[{site}] sync ok: {json.dumps(result)}")
        except Exception as e:
            print(f"[{site}] GAGAL - {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
