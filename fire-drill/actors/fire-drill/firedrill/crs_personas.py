"""CRS sandbox test identities, used as the parties behind a drill's phones.

A callback control rests on one question: **does this number belong to the
party the vendor file says it does, and who are they?** Until the numbers were
real, CRS had nothing to say about them and returned the same answer for the
vendor and the attacker alike — a bolt-on.

These are CRS's own sandbox personas, so CRS answers both halves:

| | Number on file | Number offered in the request |
| --- | --- | --- |
| Reverse lookup | the contact the vendor file names | a stranger, or no record |
| Fraud Finder | a low risk score | a high one |

**Send the whole body.** CRS matches a persona on the full request — name,
phone, email, IP and address. A request missing a field does not match, falls
through to the real vendor, and comes back useless (and billable). Calling
Fraud Finder with the email alone scored `None` for every persona; with the
body, Victor Anand scores 85 and Grace Nakamura 9.

Every entry below was checked against the live sandbox. `expect` is what the
reverse lookup returns and `risk` what Fraud Finder scores;
`scripts/check_integrations.py` re-asks CRS whether they still hold.

The numbers are CRS's: area code 555, then an exchange starting `0`. Neither
is assignable in the North American plan, so these can no more reach a real
person than `+1-415-555-01xx` did, and they are speakable on a voice drill.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    """One CRS sandbox identity, with everything a product match needs."""
    id: str
    number: str          # as a person would say it, and as CRS resolves it
    expect: str | None   # who the reverse lookup returns, None for "no record"
    risk: int            # the Fraud Finder score, 0-100, higher is riskier
    first: str
    last: str
    email: str
    ip: str
    line1: str
    city: str
    state: str
    postal: str

    @property
    def name(self) -> str:
        return f"{self.first} {self.last}"

    def fraud_finder_body(self) -> dict:
        """The exact shape CRS matches a persona on. Anything less misses."""
        return {
            "firstName": self.first,
            "lastName": self.last,
            "phoneNumber": "".join(c for c in self.number if c.isdigit())[-10:],
            "email": self.email,
            "ipAddress": self.ip,
            "address": {"addressLine1": self.line1, "city": self.city,
                        "state": self.state, "postalCode": self.postal},
        }


# Personas whose reverse lookup names them and whom Fraud Finder scores low:
# a plausible accounts-payable contact to hold the number on file.
CONTACTS = (
    Persona("P01", "+1-555-010-1001", "MARGARET OKAFOR", 11, "MARGARET", "OKAFOR",
            "margaret.okafor@example.com", "203.0.113.11",
            "1420 WILLOW CREEK DR", "SAN JOSE", "CA", "95125"),
    Persona("P02", "+1-555-010-1002", "DANIEL WHITFIELD", 9, "DANIEL", "WHITFIELD",
            "daniel.whitfield@example.com", "203.0.113.12",
            "88 LAKESHORE BLVD", "AUSTIN", "TX", "78746"),
    Persona("P10", "+1-555-010-1010", "LAUREN KOWALCZYK", 10, "LAUREN", "KOWALCZYK",
            "lauren.kowalczyk@example.com", "203.0.113.20",
            "1181 WOODWARD AVE", "DETROIT", "MI", "48226"),
    Persona("P18", "+1-555-010-1018", "TERRENCE ABERNATHY", 12, "TERRENCE", "ABERNATHY",
            "terrence.abernathy@example.com", "203.0.113.28",
            "2102 S HALSTED ST", "CHICAGO", "IL", "60608"),
    Persona("P19", "+1-555-010-1019", "GRACE NAKAMURA", 9, "GRACE", "NAKAMURA",
            "grace.nakamura@example.com", "203.0.113.29",
            "1850 SOLANO AVE", "BERKELEY", "CA", "94707"),
    Persona("P20", "+1-555-010-1020", "DOLORES WHITCOMB", 8, "DOLORES", "WHITCOMB",
            "dolores.whitcomb@example.com", "203.0.113.30",
            "612 OCEAN VIEW DR", "SANTA BARBARA", "CA", "93109"),
)

# Parties who are not the vendor's contact, and whom CRS scores accordingly.
# P12 is the identity-mismatch persona: the reverse lookup answers with someone
# else entirely. P13 is synthetic identity and P14 is a deceased indicator;
# both are high risk, and P13 holds no record at all.
IMPOSTORS = (
    Persona("P12", "+1-555-010-1012", "RAJESH MENON", 85, "VICTOR", "ANAND",
            "v.anand.1968@example.com", "198.51.100.12",
            "55 WATER ST FL 20", "NEW YORK", "NY", "10041"),
    Persona("P13", "+1-555-010-1013", None, 88, "KAYLA", "BRENNAN",
            "kb.9921x@example.com", "198.51.100.13",
            "9021 KINGSTON PIKE", "KNOXVILLE", "TN", "37923"),
    Persona("P14", "+1-555-010-1014", "HAROLD PETTIGREW", 80, "HAROLD", "PETTIGREW",
            "harold.pettigrew@example.com", "203.0.113.24",
            "310 ELM ST", "DAYTON", "OH", "45402"),
)

ALL = CONTACTS + IMPOSTORS
BY_NUMBER = {p.number: p for p in ALL}
