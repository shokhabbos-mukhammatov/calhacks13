"""Trace sink port: every drill turn, tool call and verdict is emitted here.

Adapters: MemorySink (tests, the scorecard's local feed), ElasticSink
(Elastic Agent Builder, added if Elastic's criteria call for it) and an
Apify dataset sink inside the fire-drill Actor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class TraceEvent:
    drill_id: str
    turn: int
    kind: str                 # "message" | "tool_call" | "verdict"
    data: dict[str, Any]


class TraceSink(Protocol):
    def emit(self, event: TraceEvent) -> None: ...


@dataclass
class MemorySink:
    events: list[TraceEvent] = field(default_factory=list)

    def emit(self, event: TraceEvent) -> None:
        self.events.append(event)
