"""Drill records: one JSON file per drill under records/.

The file is named by card, seed and a fingerprint of the victim config, so
re-running the same drill overwrites itself. The fingerprint covers what the
agent can see and do (model, policy, tool scope, whether verify_vendor is
offered); the payment rail only mirrors, so it is recorded but not hashed.
The Remediator reads failing records; scripts/report.py aggregates them.
Records hold the attacker's turns, so records/ is gitignored; commit-reveal
decides what is published.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from firedrill.drill import Drill, VictimConfig

RECORDS_DIR = Path(__file__).resolve().parents[1] / "records"


def model_id(model: Any) -> str:
    return getattr(model, "_model", None) or type(model).__name__


def config_summary(config: VictimConfig) -> dict:
    return {
        "name": config.name,
        "model": model_id(config.model),
        "policy": config.policy,
        "tool_scope": config.tool_scope or {},
        "verify_vendor": config.verifier is not None,
    }


def fingerprint_of(summary: dict) -> str:
    return hashlib.sha256(json.dumps(summary, sort_keys=True).encode()).hexdigest()


def config_fingerprint(config: VictimConfig) -> str:
    return fingerprint_of(config_summary(config))


def drill_to_record(drill: Drill, config: VictimConfig) -> dict:
    return {
        "card": asdict(drill.card),
        "seed": drill.seed,
        "config": {
            **config_summary(config),
            "rail": type(config.rail).__name__ if config.rail else None,
            "fingerprint": config_fingerprint(config),
        },
        "kit": asdict(drill.kit),
        "transcript": [
            {"turn": t.turn, "sender": t.message.sender, "subject": t.message.subject,
             "body": t.message.body, "reply": t.reply}
            for t in drill.transcript
        ],
        "tool_calls": [
            {"turn": e.turn, **e.data} for e in drill.events if e.kind == "tool_call"
        ],
        "verdict": asdict(drill.verdict),
        "cap_turn": drill.cap_turn,
        "ended_by": drill.ended_by,
        "paid_on_file": drill.paid_on_file,
        "payments": [asdict(p) for p in drill.state.payments],
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def record_name(card_id: str, seed: int, fingerprint: str) -> str:
    return f"{card_id}-s{seed}-{fingerprint[:8]}.json"


def record_path(drill: Drill, config: VictimConfig, directory: Path = RECORDS_DIR) -> Path:
    return directory / record_name(drill.card.id, drill.seed, config_fingerprint(config))


def save_drill(drill: Drill, config: VictimConfig, directory: Path = RECORDS_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = record_path(drill, config, directory)
    path.write_text(json.dumps(drill_to_record(drill, config), indent=1), encoding="utf-8")
    return path


def load_records(directory: Path = RECORDS_DIR) -> list[dict]:
    if not directory.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.json"))]
