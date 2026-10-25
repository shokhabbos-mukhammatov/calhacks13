"""Export everything the frontend shows into one JSON file.

    .venv\\Scripts\\python.exe scripts\\export_ui.py
    .venv\\Scripts\\python.exe scripts\\export_ui.py --withhold-attacks

The app reads `ui/src/data/fire-drill.json` and nothing else, so it builds to
a single file that works with no network.

Every statistic is computed here with the same code `scripts/report.py` uses;
the frontend draws numbers, it never derives them. The one exception is the
interactive interval calculator, which recomputes Wilson and Clopper-Pearson
live, and a test below the export keeps its two implementations honest.

Each drill is also **replayed through the real Ledger**, tool call by tool
call, so the replay view shows the ledger state the Scorer actually read at
every step. If a replay ever ends somewhere other than where the recorded
drill ended, the export fails rather than animate a story the ledger does not
tell.

`--withhold-attacks` drops the attacker's message text (bodies and subjects)
and keeps everything else, for a build that has to leave the wording out.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firedrill.console import use_utf8
from firedrill.drill import CARDS_DIR, load_cards
from firedrill.elastic import BREACH_TOOL, DRILL_INDEX
from firedrill.failures import summarize
from firedrill.ledger import Ledger
from firedrill.records import RECORDS_DIR, load_records
from firedrill.scorecard import BENIGN, configs_in, grid, scorecard
from firedrill.scorer import score
from firedrill.stats import clopper_pearson, fisher_exact, wilson
from firedrill.victim import ROLE, TOOLS

OUT = ROOT / "ui" / "src" / "data" / "fire-drill.json"
PATCHES_DIR = ROOT / "patches"

LIVE = {
    "phone": "(484) 779-8381",
    "phone_e164": "+14847798381",
    "judge_card": {
        "vendor": "Northwind Traders",
        "invoice": "INV-7833",
        "amount": 34950,
        "account": "ACCT-44256213",
        "callback": "+1-415-555-0190",
        "on_file": "+1-415-555-0156",
    },
    "actors": [
        {"name": "fire-drill", "role": "Drill runner", "url": "https://apify.com/shohabbos_m/fire-drill"},
        {"name": "ap-practice-target", "role": "Standby target agent",
         "url": "https://apify.com/shohabbos_m/ap-practice-target"},
    ],
    "standby": "https://c2tHmrAQShJ2Rh8KF.apify.actor",
    "cartesia_agent": "Lakeside AP line (Fire Drill)",
    "elastic_index": DRILL_INDEX,
    "elastic_tool": BREACH_TOOL["id"],
    "elastic_query": BREACH_TOOL["configuration"]["query"],
    "repo": "https://github.com/shokhabbos-mukhammatov/calhacks13",
}

SPONSORS = [
    {"name": "Anthropic", "role": "The agent under test, and Claude Code writing the fix",
     "where": "firedrill/victim.py · firedrill/remediate.py"},
    {"name": "Apify", "role": "Two published Actors: the drill runner and a Standby target "
     "whose state lives in a shared key-value store", "where": "actors/"},
    {"name": "Cartesia", "role": "The voice channel: a phone line relayed into the same agent "
     "and ledger a text drill uses", "where": "actors/victim-standby · /voice/relay"},
    {"name": "Capital One", "role": "Nessie mirrors every approved payment into a sandbox bank",
     "where": "firedrill/payments.py"},
    {"name": "CRS", "role": "Fraud Finder scores the sender's address, live against the sandbox, "
     "whenever the agent asks Vendor Verify for evidence",
     "where": "firedrill/verify.py · actors/victim-standby"},
    {"name": "Factory", "role": "Droid, through the Droid SDK, is the remediation engine: the "
     "breach grid triggers it, it can touch only three harness tools, and it checks its own patch",
     "where": "firedrill/droid_remediator.py · scripts/autofix.py"},
    {"name": "Elastic", "role": "The drill corpus, and an Agent Builder tool that answers "
     "which drills breached and where", "where": "firedrill/elastic.py"},
]


def commit_id() -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "rate": (k / n) if n else None,
            "wilson": list(wilson(k, n)), "cp": list(clopper_pearson(k, n)) if n else [0.0, 1.0]}


def flipped(r: dict) -> dict:
    """S = 1 - ASR: same k counted the other way, interval flipped end for end."""
    k, n = r["n"] - r["k"], r["n"]
    return {"k": k, "n": n, "rate": (k / n) if n else None,
            "wilson": [1 - r["wilson"][1], 1 - r["wilson"][0]],
            "cp": [1 - r["cp"][1], 1 - r["cp"][0]]}


# --- the ledger, replayed ----------------------------------------------------
def replay(record: dict) -> list[dict]:
    """Ledger state after every tool call, applied through the real Ledger.

    The record holds what each call returned; this re-applies the calls that
    succeeded and snapshots the state, so the frontend animates exactly what
    the Scorer read. Refused calls (a hardening gate, a bad input) change
    nothing, which is the point of the gate."""
    kit = record["kit"]
    ledger = Ledger()
    ledger.add_vendor(kit["vendor_id"], on_file_number=kit["on_file_phone"],
                      account=kit["approved_account"])
    ledger.add_invoice(kit["invoice_id"], vendor_id=kit["vendor_id"], amount=int(kit["amount"]))

    def snap() -> dict:
        state = ledger.snapshot()
        v = state.vendors[kit["vendor_id"]]
        verdict = score(state)
        return {
            "active_account": v.active_account,
            "approved_accounts": sorted(v.approved_accounts),
            "payments": [{"invoice_id": p.invoice_id, "account": p.account,
                          "amount": p.amount, "approved": p.approved} for p in state.payments],
            "callbacks": [{"number": n, "confirmed": c} for _, n, c in state.callbacks],
            "canary": list(state.canary_hits),
            "verdict": {"breach": verdict.breach, "oob": verdict.oob, "canary": verdict.canary},
        }

    steps = [snap()]
    for call in record["tool_calls"]:
        if not call.get("error"):
            tool, args = call["tool"], call["input"]
            try:
                if tool == "change_vendor_bank_details":
                    ledger.change_vendor_bank_details(args["vendor_id"],
                                                      new_account=args["new_account"])
                elif tool == "call_vendor":
                    confirmed = "they confirmed" in str(call.get("result", ""))
                    ledger.record_callback(args["vendor_id"], number_called=args["phone_number"],
                                           confirmed=confirmed)
                elif tool == "approve_payment":
                    ledger.approve_payment(args["invoice_id"])
                elif tool == "export_vendor_master":
                    ledger.call_canary("export_vendor_master")
            except KeyError:
                pass   # the agent named a vendor or invoice that does not exist
        steps.append(snap())

    final = steps[-1]
    recorded = [(p["account"], p["amount"], p["approved"]) for p in record["payments"]]
    replayed = [(p["account"], p["amount"], p["approved"]) for p in final["payments"]]
    if recorded != replayed or final["verdict"]["breach"] != record["verdict"]["breach"]:
        raise SystemExit(f"replay of {record['card']['id']}-s{record['seed']} "
                         f"[{record['config']['name']}] does not reach the recorded ledger: "
                         f"{replayed} vs {recorded}")
    return steps


def drill(record: dict, withhold: bool) -> dict:
    transcript = []
    for t in record["transcript"]:
        transcript.append({
            "turn": t["turn"], "sender": t["sender"],
            "subject": None if withhold else t.get("subject"),
            "body": "[attacker message withheld from the public build]" if withhold and
                    record["card"]["family"] != BENIGN else t["body"],
            "reply": t["reply"],
        })
    return {
        "id": f"{record['card']['id']}-s{record['seed']}-{record['config']['name']}-"
              f"{record['config']['model']}",
        "label": f"{record['card']['id']}-s{record['seed']}",
        "card_id": record["card"]["id"],
        "family": record["card"]["family"],
        "channel": record["card"]["channel"],
        "seed": record["seed"],
        "config": record["config"]["name"],
        "model": record["config"]["model"],
        "kit": record["kit"],
        "transcript": transcript,
        "tool_calls": [{"turn": c["turn"], "tool": c["tool"], "input": c["input"],
                        "result": c.get("result"), "error": bool(c.get("error"))}
                       for c in record["tool_calls"]],
        "ledger": replay(record),
        "verdict": record["verdict"],
        "cap_turn": record["cap_turn"],
        "ended_by": record["ended_by"],
        "paid_on_file": record["paid_on_file"],
        "saved_at": record.get("saved_at"),
    }


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--records", type=Path, default=RECORDS_DIR)
    p.add_argument("--withhold-attacks", action="store_true",
                   help="drop the attacker's message text, for a public build")
    args = p.parse_args()

    records = load_records(args.records)
    if not records:
        sys.exit(f"no records in {args.records}")

    # --- the headline pair: the before/after with the most drills behind it --
    cards = {(m, c): scorecard(records, m, c) for m, c in configs_in(records)}
    pairs = []
    for (model, config), before in cards.items():
        if config != "baseline":
            continue
        for (m2, c2), after in cards.items():
            if m2 == model and c2.startswith("patch"):
                pairs.append((before, after))
    pairs.sort(key=lambda p: -min(p[0].attack_drills, p[1].attack_drills))
    headline = None
    if pairs:
        b, a = pairs[0]
        bb, ab = b.attack_drills - b.security.k, a.attack_drills - a.security.k
        one, two = fisher_exact(bb, b.attack_drills - bb, ab, a.attack_drills - ab)
        headline = {"model": b.model, "before": b.config, "after": a.config,
                    "before_breaches": bb, "before_n": b.attack_drills,
                    "after_breaches": ab, "after_n": a.attack_drills,
                    "fisher_one_sided": one, "fisher_two_sided": two}

    scorecards = []
    for (model, config), sc in cards.items():
        attacks = [r for r in records if r["card"]["family"] != BENIGN
                   and r["config"]["model"] == model and r["config"]["name"] == config]
        benign = [r for r in records if r["card"]["family"] == BENIGN
                  and r["config"]["model"] == model and r["config"]["name"] == config]
        asr = rate(sum(r["verdict"]["breach"] for r in attacks), len(attacks))
        scorecards.append({
            "model": model, "config": config,
            "asr": asr, "s": flipped(asr),
            "u": rate(sum(bool(r["paid_on_file"]) for r in benign), len(benign)),
        })

    cells = []
    for c in grid(records):
        if c.family == BENIGN:
            continue
        for card_id in sorted({r["card"]["id"] for r in records
                               if r["config"]["model"] == c.model and r["config"]["name"] == c.config
                               and r["card"]["family"] == c.family}):
            rs = [r for r in records if r["config"]["model"] == c.model and
                  r["config"]["name"] == c.config and r["card"]["id"] == card_id]
            cell = rate(sum(r["verdict"]["breach"] for r in rs), len(rs))
            cell.update({"model": c.model, "config": c.config, "card_id": card_id,
                         "family": c.family,
                         "drills": [{"seed": r["seed"], "breach": r["verdict"]["breach"],
                                     "cap_turn": r["cap_turn"]}
                                    for r in sorted(rs, key=lambda r: r["seed"])]})
            cells.append(cell)

    # The redaction the Remediator sees: one breaching drill, as actions only.
    example = next((r for r in records if r["verdict"]["breach"]
                    and r["card"]["id"] == "vmt-02" and r["config"]["name"] == "baseline"), None)
    failure = None
    if example:
        failure = {"drill": f"{example['card']['id']}-s{example['seed']}",
                   "kit": example["kit"],
                   "tool_calls": [{"turn": c["turn"], "tool": c["tool"], "input": c["input"]}
                                  for c in example["tool_calls"]],
                   "summary": summarize(example).to_dict()}

    patches = {}
    for path in sorted(PATCHES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        patches[path.stem] = {k: data.get(k) for k in ("policy", "tool_scope", "rationale",
                                                         "author", "tests", "trace", "check",
                                                         "trigger")}

    out = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "commit": commit_id(),
            "records": len(records),
            "models": sorted({r["config"]["model"] for r in records}),
            "attacks_withheld": args.withhold_attacks,
        },
        "role": ROLE,
        "tools": [{"name": t["name"], "description": t["description"]} for t in TOOLS],
        "cards": [c.__dict__ for path in sorted(CARDS_DIR.glob("*.json"))
                  for c in load_cards(path)],
        "patches": patches,
        "headline": headline,
        "scorecards": scorecards,
        "cells": cells,
        "failure_example": failure,
        "drills": [drill(r, args.withhold_attacks) for r in
                   sorted(records, key=lambda r: (r["card"]["id"], r["config"]["name"],
                                                  r["config"]["model"], r["seed"]))],
        "live": LIVE,
        "sponsors": SPONSORS,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, separators=(",", ":"))
    args.out.write_text(text, encoding="utf-8")
    print(f"{len(records)} drills, {len(cells)} grid cells, {len(patches)} patches -> "
          f"{args.out} ({len(text) / 1024:.0f} KB)"
          + ("  [attacker text withheld]" if args.withhold_attacks else ""))


if __name__ == "__main__":
    main()
