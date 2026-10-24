"""Payment rail port. The Ledger stays the source of truth for scoring;
the rail mirrors approved payments to a real sandbox for demo realism.

Adapters: MemoryRail (tests, offline fallback) and NessieRail (Capital One,
added when the Nessie API key arrives).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Transfer:
    invoice_id: str
    account: str
    amount: int


@dataclass
class Receipt:
    ok: bool
    reference: str | None = None


class PaymentRail(Protocol):
    def transfer(self, *, invoice_id: str, account: str, amount: int) -> Receipt: ...


@dataclass
class MemoryRail:
    transfers: list[Transfer] = field(default_factory=list)

    def transfer(self, *, invoice_id: str, account: str, amount: int) -> Receipt:
        self.transfers.append(Transfer(invoice_id, account, amount))
        return Receipt(ok=True, reference=f"mem-{len(self.transfers)}")
