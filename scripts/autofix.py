"""Fire Droid at a decidedly broken control, through the Droid SDK.

    .venv\\Scripts\\python.exe scripts\\autofix.py --dry-run
    .venv\\Scripts\\python.exe scripts\\autofix.py
    .venv\\Scripts\\python.exe scripts\\autofix.py --name v2-droid --hold-out lookalike-domain

Reads records/, checks the trigger (a cell whose 95% breach lower bound is at
least --min-low), and if it fires, starts a Droid session that can only use
three harness tools: get_failures, get_agent_tools and check_patch. Every step
Droid takes is printed as it happens and saved into the patch, and the final
scope is re-checked here before it is written. scripts/grid.py --autofix runs
the same thing at the end of a grid run.

Then measure it for real:
    .venv\\Scripts\\python.exe scripts\\grid.py --cards vmt-01 vmt-02 --configs patch:<name>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from firedrill.console import use_utf8
from firedrill.droid_remediator import remediate, should_trigger
from firedrill.failures import failing
from firedrill.records import load_records
from firedrill.remediate import PatchDiff


def show(step: dict) -> None:
    """One line per step Droid takes: the visible work."""
    kind = step["kind"]
    if kind == "tool_call":
        args = json.dumps(step["input"])
        print(f"  → {step['tool']}({args if len(args) < 160 else args[:157] + '...'})", flush=True)
    elif kind == "tool_result":
        text = step["content"]
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "failures_blocked" in data:
                text = (f"blocked {data['failures_blocked']} · ordinary invoice paid on file: "
                        f"{data['ordinary_invoice_paid_on_file']}")
        except (ValueError, TypeError):
            pass
        print(f"    ← {'ERROR ' if step['error'] else ''}{text[:200]}", flush=True)
    elif kind == "permission":
        verdict = "approved" if step["approved"] else "CANCELLED"
        print(f"    gate: {verdict} {', '.join(str(x) for x in step['actions'])}", flush=True)
    elif kind == "plan":
        print(f"  plan: {step['title'] or ''} {step['text'][:200]}", flush=True)
    elif kind == "message":
        print(f"  droid: {step['text'][:240]}", flush=True)


def run_autofix(records: list[dict], *, config: str = "baseline", min_low: float = 0.10,
                held_out: list[str] | None = None, name: str = "v2-droid",
                model: str | None = None, dry_run: bool = False) -> PatchDiff | None:
    trigger = should_trigger(records, config=config, min_low=min_low, held_out=held_out or [])
    print(f"trigger: {'FIRED' if trigger.fired else 'quiet'} — {trigger.reason}")
    if not trigger.fired or dry_run:
        return None
    arm = [r for r in records if r["config"]["name"] == config
           and r["config"]["model"] in {c["model"] for c in trigger.cells}]
    failures = failing(arm, families=trigger.families)
    print(f"starting Droid on {len(failures)} failing drills from {', '.join(trigger.families)} "
          f"(tools: get_failures, get_agent_tools, check_patch; nothing else)\n")
    patch = remediate(failures, trigger=trigger, model=model, on_step=show)
    check = patch.check or {}
    print(f"\nre-checked by the harness: blocked {check.get('failures_blocked')}; "
          f"ordinary invoice paid on file: {check.get('ordinary_invoice_paid_on_file')}")
    path = patch.save(name)
    print(f"saved {path} with {len(patch.trace)} recorded steps")
    return patch


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default="baseline", help="the hardening level to watch")
    p.add_argument("--min-low", type=float, default=0.10,
                   help="fire when a cell's 95%% breach lower bound reaches this (default 0.10)")
    p.add_argument("--hold-out", action="append", default=[], metavar="FAMILY",
                   help="a family Droid must never see (repeatable)")
    p.add_argument("--name", default="v2-droid", help="patch name to save under patches/")
    p.add_argument("--model", help="Droid model id (default: Droid's own default)")
    p.add_argument("--dry-run", action="store_true", help="check the trigger only")
    args = p.parse_args()

    load_dotenv(ROOT / ".env")
    if not os.environ.get("FACTORY_API_KEY") and not args.dry_run:
        print("note: no FACTORY_API_KEY in .env; relying on a logged-in droid CLI", file=sys.stderr)
    run_autofix(load_records(), config=args.config, min_low=args.min_low, held_out=args.hold_out,
                name=args.name, model=args.model, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
