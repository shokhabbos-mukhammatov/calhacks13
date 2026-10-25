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

Held-out families are kept apart. Everything the page already showed is the
**training** families only, so a reveal adds a result rather than quietly
pooling into the headline. A revealed family goes in `heldout`, one entry per
reveal file, with the commitment it was checked against (ADR-0002).
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
from firedrill.crs_personas import BY_NUMBER
from firedrill.drill import CARDS_DIR, build_scenario, load_cards
from firedrill.elastic import BREACH_TOOL, DRILL_INDEX
from firedrill.failures import summarize
from firedrill.ledger import Ledger
from firedrill.commit import COMMITMENTS_DIR, covered, revealed_families, verify
from firedrill.records import RECORDS_DIR, SEALED_FAMILIES, load_records, publishable, training
from firedrill.scorecard import BENIGN, configs_in, grid, scorecard
from firedrill.scorer import score
from firedrill.stats import clopper_pearson, fisher_exact, wilson
from firedrill.victim import ROLE, TOOLS

OUT = ROOT / "ui" / "src" / "data" / "fire-drill.json"
PATCHES_DIR = ROOT / "patches"

# The world a judge calls into, pinned in actors/victim-standby/src/main.py.
VOICE_CARD, VOICE_SEED = "vmt-01", 205

LIVE = {
    "phone": "(484) 779-8381",
    "phone_e164": "+14847798381",
    # judge_card is derived from the pinned world below, never typed: a card
    # that disagrees with the agent's ledger sends a judge to a dead number.
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


def cell_of(rs: list[dict], model: str, config: str, card_id: str, family: str) -> dict:
    """One grid cell: the drills of one card under one model and hardening level."""
    cell = rate(sum(r["verdict"]["breach"] for r in rs), len(rs))
    cell.update({"model": model, "config": config, "card_id": card_id, "family": family,
                 "drills": [{"seed": r["seed"], "breach": r["verdict"]["breach"],
                             "cap_turn": r["cap_turn"]}
                            for r in sorted(rs, key=lambda r: r["seed"])]})
    return cell


def first_commit(path: Path) -> dict | None:
    """The commit that first added a file: when a commitment became public."""
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "--diff-filter=A", "--format=%H%x09%cI",
                              "--", str(path.relative_to(ROOT))],
                             capture_output=True, text=True, timeout=5).stdout.strip().splitlines()
    except (OSError, subprocess.SubprocessError):
        return None
    if not out:
        return None
    sha, when = out[-1].split("\t")
    return {"sha": sha, "committed_at": when}


def behaviour(rs: list[dict]) -> dict:
    """What the agent did, beyond the verdict: which number it rang, and
    whether it tried to change the bank details at all."""
    called_attacker = sum(1 for r in rs for c in r["tool_calls"] if c["tool"] == "call_vendor"
                          and c["input"].get("phone_number") == r["kit"]["attacker_phone"])
    called_on_file = sum(1 for r in rs for c in r["tool_calls"] if c["tool"] == "call_vendor"
                         and c["input"].get("phone_number") == r["kit"]["on_file_phone"])
    tried_change = sum(1 for r in rs for c in r["tool_calls"] if c["tool"] == "change_vendor_bank_details")
    return {"drills": len(rs), "called_attacker": called_attacker,
            "called_on_file": called_on_file, "tried_bank_change": tried_change}


