"""Apify adapters: what the Actors need and the core does not.

Nothing here imports `apify`. The Actors pass their own storage objects in,
so every adapter is testable offline and the core stays runnable without the
platform (the fallback-adapter rule in the architecture note).

The Victim Agent's store interface is synchronous while Apify's storages are
async, so a Standby turn reads the conversation before the turn and writes it
after, with `PrefetchedStore` standing in between (ADR-0003).
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from typing import Any

# Apify key-value store keys allow letters, digits and ! - _ . ' ( ) only.
_UNSAFE = re.compile(r"[^a-zA-Z0-9!\-_.'()]")


def conversation_key(conversation_id: str) -> str:
    """The key a drill's conversation is stored under."""
    return f"conversation-{_UNSAFE.sub('-', conversation_id)}"


def world_key(conversation_id: str) -> str:
    """The key a drill's Ledger state is stored under."""
    return f"world-{_UNSAFE.sub('-', conversation_id)}"


def call_key(call_id: str) -> str:
    """Which drill a phone call belongs to.

    A voice turn carries the telephony provider's call id, and the server
    maps it to a drill. The caller is not asked to carry a drill id: on the
    first turn it would not exist yet."""
    return f"call-{_UNSAFE.sub('-', call_id)}"


@dataclass
class PrefetchedStore:
    """A ConversationStore over messages already fetched from a key-value
    store. The Actor loads before the turn and writes back after, so any run
    can serve any turn and the process keeps nothing of its own."""

    messages: list[dict] = field(default_factory=list)
    dirty: bool = False

    def load(self, conversation_id: str) -> list[dict]:
        return self.messages

    def save(self, conversation_id: str, messages: list[dict]) -> None:
        # JSON round-trip, as the real store would: nothing unserializable
        # can reach the platform and fail there instead of here.
        self.messages = json.loads(json.dumps(messages))
        self.dirty = True


def drill_row(drill: Any, config: Any) -> dict:
    """One dataset row per drill: the Actor's output contract.

    Flat and self-describing, so the row reads on its own in Apify's dataset
    view, in a webhook payload, and in Elastic. Holds the tactic, the source
    report and the outcome; the attacker's message text stays out."""
    verdict = drill.verdict
    return {
        "drill_id": f"{drill.card.id}-s{drill.seed}",
        "card_id": drill.card.id,
        "family": drill.card.family,
        "channel": drill.card.channel,
        "sender_kind": drill.card.sender,
        "source_url": drill.card.source_url,
        "seed": drill.seed,
        "model": getattr(config.model, "_model", type(config.model).__name__),
        "config": config.name,
        "breach": verdict.breach,
        "verified_out_of_band": verdict.oob,
        "canary_touched": verdict.canary,
        "capitulation_turn": drill.cap_turn,
        "paid_on_file": drill.paid_on_file,
        "ended_by": drill.ended_by,
        "turns": len(drill.transcript),
        "money_moved": sum(p.amount for p in drill.state.payments if not p.approved),
        "payments": [{"invoice_id": p.invoice_id, "account": p.account,
                      "amount": p.amount, "approved": p.approved} for p in drill.state.payments],
        "tool_calls": [f"t{e.turn}:{e.data['tool']}" + ("[refused]" if e.data["error"] else "")
                       for e in drill.events if e.kind == "tool_call"],
    }


def report_html(rows: list[dict], *, title: str = "Fire Drill report") -> str:
    """The audit artefact written to the key-value store as REPORT.html:
    every drill, its verdict and the public report its tactic came from."""
    breaches = sum(1 for r in rows if r["breach"])
    attacks = [r for r in rows if r["family"] != "benign"]
    benign = [r for r in rows if r["family"] == "benign"]
    paid = sum(1 for r in benign if r["paid_on_file"])
    head = (
        f"<p>{len(rows)} drills · <strong>{breaches} breach(es)</strong> in {len(attacks)} attack drills"
        + (f" · {paid}/{len(benign)} honest invoices still paid" if benign else "")
        + "</p>"
    )
    cells = []
    for r in sorted(rows, key=lambda r: (r["family"], r["card_id"], r["seed"])):
        verdict = "BREACH" if r["breach"] else ("paid on file" if r["paid_on_file"] else "held")
        colour = "#b00020" if r["breach"] else "#1b7f3b"
        source = (f'<a href="{html.escape(r["source_url"])}">source</a>' if r["source_url"] else "—")
        cells.append(
            "<tr>"
            f"<td>{html.escape(r['drill_id'])}</td>"
            f"<td>{html.escape(r['family'])}</td>"
            f"<td>{html.escape(r['channel'])}</td>"
            f"<td>{html.escape(r['config'])}</td>"
            f"<td>{html.escape(r['model'])}</td>"
            f'<td style="color:{colour};font-weight:600">{verdict}</td>'
            f"<td>{r['capitulation_turn'] if r['capitulation_turn'] is not None else '—'}</td>"
            f"<td>{r['money_moved'] or '—'}</td>"
            f"<td>{source}</td>"
            "</tr>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        "<style>body{font:14px/1.5 system-ui,sans-serif;margin:2rem;max-width:60rem}"
        "table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #ddd;"
        "padding:.4rem .6rem;text-align:left}th{background:#f6f6f6}</style></head><body>"
        f"<h1>{html.escape(title)}</h1>{head}"
        "<table><tr><th>Drill</th><th>Family</th><th>Channel</th><th>Config</th><th>Model</th>"
        "<th>Verdict</th><th>Capitulation turn</th><th>Money moved</th><th>Tactic source</th></tr>"
        + "".join(cells)
        + "</table><p><small>Verdicts are read from final ledger state, never from the "
        "transcript (ADR-0001).</small></p></body></html>"
    )
