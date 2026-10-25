"""Commit-reveal over the held-out drills (ADR-0002).

The commitment is published before any patch is written; the drills and
salts are published after the re-run. Anyone can then recompute the root.
"""
import copy
from datetime import datetime, timezone

from firedrill.commit import Commitment, canonical, commit, leaf, merkle_root, verify

NOW = lambda: datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)


def record(card_id, seed, family="lookalike-domain", breach=True):
    return {
        "card": {"id": card_id, "family": family, "channel": "invoice", "sender": "lookalike_domain"},
        "seed": seed,
        "config": {"name": "baseline", "model": "claude-haiku-4-5", "fingerprint": "f00d"},
        "kit": {"invoice_id": f"INV-{seed}"},
        "transcript": [{"turn": 1, "body": "...", "reply": "..."}],
        "tool_calls": [],
        "verdict": {"breach": breach, "oob": False, "canary": False},
        "payments": [],
        "saved_at": "2026-10-24T00:00:00+00:00",
    }


HELD = [record("ld-01", 1), record("ld-01", 2), record("ld-02", 1)]


def test_a_commitment_covers_the_drills_and_hides_them():
    c, salts = commit(HELD, now=NOW)
    assert c.count == 3 and len(salts) == 3 and len(set(salts)) == 3
    assert c.families == ["lookalike-domain"]
    assert c.drill_ids == ["ld-01-s1", "ld-01-s2", "ld-02-s1"]
    assert c.committed_at == "2026-10-24T12:00:00+00:00"
    published = str(c.to_dict())
    assert "INV-1" not in published and not any(s in published for s in salts)


def test_the_root_recomputes_from_the_reveal():
    c, salts = commit(HELD, now=NOW)
    assert verify(c.to_dict(), HELD, salts) is True
    assert verify(c.to_dict(), list(reversed(HELD)), salts) is True  # order is canonical


def test_swapping_a_drill_breaks_the_root():
    c, salts = commit(HELD, now=NOW)
    swapped = copy.deepcopy(HELD)
    swapped[0]["verdict"]["breach"] = False
    assert verify(c.to_dict(), swapped, salts) is False


def test_dropping_or_adding_a_drill_breaks_the_root():
    c, salts = commit(HELD, now=NOW)
    assert verify(c.to_dict(), HELD[:2], salts[:2]) is False
    assert verify(c.to_dict(), HELD + [record("ld-02", 2)], salts + ["00"]) is False


def test_wrong_salts_break_the_root():
    c, _ = commit(HELD, now=NOW)
    assert verify(c.to_dict(), HELD, ["00" * 16] * 3) is False


def test_volatile_fields_are_not_committed_to():
    a, b = HELD[0], {**HELD[0], "saved_at": "2027-01-01T00:00:00+00:00", "relabeled": "note"}
    assert canonical(a) == canonical(b)
    assert leaf("s", a) == leaf("s", b)


def test_two_commitments_of_the_same_drills_differ():
    first, _ = commit(HELD, now=NOW)
    second, _ = commit(HELD, now=NOW)
    assert first.root != second.root  # fresh salts hide whether the set repeated


def test_merkle_promotes_odd_nodes():
    assert merkle_root([]) == merkle_root([])
    assert merkle_root(["a"]) == "a"
    import hashlib
    ab = hashlib.sha256(b"ab").hexdigest()
    assert merkle_root(["a", "b"]) == ab
    assert merkle_root(["a", "b", "c"]) == hashlib.sha256((ab + "c").encode()).hexdigest()
