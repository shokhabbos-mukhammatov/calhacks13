"""The CRS personas a drill's phone numbers are drawn from.

The live sandbox check lives in scripts/check_integrations.py, which asks CRS
whether each persona still answers as recorded. These tests hold the
properties the drill depends on, offline.
"""
import re

from firedrill.crs_personas import BY_NUMBER, CONTACTS, IMPOSTORS
from firedrill.verify import digits


def test_a_contact_is_registered_to_someone_and_an_impostor_is_not_that_someone():
    """The whole point: the two groups answer differently, so a callback
    control has something to check."""
    assert all(p.expect for p in CONTACTS)
    contacts = {p.expect for p in CONTACTS}
    for p in IMPOSTORS:
        assert p.expect not in contacts          # a stranger, or nobody at all


def test_every_number_is_unreachable_and_speakable():
    for p in CONTACTS + IMPOSTORS:
        # Area code 555 with an exchange starting 0: unassignable in the North
        # American plan, so it can never ring a real person.
        assert re.fullmatch(r"\+1-555-010-10\d\d", p.number), p.number
        assert len(digits(p.number)) == 10


def test_no_number_serves_two_personas():
    assert len(BY_NUMBER) == len(CONTACTS) + len(IMPOSTORS)


def test_there_are_enough_contacts_to_vary_a_grid():
    """A 24-seed grid should not put the same contact on every drill."""
    assert len(CONTACTS) >= 6 and len(IMPOSTORS) >= 3
