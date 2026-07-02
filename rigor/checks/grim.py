"""
GRIM test (Granularity-Related Inconsistency of Means).

Given a reported mean, a sample size, and how many integer items were averaged,
some means are *arithmetically impossible*. Example: the mean of 10 whole-number
answers can only land on x.0, x.1, ... x.9 - so a reported mean of 3.45 (N=10)
cannot exist. This catches fabricated or mistyped data with pure arithmetic - no
model, no judgment call.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class GrimResult:
    reported_mean: float
    n: int
    n_items: int
    decimals: int
    possible: bool
    nearest_possible: list[float]
    message: str


def grim(reported_mean: float, n: int, n_items: int = 1, decimals: int = 2) -> GrimResult:
    """Is `reported_mean` achievable as the mean of `n` * `n_items` integer responses?"""
    scale = n * n_items
    target = round(reported_mean, decimals)
    approx_sum = reported_mean * scale

    possible = False
    achievable: list[float] = []
    lo, hi = math.floor(approx_sum) - 2, math.ceil(approx_sum) + 2
    for candidate_sum in range(lo, hi + 1):
        recon = candidate_sum / scale
        achievable.append(round(recon, decimals))
        if round(recon, decimals) == target:
            possible = True

    # nearest achievable means around the reported one (for the report)
    nearest = sorted(set(achievable), key=lambda m: abs(m - reported_mean))[:2]

    if possible:
        msg = f"POSSIBLE: mean {target} is achievable with N={n} (items={n_items})"
    else:
        msg = (
            f"IMPOSSIBLE: mean {target} cannot be the mean of {scale} integer "
            f"responses. Nearest achievable: {nearest}"
        )
    return GrimResult(
        reported_mean=reported_mean,
        n=n,
        n_items=n_items,
        decimals=decimals,
        possible=possible,
        nearest_possible=nearest,
        message=msg,
    )
