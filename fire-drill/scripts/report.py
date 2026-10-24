"""Breach and utility rates over saved drills (records/), with Wilson 95% intervals.

    .venv/Scripts/python scripts/report.py

One row per (victim config, tactic family). Attack families report the attack
success rate: the share of drills that ended in a breach. The benign family
reports utility: the share paid to the account on file. Rank hardening
levels by the interval's lower bound, never by the bare rate.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from firedrill.records import RECORDS_DIR, load_records
from firedrill.stats import wilson


def main() -> None:
    records = load_records()
    if not records:
        sys.exit(f"no records in {RECORDS_DIR}; run scripts/run_drill.py with --save first")
    cells: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])  # (config, family) -> [hits, n]
    for r in records:
        key = (r["config"]["name"], r["card"]["family"])
        hit = r["paid_on_file"] if r["card"]["family"] == "benign" else r["verdict"]["breach"]
        cells[key][0] += int(hit)
        cells[key][1] += 1

    print(f"{'config':<14} {'family':<26} {'measure':<8} {'n':>3} {'hits':>4} {'rate':>6}  95% interval")
    for (config, family), (k, n) in sorted(cells.items()):
        low, high = wilson(k, n)
        measure = "utility" if family == "benign" else "breach"
        print(f"{config:<14} {family:<26} {measure:<8} {n:>3} {k:>4} {k / n:>6.2f}  [{low:.2f}, {high:.2f}]")
    print(f"\n{len(records)} drills in {RECORDS_DIR}")


if __name__ == "__main__":
    main()
