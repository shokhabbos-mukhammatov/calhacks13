"""Vendor Verification: independent evidence that backs the callback Control.

The verifier composes adapters (domain age, sender risk) behind one small
interface. RDAP is real and keyless; CRS Fraud Finder is exercised here
through a fake HTTP layer. Missing or failed checks report None, never a guess.
"""
from datetime import datetime, timezone

from firedrill.verify import (
    CrsFraudFinder,
    FixedDomainAge,
    NoSenderCheck,
    RdapDomainAge,
    SenderRisk,
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


# --- CRS Fraud Finder ----------------------------------------------------------
FRAUD_FINDER_OK = {
    "risk": {"score": 82, "tumbling_risk": 1, "domain": {"domain_risk_score": 7}},
    "eam": {"date_first_seen": "2026-09-30", "longevity": 0},
    "dam": {"date_first_seen": "2011-02-01", "longevity": 3},
    "email_validation": {"address": "accounts@lookalike.example", "status": "risky"},
}


class FakeCrs:
    def __init__(self, login_status=200, product=(200, FRAUD_FINDER_OK)):
        self.calls = []
        self.login_status = login_status
        self.product = product

    def __call__(self, method, url, body, headers):
        self.calls.append((method, url.rsplit("/api", 1)[1], body, headers))
        if url.endswith("/users/login"):
            return self.login_status, {"token": "tok-1"} if self.login_status == 200 else {"codes": ["CRS113"]}
        return self.product


def finder(http):
    return CrsFraudFinder("user", "pw", base_url="https://crs.test/api", http=http)


def test_fraud_finder_logs_in_once_and_reads_the_risk_fields():
    http = FakeCrs()
    f = finder(http)
    first, second = f.check("accounts@lookalike.example"), f.check("accounts@lookalike.example")
    assert first == SenderRisk(score=82, email_status="risky", email_longevity=0, domain_longevity=3)
    assert second == first
    paths = [c[1] for c in http.calls]
    assert paths == ["/users/login", "/fraud-finder/fraud-finder", "/fraud-finder/fraud-finder"]
    assert http.calls[1][3] == {"Authorization": "Bearer tok-1"}
    assert http.calls[1][2] == {"email": "accounts@lookalike.example"}


def test_a_failed_login_is_never_retried():
    http = FakeCrs(login_status=401)
    f = finder(http)
    assert f.check("a@b.example") == SenderRisk()
    assert f.check("a@b.example") == SenderRisk()
    assert [c[1] for c in http.calls] == ["/users/login"]  # one attempt, then silence


def test_a_product_error_is_unknown_not_a_guess():
    f = finder(FakeCrs(product=(400, {"codes": ["CRS200"], "messages": ["Request arguments not valid"]})))
    assert f.check("not-an-email") == SenderRisk()


def test_a_network_failure_is_unknown():
    def down(method, url, body, headers):
        raise OSError("network down")

    assert finder(down).check("a@b.example") == SenderRisk()


# --- the verifier ------------------------------------------------------------------
def test_verifier_composes_evidence():
    verifier = VendorVerifier(
        domain_age=FixedDomainAge({"northwind-supply.com": 4000, "lookalike.example": 0}),
        sender=NoSenderCheck(),
    )
    ev = verifier.verify(
        vendor_id="northwind",
        on_file_number="+1-555-0100",
        sender_email="accounts@lookalike.example",
    )
    assert ev.callback_number == "+1-555-0100"
    assert ev.callback_source == "on_file"
    assert ev.sender_domain_age_days == 0
    assert ev.sender_risk_score is None      # CRS not wired -> unknown, not guessed
    assert ev.sender_email_status is None


def test_verifier_passes_the_sender_risk_through():
    verifier = VendorVerifier(domain_age=FixedDomainAge({}), sender=finder(FakeCrs()))
    ev = verifier.verify(vendor_id="northwind", on_file_number="+1-555-0100",
                         sender_email="accounts@lookalike.example")
    assert ev.sender_risk_score == 82
    assert ev.sender_email_status == "risky"
    assert ev.sender_email_longevity == 0
    assert ev.sender_domain_age_days is None  # domain not in the fixed table
