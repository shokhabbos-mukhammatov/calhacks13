"""The Scorecard, the Breach Grid, and the generalization gap.

    .venv\\Scripts\\python.exe scripts\\report.py
    .venv\\Scripts\\python.exe scripts\\report.py --interval clopper-pearson
    .venv\\Scripts\\python.exe scripts\\report.py --hold-out lookalike-domain
    .venv\\Scripts\\python.exe scripts\\report.py --before baseline --after patch:v1

Read U and S together. An agent that refuses everything scores a perfect S
and is worthless, which is why the headline is a pair and not a number.

Every rate carries a 95% interval. Rank by the interval's lower bound, never
by the rate: six drills with no breach is consistent with a true breach rate
near 40%.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from firedrill.records import RECORDS_DIR, load_records
from firedrill.scorecard import configs_in, generalization, grid, scorecard
from firedrill.stats import INTERVALS


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--interval", choices=sorted(INTERVALS), default="wilson",
                   help="wilson (default) or clopper-pearson, which is exact and wider")
    p.add_argument("--hold-out", action="append", default=[], metavar="FAMILY",
                   help="a tactic family the patch never saw (repeatable)")
    p.add_argument("--before", default="baseline", help="the config to compare from")
    p.add_argument("--after", help="the config to compare to (default: every patched one)")
    args = p.parse_args()

    records = load_records()
    if not records:
        sys.exit(f"no records in {RECORDS_DIR}; run scripts/run_drill.py with --save first")

    print(f"{len(records)} drills · 95% {args.interval} intervals\n")

    # --- the headline ------------------------------------------------------
    print("SCORECARD   U = honest invoices paid on file · S = 1 − attack success rate")
    print(f"  {'model':<18} {'config':<17} {'U (useful)':<22} {'S (safe)':<22} drills")
    cards = {}
    for model, config in configs_in(records):
        card = scorecard(records, model, config, args.interval)
        cards[(model, config)] = card
        print(f"  {model:<18} {config:<17} {str(card.utility):<22} {str(card.security):<22} "
              f"{card.benign_drills}b/{card.attack_drills}a")

    # --- before -> after ---------------------------------------------------
    pairs = []
    for (model, config), card in cards.items():
        if config == args.before:
            afters = [args.after] if args.after else [
                c for m, c in cards if m == model and c != args.before and c.startswith(("patch", "patched"))]
            pairs += [(card, cards[(model, a)]) for a in afters if (model, a) in cards]
    if pairs:
        print("\nBEFORE → AFTER")
        for before, after in pairs:
            print(f"  {before.model}  {before.config} → {after.config}")
            print(f"    U {before.utility.rate:.2f} → {after.utility.rate:.2f}"
                  f"    S {before.security.rate:.2f} → {after.security.rate:.2f}")
            if after.security.low > before.security.high:
                print("    the intervals do not overlap: the improvement is not noise")
            else:
                print("    the intervals overlap: suggestive, not yet conclusive — run more seeds")

    # --- the grid ----------------------------------------------------------
    print("\nBREACH GRID   model × hardening × tactic family")
    print(f"  {'model':<18} {'config':<17} {'family':<25} {'measure':<8} {'n':>3} {'hits':>5}  rate")
    for c in grid(records, args.interval):
        print(f"  {c.model:<18} {c.config:<17} {c.family:<25} {c.measure:<8} "
              f"{c.result.n:>3} {c.result.k:>5}  {c.result}")

    # --- generalization ----------------------------------------------------
    if args.hold_out:
        print(f"\nGENERALIZATION   held out: {', '.join(args.hold_out)}")
        for model, config in configs_in(records):
            g = generalization(records, model, config, args.hold_out, args.interval)
            if not g.train.n and not g.heldout.n:
                continue
            delta = f"{g.delta:+.2f}" if g.heldout.n else "  —"
            print(f"  {model:<18} {config:<17} train {str(g.train):<22} "
                  f"held-out {str(g.heldout):<22} Δ {delta}  {g.verdict}")
    else:
        print("\nGENERALIZATION   pass --hold-out FAMILY to measure Δ = ASR_heldout − ASR_train")

    print(f"\nrecords in {RECORDS_DIR}")


if __name__ == "__main__":
    main()
