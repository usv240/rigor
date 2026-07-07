"""
Effect-size consistency: does a reported Cohen's d agree with its t-statistic?

For a two-independent-sample t-test, the test statistic and the effect size are
tied by the group sizes:  t = d / sqrt(1/n1 + 1/n2),  so  d = t * sqrt(1/n1 + 1/n2).
For a paired / one-sample t on N observations:  d = t / sqrt(N).

If a paper prints both a t and a Cohen's d, they must be mutually consistent. This
recomputes d from t and flags a mismatch that rounding cannot explain.

Conservative by construction: it returns None (declines) unless it has exactly the
inputs that make the recomputation unambiguous, so it never fires spuriously. Like
every Rigor check, the verdict is arithmetic - the LLM only supplies the numbers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class EffectSizeResult:
    reported_d: float
    computed_d: float
    consistent: bool
    design: str          # "independent" | "paired"
    message: str


def check_cohens_d(
    t: float,
    reported_d: float,
    *,
    n1: int | None = None,
    n2: int | None = None,
    n: int | None = None,
    design: str = "independent",
) -> EffectSizeResult | None:
    """Recompute Cohen's d from a t-statistic and compare it to the reported d.

    Independent-samples: provide n1 and n2. Paired/one-sample: provide n. Returns
    None if the inputs are insufficient to recompute d unambiguously.
    """
    if t is None or reported_d is None:
        return None
    design = design.lower()
    if design == "independent" and n1 and n2 and n1 > 0 and n2 > 0:
        computed = abs(t) * math.sqrt(1.0 / n1 + 1.0 / n2)
    elif design == "paired" and n and n > 0:
        computed = abs(t) / math.sqrt(n)
    else:
        return None

    rd = abs(reported_d)
    # Tolerance absorbs 2-decimal rounding on d, t, and the derived sqrt term; a real
    # mismatch (e.g. d reported ~2x too large) sits far outside this band.
    tol = 0.05 + 0.03 * rd
    consistent = abs(computed - rd) <= tol
    verdict = "CONSISTENT" if consistent else "INCONSISTENT"
    msg = (f"{verdict}: reported d = {reported_d:g}, recomputed d = {computed:.3g} "
           f"from t = {t:g} ({design})")
    return EffectSizeResult(reported_d, computed, consistent, design, msg)
