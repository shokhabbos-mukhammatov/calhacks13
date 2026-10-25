"""Run the Breach Grid: every model x hardening x tactic card, concurrently.

    .venv\\Scripts\\python.exe scripts\\grid.py --dry-run
    .venv\\Scripts\\python.exe scripts\\grid.py --cards vmt-01 vmt-02 --configs baseline patch:v1
    .venv\\Scripts\\python.exe scripts\\grid.py --cards vmt-01 --configs baseline patch:v1 --benign --max-n 12
    .venv\\Scripts\\python.exe scripts\\grid.py --cards vmt-01 vmt-02 --configs baseline --autofix

Each cell runs in **looks** of six drills and stops as soon as its interval,
widened for the number of looks planned in advance, is narrow enough. A cell
that is obviously safe or obviously broken finishes early; one near 50% keeps
running, which is where the drills are worth spending.

Attacker turns come from turns/<card>.txt; the benign pack ships with the
repository. Every drill is saved to records/, so scripts/report.py picks it
up afterwards.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from firedrill.console import use_utf8
from firedrill.drill import (
    BENIGN_CARD,
    CARDS_DIR,
    ScriptedAttacker,
    build_scenario,
    load_cards,
    make_config,
    run_drill,
)
from firedrill.grid import CellSpec, run_grid, saved
from firedrill.payments import NessieRail
from firedrill.records import save_drill
from firedrill.verify import (
    CrsFraudFinder,
    CrsReverseLookup,
    NoPhoneOwner,
    NoSenderCheck,
    RdapDomainAge,
    VendorVerifier,
)
from firedrill.victim import AnthropicModel

CARDS = {c.id: c for path in CARDS_DIR.glob("*.json") for c in load_cards(path)}
BENIGN_DIR, TURNS_DIR = ROOT / "benign", ROOT / "turns"


def turns_for(card_id: str | None, seed: int) -> list[str] | None:
    """The messages for one drill, filled in for this seed's world."""
    if card_id is None:
        packs = sorted(BENIGN_DIR.glob("*.txt"))
        card, path = BENIGN_CARD, packs[(seed - 1) % len(packs)] if packs else None
    else:
        card, path = CARDS[card_id], TURNS_DIR / f"{card_id}.txt"
    if path is None or not path.exists():
        return None
    kit = asdict(build_scenario(card, seed).kit)
    blocks = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n---\n")
    return [b.strip().format(**kit) for b in blocks if b.strip()]


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cards", nargs="*", default=[], help="card ids; needs turns/<card>.txt")
    p.add_argument("--benign", action="store_true", help="also run the honest invoice pack")
    p.add_argument("--configs", nargs="*", default=["baseline"], help="hardening levels")
    p.add_argument("--models", nargs="*", default=["claude-haiku-4-5"])
    p.add_argument("--look", type=int, default=6, help="drills per look (default 6)")
    p.add_argument("--max-n", type=int, default=24, help="most drills per cell (default 24)")
    p.add_argument("--width", type=float, default=0.45, help="stop when the adjusted interval is this narrow")
    p.add_argument("--concurrency", type=int, default=4, help="drills at once within a look")
    p.add_argument("--cells", type=int, default=2, help="cells at once")
    p.add_argument("--dry-run", action="store_true", help="list the cells and stop")
    p.add_argument("--autofix", action="store_true",
                   help="when the run leaves a cell decidedly breaching, start Droid on it "
                        "(scripts/autofix.py) and save the patch it writes")
    p.add_argument("--autofix-name", default="v2-droid", help="patch name for --autofix")
    args = p.parse_args()

    load_dotenv(ROOT / ".env")
    unknown = [c for c in args.cards if c not in CARDS]
    if unknown:
        p.error(f"unknown card(s) {', '.join(unknown)}; known: {', '.join(sorted(CARDS))}")
    missing = [c for c in args.cards if not (TURNS_DIR / f"{c}.txt").exists()]
    if missing:
        p.error(f"no attacker turns for {', '.join(missing)}: write turns/<card>.txt first")
    if not args.cards and not args.benign:
        p.error("give --cards, or --benign, or both")

    targets: list[str | None] = list(args.cards) + ([None] if args.benign else [])
    specs = [CellSpec(model, config, card)
             for model in args.models for config in args.configs for card in targets]
    seeds = list(range(1, args.max_n + 1))

    print(f"{len(specs)} cells, up to {args.max_n} drills each, in looks of {args.look}")
    for s in specs:
        print(f"  {s.label}")
    if args.dry_run:
        print("\ndry run: nothing was drilled")
        return

    rail = NessieRail.from_env(os.environ)
    verifier = VendorVerifier(RdapDomainAge(),
                              CrsFraudFinder.from_env(os.environ) or NoSenderCheck(),
                              CrsReverseLookup.from_env(os.environ) or NoPhoneOwner())

    def run_one(spec: CellSpec, seed: int):
        card = CARDS[spec.card_id] if spec.card_id else BENIGN_CARD
        messages = turns_for(spec.card_id, seed)
        config = make_config(spec.config, model=AnthropicModel(spec.model),
                             verifier=verifier, rail=rail)
        drill = run_drill(card, seed, attacker=ScriptedAttacker(messages), victim=config)
        save_drill(drill, config)
        return drill

    def is_hit(drill) -> bool:
        return drill.paid_on_file if drill.card.family == "benign" else drill.verdict.breach

    done = {"n": 0}

    def tick(spec: CellSpec, drill) -> None:
        done["n"] += 1
        mark = "HIT " if is_hit(drill) else "    "
        print(f"  {mark} {spec.label}  seed {drill.seed}", flush=True)

    started = time.monotonic()
    results = run_grid(specs, seeds, run_one=run_one, is_hit=is_hit,
                       look=args.look, max_n=args.max_n, target_width=args.width,
                       concurrency=args.concurrency, cell_concurrency=args.cells,
                       on_drill=tick)

    print("\nCELLS")
    for r in sorted(results, key=lambda r: r.spec.label):
        measure = "paid on file" if r.spec.card_id is None else "breaches"
        print(f"  {r.spec.label:<46} {r.hits}/{r.n} {measure:<13} {r.stopped}")

    ran, fixed = saved(results, args.look, args.max_n)
    print(f"\n{ran} drills in {time.monotonic() - started:.0f}s "
          f"({fixed} if every cell had run to {args.max_n}: {100 * (1 - ran / fixed):.0f}% fewer)")
    print("records written. Now:  .venv\\Scripts\\python.exe scripts\\report.py")

    # The trigger: the grid's own fresh result decides whether Droid runs.
    if args.autofix:
        from autofix import run_autofix  # scripts/ is on the path when this runs

        from firedrill.records import load_records
        print()
        for config in args.configs:
            run_autofix(load_records(), config=config, name=args.autofix_name)


if __name__ == "__main__":
    main()
