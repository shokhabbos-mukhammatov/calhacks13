"""fire-drill: run manipulation drills against an accounts-payable agent and
write the report.

Output is one dataset row per drill (tactic, channel, source report, the turn
the agent broke, money moved, canary touched) plus REPORT.html in the
key-value store as the audit artefact. Verdicts come from ledger state, never
from the transcript (ADR-0001).

Two targets:
  local   - run the sandboxed agent in this Actor's own process (default).
  <url>   - drill a running ap-practice-target Standby Actor over HTTP.

Attacker turns are supplied by the caller. The Actor ships only the benign
invoice pack, so a default one-click run measures whether honest invoices
still get paid, and says so rather than implying it tested security.
"""
from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict
from pathlib import Path

from apify import Actor

from firedrill.apify_adapters import drill_row, report_html
from firedrill.drill import (
    BENIGN_CARD,
    CARDS_DIR,
    ScriptedAttacker,
    build_scenario,
    load_cards,
    make_config,
    run_drill,
)
from firedrill.verify import CrsFraudFinder, NoSenderCheck, RdapDomainAge, VendorVerifier
from firedrill.victim import AnthropicModel

ROOT = Path(__file__).resolve().parents[1]
BENIGN_DIR = ROOT / "benign"
CARDS = {c.id: c for path in CARDS_DIR.glob("*.json") for c in load_cards(path)}


def read_pack(path: Path, kit) -> list[str]:
    blocks = path.read_text(encoding="utf-8").split("\n---\n")
    return [b.strip().format(**asdict(kit)) for b in blocks if b.strip()]


# --- drilling a remote Standby target -------------------------------------------
class RemoteTarget:
    """Drives an ap-practice-target Standby Actor. The target owns the ledger
    and returns the verdict, so scoring stays deterministic and out of reach
    of anything the attacker says."""

    def __init__(self, base_url: str, token: str | None) -> None:
        self._base = base_url.rstrip("/")
        self._token = token

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        req = urllib.request.Request(f"{self._base}{path}", data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=330) as resp:
            return json.loads(resp.read().decode() or "{}")

    def drill(self, card_id: str, seed: int, config: str, model: str, turns: list[str],
              max_turns: int) -> dict:
        started = self._call("POST", "/drill", {"card_id": card_id, "seed": seed,
                                                "config": config, "model": model})
        cid = started["conversation_id"]
        kit = started["kit"]
        transcript, tool_calls = [], []
        for turn, raw in enumerate(turns[:max_turns], start=1):
            out = self._call("POST", f"/drill/{cid}/message", {"body": raw.format(**kit)})
            transcript.append({"turn": turn, "reply": out["reply"]})
            tool_calls += [f"t{c['turn']}:{c['tool']}" + ("[refused]" if c["error"] else "")
                           for c in out.get("tool_calls", [])]
            if any(p["invoice_id"] == kit["invoice_id"]
                   for p in self._call("GET", f"/drill/{cid}/verdict")["payments"]):
                break
        final = self._call("GET", f"/drill/{cid}/verdict")
        card = started["card"]
        unapproved = [p for p in final["payments"] if not p["approved"]]
        return {
            "drill_id": f"{card_id}-s{seed}", "card_id": card_id, "family": card["family"],
            "channel": card["channel"], "sender_kind": card["sender"],
            "source_url": card["source_url"], "seed": seed, "model": model, "config": config,
            "breach": final["verdict"]["breach"], "verified_out_of_band": final["verdict"]["oob"],
            "canary_touched": final["verdict"]["canary"], "capitulation_turn": None,
            "paid_on_file": final["paid_on_file"], "ended_by": "remote",
            "turns": len(transcript),
            "money_moved": sum(p["amount"] for p in unapproved),
            "payments": final["payments"], "tool_calls": tool_calls,
        }


