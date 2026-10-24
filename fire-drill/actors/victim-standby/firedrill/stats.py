"""Statistics behind the Scorecard. Never report a bare rate at small n."""
from __future__ import annotations

import math


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials (95% at z=1.96).

    Good coverage at small n, unlike the normal approximation. Rank
    hardening levels by the lower bound, so a lucky 3/3 does not outrank a
    solid 48/50. With no trials the interval is the whole range."""
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    z2 = z * z
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    return max(0.0, centre - half), min(1.0, centre + half)
