"""CRS sandbox test identities, used as the people behind a drill's phones.

A callback control rests on one question: **does this number belong to the
party the vendor file says it does?** Until now a drill's numbers were made up,
so CRS had nothing to say about them and returned the same answer for the
vendor and the attacker alike — a bolt-on.

These are CRS's own sandbox personas, and their reverse lookups differ in
exactly the way the control cares about:

- a **contact** number comes back registered to that contact, which is what
  the vendor file claims;
- an **impostor** number comes back registered to a different person, or to
  nobody at all — the shape of a number a fraudster puts in a message.

Every entry below was checked against the live sandbox, not copied from a
list. CRS's own note on the personas says *most* return their own name, so
`expect` records what each one actually did and `tests/test_crs_personas.py`
holds the set to the ones that behaved.

The numbers are CRS's: area code 555, then an exchange starting `0`. Neither
is assignable in the North American plan, so these can no more reach a real
person than `+1-415-555-01xx` did, and they are speakable on a voice drill.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    id: str
    number: str          # as a person would say it, and as CRS resolves it
    expect: str | None   # who CRS returns, or None for "no record"
    city: str | None = None


# Personas whose reverse lookup names them: a plausible AP contact on file.
CONTACTS = (
    Persona("P01", "+1-555-010-1001", "MARGARET OKAFOR", "SAN JOSE"),
    Persona("P02", "+1-555-010-1002", "DANIEL WHITFIELD", "AUSTIN"),
    Persona("P10", "+1-555-010-1010", "LAUREN KOWALCZYK", "DETROIT"),
    Persona("P18", "+1-555-010-1018", "TERRENCE ABERNATHY", "CHICAGO"),
    Persona("P19", "+1-555-010-1019", "GRACE NAKAMURA", "BERKELEY"),
    Persona("P20", "+1-555-010-1020", "DOLORES WHITCOMB", "SANTA BARBARA"),
)

# Numbers that do not belong to the vendor's contact. P12 is CRS's
# identity-mismatch persona and answers with someone else entirely; P04 and
# P13 (credit-invisible and synthetic identity) have no record to return.
IMPOSTORS = (
    Persona("P12", "+1-555-010-1012", "RAJESH MENON", "NEW YORK"),
    Persona("P13", "+1-555-010-1013", None),
    Persona("P04", "+1-555-010-1004", None),
)

BY_NUMBER = {p.number: p for p in CONTACTS + IMPOSTORS}
