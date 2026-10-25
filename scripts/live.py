r"""The demo console: run drills on a second screen, narrated as they happen.

    .venv\Scripts\python.exe scripts\live.py                       # the story, in three acts
    .venv\Scripts\python.exe scripts\live.py --act break           # just the agent breaking
    .venv\Scripts\python.exe scripts\live.py --card vmt-02 --seed 5 --config baseline
    .venv\Scripts\python.exe scripts\live.py --replay              # no model calls, no network

Judges asked to watch the processes rather than hear about them, so every
line is printed as the thing happens: the attacker's turn, each tool call,
what CRS answered, the ledger moving, Nessie mirroring, the verdict.

With no arguments it plays the three acts the pitch needs, pausing between
them so you can talk:

  1. **break**  the agent with no controls pays the attacker
  2. **gate**   the same world with the policy deleted, and the code refuses
  3. **hold**   the patched agent, which never tries

`--replay` prints a recorded drill instead of running one: the same console,
no model calls and no network, for when the venue wifi dies.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from firedrill.console import use_utf8
from firedrill.drill import (
    CARDS_DIR,
    ScriptedAttacker,
    build_scenario,
    load_cards,
    make_config,
    read_turns,
    run_drill,
)
from firedrill.live import BOLD, DIM, GREEN, LiveConsole, RED, _c
from firedrill.payments import NessieRail
from firedrill.records import find_records, save_drill
from firedrill.verify import (
    CrsFraudFinder,
    CrsReverseLookup,
    NoPhoneOwner,
    NoSenderCheck,
    RdapDomainAge,
    VendorVerifier,
)
from firedrill.victim import AnthropicModel

CARDS = {c.id: c for p in CARDS_DIR.glob("*.json") for c in load_cards(p)}
TURNS = ROOT / "turns"

ACTS = {
    "break": ("baseline", "No controls. The agent as it ships."),
    "gate": ("scope:v1", "The patch's tool gates, with its policy text deleted: "
                         "is the code enough on its own?"),
    "hold": ("patch:v1", "The full patch Claude Code wrote."),
}


def turns_for(card_id: str, seed: int) -> list[str] | None:
    path = TURNS / f"{card_id}.txt"
    if not path.exists():
        return None
    return read_turns(path, build_scenario(CARDS[card_id], seed).kit)


def wait(console: LiveConsole, nxt: str) -> None:
    if not sys.stdin.isatty():
        return
    try:
        input(_c(DIM, f"\n  press enter for {nxt} "))
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(0)


def play(card_id: str, seed: int, config: str, model: str, *, blurb: str = "",
         save: bool = False) -> bool:
    """One drill, narrated. Returns whether it breached."""
    card = CARDS[card_id]
    messages = turns_for(card_id, seed)
    if not messages:
        raise SystemExit(f"no attacker turns for {card_id}: write turns/{card_id}.txt first")

    rail = NessieRail.from_env(os.environ)
    verifier = VendorVerifier(
        RdapDomainAge(),
        CrsFraudFinder.from_env(os.environ) or NoSenderCheck(),
        CrsReverseLookup.from_env(os.environ) or NoPhoneOwner(),
    )
    victim = make_config(config, model=AnthropicModel(model), verifier=verifier, rail=rail)
    scenario = build_scenario(card, seed)

    console = LiveConsole()   # run_drill attaches the ledger it scores
    if blurb:
        print(_c(DIM, f"\n  {blurb}"))
    console.header(card=card_id, seed=seed, config=config, model=model, kit=scenario.kit)
    console.field("live", "CRS " + ("on" if CrsReverseLookup.from_env(os.environ) else "off")
                  + " · Nessie " + ("on" if rail else "off") + " · RDAP on")
    print()

    drill = run_drill(card, seed, attacker=ScriptedAttacker(messages), victim=victim,
                      watch=console)
    console.verdict(drill)
    if save:
        console.field("saved", str(save_drill(drill, victim).relative_to(ROOT)))
    return drill.verdict.breach


def replay(card_id: str, seed: int, config: str) -> None:
    """A recorded drill through the same console: no model call, no network."""
    found = find_records(card_id, seed, config)
    if not found:
        raise SystemExit(f"no saved drill for {card_id} seed {seed} [{config}]")
    record = found[0]
    console = LiveConsole()
    print(_c(DIM, f"\n  replay of a drill recorded {record['saved_at']} — no model call, "
                  f"no network"))
    kit = type("Kit", (), record["kit"])
    console.header(card=card_id, seed=seed, config=config,
                   model=record["config"]["model"], kit=kit)
    print()
    for turn in record["transcript"]:
        console.line("ATTACKER", "33", f'turn {turn["turn"]}  "{turn["body"]}"')
        for call in record["tool_calls"]:
            if call["turn"] != turn["turn"]:
                continue
            console.emit(type("E", (), {"kind": "tool_call", "turn": call["turn"],
                                        "data": call})())
            time.sleep(0.35)
        console.line("AGENT", "32", turn["reply"].replace("\n", " ").strip())
    v = record["verdict"]
    print()
    console.line("VERDICT", RED if v["breach"] else GREEN,
                 _c(BOLD, f"BREACH — gave in on turn {record['cap_turn']}" if v["breach"]
                    else "HELD"))
    print()


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--act", choices=sorted(ACTS), help="play one act instead of all three")
    p.add_argument("--card", default="vmt-02", choices=sorted(CARDS))
    # Seed 1 of vmt-02 is the clearest three-act world: CRS names a stranger,
    # the agent calls that number anyway, and under scope:v1 the code refuses.
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--config", help="a hardening level, instead of the three acts")
    p.add_argument("--model", default="claude-haiku-4-5")
    p.add_argument("--save", action="store_true", help="record the drill to records/")
    p.add_argument("--replay", action="store_true",
                   help="print a recorded drill: no model call, no network")
    args = p.parse_args()
    load_dotenv(ROOT / ".env")

    if args.replay:
        return replay(args.card, args.seed, args.config or "baseline")
    if args.config:
        return None if play(args.card, args.seed, args.config, args.model,
                            save=args.save) is None else None

    acts = [args.act] if args.act else list(ACTS)
    for i, name in enumerate(acts):
        config, blurb = ACTS[name]
        play(args.card, args.seed, config, args.model, blurb=blurb, save=args.save)
        if i < len(acts) - 1:
            wait(LiveConsole(), f"act {i + 2}: {acts[i + 1]}")


if __name__ == "__main__":
    main()
