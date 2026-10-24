"""Capital One Nessie adapter for the PaymentRail port.

Mirrors each approved Ledger payment as a Nessie sandbox transfer, so "money
moved" is concrete for judges. The Ledger stays the source of truth for
scoring; a rail failure returns a failed Receipt and never breaks a drill.

Endpoints (from the Nessie docs): POST /customers, POST /customers/{id}/accounts,
POST /accounts/{id}/deposits, POST /accounts/{id}/transfers. The API key goes on
every request as the `key` query parameter.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import date
from typing import Callable, Protocol

from firedrill.payments import Receipt


class Http(Protocol):
    def post_json(self, url: str, body: dict) -> dict: ...


class UrllibHttp:
    def post_json(self, url: str, body: dict) -> dict:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)


class NessieRail:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        source_account_id: str,
        account_map: dict[str, str],
        http: Http | None = None,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._source = source_account_id
        self._accounts = account_map  # Ledger account -> Nessie account id
        self._http = http or UrllibHttp()
        self._today = today

    @classmethod
    def from_env(cls, *, source_account_id: str, account_map: dict[str, str]) -> "NessieRail":
        return cls(
            base_url=os.environ.get("NESSIE_BASE_URL", "https://prod-api.nessieisreal.com"),
            api_key=os.environ["NESSIE_API_KEY"],
            source_account_id=source_account_id,
            account_map=account_map,
        )

    def transfer(self, *, invoice_id: str, account: str, amount: int) -> Receipt:
        payee = self._accounts.get(account)
        if payee is None:
            return Receipt(ok=False, reference=None)
        url = f"{self._base}/accounts/{self._source}/transfers?key={self._key}"
        body = {
            "medium": "balance",
            "payee_id": payee,
            "amount": amount,
            "transaction_date": self._today().isoformat(),
            "description": invoice_id,
        }
        try:
            resp = self._http.post_json(url, body)
        except Exception:
            return Receipt(ok=False, reference=None)
        created = resp.get("objectCreated") or resp
        return Receipt(ok=True, reference=created.get("_id"))
