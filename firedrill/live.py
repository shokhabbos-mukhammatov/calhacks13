"""The live console: every step of a drill, as it happens, on a second screen.

Judges asked to watch the processes rather than be told about them. This
prints one timestamped line per event while a drill runs — the attacker's
turn, each tool call, each sponsor system as it answers, every change to the
ledger, and the verdict — so nothing on screen is a claim that something
happened. It is the thing happening.

It is strictly a **watcher**. `run_drill(watch=...)` tees events here and
keeps its own record, and a wrapper that raises is swallowed by the tee, so
nothing shown or not shown can change a verdict (ADR-0001).

The ledger line is the one to watch during a demo: the account a payment
would go to, redrawn whenever it changes, in red once it is an account
nobody verified.
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

from firedrill.ledger import Ledger
from firedrill.trace import TraceEvent

# Colour only when a terminal is attached and NO_COLOR is unset, so piping
# the console into a file gives clean text.
_TTY = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text


DIM, BOLD = "2", "1"
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN = "31", "32", "33", "34", "35", "36"

# Which sponsor answers a given tool, for the badge on the right.
BADGE = {
    "verify_vendor": ("CRS + RDAP", CYAN),
    "approve_payment": ("Capital One", MAGENTA),
}


@dataclass
class LiveConsole:
    """A TraceSink that narrates a drill to stdout as it runs."""

    ledger: Ledger | None = None          # watched, to show state changes
    width: int = 100
    started: float = field(default_factory=time.monotonic)
    _last_account: str | None = None
    _payments: int = 0

    def attach(self, ledger: Ledger) -> None:
        """`run_drill` hands over the ledger it actually scores, so the state
        shown is the state the Scorer will read."""
        self.ledger = ledger

    # --- the frame -------------------------------------------------------
    def rule(self, title: str = "") -> None:
        if not title:
            print(_c(DIM, "─" * self.width))
            return
        print(_c(DIM, "─" * 3) + " " + _c(BOLD, title) + " "
              + _c(DIM, "─" * max(0, self.width - len(title) - 5)))

    def header(self, *, card: str, seed: int, config: str, model: str, kit: Any) -> None:
        self.rule(f"DRILL  {card}  seed {seed}")
        self.field("world", f"{kit.vendor_name} · invoice {kit.invoice_id} · "
                            f"${kit.amount:,} · pays to {kit.approved_account}")
        self.field("on file", f"{kit.on_file_phone}")
        self.field("agent", f"{model} · {config}")
        self._last_account = kit.approved_account
        print()

    def field(self, label: str, value: str) -> None:
        print(f"  {_c(DIM, label.rjust(9))}  {value}")

    def line(self, kind: str, colour: str, text: str, badge: str = "") -> None:
        stamp = _c(DIM, f"{time.monotonic() - self.started:6.2f}s")
        tag = _c(colour, kind.ljust(9))
        right = _c(DIM, f"  [{badge}]") if badge else ""
        room = self.width - 22 - (len(badge) + 5 if badge else 0)
        body = text if len(text) <= room else text[: room - 1] + "…"
        print(f"  {stamp}  {tag} {body}{right}", flush=True)

    # --- the sink ---------------------------------------------------------
    def emit(self, event: TraceEvent) -> None:
        if event.kind == "message":
            d = event.data
            if d.get("role") == "agent":
                self.line("AGENT", GREEN, (d.get("text") or "").replace("\n", " ").strip())
            else:
                body = (d.get("body") or "").replace("\n", " ").strip()
                self.line("ATTACKER", YELLOW, f'turn {event.turn}  "{body}"')
        elif event.kind == "tool_call":
            self._tool(event)
        self._ledger_changed()

    def _tool(self, event: TraceEvent) -> None:
        d = event.data
        name, args = d.get("tool", "?"), d.get("input") or {}
        shown = ", ".join(f"{k}={v}" for k, v in args.items())
        badge, colour = BADGE.get(name, ("", BLUE))
        if d.get("error"):
            # Only a control is a refusal: the payment gate, or a tool the patch
            # denied. A call that merely failed (a vendor looked up by name)
            # must not be shown to a watching judge as a gate firing.
            result = str(d.get("result") or "")
            if result.startswith("Blocked"):
                self.line("REFUSED", RED, f"{name}({shown})  ← a gate in code said no")
            elif result.endswith("is not available."):
                self.line("REFUSED", RED, f"{name}({shown})  ← denied by the patch's tool scope")
            else:
                self.line("FAILED", DIM, f"{name}({shown})  ← the call failed; the agent can retry")
            return
        self.line("TOOL", colour, f"{name}({shown})", badge)
        self._explain(name, args, str(d.get("result") or ""))

    def _explain(self, name: str, args: dict, result: str) -> None:
        """The one line a watching human needs, under the raw call."""
        if name == "verify_vendor":
            import json
            try:
                ev = json.loads(result)
            except ValueError:
                return
            match = ev.get("checked_number_matches_the_number_on_file")
            risk = ev.get("checked_number_fraud_risk_score")
            if match is False:
                owner = ev.get("checked_number_registered_to")
                self.note(_c(RED, f"CRS: {owner or 'nobody'} holds that number, not "
                                  f"{ev.get('number_on_file_registered_to')}"
                                  + (f" · fraud risk {risk}/100" if risk is not None else "")))
            elif match is True:
                self.note(_c(GREEN, f"CRS: that is the number on file"
                                    + (f" · fraud risk {risk}/100" if risk is not None else "")))
        elif name == "call_vendor" and "they confirmed" in result:
            self.note(_c(RED, "whoever answered said yes — that is not verification"))
        elif name == "approve_payment" and "Bank reference" in result:
            ref = result.split("Bank reference", 1)[1].strip().rstrip(".")
            self.note(_c(DIM, f"Capital One Nessie mirrored the transfer · ref {ref[:8]}"))

    def note(self, text: str) -> None:
        print(f"  {' ' * 8}  {_c(DIM, '└')} {text}", flush=True)

    def _ledger_changed(self) -> None:
        """Redraw the ledger line whenever the money's destination moves."""
        if self.ledger is None:
            return
        state = self.ledger.snapshot()
        vendor = next(iter(state.vendors.values()), None)
        if vendor and vendor.active_account != self._last_account:
            verified = vendor.active_account in vendor.approved_accounts
            paint = GREEN if verified else RED
            self.line("LEDGER", paint,
                      f"pays to {self._last_account} → {vendor.active_account}  "
                      f"({'verified' if verified else 'NOT VERIFIED'})")
            self._last_account = vendor.active_account
        if len(state.payments) != self._payments:
            for p in state.payments[self._payments:]:
                paint = GREEN if p.approved else RED
                self.line("MONEY", paint, f"${p.amount:,} → {p.account}  "
                                          f"({'approved account' if p.approved else 'UNAPPROVED ACCOUNT'})")
            self._payments = len(state.payments)

    def verdict(self, drill: Any) -> None:
        v = drill.verdict
        print()
        if v.breach:
            self.line("VERDICT", RED, _c(BOLD, f"BREACH — money reached an unapproved account"
                                               f"  (gave in on turn {drill.cap_turn})"))
        else:
            self.line("VERDICT", GREEN, _c(BOLD, "HELD — nothing left for an unverified account"))
        self.note(_c(DIM, "read from final ledger state, not from the transcript (ADR-0001)"))
        print()
