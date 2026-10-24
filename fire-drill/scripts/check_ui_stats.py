r"""Check the frontend's interval lab against the Python statistics.

    .venv\Scripts\python.exe scripts\check_ui_stats.py

The interval lab is the one place the frontend computes statistics itself, so
its port of Wilson and Clopper-Pearson (ui/src/lib/stats.ts) is compared here
with firedrill/stats.py over a grid of (k, n). Needs Node 22.6 or newer, which
can run the TypeScript file directly.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firedrill.stats import clopper_pearson, wilson

TOLERANCE = 1e-6


def main() -> None:
    out = subprocess.run(
        ["node", "--experimental-strip-types", "--no-warnings", "scripts/dump_stats.mjs"],
        cwd=ROOT / "ui", capture_output=True, text=True, timeout=60, check=True)
    worst = 0.0
    for row in json.loads(out.stdout):
        k, n = row["k"], row["n"]
        for name, ours in (("wilson", wilson(k, n)), ("cp", clopper_pearson(k, n))):
            diff = max(abs(a - b) for a, b in zip(ours, row[name]))
            worst = max(worst, diff)
            if diff > TOLERANCE:
                sys.exit(f"{name}({k}, {n}): python {ours} vs ui {row[name]}")
    print(f"ui/src/lib/stats.ts matches firedrill/stats.py on {len(json.loads(out.stdout))} "
          f"(k, n) pairs; worst difference {worst:.1e}")


if __name__ == "__main__":
    main()
