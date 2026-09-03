"""Verifikasi rubric LLM cannibalization vs topic cluster (2026-09-03, permintaan Agus).
Test live (biaya kecil, real LLM call) - pakai contoh PERSIS dari rubric yang diberikan
Agus supaya hasilnya bisa dibandingkan langsung dgn ekspektasi rubric-nya.

Jalankan: venv/bin/python -m scripts.test_cannibalization_rubric
"""
import asyncio
from scripts.seo_agent import _cek_cannibalization_llm

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"✓ {name}")
    else:
        failed += 1
        print(f"✗ {name} — {detail}")


async def main():
    # Kasus AMAN (topic cluster) - contoh PERSIS dari rubric Agus.
    r1 = await _cek_cannibalization_llm(
        "penginapan Bedugul dengan akses mudah ke kebun stroberi",
        "penginapan Bedugul dekat jalur sepeda gunung",
    )
    check("Kebun stroberi vs jalur sepeda gunung -> AMAN (long-tail beda)", r1["status"] == "AMAN", str(r1))
    check("AMAN punya daftar pembeda", len(r1["pembeda"]) > 0, str(r1))

    # Kasus CANNIBALIZATION genuine (search intent + audiens + judul akan identik).
    r2 = await _cek_cannibalization_llm(
        "harga kamar cottage bedugul murah",
        "berapa harga cottage bedugul yang murah",
    )
    check("2 keyword harga cottage murah, cuma beda susunan kata -> CANNIBALIZATION", r2["status"] == "CANNIBALIZATION", str(r2))
    check("CANNIBALIZATION punya saran", bool(r2.get("saran")), str(r2))

    # Kasus AMAN - use-case beda (leisure vs corporate, dari contoh rubric).
    r3 = await _cek_cannibalization_llm(
        "penginapan Bedugul untuk healing keluarga",
        "penginapan Bedugul untuk retreat corporate dengan ruang meeting",
    )
    check("Keluarga leisure vs corporate retreat -> AMAN (use-case beda)", r3["status"] == "AMAN", str(r3))

    print(f"\n{passed} passed, {failed} failed")
    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