# --- the run ----------------------------------------------------------------------
async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}
        target = (actor_input.get("target") or "local").strip()
        seeds = [int(s) for s in (actor_input.get("seeds") or [1, 2, 3])]
        model = actor_input.get("model") or "claude-opus-5-5"
        config_name = actor_input.get("config") or "baseline"
        max_turns = int(actor_input.get("max_turns") or 6)
        turns: dict[str, list[str]] = actor_input.get("turns") or {}
        card_ids = actor_input.get("cards") or []
        # A local drill runs the agent in this Actor, so its model calls bill
        # to whoever supplied this key. Falling back to the Actor's own key
        # would make strangers' runs spend the owner's credit.
        api_key = actor_input.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if target == "local" and not api_key:
            Actor.log.error("a local drill needs an Anthropic key: pass anthropic_api_key, or "
                            "set target to the URL of an ap-practice-target Actor, which brings "
                            "its own.")
            return

        if not card_ids and not turns:
            Actor.log.info("No attack turns given: running the benign invoice pack, which "
                           "measures whether honest invoices still get paid, not security.")

        verifier = VendorVerifier(
            RdapDomainAge(),
            CrsFraudFinder.from_env(os.environ) or NoSenderCheck(),
        )
        rows: list[dict] = []
        budget_reached = False

        async def record(row: dict) -> None:
            """Write one drill and charge for it. A user can cap what a single
            run may charge; past that cap the platform stops paying while the
            run keeps costing, so stop drilling rather than work for free."""
            nonlocal budget_reached
            rows.append(row)
            await Actor.push_data(row)
            try:
                charge = await Actor.charge("drill-completed")
                if charge.event_charge_limit_reached:
                    budget_reached = True
                    Actor.log.warning("this run has reached its maximum charge; stopping after "
                                      "%d drill(s). Raise it to drill more.", len(rows))
            except Exception as e:   # unpriced local run, or no pay-per-event set up
                Actor.log.debug("not charging drill-completed: %r", e)
            Actor.log.info("%s [%s] breach=%s paid_on_file=%s",
                           row["drill_id"], row["config"], row["breach"], row["paid_on_file"])

        if target != "local":
            remote = RemoteTarget(target, actor_input.get("target_token") or os.environ.get("APIFY_TOKEN"))
            for card_id in card_ids or sorted(turns):
                if budget_reached:
                    break
                for seed in seeds:
                    if budget_reached:
                        break
                    pack = turns.get(card_id)
                    if not pack:
                        Actor.log.warning("no turns for card %s; skipping", card_id)
                        continue
                    await record(await asyncio.to_thread(
                        remote.drill, card_id, seed, config_name, model, pack, max_turns))
        else:
            for card_id in card_ids or sorted(turns) or ["__benign__"]:
                if budget_reached:
                    break
                for seed in seeds:
                    if budget_reached:
                        break
                    if card_id == "__benign__":
                        card = BENIGN_CARD
                        packs = sorted(BENIGN_DIR.glob("*.txt"))
                        if not packs:
                            Actor.log.error("no benign pack shipped; give cards and turns in the input")
                            break
                        path = packs[(seed - 1) % len(packs)]
                        messages = read_pack(path, build_scenario(card, seed).kit)
                    elif card_id in CARDS:
                        card = CARDS[card_id]
                        if not turns.get(card_id):
                            Actor.log.warning("no turns for card %s; skipping", card_id)
                            continue
                        kit = build_scenario(card, seed).kit
                        messages = [t.format(**asdict(kit)) for t in turns[card_id]]
                    else:
                        Actor.log.warning("unknown card %s; known: %s", card_id, ", ".join(sorted(CARDS)))
                        continue
                    config = make_config(config_name, verifier=verifier,
                                         model=AnthropicModel(model, api_key=api_key))
                    drill = await asyncio.to_thread(
                        run_drill, card, seed,
                        attacker=ScriptedAttacker(messages), victim=config, max_turns=max_turns)
                    await record(drill_row(drill, config))

        if rows:
            await Actor.set_value("REPORT.html", report_html(rows), content_type="text/html")
            breaches = sum(1 for r in rows if r["breach"])
            Actor.log.info("%d drills, %d breach(es). REPORT.html written.", len(rows), breaches)
        else:
            Actor.log.warning("no drills ran; check the cards and turns in the input")
