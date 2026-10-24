"""NessieRail mirrors Ledger payments into the Capital One sandbox. A fake
HTTP layer pins the request shapes; the live check is scripts/nessie_seed.py.
"""
import datetime
from urllib.parse import parse_qs, urlsplit

import pytest

from firedrill.payments import NessieRail

TODAY = datetime.date(2026, 10, 24)


class FakeNessie:
    """Answers like the sandbox: 201 + objectCreated for every create."""

    def __init__(self, reject: str | None = None) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []
        self.reject = reject  # a path suffix to answer with 400

    def __call__(self, method, url, body):
        parts = urlsplit(url)
        self.calls.append((method, parts.path, body))
        assert parse_qs(parts.query) == {"key": ["k-test"]}  # the key rides in the query string
        if self.reject and parts.path.endswith(self.reject):
            return 400, {"code": 400, "message": "rejected"}
        if parts.path.endswith("/accounts"):
            return 201, {"code": 201, "objectCreated": {"_id": f"acct-{body['nickname']}"}}
        return 201, {"code": 201, "objectCreated": {"_id": f"obj-{len(self.calls)}"}}


def rail(http):
    return NessieRail("k-test", payer_account_id="payer-1", payee_customer_id="cust-payees",
                      base_url="https://nessie.test", http=http, today=lambda: TODAY)


def test_a_payment_becomes_a_transfer_on_the_payer_and_a_deposit_on_the_payee():
    http = FakeNessie()
    receipt = rail(http).transfer(invoice_id="INV-7", account="ACCT-123", amount=5_000)
    assert receipt.ok is True and receipt.reference == "obj-2"
    assert http.calls == [
        ("POST", "/customers/cust-payees/accounts",
         {"type": "Checking", "nickname": "ACCT-123", "rewards": 0, "balance": 0}),
        ("POST", "/accounts/payer-1/transfers",
         {"transaction_date": "2026-10-24", "status": "completed", "amount": 5_000,
          "description": "INV-7 to ACCT-123"}),
        ("POST", "/accounts/acct-ACCT-123/deposits",
         {"medium": "balance", "transaction_date": "2026-10-24", "status": "completed",
          "amount": 5_000, "description": "INV-7 from Lakeside AP"}),
    ]


def test_a_known_account_is_not_created_twice():
    http = FakeNessie()
    r = rail(http)
    r.transfer(invoice_id="INV-1", account="ACCT-123", amount=1)
    r.transfer(invoice_id="INV-2", account="ACCT-123", amount=2)
    assert len([c for c in http.calls if c[1].endswith("/accounts")]) == 1


def test_a_rejected_transfer_is_a_failed_receipt_not_an_exception():
    receipt = rail(FakeNessie(reject="/transfers")).transfer(invoice_id="INV-1", account="A", amount=10)
    assert receipt.ok is False and receipt.reference is None
    assert "transfer" in receipt.error and "rejected" in receipt.error


def test_a_rejected_deposit_keeps_the_transfer_reference():
    receipt = rail(FakeNessie(reject="/deposits")).transfer(invoice_id="INV-1", account="A", amount=10)
    assert receipt.ok is False and receipt.reference == "obj-2"
    assert receipt.error.startswith("deposit")


def test_a_network_failure_is_a_failed_receipt_not_an_exception():
    def down(method, url, body):
        raise OSError("network down")

    receipt = rail(down).transfer(invoice_id="INV-1", account="A", amount=10)
    assert receipt.ok is False and "network down" in receipt.error


def test_from_env_needs_all_three_ids():
    assert NessieRail.from_env({"NESSIE_API_KEY": "k"}) is None
    r = NessieRail.from_env({"NESSIE_API_KEY": "k", "NESSIE_PAYER_ACCOUNT_ID": "p",
                             "NESSIE_PAYEE_CUSTOMER_ID": "c", "NESSIE_BASE_URL": "https://nessie.test/"})
    assert isinstance(r, NessieRail)
