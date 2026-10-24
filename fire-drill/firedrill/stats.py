"""Statistics behind the Scorecard. Never report a bare rate at small n.

Two intervals, because they answer different questions:

- **Wilson** is the default. Good coverage at small n, unlike the textbook
  normal approximation, which collapses near 0 and 1 — exactly where a
  breach rate lives.
- **Clopper-Pearson** is exact and guaranteed conservative: its coverage is
  never below the nominal level. It is wider, so it is the one to quote when
  someone wants a bound they cannot argue with.

Rank hardening levels by an interval's lower bound, never by the bare rate,
so a lucky 3 of 3 cannot outrank a solid 48 of 50.
"""
from __future__ import annotations

import math

Z95 = 1.959963984540054  # the normal quantile for a two-sided 95% interval


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials."""
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    z2 = z * z
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    low, high = centre - half, centre + half
    # At the edges the bounds are exactly 0 and 1 — the algebra cancels — but
    # the floating-point arithmetic lands a few ulps short, which then prints
    # as 1.00 while comparing as less than 1.
    return (0.0 if k == 0 else max(0.0, low)), (1.0 if k == n else min(1.0, high))


# --- the regularized incomplete beta, for Clopper-Pearson -------------------
def _betacf(a: float, b: float, x: float, iterations: int = 300) -> float:
    """Continued fraction for the incomplete beta (Lentz's method)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, iterations + 1):
        m2 = 2 * m
        for num in (m * (b - m) * x / ((qam + m2) * (a + m2)),
                    -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))):
            d = 1.0 + num * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + num / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            h *= d * c
        if abs(d * c - 1.0) < 1e-15:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """I_x(a, b): the regularized incomplete beta function."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log1p(-x))
    # The fraction converges quickly only on one side; reflect otherwise.
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def beta_quantile(p: float, a: float, b: float) -> float:
    """The x where I_x(a, b) == p, by bisection.

    Bisection rather than Newton: 200 halvings of [0, 1] are exact to well
    under a printed decimal, and it cannot diverge at the edges, which is
    where every breach rate sits."""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if betainc(a, b, mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact (conservative) binomial interval, from the Beta quantiles.

    lower = Beta(alpha/2; k, n-k+1), upper = Beta(1-alpha/2; k+1, n-k),
    with the closed forms at k = 0 and k = n."""
    if n <= 0:
        return 0.0, 1.0
    lower = 0.0 if k == 0 else beta_quantile(alpha / 2, k, n - k + 1)
    upper = 1.0 if k == n else beta_quantile(1 - alpha / 2, k + 1, n - k)
    return lower, upper


INTERVALS = {"wilson": wilson, "clopper-pearson": lambda k, n: clopper_pearson(k, n)}


def interval(k: int, n: int, kind: str = "wilson") -> tuple[float, float]:
    try:
        return INTERVALS[kind](k, n)
    except KeyError:
        raise ValueError(f"unknown interval {kind!r}; known: {', '.join(INTERVALS)}") from None
