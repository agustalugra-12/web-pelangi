"""Smoke test murni (tanpa DB/API) utk expand_title_pool.py - fungsi pure yang bisa
dites tanpa biaya. Live end-to-end (embedding dedup, LLM generation, dedup lintas
batch) divalidasi via pilot run manual (1 cluster, target kecil) sebelum campaign
penuh - lihat TITLE_EXPANSION_REPORT.md.

Jalankan: venv/bin/python -m scripts.test_expand_title_pool
"""
from scripts.expand_title_pool import split_target_evenly, campaign_tag

passed = 0
failed = 0


def check(name: str, condition: bool):
    global passed, failed
    if condition:
        passed += 1
        print(f"✓ {name}")
    else:
        failed += 1
        print(f"✗ {name}")


def main():
    clusters = [f"C{i}" for i in range(17)]

    # Test: 300 / 17 cluster = 17 sisa 11 -> 11 cluster dapat 18, 6 cluster dapat 17.
    targets = split_target_evenly(300, clusters, {})
    check("Total tepat 300 (tidak lebih/kurang)", sum(targets.values()) == 300)
    check("Semua cluster dapat 17 atau 18 (merata, bukan 300/cluster)", all(v in (17, 18) for v in targets.values()))
    check("Tepat 11 cluster dapat 18 (sisa pembagian)", sum(1 for v in targets.values() if v == 18) == 300 % 17)

    # Test: remainder harus jatuh ke cluster demand TERTINGGI (bukan acak/urutan dict).
    demand = {"C0": 1000, "C1": 500}
    targets_demand = split_target_evenly(300, clusters, demand)
    check("Remainder diprioritaskan ke cluster demand tertinggi (GSC riil)", targets_demand["C0"] == 18)

    # Test: pembagian genap tanpa sisa.
    targets_even = split_target_evenly(34, clusters[:17], {})
    check("Pembagian genap (34/17=2) - semua dapat persis 2", all(v == 2 for v in targets_even.values()))

    # Test: campaign_tag unik per situs (idempotency key harus beda Pelangi vs Harmoni).
    check("Tag kampanye beda per situs (tidak collide Pelangi/Harmoni)", campaign_tag("pelangi") != campaign_tag("harmoni"))

    print(f"\n{passed} passed, {failed} failed")
    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
