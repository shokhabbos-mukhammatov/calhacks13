"""Write a structural patch from the failing drills, with commit-reveal.

    .venv/Scripts/python scripts/remediate.py --hold-out lookalike-domain --agent claude-code --name v1
    .venv/Scripts/python scripts/remediate.py --hold-out lookalike-domain --agent droid --name v1-droid
    .venv/Scripts/python scripts/remediate.py --dry-run            # show the brief, call nothing
    .venv/Scripts/python scripts/remediate.py --reveal v1          # after the re-run

Order matters and the script enforces it:
1. Commit to the held-out drills (a salted Merkle root, written to
   commitments/<name>.commit.json) BEFORE any patch exists. Commit that file
   to git, so its timestamp predates the patch.
2. Summarise the failing drills of the TRAINING families only, as actions and
   ledger outcomes with no message text (firedrill.failures), and hand them to
   a code agent behind the port (ADR-0004).
3. Save the PatchDiff to patches/<name>.json. Re-run drills against it with
   scripts/run_drill.py --config patch:<name>, including the held-out family.
4. --reveal writes commitments/<name>.reveal.json (drills + salts) and checks
   the root still matches. Publishing that file is your call: it contains the
   drills themselves.
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
from firedrill.commit import commit, verify
from firedrill.failures import as_json, failing
from firedrill.records import RECORDS_DIR, load_records
from firedrill.remediate import AGENTS, PATCHES_DIR, build_brief

COMMITMENTS_DIR = ROOT / "commitments"


def families_of(records: list[dict]) -> set[str]:
    return {r["card"]["family"] for r in records if r["card"]["family"] != "benign"}


def do_reveal(name: str) -> None:
    commit_path = COMMITMENTS_DIR / f"{name}.commit.json"
    salts_path = COMMITMENTS_DIR / f"{name}.salts.json"
    if not (commit_path.exists() and salts_path.exists()):
        sys.exit(f"need both {commit_path.name} and {salts_path.name}")
    commitment = json.loads(commit_path.read_text(encoding="utf-8"))
    salts = json.loads(salts_path.read_text(encoding="utf-8"))
    held = [r for r in load_records() if r["card"]["family"] in commitment["families"]]
    ok = verify(commitment, held, salts)
    reveal = COMMITMENTS_DIR / f"{name}.reveal.json"
    reveal.write_text(json.dumps({"commitment": commitment, "salts": salts, "drills": held}, indent=1),
                      encoding="utf-8")
    print(f"root recomputes: {'MATCHES' if ok else 'DOES NOT MATCH'}")
    print(f"wrote {reveal} ({len(held)} drills). Publishing it is your call: it holds the drills themselves.")
    sys.exit(0 if ok else 1)


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--hold-out", action="append", default=[], metavar="FAMILY",
                   help="a tactic family the patch never sees (repeatable)")
    p.add_argument("--agent", choices=sorted(AGENTS), default="fake")
    p.add_argument("--agent-model", help="model id for the code agent (its own default otherwise)")
    p.add_argument("--name", default="v1", help="patch and commitment name (default: v1)")
    p.add_argument("--policy", default="", help="the policy being replaced (default: none)")
    p.add_argument("--dry-run", action="store_true", help="print the brief and stop")
    p.add_argument("--reveal", metavar="NAME", help="reveal a commitment after the re-run")
    args = p.parse_args()

    load_dotenv(ROOT / ".env")
    COMMITMENTS_DIR.mkdir(exist_ok=True)
    if args.reveal:
        do_reveal(args.reveal)

    records = load_records()
    if not records:
        sys.exit(f"no records in {RECORDS_DIR}; run scripts/run_drill.py --save first")
    known = families_of(records)
    unknown = [f for f in args.hold_out if f not in known]
    if unknown:
        sys.exit(f"no drills for held-out {', '.join(unknown)}; have: {', '.join(sorted(known))}")
    train = sorted(known - set(args.hold_out))
    if not train:
        sys.exit("every family is held out; nothing to learn from")

    # 1. Commit to the held-out drills before the patch exists.
    held = [r for r in records if r["card"]["family"] in args.hold_out]
    if held and not args.dry_run:
        commitment, salts = commit(held)
        (COMMITMENTS_DIR / f"{args.name}.commit.json").write_text(
            json.dumps(commitment.to_dict(), indent=1), encoding="utf-8")
        (COMMITMENTS_DIR / f"{args.name}.salts.json").write_text(json.dumps(salts), encoding="utf-8")
        print(f"committed to {commitment.count} held-out drills ({', '.join(commitment.families)})")
        print(f"  root {commitment.root}")
        print(f"  -> commitments/{args.name}.commit.json: commit this to git NOW, before the patch")
    elif args.hold_out:
        print(f"no saved drills for held-out {', '.join(args.hold_out)}: nothing to commit to yet")

    # 2. Summarise the failing training drills: actions and outcomes, no message text.
    failures = failing(records, families=train)
    print(f"\ntraining families: {', '.join(train)}")
    print(f"held out:          {', '.join(args.hold_out) or '(none)'}")
    print(f"failing drills:    {len(failures)} of {sum(1 for r in records if r['card']['family'] in train)}")
    if not failures:
        sys.exit("no failing drills in the training families: nothing to patch")

    if args.dry_run:
        print("\n=== brief ===\n" + build_brief(failures, args.policy, train))
        return

    # 3. The code agent writes the patch.
    print(f"\nasking {args.agent} for a patch...")
    agent = AGENTS[args.agent](model=args.agent_model) if args.agent != "fake" else AGENTS[args.agent]()
    patch = agent.patch(failing=failures, policy=args.policy, train_families=train)
    path = patch.save(args.name)
    print(f"\npolicy:\n  {patch.policy}")
    print("tool scope:")
    for tool, scope in sorted(patch.tool_scope.items()):
        print(f"  {tool:<28} {scope}")
    if patch.rationale:
        print("rationale:")
        for line in patch.rationale:
            print(f"  - {line}")
    print(f"\nsaved {path} (author: {patch.author})")
    print(f"re-run with:  scripts/run_drill.py <card> --seed N --turns ... --config patch:{args.name} --save")


if __name__ == "__main__":
    main()
