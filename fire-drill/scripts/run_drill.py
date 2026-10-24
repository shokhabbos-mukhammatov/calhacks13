"""Run one drill against the Claude Victim Agent, with the attacker's turns
written by a person: the text-channel version of the judge-on-the-phone demo.

    .venv/Scripts/python scripts/run_drill.py vmt-01 --seed 1                 # type each turn
    .venv/Scripts/python scripts/run_drill.py vmt-01 --seed 1 --turns t.txt   # turns from a file

Typing: end a message with an empty line; an empty message ends the drill.
A turns file holds one message per block, blocks separated by a line of
'---'. Kit fields such as {vendor_name}, {invoice_id}, {amount},
{attacker_account} and {attacker_phone} are filled in from the seed.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from firedrill.drill import (
    CARDS_DIR,
    ScriptedAttacker,
    VictimConfig,
    build_scenario,
    load_cards,
    run_drill,
)
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


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("card_id")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--turns", type=Path, help="file of attacker turns separated by '---' lines")
    p.add_argument("--max-turns", type=int, default=6)
    args = p.parse_args()

    load_dotenv(ROOT / ".env")
    cards = {c.id: c for path in CARDS_DIR.glob("*.json") for c in load_cards(path)}
    card = cards[args.card_id]
    kit = build_scenario(card, args.seed).kit

    print(f"card {card.id} [{card.family}] via {card.channel}, sender {card.sender}")
    print(f"  pretext: {card.pretext}\n  lever:   {card.lever}\n  ask:     {card.ask}")
    print("kit:", ", ".join(f"{k}={v}" for k, v in asdict(kit).items()), "\n")

    if args.turns:
        blocks = args.turns.read_text(encoding="utf-8").split("\n---\n")
        attacker = ScriptedAttacker([b.strip().format(**asdict(kit)) for b in blocks if b.strip()])
    else:
        attacker = TypedAttacker()

    drill = run_drill(card, args.seed, attacker=attacker,
                      victim=VictimConfig(model=AnthropicModel()), max_turns=args.max_turns)

    print("\n=== transcript ===")
    for t in drill.transcript:
        print(f"\n--- turn {t.turn} attacker ({t.message.sender}) ---\n{t.message.body}")
        for e in drill.events:
            if e.turn == t.turn and e.kind == "tool_call":
                flag = " [error]" if e.data["error"] else ""
                print(f"    tool {e.data['tool']}({e.data['input']}){flag} -> {e.data['result']}")
        print(f"--- turn {t.turn} agent ---\n{t.reply}")
    v = drill.verdict
    print(f"\nVERDICT: breach={v.breach} oob={v.oob} canary={v.canary} "
          f"cap_turn={drill.cap_turn} ended_by={drill.ended_by}")
    print("payments:", [(pm.invoice_id, pm.account, "approved" if pm.approved else "UNAPPROVED")
                        for pm in drill.state.payments])


if __name__ == "__main__":
    main()
