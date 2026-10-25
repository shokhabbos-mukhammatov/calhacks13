"""Run one drill against the Claude Victim Agent, with the attacker's turns
written by a person: the text-channel version of the judge-on-the-phone demo.

    .venv/Scripts/python scripts/run_drill.py vmt-01 --seed 1                                   # type each turn
    .venv/Scripts/python scripts/run_drill.py vmt-01 --seed 1 --turns turns/vmt-01.txt --dry-run # check a turns file
    .venv/Scripts/python scripts/run_drill.py vmt-01 --seed 1 --turns turns/vmt-01.txt --save    # run and record
    .venv/Scripts/python scripts/run_drill.py vmt-02 --seed 1 --config baseline --replay          # no model call
    .venv/Scripts/python scripts/run_drill.py --benign --turns benign/invoice-01.txt --seed 1 --save
    .venv/Scripts/python scripts/run_drill.py vmt-01 --seed 1 --turns turns/vmt-01.txt --config patched --model claude-haiku-5-5 --save

--config picks the hardening level: baseline (default; no policy, no
verify_vendor), baseline+verify (verify_vendor offered), or patched
(FakeCodeAgent's patch plus verify_vendor). --model picks the victim model.

Typing: end a message with an empty line; an empty message ends the drill.
A turns file holds one message per block, blocks separated by a line of
'---'. Kit fields such as {vendor_name}, {invoice_id}, {amount},
{attacker_account} and {attacker_phone} are filled in from the seed.
--dry-run prints the kit and the filled turns without calling the model.
--save writes the drill to records/ for the Remediator and scripts/report.py.
--benign runs honest turns against the built-in benign card (utility).
--replay re-prints a drill already in records/ without a key, a model call or
a network: the rehearsal path, and what to run if the venue wifi dies.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from firedrill.console import use_utf8
from firedrill.drill import (
    BENIGN_CARD,
    CARDS_DIR,
    CONFIGS,
    ScriptedAttacker,
    build_scenario,
    load_cards,
    make_config,
    read_turns,
    run_drill,
)
from firedrill.payments import NessieRail
from firedrill.records import drill_to_record, find_records, save_drill
from firedrill.verify import (
    CrsFraudFinder,
    CrsReverseLookup,
    NoPhoneOwner,
    NoSenderCheck,
    RdapDomainAge,
    VendorVerifier,
)
from firedrill.openai_compat import model_for


class TypedAttacker:
    """Reads each turn from the keyboard, showing the agent's last reply."""

    def compose(self, card, kit, transcript):
        if transcript:
            print(f"\nagent> {transcript[-1].reply}\n")
        print(f"attacker (turn {len(transcript) + 1}, empty line to send, empty message to stop)>")
        lines = []
        while (line := input()) != "":
            lines.append(line)
        return "\n".join(lines) or None