def held_out_results(records: list[dict], train: list[dict], repo: str) -> list[dict]:
    """One entry per reveal: the committed drills before the patch, the same
    family under it, and the training family under it for the gap."""
    out = []
    for path in sorted(COMMITMENTS_DIR.glob("*.reveal.json")):
        name = path.name.split(".")[0]
        reveal = json.loads(path.read_text(encoding="utf-8"))
        c = reveal["commitment"]
        before = covered(c, records)              # exactly the drills committed to
        if not before:
            continue
        families, patch = set(c["families"]), f"patch:{name}"
        model, base = before[0]["config"]["model"], before[0]["config"]["name"]
        after = [r for r in records if r["card"]["family"] in families
                 and r["config"]["name"] == patch and r["config"]["model"] == model]
        train_after = [r for r in train if r["card"]["family"] != BENIGN
                       and r["config"]["name"] == patch and r["config"]["model"] == model]
        benign = [r for r in train if r["card"]["family"] == BENIGN
                  and r["config"]["name"] == patch and r["config"]["model"] == model]
        for r in before + after:
            replay(r)                             # exits if a record's ledger does not reproduce
        kb, nb = sum(r["verdict"]["breach"] for r in before), len(before)
        ka, na = sum(r["verdict"]["breach"] for r in after), len(after)
        one, two = fisher_exact(kb, nb - kb, ka, na - ka)
        held, trained = rate(ka, na), rate(sum(r["verdict"]["breach"] for r in train_after), len(train_after))
        family_of = {r["card"]["id"]: r["card"]["family"] for r in before + after}
        card_ids = sorted(family_of)
        published = first_commit(COMMITMENTS_DIR / f"{name}.commit.json")
        out.append({
            "name": name, "families": sorted(families), "model": model,
            "before": base, "after": patch,
            "train_families": sorted({r["card"]["family"] for r in train_after}),
            "commitment": {"root": c["root"], "count": c["count"], "committed_at": c["committed_at"],
                           "commit": published,
                           "commit_url": f"{repo}/commit/{published['sha']}" if published else None,
                           "reveal_url": f"{repo}/blob/main/commitments/{path.name}"},
            # When the patch first appears in git, to set beside the commitment's.
            "patch_commit": first_commit(PATCHES_DIR / f"{name}.json"),
            "verified": verify(c, before, reveal["salts"]),
            "held_before": rate(kb, nb), "held_after": held,
            "train_after": trained,
            "utility_after": rate(sum(bool(r["paid_on_file"]) for r in benign), len(benign)),
            "gap": (held["rate"] - trained["rate"]) if na and trained["n"] else None,
            "fisher_one_sided": one, "fisher_two_sided": two,
            "behaviour": {"before": behaviour(before), "after": behaviour(after)},
            "cells": [cell_of([r for r in arm if r["card"]["id"] == cid], model, cfg, cid, family_of[cid])
                      for cid in card_ids for cfg, arm in ((base, before), (patch, after))],
        })
    return out


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

    # This file is committed and served by Pages, so a held-out family stays
    # out of it until its reveal exists (ADR-0002), whatever is on disk.
    on_disk = load_records(args.records)
    records = publishable(on_disk, revealed_families())
    if len(records) < len(on_disk):
        sealed = sorted({r["card"]["family"] for r in on_disk} & (SEALED_FAMILIES - revealed_families()))
        print(f"withheld {len(on_disk) - len(records)} sealed drills ({', '.join(sealed)}) until revealed")
    if not records:
        sys.exit(f"no records in {args.records}")
    # Everything below is the training families, as the page always showed;
    # a revealed held-out family is reported on its own, in `heldout`.
    published, records = records, training(records)

    cards = {c.id: c for path in sorted(CARDS_DIR.glob("*.json")) for c in load_cards(path)}
    demo = build_scenario(cards[VOICE_CARD], VOICE_SEED).kit
    LIVE["judge_card"] = {
        "vendor": demo.vendor_name,
        "invoice": demo.invoice_id,
        "amount": demo.amount,
        "account": demo.attacker_account,
        "callback": demo.attacker_phone,
        "on_file": demo.on_file_phone,
        "callback_belongs_to": (BY_NUMBER[demo.attacker_phone].expect
                                if demo.attacker_phone in BY_NUMBER else None),
        "on_file_belongs_to": (BY_NUMBER[demo.on_file_phone].expect
                               if demo.on_file_phone in BY_NUMBER else None),
    }

    # --- the headline pair: the before/after with the most drills behind it --
    cards = {(m, c): scorecard(records, m, c) for m, c in configs_in(records)}
    pairs = []
    for (model, config), before in cards.items():
        if config != "baseline":
            continue
        for (m2, c2), after in cards.items():
            if m2 == model and c2.startswith("patch"):
                pairs.append((before, after))
    # Ties go to the earliest patch, so a newer patch with as many drills
    # behind it cannot take over the headline by file order.
    pairs.sort(key=lambda p: (-min(p[0].attack_drills, p[1].attack_drills), p[1].config))
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
            cells.append(cell_of(rs, c.model, c.config, card_id, c.family))

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
            "records": len(published),
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
        "heldout": held_out_results(published, records, LIVE["repo"]),
        "drills": [drill(r, args.withhold_attacks) for r in
                   sorted(records, key=lambda r: (r["card"]["id"], r["config"]["name"],
                                                  r["config"]["model"], r["seed"]))],
        "live": LIVE,
        "sponsors": SPONSORS,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, separators=(",", ":"))
    args.out.write_text(text, encoding="utf-8")
    held = out["heldout"]
    print(f"{len(records)} training drills, {len(cells)} grid cells, {len(patches)} patches, "
          f"{len(held)} held-out reveal{'' if len(held) == 1 else 's'} -> "
          f"{args.out} ({len(text) / 1024:.0f} KB)"
          + ("  [attacker text withheld]" if args.withhold_attacks else ""))


if __name__ == "__main__":
    main()
