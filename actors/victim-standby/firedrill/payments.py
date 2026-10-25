"""Payment rail port. The Ledger stays the source of truth for scoring;
the rail mirrors approved payments to a real sandbox for demo realism.

Adapters: MemoryRail (tests, offline fallback) and NessieRail (Capital One
Nessie sandbox). A rail failure is reported in the Receipt, never raised
into a drill.
"""
from __future__ import annotations

import datetime
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol


@dataclass
class Transfer:
    invoice_id: str
    account: str
    amount: int


@dataclass
class Receipt:
    ok: bool
    reference: str | None = None
    error: str | None = None


class PaymentRail(Protocol):
    def transfer(self, *, invoice_id: str, account: str, amount: int) -> Receipt: ...


@dataclass
class MemoryRail:
    transfers: list[Transfer] = field(default_factory=list)

    def transfer(self, *, invoice_id: str, account: str, amount: int) -> Receipt:
        self.transfers.append(Transfer(invoice_id, account, amount))
        return Receipt(ok=True, reference=f"mem-{len(self.transfers)}")


# --- Capital One Nessie ------------------------------------------------------
HttpJson = Callable[[str, str, dict | None], tuple[int, Any]]  # (method, url, body) -> (status, json)


def _http_json(method: str, url: str, body: dict | None) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw


class NessieRail:
    """Mirrors each approved payment into the Nessie sandbox as two records:
    a transfer on the AP checking account (the payer) and a deposit on an
    account named after the Ledger's account label, created on first use
    under one payee customer. A breach then shows the invoice's money
    landing in an account that is not the vendor's. This Nessie keeps
    records; it does not move balances.

    Create the payer account and payee customer with scripts/nessie_seed.py."""

    def __init__(
        self,
        api_key: str,
        *,
        payer_account_id: str,
        payee_customer_id: str,
        base_url: str = "https://prod-api.nessieisreal.com",
        http: HttpJson = _http_json,
        today: Callable[[], datetime.date] = datetime.date.today,
    ) -> None:
        self._key = api_key
        self._payer = payer_account_id
        self._payee_customer = payee_customer_id
        self._base = base_url.rstrip("/")
        self._http = http
        self._today = today
        self._accounts: dict[str, str] = {}  # ledger account label -> Nessie account id

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> NessieRail | None:
        """The rail when all four NESSIE_* values are set, else None (use MemoryRail)."""
        key, payer, payee = (env.get(k, "") for k in
                             ("NESSIE_API_KEY", "NESSIE_PAYER_ACCOUNT_ID", "NESSIE_PAYEE_CUSTOMER_ID"))
        if not (key and payer and payee):
            return None
        return cls(key, payer_account_id=payer, payee_customer_id=payee,
                   base_url=env.get("NESSIE_BASE_URL") or "https://prod-api.nessieisreal.com")

    def transfer(self, *, invoice_id: str, account: str, amount: int) -> Receipt:
        try:
            payee = self.account_id(account)
            today = self._today().isoformat()
            status, body = self._call("POST", f"/accounts/{self._payer}/transfers", {
                "transaction_date": today, "status": "completed",
                "amount": amount, "description": f"{invoice_id} to {account}",
            })
            if status != 201:
                return Receipt(ok=False, error=f"transfer: HTTP {status}: {body}")
            reference = body["objectCreated"]["_id"]
            status, body = self._call("POST", f"/accounts/{payee}/deposits", {
                "medium": "balance", "transaction_date": today, "status": "completed",
                "amount": amount, "description": f"{invoice_id} from Lakeside AP",
            })
            if status != 201:
                return Receipt(ok=False, reference=reference, error=f"deposit: HTTP {status}: {body}")
            return Receipt(ok=True, reference=reference)
        except Exception as e:  # network, bad JSON: the Ledger already recorded the payment
            return Receipt(ok=False, error=repr(e))

    def account_id(self, label: str) -> str:
        """The Nessie account for a Ledger account label, created on first use."""
        if label not in self._accounts:
            status, body = self._call("POST", f"/customers/{self._payee_customer}/accounts", {
                "type": "Checking", "nickname": label, "rewards": 0, "balance": 0,
            })
            if status != 201:
                raise RuntimeError(f"could not create payee account {label}: HTTP {status}: {body}")
            self._accounts[label] = body["objectCreated"]["_id"]
        return self._accounts[label]

    def _call(self, method: str, path: str, body: dict | None) -> tuple[int, Any]:
        url = f"{self._base}{path}?" + urllib.parse.urlencode({"key": self._key})
        return self._http(method, url, body)
