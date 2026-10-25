"""Vendor Verification: independent evidence behind the callback Control.

`VendorVerifier.verify` is the one call callers learn. Behind it sit adapters:
- DomainAge: RDAP (real, keyless) or a fixed table for tests.
- SenderCheck: CRS Fraud Finder (AtData) on the sender's email address, or none.
- PhoneOwnerCheck: CRS AccurateAppend reverse lookup — who a phone number is
  registered to — so a number that arrived with a request can be checked
  against whoever holds the number on file before anyone calls it.

A check that isn't wired, or fails, reports None ("unknown"), never a
guessed value. Evidence is for the callback decision: it says what is known
about the sender, and the callback number always comes from the file.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol


@dataclass
class Evidence:
    vendor_id: str
    callback_number: str | None
    callback_source: str | None          # "on_file": never a number from the request
    sender_domain_age_days: int | None   # RDAP registration age of the sender's domain
    sender_risk_score: int | None        # Fraud Finder 0-100, higher is riskier
    sender_email_status: str | None      # valid | invalid | risky | unverifiable | unknown
    sender_email_longevity: int | None   # 0-3: how long the address has been seen
    sources: list[str] = field(default_factory=list)
    # A number the agent was handed (in a message, an invoice, a call) and
    # asked about: who holds it, who holds the number on file, and whether
    # they are the same. None wherever CRS could not say.
    number_checked: str | None = None
    number_found: bool | None = None
    number_registered_to: str | None = None
    on_file_registered_to: str | None = None
    number_matches_on_file: bool | None = None


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


# --- sender risk (CRS Fraud Finder) ----------------------------------------------
@dataclass
class SenderRisk:
    score: int | None = None
    email_status: str | None = None
    email_longevity: int | None = None
    domain_longevity: int | None = None


class SenderCheck(Protocol):
    def check(self, email: str) -> SenderRisk: ...


class NoSenderCheck:
    """Fallback when CRS isn't configured: everything unknown."""

    def check(self, email: str) -> SenderRisk:
        return SenderRisk()


HttpJson = Callable[[str, str, dict | None, dict], tuple[int, Any]]


