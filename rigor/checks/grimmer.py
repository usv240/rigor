"""
GRIMMER test (Granularity-Related Inconsistency of Means Mapped to Error Repeats).

The successor to GRIM (Anaya, 2016). GRIM checks a reported MEAN; GRIMMER checks
a reported standard deviation / variance for the same granularity impossibility.

Given a mean M, an SD, and N whole-number responses, the SD is not free: the sum
S = M*N must be an integer (GRIM), and the sum of squares Q = SD^2*(N-1) + S^2/N
must ALSO be an integer - because every response is an integer, so every squared
response is an integer, so their sum is an integer. GRIMMER adds one more, subtler
constraint that pure integrality misses: because k^2 and k always share the same
parity, Q must have the SAME parity as S. Many SDs that survive "is Q an integer?"
die on that parity test.

Design choice - conservative, like the df-vs-N check: we use only NECESSARY
conditions that need no knowledge of the scale's min/max. That makes every flag a
PROVABLE impossibility (zero false positives), at the cost of missing a few
impossibilities that scale bounds would also catch. Credibility first: Rigor never
cries wolf.

Only applies to single-item integer responses (n_items = 1); composite/multi-item
scores make the integer-response model ambiguous, so we decline rather than guess.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class GrimmerResult:
    reported_mean: float
    reported_sd: float
    n: int
    possible: bool
    reason: str            # "" if possible; else "mean" | "sd"
    message: str


def _ulp(decimals: int) -> float:
    """Half the last-digit unit: the rounding half-width at `decimals` places."""
    return 0.5 * 10 ** (-decimals)


def grimmer(
    reported_mean: float,
    reported_sd: float,
    n: int,
    n_items: int = 1,
    decimals: int = 2,
    sd_decimals: int | None = None,
) -> GrimmerResult:
    """Is `reported_sd` achievable for `n` integer responses with mean `reported_mean`?

    Returns possible=False ONLY when it is arithmetically impossible (a proof), so a
    False is always trustworthy. Returns possible=True when it cannot be disproven.
    """
    if sd_decimals is None:
        sd_decimals = decimals
    if n_items != 1 or n < 2 or reported_sd < 0:
        # ambiguous or undefined (SD needs N >= 2); decline to judge.
        return GrimmerResult(reported_mean, reported_sd, n, True, "",
                             "NOT APPLICABLE: GRIMMER needs single-item integer responses, N>=2")

    scale = n
    m_target = round(reported_mean, decimals)

    # GRIM step: integer sums S whose mean rounds to the reported mean.
    approx = reported_mean * scale
    candidate_sums = [
        S for S in range(math.floor(approx) - 2, math.ceil(approx) + 3)
        if round(S / scale, decimals) == m_target
    ]
    if not candidate_sums:
        return GrimmerResult(
            reported_mean, reported_sd, n, False, "mean",
            f"IMPOSSIBLE: mean {m_target} is itself GRIM-impossible for N={n}, so no SD can be valid",
        )

    sd_lo = max(0.0, reported_sd - _ulp(sd_decimals))
    sd_hi = reported_sd + _ulp(sd_decimals)
    eps = 1e-9

    for S in candidate_sums:
        # Q = sum of squared responses implied by this sum and the reported SD range.
        # sample variance uses ddof=1: SD^2 = (Q - S^2/N) / (N - 1).
        base = (S * S) / scale
        q_lo = sd_lo * sd_lo * (scale - 1) + base
        q_hi = sd_hi * sd_hi * (scale - 1) + base
        first = math.ceil(q_lo - eps)
        last = math.floor(q_hi + eps)
        for Q in range(first, last + 1):
            # Necessary conditions: Q integer (Q is int here), variance >= 0 (Q >= S^2/N),
            # and parity Q ≡ S (mod 2) because k^2 ≡ k (mod 2) for every integer k.
            if Q + eps >= base and (Q - S) % 2 == 0:
                return GrimmerResult(
                    reported_mean, reported_sd, n, True, "",
                    f"POSSIBLE: SD {round(reported_sd, sd_decimals)} is achievable for N={n} "
                    f"(mean {m_target})",
                )

    return GrimmerResult(
        reported_mean, reported_sd, n, False, "sd",
        f"IMPOSSIBLE: SD {round(reported_sd, sd_decimals)} cannot occur for N={n} integer "
        f"responses with mean {m_target} (no integer sum-of-squares of matching parity exists)",
    )