def print_drill(record: dict) -> None:
    """A drill, printed from its record.

    One printer, whether the drill just ran or was saved hours ago: a replay
    that reconstructed the output by some other route could disagree with the
    live run, and the whole point of a replay is that it cannot."""
    print("\n=== transcript ===")
    for t in record["transcript"]:
        print(f"\n--- turn {t['turn']} attacker ({t['sender']}) ---\n{t['body']}")
        for call in record["tool_calls"]:
            if call["turn"] == t["turn"]:
                flag = " [error]" if call["error"] else ""
                print(f"    tool {call['tool']}({call['input']}){flag} -> {call['result']}")
        print(f"--- turn {t['turn']} agent ---\n{t['reply']}")
    v = record["verdict"]
    print(f"\nVERDICT: breach={v['breach']} oob={v['oob']} canary={v['canary']} "
          f"cap_turn={record['cap_turn']} paid_on_file={record['paid_on_file']} "
          f"ended_by={record['ended_by']}")
    print("payments:", [(p["invoice_id"], p["account"],
                         "approved" if p["approved"] else "UNAPPROVED")
                        for p in record["payments"]])


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("card_id", nargs="?", help="a card id from cards/*.json (omit with --benign)")
    p.add_argument("--benign", action="store_true", help="honest turns against the built-in benign card")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--turns", type=Path, help="file of attacker turns separated by '---' lines")
    p.add_argument("--max-turns", type=int, default=6)
    p.add_argument("--config", default="baseline",
                   help=f"hardening level: {', '.join(CONFIGS)}, or patch:<name> from patches/ (default: baseline)")
    p.add_argument("--model", default="claude-opus-5-5", help="victim model: a Claude name, or provider/model such as openai/gpt-4.1-mini "
                        "or deepseek/deepseek-chat (default: claude-opus-5-5)")
    p.add_argument("--dry-run", action="store_true", help="print the kit and filled turns; no model calls")
    p.add_argument("--replay", action="store_true",
                   help="re-print a drill already in records/; no key, no model call, no network")
    p.add_argument("--save", action="store_true", help="write the drill to records/")
    args = p.parse_args()

    if args.benign:
        card = BENIGN_CARD
        if not args.turns:
            p.error("--benign needs --turns")
    elif args.card_id:
        cards = {c.id: c for path in CARDS_DIR.glob("*.json") for c in load_cards(path)}
        if args.card_id not in cards:
            p.error(f"unknown card {args.card_id!r}; known: {', '.join(sorted(cards))}")
        card = cards[args.card_id]
    else:
        p.error("give a card id or --benign")
    kit = build_scenario(card, args.seed).kit

    print(f"card {card.id} [{card.family}] via {card.channel}, sender {card.sender}")
    print(f"  pretext: {card.pretext}\n  lever:   {card.lever}\n  ask:     {card.ask}")
    print("kit:", ", ".join(f"{k}={v}" for k, v in asdict(kit).items()), "\n")

    if args.dry_run:
        if not args.turns:
            p.error("--dry-run needs --turns")
        for i, block in enumerate(read_turns(args.turns, kit), 1):
            print(f"--- turn {i} ---\n{block}\n")
        print("dry run: no model calls made")
        return

    # The rehearsal path, and the one to reach for if the venue network dies.
    # It runs before anything loads a key, so it cannot fail for want of one.
    if args.replay:
        found = find_records(card.id, args.seed, args.config)
        if not found:
            p.error(f"no saved drill for card {card.id}, seed {args.seed}, config "
                    f"{args.config!r}. Run it once with --save, or see what is already "
                    f"recorded with: scripts/scorecard.py --open")
        record = found[0]
        print(f"REPLAY of {record['card']['id']}-s{record['seed']} [{record['config']['name']} "
              f"on {record['config']['model']}] recorded {record['saved_at']}")
        print("no model call, no network: this is the drill exactly as it ran.")
        print_drill(record)
        return

    load_dotenv(ROOT / ".env")
    rail = NessieRail.from_env(os.environ)
    sender_check = CrsFraudFinder.from_env(os.environ)
    verifier = VendorVerifier(RdapDomainAge(), sender_check or NoSenderCheck(),
                              CrsReverseLookup.from_env(os.environ) or NoPhoneOwner())
    try:
        config = make_config(args.config, model=model_for(args.model), verifier=verifier, rail=rail)
    except (ValueError, FileNotFoundError) as e:
        p.error(str(e))
    verify_note = "off"
    if config.verifier:
        verify_note = "on (CRS Fraud Finder)" if sender_check else "on (no sender check; set CRS_* in .env)"
    print(f"config: {config.name} | model: {args.model} | verify_vendor: {verify_note} | "
          f"rail: {'Nessie' if rail else 'none (set NESSIE_* in .env)'}")

    attacker = ScriptedAttacker(read_turns(args.turns, kit)) if args.turns else TypedAttacker()
    drill = run_drill(card, args.seed, attacker=attacker, victim=config, max_turns=args.max_turns)

    print_drill(drill_to_record(drill, config))
    if args.save:
        print("saved:", save_drill(drill, config))


if __name__ == "__main__":
    main()
