"""
Deterministic statistical-consistency checking (statcheck-style).

THE ANTI-WRAPPER CORE. These functions recompute a p-value from a reported test
statistic using exact distributions (SciPy). No LLM, no guessing - just math. If
the reported p-value disagrees with the recomputed one, that is a provable error,
and if the significance *decision* flips at alpha, that is a serious one.

Elsewhere in Rigor, an LLM extracts `t(48) = 1.9, p < .001` from paper prose;
the *verdict* is computed here and cannot be hallucinated.

Prior art (cited honestly): the `statcheck` R package pioneered p-value
recomputation, but only on rigidly APA-formatted stats. Rigor's contribution is
LLM extraction that generalises these checks to arbitrary papers + a battery of
additional checks. The checks themselves are standard, validated science - which
is exactly why the verdicts are trustworthy.
"""
from __future__ import annotations

from dataclasses import dataclass

from scipy import stats


@dataclass
class StatResult:
    test: str
    statistic: float
    reported_p: float
    computed_p: float
    comparator: str
    consistent: bool
    decision_error: bool  # significance decision flips at alpha => serious
    message: str


def _p_from_t(t: float, df: float) -> float:
    return float(2 * stats.t.sf(abs(t), df))  # two-tailed


def _p_from_f(f: float, df1: float, df2: float) -> float:
    return float(stats.f.sf(f, df1, df2))


def _p_from_chi2(x: float, df: float) -> float:
    return float(stats.chi2.sf(x, df))


def _p_from_r(r: float, df: float) -> float:
    # df = n - 2; the number printed as r(df) is the degrees of freedom, not n.
    t = r * ((df / (1 - r**2)) ** 0.5)
    return _p_from_t(t, df)


def _p_from_z(z: float) -> float:
    return float(2 * stats.norm.sf(abs(z)))  # two-tailed


def _decimals(x: float) -> int:
    s = repr(float(x))
    return len(s.split(".")[1]) if "." in s else 0


def _is_consistent(reported_p: float, computed_p: float, comparator: str) -> bool:
    if comparator == "<":
        return computed_p <= reported_p
    if comparator == ">":
        return computed_p >= reported_p
    # exact "="  -> consistent if they round the same at the reported precision
    d = min(max(_decimals(reported_p), 2), 4)
    return abs(round(computed_p, d) - round(reported_p, d)) <= 10 ** (-d)


def _reported_significant(reported_p: float, comparator: str, alpha: float) -> bool:
    if comparator == ">":
        return False  # e.g. "p > .05" -> treated as not significant
    return reported_p <= alpha if comparator == "<" else reported_p < alpha


def check_pvalue(
    test: str,
    statistic: float,
    reported_p: float,
    *,
    df1: float | None = None,
    df2: float | None = None,
    n: int | None = None,
    comparator: str = "=",
    alpha: float = 0.05,
    one_tailed: bool = False,
) -> StatResult:
    """Recompute the p-value for a reported test and compare it to what was printed."""
    test = test.lower()
    if test == "t":
        p = _p_from_t(statistic, df1)  # df1 = df
    elif test == "f":
        p = _p_from_f(statistic, df1, df2)
    elif test in ("chi2", "chisq", "x2"):
        p = _p_from_chi2(statistic, df1)
    elif test == "r":
        df = df1 if df1 is not None else (n - 2)  # accept df directly or derive from n
        p = _p_from_r(statistic, df)
    elif test == "z":
        p = _p_from_z(statistic)
    else:
        raise ValueError(f"unsupported test: {test!r} (use t/f/chi2/r/z)")

    if one_tailed and test in ("t", "z", "r"):
        p /= 2

    consistent = _is_consistent(reported_p, p, comparator)
    decision_error = _reported_significant(reported_p, comparator, alpha) != (p < alpha)

    verdict = "CONSISTENT" if consistent else ("DECISION ERROR" if decision_error else "INCONSISTENT")
    msg = (
        f"{verdict}: reported p {comparator} {reported_p:g}, "
        f"recomputed p = {p:.4g}"
    )
    if decision_error:
        claimed = "significant" if _reported_significant(reported_p, comparator, alpha) else "n.s."
        actual = "significant" if p < alpha else "n.s."
        msg += f"  ->  claimed {claimed}, actually {actual} at alpha={alpha:g}"

    return StatResult(
        test=test,
        statistic=statistic,
        reported_p=reported_p,
        computed_p=p,
        comparator=comparator,
        consistent=consistent,
        decision_error=decision_error,
        message=msg,
    )
