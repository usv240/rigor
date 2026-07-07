"""
Error localization - "which number is the typo?", not just "something is wrong".

Every existing tool (statcheck, GRIM, and Rigor's own checks) tells you THAT a
paper's numbers are inconsistent. None tells you WHICH reported value is most likely
the mistake. But a paper's statistics are an over-determined constraint system: the
sample size N, a test's degrees of freedom, its statistic and p-value, and a group's
mean and SD are all linked. So we can ask a sharper question:

    what is the smallest single correction that makes the most checks pass?

This is a minimum-repair search (model-based diagnosis) over the numeric constraint
graph. It spans two check families:

  * df-vs-N clusters: one wrong study N can explain a whole cluster of degrees-of-
    freedom clashes, so a single correction resolves many findings at once.
  * GRIM-impossible means: for a mean that cannot exist at the reported N, we find
    the nearest N that WOULD make it possible, and offer that or the corrected mean
    as the two minimal single-value repairs.

Crucially it stays provable: every proposed repair is VERIFIED by re-running the
deterministic checks with the substituted value, and results are presented as
parsimony-ranked *hypotheses* for the human reviewer - never as certainties. No other
statistics-integrity tool does this.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from rigor.checks import check_df_vs_n, grim


@dataclass
class Hypothesis:
    summary: str        # plain-language root-cause hypothesis
    implicates: str     # the reported value(s) implicated
    repair: str         # the concrete corrected value(s)
    explains: int       # how many findings this single repair provably resolves
    kind: str           # "shared-n" | "grim-repair"

    def to_dict(self) -> dict:
        return asdict(self)


def localize(stats: list[dict], means: list[dict], stated_n: int | None) -> list[Hypothesis]:
    """Return parsimony-ranked root-cause hypotheses, each provably resolving >= 1 finding.

    Combines two minimum-repair diagnoses (df-vs-N clusters and GRIM-impossible means)
    and ranks them most-explanatory first, so a single correction that resolves several
    findings leads. Every repair is proven by re-running the deterministic check, and
    presented as a hypothesis for the reviewer, since we cannot know which of the linked
    reported values is the true error.
    """
    hyps = _dfn_hypotheses(stats, stated_n) + _grim_hypotheses(means)
    hyps.sort(key=lambda h: h.explains, reverse=True)  # most parsimonious first (stable)
    return hyps


def _dfn_hypotheses(stats: list[dict], stated_n: int | None) -> list[Hypothesis]:
    """The flagship diagnosis: a single wrong study N can explain a whole cluster of
    degrees-of-freedom clashes. Rather than assert it, we PROVE it - a candidate N is
    accepted only after re-running the df-vs-N check confirms it reconciles every
    flagged test - and present it as a hypothesis, since we cannot know whether the N
    or the df values are the true error."""
    hyps: list[Hypothesis] = []
    if stated_n is None:
        return hyps

    dfn_hits = []
    for s in stats:
        d = check_df_vs_n(str(s.get("test", "")), s.get("df1"), stated_n)
        if d is not None and not d.consistent:
            dfn_hits.append((s, d))
    if not dfn_hits:
        return hyps

    needed = max(d.implied_min_n for _, d in dfn_hits)
    # PROVE it: N = needed must make every one of these checks consistent.
    resolved = all(
        (r := check_df_vs_n(str(s.get("test", "")), s.get("df1"), needed)) is not None
        and r.consistent
        for s, _ in dfn_hits
    )
    if not resolved:
        return hyps

    if len(dfn_hits) >= 2:
        hyps.append(Hypothesis(
            summary=(f"One correction explains {len(dfn_hits)} findings: the stated sample size "
                     f"N={stated_n} is the likely typo. Every flagged test's degrees of freedom "
                     f"become consistent once N is at least {needed} - it is more parsimonious that "
                     f"one N is wrong than that {len(dfn_hits)} separate df values are."),
            implicates=f"sample size N={stated_n}",
            repair=f"N >= {needed}",
            explains=len(dfn_hits), kind="shared-n"))
    else:
        s, d = dfn_hits[0]
        t = str(s.get("test", "")).lower()
        max_df = stated_n - (1 if t == "t" else 2)
        hyps.append(Hypothesis(
            summary=(f"This degrees-of-freedom clash has two minimal fixes: raise the stated N to "
                     f"at least {d.implied_min_n}, or lower the reported df to fit N={stated_n}."),
            implicates=f"N={stated_n} or df={s.get('df1')}",
            repair=f"N >= {d.implied_min_n}  (or df <= {max_df})",
            explains=1, kind="shared-n"))

    return hyps


def _smallest_n_fix(mean: float, n: int, n_items: int, decimals: int, reach: int | None = None) -> int | None:
    """The N nearest to the reported one that makes `mean` GRIM-possible, or None if
    none is found within `reach`. Searched by growing distance so the closest fix wins."""
    if reach is None:
        reach = max(20, n)
    for delta in range(1, reach + 1):
        for cand in (n + delta, n - delta):
            if cand >= 2 and grim(mean, cand, n_items, decimals).possible:
                return cand
    return None


def _grim_hypotheses(means: list[dict]) -> list[Hypothesis]:
    """For each GRIM-impossible mean, offer the two minimal single-value repairs: the
    nearest N that makes the mean achievable (proven by re-running GRIM), or the nearest
    achievable mean. One of the two reported values is wrong, and we say which two."""
    hyps: list[Hypothesis] = []
    for m in means:
        try:
            value, n = float(m["value"]), int(m["n"])
        except (TypeError, ValueError, KeyError):
            continue
        ni, dec = m.get("n_items"), m.get("decimals")
        n_items = 1 if ni is None else int(ni)
        decimals = 2 if dec is None else int(dec)
        try:
            g = grim(value, n, n_items, decimals)
        except Exception:  # noqa: BLE001 - malformed extraction; skip
            continue
        if g.possible or n_items != 1:
            continue  # nothing to repair, or a composite score we decline to diagnose
        nearest = g.nearest_possible[0] if g.nearest_possible else None

        n_fix = _smallest_n_fix(value, n, n_items, decimals)
        if n_fix is not None and not grim(value, n_fix, n_items, decimals).possible:
            n_fix = None  # PROVE it; drop the N repair if it does not actually hold

        if n_fix is not None:
            hyps.append(Hypothesis(
                summary=(f"The mean {value:g} is impossible for N={n}. The smallest single correction "
                         f"is N={n_fix} (the nearest N that makes {value:g} achievable); the alternative "
                         f"is that the mean is a typo for {nearest:g}. One of these two reported values is "
                         f"wrong, not both."),
                implicates=f"N={n} or mean={value:g}",
                repair=f"N={n_fix}  (or mean={nearest:g})",
                explains=1, kind="grim-repair"))
        elif nearest is not None:
            hyps.append(Hypothesis(
                summary=(f"The mean {value:g} is impossible for N={n} and no nearby N resolves it, so the "
                         f"mean itself is the likely typo (nearest achievable value: {nearest:g})."),
                implicates=f"mean={value:g}",
                repair=f"mean={nearest:g}",
                explains=1, kind="grim-repair"))
    return hyps
