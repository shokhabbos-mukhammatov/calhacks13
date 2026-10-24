"""The Breach Grid runner, and looking at a result more than once honestly.

These run no models: `run_one` is injected, so the whole stopping rule is
testable offline and deterministically.
"""
import pytest

from firedrill.grid import CellSpec, run_cell, run_grid, saved
from firedrill.stats import alpha_per_look, decided, fisher_exact, sequential_interval, wilson


class FakeDrill:
    def __init__(self, seed, hit):
        self.seed, self.hit = seed, hit


def runner(pattern):
    """A cell whose drills hit according to `pattern`, cycled."""
    calls = []

    def run_one(spec, seed):
        calls.append((spec, seed))
        return FakeDrill(seed, pattern[(seed - 1) % len(pattern)])

    return run_one, calls


def hit(drill):
    return drill.hit


# --- Fisher's exact test ---------------------------------------------------------
def test_fisher_on_the_projects_own_before_and_after():
    one, two = fisher_exact(4, 2, 0, 6)      # 4 of 6 breaches vs 0 of 6
    assert one == pytest.approx(0.0303, abs=1e-4)
    assert two == pytest.approx(0.0606, abs=1e-4)


def test_fisher_matches_a_known_table():
    """The classic 3/3 vs 1/4 tea-tasting style table."""
    one, two = fisher_exact(3, 1, 1, 3)
    assert one == pytest.approx(0.2429, abs=1e-4)
    assert two == pytest.approx(0.4857, abs=1e-4)


def test_fisher_is_unbothered_by_an_arm_with_no_events():
    """Exactly the case that makes a logistic fit diverge."""
    one, _ = fisher_exact(12, 6, 0, 18)
    assert 0.0 < one < 0.001


def test_fisher_on_no_difference_is_not_significant():
    one, two = fisher_exact(3, 3, 3, 3)
    assert one > 0.5 and two == pytest.approx(1.0)


def test_fisher_needs_two_arms_and_some_events():
    assert fisher_exact(0, 0, 0, 0) == (1.0, 1.0)
    assert fisher_exact(0, 6, 0, 6) == (1.0, 1.0)   # no events anywhere


# --- looking more than once ---------------------------------------------------------
def test_alpha_is_split_across_the_looks_planned():
    assert alpha_per_look(4) == pytest.approx(0.0125)
    assert alpha_per_look(1) == pytest.approx(0.05)


def test_an_adjusted_interval_is_never_narrower_than_the_fixed_one():
    """The price of peeking, paid up front."""
    for k, n in ((0, 6), (3, 6), (4, 12), (12, 24)):
        a_low, a_high = sequential_interval(k, n, looks=4)
        w_low, w_high = wilson(k, n)
        assert (a_high - a_low) >= (w_high - w_low) - 1e-12


def test_one_look_is_the_ordinary_interval():
    assert sequential_interval(4, 12, looks=1) == pytest.approx(wilson(4, 12), abs=1e-9)


def test_a_clear_cell_is_decided_sooner_than_a_coin_flip():
    """The whole saving: 0 of 12 settles, 6 of 12 does not."""
    assert decided(0, 12, looks=4, target_width=0.45)
    assert not decided(6, 12, looks=4, target_width=0.45)


# --- the runner -----------------------------------------------------------------------
def test_a_decided_cell_stops_early():
    run_one, calls = runner([False])          # nothing ever breaches
    spec = CellSpec("claude-haiku-4-5", "patch:v1", "vmt-01")
    r = run_cell(spec, range(1, 25), run_one=run_one, is_hit=hit, look=6, max_n=24, target_width=0.45)
    assert r.n < 24 and "decided" in r.stopped
    assert len(calls) == r.n                   # no drill was run after the decision


def test_an_undecided_cell_runs_to_the_cap():
    run_one, _ = runner([True, False])         # a coin flip
    spec = CellSpec("claude-haiku-4-5", "baseline", "vmt-01")
    r = run_cell(spec, range(1, 25), run_one=run_one, is_hit=hit, look=6, max_n=24, target_width=0.20)
    assert r.n == 24 and "ran out of seeds" in r.stopped
    assert r.hits == 12


def test_a_cell_counts_hits_and_keeps_its_drills():
    run_one, _ = runner([True, True, False])
    spec = CellSpec("m", "baseline", "vmt-01")
    r = run_cell(spec, range(1, 7), run_one=run_one, is_hit=hit, look=6, max_n=6, target_width=0.99)
    assert (r.hits, r.n) == (4, 6) and len(r.drills) == 6
    assert r.rate == pytest.approx(4 / 6)


def test_every_cell_in_the_grid_runs():
    run_one, calls = runner([False])
    specs = [CellSpec(m, c, "vmt-01") for m in ("a", "b") for c in ("baseline", "patch:v1")]
    results = run_grid(specs, range(1, 7), run_one=run_one, is_hit=hit,
                       look=6, max_n=6, target_width=0.99, cell_concurrency=2)
    assert len(results) == 4
    assert {r.spec for r in results} == set(specs)
    assert len(calls) == 24


def test_the_saving_is_reported_against_a_fixed_grid():
    run_one, _ = runner([False])
    specs = [CellSpec("m", "patch:v1", "vmt-01")]
    results = run_grid(specs, range(1, 25), run_one=run_one, is_hit=hit,
                       look=6, max_n=24, target_width=0.45)
    ran, fixed = saved(results, 6, 24)
    assert fixed == 24 and ran < fixed
