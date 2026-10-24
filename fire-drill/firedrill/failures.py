"""Structured failure summaries: what the Remediator is allowed to see.

A summary says what the agent *did* and what the Ledger recorded, with every
concrete value replaced by its role (the attacker's account becomes
`attacker_account`, a number taken from the request becomes
`number_from_request`). It carries no message text at all.

That is the point of ADR-0002: a patch written from wording can block those
phrases and still fail on the held-out family, while a patch written from
actions has to change behaviour. It also keeps attacker text out of anything
we send to a code agent.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

# Ledger/kit values -> the role the Remediator sees instead.
ROLE_OF = {
    "attacker_account": "attacker_account",      # the account the request asked for
    "approved_account": "account_on_file",       # the vendor's verified account
    "attacker_phone": "number_from_request",     # a number supplied in the request
    "on_file_phone": "number_on_file",           # the number already on file
    "sender": "sender_address",
    "vendor_id": "vendor",
    "vendor_name": "vendor",
    "invoice_id": "invoice",
}


@dataclass
class ToolStep:
    turn: int
    tool: str
    args: dict[str, str]   # values replaced by their role
    blocked: bool          # the call was refused (a hardening gate or a bad input)


@dataclass
class FailureSummary:
    """One failing drill, as actions and outcomes only."""
    drill_id: str
    family: str
    channel: str
    sender_kind: str                 # vendor_mailbox | lookalike_domain | internal_colleague
    model: str
    config: str
    steps: list[ToolStep] = field(default_factory=list)
    breach: bool = False
    verified_out_of_band: bool = False
    canary_touched: bool = False
    capitulation_turn: int | None = None
    money_went_to: str | None = None   # a role, never an account number
    turns: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def _roles_for(kit: dict) -> dict[str, str]:
    """Concrete value -> role label, longest values first so no value that
    contains another is replaced by the wrong role."""
    pairs = [(str(kit[k]), role) for k, role in ROLE_OF.items() if kit.get(k) not in (None, "")]
    return dict(sorted(pairs, key=lambda p: -len(p[0])))


def _label(value, roles: dict[str, str]) -> str:
    text = str(value)
    if text in roles:
        return roles[text]
    for concrete, role in roles.items():  # a value quoted inside a longer string
        if concrete in text:
            text = text.replace(concrete, f"<{role}>")
    return text


def summarize(record: dict) -> FailureSummary:
    """A record (which holds attacker turns) -> a summary that does not."""
    kit, config, verdict = record["kit"], record["config"], record["verdict"]
    roles = _roles_for(kit)
    steps = [
        ToolStep(
            turn=call["turn"],
            tool=call["tool"],
            args={k: _label(v, roles) for k, v in call["input"].items()},
            blocked=bool(call.get("error")),
        )
        for call in record["tool_calls"]
    ]
    unapproved = [p for p in record["payments"] if not p["approved"]]
    return FailureSummary(
        drill_id=f"{record['card']['id']}-s{record['seed']}",
        family=record["card"]["family"],
        channel=record["card"]["channel"],
        sender_kind=record["card"]["sender"],
        model=config["model"],
        config=config["name"],
        steps=steps,
        breach=verdict["breach"],
        verified_out_of_band=verdict["oob"],
        canary_touched=verdict["canary"],
        capitulation_turn=record["cap_turn"],
        money_went_to=_label(unapproved[0]["account"], roles) if unapproved else None,
        turns=len(record["transcript"]),
    )


def failing(records: list[dict], *, families: list[str] | None = None) -> list[FailureSummary]:
    """Summaries of the breaching drills, optionally restricted to the
    training families (the held-out families must never reach a patch)."""
    out = []
    for r in records:
        if not r["verdict"]["breach"]:
            continue
        if families is not None and r["card"]["family"] not in families:
            continue
        out.append(summarize(r))
    return sorted(out, key=lambda s: s.drill_id)


def as_json(summaries: list[FailureSummary]) -> str:
    return json.dumps([s.to_dict() for s in summaries], indent=1, sort_keys=True)