def _http_json(method: str, url: str, body: dict | None, headers: dict) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    if data:
        headers = {**headers, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw


CRS_SANDBOX = "https://api-sandbox.stitchcredit.com/api"


class _CrsSession:
    """One CRS sandbox login, behind every CRS product call.

    Logs in once and reuses the token; a 401 on a product call triggers one
    re-login. A failed login is remembered and never retried in-process,
    because repeated failed logins lock the sandbox account."""

    def __init__(self, username: str, password: str, *, base_url: str = CRS_SANDBOX,
                 http: HttpJson = _http_json) -> None:
        self._user, self._password = username, password
        self._base = base_url.rstrip("/")
        self._http = http
        self._token: str | None = None
        self._login_failed = False

    @classmethod
    def from_env(cls, env: Mapping[str, str]):
        """The adapter when CRS_USERNAME and CRS_PASSWORD are set, else None."""
        user, password = env.get("CRS_USERNAME", ""), env.get("CRS_PASSWORD", "")
        if not (user and password):
            return None
        return cls(user, password, base_url=env.get("CRS_BASE_URL") or CRS_SANDBOX)

    def _post_retrying(self, path: str, body: dict) -> tuple[int, Any]:
        status, reply = self._post(path, body)
        if status == 401 and self._token:
            self._token = None  # expired: one re-login, then give up
            status, reply = self._post(path, body)
        return status, reply

    def _post(self, path: str, body: dict) -> tuple[int, Any]:
        token = self._login()
        if token is None:
            return 401, "login unavailable"
        return self._http("POST", f"{self._base}{path}", body, {"Authorization": f"Bearer {token}"})

    def _login(self) -> str | None:
        if self._token:
            return self._token
        if self._login_failed:
            return None
        status, body = self._http("POST", f"{self._base}/users/login",
                                  {"username": self._user, "password": self._password}, {})
        if status == 200 and isinstance(body, dict) and body.get("token"):
            self._token = body["token"]
            return self._token
        self._login_failed = True
        return None


class CrsFraudFinder(_CrsSession):
    """CRS Credit API sandbox, Fraud Finder (AtData): fraud risk for an email
    address plus how long the address and its domain have been seen."""

    def __init__(self, username: str, password: str, *, base_url: str = CRS_SANDBOX,
                 config: str = "fraud-finder", http: HttpJson = _http_json) -> None:
        super().__init__(username, password, base_url=base_url, http=http)
        self._config = config

    def check(self, email: str) -> SenderRisk:
        try:
            status, body = self._post_retrying(f"/fraud-finder/{self._config}", {"email": email})
        except Exception:
            return SenderRisk()
        if status != 200 or not isinstance(body, dict):
            return SenderRisk()
        risk = body.get("risk") or {}
        validation = body.get("email_validation") or {}
        return SenderRisk(
            score=risk.get("score"),
            email_status=validation.get("status"),
            email_longevity=(body.get("eam") or {}).get("longevity"),
            domain_longevity=(body.get("dam") or {}).get("longevity"),
        )


# --- who holds a phone number (CRS reverse lookup) --------------------------------
def digits(number: str) -> str:
    """The ten digits CRS wants: country code and punctuation dropped."""
    d = "".join(ch for ch in number if ch.isdigit())
    return d[1:] if len(d) == 11 and d.startswith("1") else d


@dataclass(frozen=True)
class PhoneOwner:
    found: bool | None = None   # None: CRS could not say. False: it looked, nobody holds it.
    name: str | None = None
    city: str | None = None


class PhoneOwnerCheck(Protocol):
    def owner(self, number: str) -> PhoneOwner: ...


class NoPhoneOwner:
    """Fallback when CRS isn't configured: every owner unknown."""

    def owner(self, number: str) -> PhoneOwner:
        return PhoneOwner()


class FixedPhoneOwner:
    """A fixed directory, for tests and offline drills. A number missing from
    it is held by nobody."""

    def __init__(self, table: dict[str, str]) -> None:
        self._table = {digits(k): v for k, v in table.items()}

    def owner(self, number: str) -> PhoneOwner:
        name = self._table.get(digits(number))
        return PhoneOwner(found=True, name=name) if name else PhoneOwner(found=False)


class CrsReverseLookup(_CrsSession):
    """CRS AccurateAppend reverse lookup: who a phone number is registered to.

    The sandbox personas answer it: most with their own name, the
    identity-mismatch persona with someone else's, the synthetic-identity
    persona with no record. That is the exact question a callback rests on —
    does this number belong to the person the vendor file says it does?"""

    def owner(self, number: str) -> PhoneOwner:
        try:
            status, body = self._post_retrying("/accurate-append/reverse",
                                               {"phoneNumber": digits(number)})
        except Exception:
            return PhoneOwner()
        if status != 200 or not isinstance(body, dict):
            return PhoneOwner()
        records = (body.get("data") or {}).get("records")
        if records is None:
            return PhoneOwner()
        if not records:
            return PhoneOwner(found=False)
        first = records[0]
        name = " ".join(x for x in (first.get("firstName"), first.get("lastName")) if x) or None
        return PhoneOwner(found=True, name=name, city=first.get("city"))


# --- the verifier ---------------------------------------------------------------
class VendorVerifier:
    def __init__(self, domain_age: DomainAge, sender: SenderCheck,
                 phone_owner: PhoneOwnerCheck | None = None) -> None:
        self._domain_age = domain_age
        self._sender = sender
        self._phone_owner = phone_owner

    def with_domain_age(self, domain_age: DomainAge) -> VendorVerifier:
        """The same checks with another domain-age source (a drill seeds one)."""
        return VendorVerifier(domain_age, self._sender, self._phone_owner)

    def verify(self, *, vendor_id: str, on_file_number: str, sender_email: str | None,
               phone_number: str | None = None) -> Evidence:
        domain = sender_email.split("@", 1)[1] if sender_email and "@" in sender_email else None
        risk = self._sender.check(sender_email) if sender_email else SenderRisk()
        ev = Evidence(
            vendor_id=vendor_id,
            callback_number=on_file_number,
            callback_source="on_file",
            sender_domain_age_days=self._domain_age.age_days(domain) if domain else None,
            sender_risk_score=risk.score,
            sender_email_status=risk.email_status,
            sender_email_longevity=risk.email_longevity,
        )
        if not phone_number or not phone_number.strip():
            return ev
        ev.number_checked = phone_number
        if self._phone_owner is None:
            return ev                               # nothing to ask: unknown, not a guess
        given = self._phone_owner.owner(phone_number)
        on_file = self._phone_owner.owner(on_file_number)
        ev.number_found, ev.number_registered_to = given.found, given.name
        ev.on_file_registered_to = on_file.name
        ev.sources.append("crs_reverse_lookup")
        if digits(phone_number) == digits(on_file_number):
            ev.number_matches_on_file = True
        elif given.found is None or on_file.found is None:
            ev.number_matches_on_file = None        # CRS could not answer for one of them
        elif given.found is False or not on_file.name:
            ev.number_matches_on_file = False
        else:
            ev.number_matches_on_file = given.name.casefold() == on_file.name.casefold()
        return ev
