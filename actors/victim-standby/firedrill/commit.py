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

A commitment names each drill by card, seed *and* config, because the re-run
saves more drills of the same cards and seeds under the patch. The reveal has
to check exactly the drills committed to, not whatever is on disk by then.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

COMMITMENTS_DIR = Path(__file__).resolve().parents[1] / "commitments"

VOLATILE = ("saved_at", "relabeled")  # not part of what we commit to


def record_id(record: dict) -> str:
    """One drill under one config: the record's file name without `.json`."""
    return f"{record['card']['id']}-s{record['seed']}-{record['config']['fingerprint'][:8]}"


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
    record_ids: list[str]    # the same, with the config, so a reveal can find them
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
        record_ids=[record_id(r) for r in ordered],
        committed_at=clock().isoformat(timespec="seconds"),
    ), salts


def verify(commitment: dict, records: list[dict], salts: list[str]) -> bool:
    """Recompute the root from the revealed drills and salts."""
    ordered = sorted(records, key=lambda r: (r["card"]["id"], r["seed"], r["config"]["fingerprint"]))
    if len(ordered) != len(salts) or len(ordered) != commitment["count"]:
        return False
    return merkle_root([leaf(s, r) for s, r in zip(salts, ordered)]) == commitment["root"]


def covered(commitment: dict, records: list[dict]) -> list[dict]:
    """The records a commitment is over, out of everything saved since."""
    ids = set(commitment["record_ids"])
    return [r for r in records if record_id(r) in ids]


def write_commitment(directory: Path, name: str, records: list[dict], *, now=None) -> Commitment:
    """Commit and write `<name>.commit.json` (public) and `<name>.salts.json`
    (secret until the reveal). Refuses to replace either: new salts would mean
    a new root, silently swapping out the one already published."""
    public, secret = directory / f"{name}.commit.json", directory / f"{name}.salts.json"
    for path in (public, secret):
        if path.exists():
            raise FileExistsError(f"{path} exists: a second commitment would replace the published one")
    commitment, salts = commit(records, now=now)
    directory.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(commitment.to_dict(), indent=1), encoding="utf-8")
    secret.write_text(json.dumps(salts), encoding="utf-8")
    return commitment


def revealed_families(directory: Path = COMMITMENTS_DIR) -> set[str]:
    """Families whose drills have been revealed, and so may be published."""
    if not directory.exists():
        return set()
    return {f for path in directory.glob("*.reveal.json")
            for f in json.loads(path.read_text(encoding="utf-8"))["commitment"]["families"]}
