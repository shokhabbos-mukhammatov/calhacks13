"""Run one drill against the Claude Victim Agent, with the attacker's turns
written by a person: the text-channel version of the judge-on-the-phone demo.

    .venv/Scripts/python scripts/run_drill.py vmt-01 --seed 1                                   # type each turn
    .venv/Scripts/python scripts/run_drill.py vmt-01 --seed 1 --turns turns/vmt-01.txt --dry-run # check a turns file
    .venv/Scripts/python scripts/run_drill.py vmt-01 --seed 1 --turns turns/vmt-01.txt --save    # run and record
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

from firedrill.drill import (
    BENIGN_CARD,
    CARDS_DIR,
    CONFIGS,
    ScriptedAttacker,
    build_scenario,
    load_cards,
    make_config,
    run_drill,
)
from firedrill.payments import NessieRail
from firedrill.records import save_drill
from firedrill.verify import CrsFraudFinder, NoSenderCheck, RdapDomainAge, VendorVerifier
from firedrill.victim import AnthropicModel


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


def read_turns(path: Path, kit) -> list[str]:
    blocks = path.read_text(encoding="utf-8").split("\n---\n")
    return [b.strip().format(**asdict(kit)) for b in blocks if b.strip()]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("card_id", nargs="?", help="a card id from cards/*.json (omit with --benign)")
    p.add_argument("--benign", action="store_true", help="honest turns against the built-in benign card")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--turns", type=Path, help="file of attacker turns separated by '---' lines")
    p.add_argument("--max-turns", type=int, default=6)
    p.add_argument("--config", default="baseline",
                   help=f"hardening level: {', '.join(CONFIGS)}, or patch:<name> from patches/ (default: baseline)")
    p.add_argument("--model", default="claude-opus-5-5", help="victim model id (default: claude-opus-5-5)")
    p.add_argument("--dry-run", action="store_true", help="print the kit and filled turns; no model calls")
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

    load_dotenv(ROOT / ".env")
    rail = NessieRail.from_env(os.environ)
    sender_check = CrsFraudFinder.from_env(os.environ)
    verifier = VendorVerifier(RdapDomainAge(), sender_check or NoSenderCheck())
    try:
        config = make_config(args.config, model=AnthropicModel(args.model), verifier=verifier, rail=rail)
    except (ValueError, FileNotFoundError) as e:
        p.error(str(e))
    verify_note = "off"
    if config.verifier:
        verify_note = "on (CRS Fraud Finder)" if sender_check else "on (no sender check; set CRS_* in .env)"
    print(f"config: {config.name} | model: {args.model} | verify_vendor: {verify_note} | "
          f"rail: {'Nessie' if rail else 'none (set NESSIE_* in .env)'}")

    attacker = ScriptedAttacker(read_turns(args.turns, kit)) if args.turns else TypedAttacker()
    drill = run_drill(card, args.seed, attacker=attacker, victim=config, max_turns=args.max_turns)

    print("\n=== transcript ===")
    for t in drill.transcript:
        print(f"\n--- turn {t.turn} attacker ({t.message.sender}) ---\n{t.message.body}")
        for e in drill.events:
            if e.turn == t.turn and e.kind == "tool_call":
                flag = " [error]" if e.data["error"] else ""
                print(f"    tool {e.data['tool']}({e.data['input']}){flag} -> {e.data['result']}")
        print(f"--- turn {t.turn} agent ---\n{t.reply}")
    v = drill.verdict
    print(f"\nVERDICT: breach={v.breach} oob={v.oob} canary={v.canary} cap_turn={drill.cap_turn} "
          f"paid_on_file={drill.paid_on_file} ended_by={drill.ended_by}")
    print("payments:", [(pm.invoice_id, pm.account, "approved" if pm.approved else "UNAPPROVED")
                        for pm in drill.state.payments])
    if args.save:
        print("saved:", save_drill(drill, config))


if __name__ == "__main__":
    main()
