"""The Breach Grid: run every cell, and stop a cell once it is decided.

A cell is one (model x hardening x tactic card). Cells are independent, so
they run concurrently; within a cell, drills run in **looks** of a fixed size
and the cell stops as soon as its adjusted interval is narrow enough.

The looks are fixed in advance and alpha is split across them. Peeking at a
result and stopping when it looks good is the optional-stopping fallacy, and
a harness whose whole claim is trustworthy measurement cannot afford one
(see `firedrill.stats.alpha_per_look`).

A cell that is obviously safe or obviously broken finishes in one or two
looks. A cell near 50% keeps running, which is where the drills are worth
spending.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, Iterable

from firedrill.stats import decided, sequential_interval

DEFAULT_LOOK = 6
DEFAULT_MAX_N = 24
DEFAULT_WIDTH = 0.45


@dataclass(frozen=True)
class CellSpec:
    """One cell of the grid. `card_id` is None for the benign pack."""
    model: str
    config: str
    card_id: str | None = None

    @property
    def label(self) -> str:
        return f"{self.card_id or 'benign':<8} {self.model:<18} {self.config}"


@dataclass
class CellResult:
    spec: CellSpec
    hits: int = 0
    n: int = 0
    stopped: str = ""            # why it stopped
    drills: list = field(default_factory=list)

    @property
    def rate(self) -> float:
        return self.hits / self.n if self.n else 0.0


RunOne = Callable[[CellSpec, int], object]   # (spec, seed) -> a Drill
IsHit = Callable[[object], bool]             # did this drill count?


def run_cell(
    spec: CellSpec,
    seeds: Iterable[int],
    *,
    run_one: RunOne,
    is_hit: IsHit,
    look: int = DEFAULT_LOOK,
    max_n: int = DEFAULT_MAX_N,
    target_width: float = DEFAULT_WIDTH,
    concurrency: int = 4,
    on_drill: Callable[[CellSpec, object], None] | None = None,
) -> CellResult:
    """Run one cell look by look, stopping as soon as it is decided."""
    seeds = list(seeds)[:max_n]
    looks_planned = max(1, -(-min(len(seeds), max_n) // look))   # ceil
    result = CellResult(spec)

    for start in range(0, len(seeds), look):
        batch = seeds[start:start + look]
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            drills = list(pool.map(lambda s: run_one(spec, s), batch))
        for drill in drills:
            result.drills.append(drill)
            result.n += 1
            result.hits += int(is_hit(drill))
            if on_drill:
                on_drill(spec, drill)
        if decided(result.hits, result.n, looks_planned, target_width):
            low, high = sequential_interval(result.hits, result.n, looks_planned)
            result.stopped = f"decided at n={result.n} (interval [{low:.2f}, {high:.2f}])"
            return result

    low, high = sequential_interval(result.hits, result.n, looks_planned)
    result.stopped = f"ran out of seeds at n={result.n} (interval [{low:.2f}, {high:.2f}])"
    return result


def run_grid(
    specs: Iterable[CellSpec],
    seeds: Iterable[int],
    *,
    run_one: RunOne,
    is_hit: IsHit,
    cell_concurrency: int = 2,
    **cell_kwargs,
) -> list[CellResult]:
    """Every cell, a few at a time. Cells are independent by construction:
    each drill builds its own world and its own Ledger."""
    specs, seeds = list(specs), list(seeds)
    with ThreadPoolExecutor(max_workers=max(1, cell_concurrency)) as pool:
        return list(pool.map(
            lambda spec: run_cell(spec, seeds, run_one=run_one, is_hit=is_hit, **cell_kwargs),
            specs,
        ))


def saved(results: list[CellResult], look: int = DEFAULT_LOOK, max_n: int = DEFAULT_MAX_N) -> tuple[int, int]:
    """(drills run, drills a fixed-size grid would have run)."""
    return sum(r.n for r in results), len(results) * max_n
