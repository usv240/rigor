"""
Cross-consistency checks - do the numbers agree with each other across the paper?

df-vs-N: a test's degrees of freedom imply a minimum sample size. If the paper
says it studied N people but reports a df that needs more, that's impossible - you
can't analyse more cases than you collected. statcheck never looks at this; it
only compares a reported p to its own test statistic. This is pure arithmetic.

Deliberately conservative (credibility first): only t-tests and correlations,
where df -> N is unambiguous, and only flags the *impossible* direction
(implied N greater than the stated N).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DfNResult:
    consistent: bool
    implied_min_n: int
    stated_n: int
    message: str


def check_df_vs_n(test: str, df1: float | None, stated_n: int) -> DfNResult | None:
    """Return a finding if the df implies more cases than the study reports, else OK/None."""
    test = test.lower()
    if df1 is None or stated_n is None:
        return None
    if test == "t":
        implied_min = int(df1) + 1  # paired: N=df+1 (independent is df+2, so +1 is the floor)
        label = f"t(df={df1:g}) needs at least N={implied_min}"
    elif test == "r":
        implied_min = int(df1) + 2  # r(df) => N = df + 2
        label = f"r(df={df1:g}) needs N={implied_min}"
    else:
        return None  # F/chi2/z: df->N is ambiguous (e.g. repeated measures), skip

    consistent = implied_min <= stated_n
    if consistent:
        msg = f"OK: {label}; consistent with the stated N={stated_n}."
    else:
        msg = (f"IMPOSSIBLE: {label}, but the study reports only N={stated_n}. "
               f"An analysis cannot use more cases than were collected.")
    return DfNResult(consistent, implied_min, stated_n, msg)
