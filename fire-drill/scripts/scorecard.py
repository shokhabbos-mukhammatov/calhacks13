"""Render the scorecard to a self-contained HTML page.

    .venv\\Scripts\\python.exe scripts\\scorecard.py
    .venv\\Scripts\\python.exe scripts\\scorecard.py --open
    .venv\\Scripts\\python.exe scripts\\scorecard.py --interval clopper-pearson
    .venv\\Scripts\\python.exe scripts\\scorecard.py --hold-out lookalike-domain
    .venv\\Scripts\\python.exe scripts\\scorecard.py --replay --out demo.html

The page is the same renderer the Actor writes to REPORT.html, so what a judge
opens at the table and what a stranger finds on Apify cannot disagree.

`--replay` is the rehearsal path: it renders whatever is already in records/
and makes no model call, so the demo survives a dead network. Records are
content-addressed, so a replay shows exactly the run it was saved from.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firedrill.console import use_utf8
from firedrill.records import RECORDS_DIR, load_records
from firedrill.render import as_row, render
from firedrill.stats import INTERVALS


def commit() -> str | None:
    """The commit the page was rendered at, when there is one to name."""
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="scorecard.html", help="where to write (default scorecard.html)")
    p.add_argument("--open", action="store_true", dest="open_it", help="open it when written")
    p.add_argument("--interval", choices=sorted(INTERVALS), default="wilson",
                   help="wilson (default) or clopper-pearson, which is exact and wider")
    p.add_argument("--hold-out", action="append", default=[], metavar="FAMILY",
                   help="a tactic family the patch never saw (repeatable)")
    p.add_argument("--before", default="baseline", help="the config to compare from")
    p.add_argument("--after", help="the config to compare to (default: every patched one)")
    p.add_argument("--look", type=int, default=6, help="drills per look, to group the grid")
    p.add_argument("--records", type=Path, default=RECORDS_DIR, help="where the drills are")
    p.add_argument("--replay", action="store_true",
                   help="say on the page that this is a saved run, not a live one")
    p.add_argument("--title", default="Fire Drill")
    args = p.parse_args()

    records = load_records(args.records)
    if not records:
        sys.exit(f"no records in {args.records}; run scripts/grid.py or scripts/run_drill.py --save first")

    extra = [f"commit {commit()}"] if commit() else []
    if args.replay:
        extra.append("replayed from saved records — no model calls")

    page = render(
        [as_row(r) for r in records],
        title=args.title,
        interval_kind=args.interval,
        before=args.before,
        after=args.after,
        look=args.look,
        hold_out=args.hold_out,
        extra_meta=extra,
    )
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.write_text(page, encoding="utf-8")
    print(f"{len(records)} drills -> {out}  ({len(page) / 1024:.0f} KB, no network)")
    if args.open_it:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
