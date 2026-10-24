"""Vendor Verification: independent evidence behind the callback Control.

`VendorVerifier.verify` is the one call callers learn. Behind it sit adapters:
- DomainAge: RDAP (real, keyless) or a fixed table for tests.
- BusinessCheck: CRS sandbox via MCP (when credentials arrive) or none.

A check that isn't wired reports None ("unknown"), never a guessed value.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Protocol


@dataclass
class Evidence:
    vendor_id: str
    callback_number: str | None
    callback_source: str | None          # "on_file" or the URL it was verified from
    sender_domain_age_days: int | None
    business_ok: bool | None             # CRS business identity / state filings
    sanctions_hit: bool | None           # CRS OFAC check
    sources: list[str] = field(default_factory=list)


# --- domain age -------------------------------------------------------------
class DomainAge(Protocol):
    def age_days(self, domain: str) -> int | None: ...


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/rdap+json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RdapDomainAge:
    """Domain age from the registration event in RDAP (rdap.org bootstrap)."""

    def __init__(
        self,
        fetch: Callable[[str], dict] = _http_get_json,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._fetch = fetch
        self._clock = clock

    def age_days(self, domain: str) -> int | None:
        try:
            data = self._fetch(f"https://rdap.org/domain/{domain}")
        except Exception:
            return None  # network or lookup failure -> unknown, never a guess
        for event in data.get("events", []):
            if event.get("eventAction") == "registration":
                registered = datetime.fromisoformat(event["eventDate"].replace("Z", "+00:00"))
                return (self._clock() - registered).days
        return None


class FixedDomainAge:
    def __init__(self, table: dict[str, int]) -> None:
        self._table = table

    def age_days(self, domain: str) -> int | None:
        return self._table.get(domain)


# --- business identity + sanctions (CRS) -------------------------------------
class BusinessCheck(Protocol):
    def check(self, legal_name: str) -> tuple[bool | None, bool | None]:
        """Return (business_ok, sanctions_hit)."""
        ...


class NoBusinessCheck:
    """Placeholder until the CRS sandbox is wired: everything unknown."""

    def check(self, legal_name: str) -> tuple[bool | None, bool | None]:
        return None, None


# --- the verifier ---------------------------------------------------------------
class VendorVerifier:
    def __init__(self, domain_age: DomainAge, business: BusinessCheck) -> None:
        self._domain_age = domain_age
        self._business = business

    def verify(
        self,
        *,
        vendor_id: str,
        on_file_number: str,
        sender_domain: str | None,
        legal_name: str,
    ) -> Evidence:
        business_ok, sanctions_hit = self._business.check(legal_name)
        return Evidence(
            vendor_id=vendor_id,
            callback_number=on_file_number,
            callback_source="on_file",
            sender_domain_age_days=(
                self._domain_age.age_days(sender_domain) if sender_domain else None
            ),
            business_ok=business_ok,
            sanctions_hit=sanctions_hit,
        )
