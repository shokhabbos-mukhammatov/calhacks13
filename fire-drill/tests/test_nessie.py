"""NessieRail: mirrors approved payments as Capital One Nessie sandbox transfers.

Tested with a fake HTTP transport; a rail failure must never break a drill,
because the Ledger (not the rail) is the source of truth for scoring.
"""
from datetime import date

from firedrill.nessie import NessieRail


class FakeHttp:
    def __init__(self, response=None, error=None):
        self.calls = []
        self._response = response or {
            "code": 201,
            "message": "Created transfer",
            "objectCreated": {"_id": "tx-123"},
        }
        self._error = error

    def post_json(self, url, body):
        self.calls.append((url, body))
        if self._error:
            raise self._error
        return self._response


def make_rail(http):
    return NessieRail(
        base_url="https://prod-api.nessieisreal.com",
        api_key="KEY",
        source_account_id="SRC",
        account_map={"ACCT-APPROVED": "NESSIE-VENDOR", "ACCT-ATTACKER": "NESSIE-MULE"},
        http=http,
        today=lambda: date(2026, 10, 24),
    )


def test_transfer_posts_to_the_documented_endpoint_with_the_key():
    http = FakeHttp()
    receipt = make_rail(http).transfer(invoice_id="INV-1", account="ACCT-APPROVED", amount=10_000)
    url, body = http.calls[0]
    assert url == "https://prod-api.nessieisreal.com/accounts/SRC/transfers?key=KEY"
    assert body == {
        "medium": "balance",
        "payee_id": "NESSIE-VENDOR",
        "amount": 10_000,
        "transaction_date": "2026-10-24",
        "description": "INV-1",
    }
    assert receipt.ok is True
    assert receipt.reference == "tx-123"


def test_redirected_payment_lands_in_the_mapped_attacker_account():
    http = FakeHttp()
    make_rail(http).transfer(invoice_id="INV-1", account="ACCT-ATTACKER", amount=10_000)
    assert http.calls[0][1]["payee_id"] == "NESSIE-MULE"


def test_unknown_account_is_not_sent():
    http = FakeHttp()
    receipt = make_rail(http).transfer(invoice_id="INV-1", account="ACCT-UNKNOWN", amount=5)
    assert receipt.ok is False
    assert http.calls == []


def test_http_failure_returns_a_failed_receipt_instead_of_raising():
    http = FakeHttp(error=OSError("network down"))
    receipt = make_rail(http).transfer(invoice_id="INV-1", account="ACCT-APPROVED", amount=5)
    assert receipt.ok is False
