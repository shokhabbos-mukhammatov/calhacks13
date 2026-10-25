"""Commit-reveal over the held-out drills (ADR-0002).

Before any patch is written we publish one hash: the Merkle root of the
held-out drills, each salted. After the re-run we publish the drills and
their salts, and anyone can recompute the root and check it against the
commit's timestamp in git. Hash commitments are binding, so the held-out set
cannot have been swapped for an easier one after seeing the patch.

    leaf_i = SHA256(salt_i || canonical(drill_i))
    root   = merkle_root([leaf_1 .. leaf_m])

An odd node is promoted unchanged to the next level (never duplicated, which
would make two different trees share a root).
"""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

VOLATILE = ("saved_at", "relabeled")  # not part of what we commit to


def canonical(record: dict) -> str:
    """The drill as committed: stable key order, no volatile fields."""
    return json.dumps({k: v for k, v in record.items() if k not in VOLATILE},
                      sort_keys=True, separators=(",", ":"))


def leaf(salt: str, record: dict) -> str:
    return hashlib.sha256((salt + canonical(record)).encode()).hexdigest()


def merkle_root(leaves: list[str]) -> str:
    if not leaves:
        return hashlib.sha256(b"").hexdigest()
    level = list(leaves)
    while len(level) > 1:
        nxt = [
            hashlib.sha256((level[i] + level[i + 1]).encode()).hexdigest()
            for i in range(0, len(level) - 1, 2)
        ]
        if len(level) % 2:
            nxt.append(level[-1])  # promote, do not duplicate
        level = nxt
    return level[0]


@dataclass
class Commitment:
    root: str
    count: int
    families: list[str]
    drill_ids: list[str]     # which drills, not what they contain
    committed_at: str
    algorithm: str = "leaf_i = SHA256(salt_i || canonical(drill_i)); odd nodes promoted"

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def commit(records: list[dict], *, now=None) -> tuple[Commitment, list[str]]:
    """Returns the public commitment and the secret salts (same order)."""
    ordered = sorted(records, key=lambda r: (r["card"]["id"], r["seed"], r["config"]["fingerprint"]))
    salts = [secrets.token_hex(16) for _ in ordered]
    root = merkle_root([leaf(s, r) for s, r in zip(salts, ordered)])
    clock = now or (lambda: datetime.now(timezone.utc))
    return Commitment(
        root=root,
        count=len(ordered),
        families=sorted({r["card"]["family"] for r in ordered}),
        drill_ids=[f"{r['card']['id']}-s{r['seed']}" for r in ordered],
        committed_at=clock().isoformat(timespec="seconds"),
    ), salts


def verify(commitment: dict, records: list[dict], salts: list[str]) -> bool:
    """Recompute the root from the revealed drills and salts."""
    ordered = sorted(records, key=lambda r: (r["card"]["id"], r["seed"], r["config"]["fingerprint"]))
    if len(ordered) != len(salts) or len(ordered) != commitment["count"]:
        return False
    return merkle_root([leaf(s, r) for s, r in zip(salts, ordered)]) == commitment["root"]
