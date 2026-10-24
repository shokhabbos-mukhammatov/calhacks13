"""Vendor Verification: independent evidence that backs the callback Control.

The verifier composes adapters (domain age, business/sanctions) behind one
small interface. RDAP is real and keyless; the CRS business check plugs in
when sandbox credentials arrive. Missing checks report None, never a guess.
"""
from datetime import datetime, timezone

from firedrill.verify import (
    FixedDomainAge,
    NoBusinessCheck,
    RdapDomainAge,
    VendorVerifier,
)

FIXED_NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)

RDAP_SAMPLE = {
    "events": [
        {"eventAction": "registration", "eventDate": "2026-10-23T08:00:00Z"},
        {"eventAction": "expiration", "eventDate": "2027-10-23T08:00:00Z"},
    ]
}


def test_rdap_domain_age_from_registration_event():
    rdap = RdapDomainAge(fetch=lambda url: RDAP_SAMPLE, clock=lambda: FIXED_NOW)
    assert rdap.age_days("example.com") == 0  # registered ~16 hours before FIXED_NOW


def test_rdap_old_domain():
    sample = {"events": [{"eventAction": "registration", "eventDate": "2009-06-02T17:14:10Z"}]}
    rdap = RdapDomainAge(fetch=lambda url: sample, clock=lambda: FIXED_NOW)
    assert rdap.age_days("apify.com") > 6000


def test_rdap_missing_registration_returns_none():
    rdap = RdapDomainAge(fetch=lambda url: {"events": []}, clock=lambda: FIXED_NOW)
    assert rdap.age_days("odd.example") is None


def test_rdap_fetch_failure_returns_none():
    def boom(url):
        raise OSError("network down")

    rdap = RdapDomainAge(fetch=boom, clock=lambda: FIXED_NOW)
    assert rdap.age_days("example.com") is None


def test_verifier_composes_evidence():
    verifier = VendorVerifier(
        domain_age=FixedDomainAge({"northwind-supply.com": 4000, "lookalike.example": 0}),
        business=NoBusinessCheck(),
    )
    ev = verifier.verify(
        vendor_id="northwind",
        on_file_number="+1-555-0100",
        sender_domain="lookalike.example",
        legal_name="Northwind Supply LLC",
    )
    assert ev.callback_number == "+1-555-0100"
    assert ev.callback_source == "on_file"
    assert ev.sender_domain_age_days == 0
    assert ev.business_ok is None      # CRS not wired yet -> unknown, not guessed
    assert ev.sanctions_hit is None
