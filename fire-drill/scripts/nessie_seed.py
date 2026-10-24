"""Seed the Capital One Nessie sandbox for Fire Drill, or check the mirror.

    .venv/Scripts/python scripts/nessie_seed.py          # create the payer account + payee customer, print ids for .env
    .venv/Scripts/python scripts/nessie_seed.py --check  # mirror one payment with the ids in .env, list the deposit

Seeding creates: a customer "Lakeside Supply Co" with a Checking account
"Lakeside AP" (NESSIE_PAYER_ACCOUNT_ID) and a customer "Fire Drill Payees"
(NESSIE_PAYEE_CUSTOMER_ID) under which NessieRail creates one account per
Ledger account label. Nessie has no delete for customers, so seed once.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import dotenv_values

from firedrill.payments import NessieRail, _http_json

ADDRESS = {"street_number": "1", "street_name": "Lakeside Dr", "city": "Oakland", "state": "CA", "zip": "94607"}


def main() -> None:
    env = {k: v or "" for k, v in dotenv_values(ROOT / ".env").items()}
    base, key = env.get("NESSIE_BASE_URL", "https://prod-api.nessieisreal.com").rstrip("/"), env["NESSIE_API_KEY"]

    def call(method, path, body=None):
        status, out = _http_json(method, f"{base}{path}?key={key}", body)
        if status not in (200, 201):
            sys.exit(f"{method} {path} -> HTTP {status}: {out}")
        return out

    if "--check" in sys.argv:
        rail = NessieRail.from_env(env)
        if rail is None:
            sys.exit("set NESSIE_PAYER_ACCOUNT_ID and NESSIE_PAYEE_CUSTOMER_ID in .env first (run without --check)")
        receipt = rail.transfer(invoice_id="INV-CHECK", account="ACCT-CHECK", amount=1)
        print("receipt:", receipt)
        deposits = call("GET", f"/accounts/{rail.account_id('ACCT-CHECK')}/deposits")
        print("deposits on ACCT-CHECK:", json.dumps(deposits, indent=1)[:600])
        return

    payer_customer = call("POST", "/customers", {"first_name": "Lakeside", "last_name": "Supply Co", "address": ADDRESS})
    payer = call("POST", f"/customers/{payer_customer['objectCreated']['_id']}/accounts",
                 {"type": "Checking", "nickname": "Lakeside AP", "rewards": 0, "balance": 5_000_000})
    payees = call("POST", "/customers", {"first_name": "Fire Drill", "last_name": "Payees", "address": ADDRESS})
    print("Add to .env:")
    print(f"NESSIE_PAYER_ACCOUNT_ID={payer['objectCreated']['_id']}")
    print(f"NESSIE_PAYEE_CUSTOMER_ID={payees['objectCreated']['_id']}")


if __name__ == "__main__":
    main()
