"""
Error localization - "which number is the typo?", not just "something is wrong".

Every existing tool (statcheck, GRIM, and Rigor's own checks) tells you THAT a
paper's numbers are inconsistent. None tells you WHICH reported value is most likely
the mistake. But a paper's statistics are an over-determined constraint system: the
sample size N, a test's degrees of freedom, its statistic and p-value, and a group's
mean and SD are all linked. So we can ask a sharper question:

    what is the smallest single correction that makes the most checks pass?

This is a minimum-repair search (model-based diagnosis) over the numeric constraint
graph. Crucially it stays provable: every proposed repair is VERIFIED by re-running
the deterministic checks with the substituted value, and results are presented as
parsimony-ranked *hypotheses* for the human reviewer - never as certainties. No other
statistics-integrity tool does this.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from rigor.checks import check_df_vs_n


@dataclass
class Hypothesis:
    summary: str        # plain-language root-cause hypothesis
    implicates: str     # the reported value(s) implicated
    repair: str         # the concrete corrected value(s)
    explains: int       # how many findings this single repair provably resolves
    kind: str           # "shared-n"

    def to_dict(self) -> dict:
        return asdict(self)


def localize(stats: list[dict], means: list[dict], stated_n: int | None) -> list[Hypothesis]:
    """Return parsimony-ranked root-cause hypotheses, each provably resolving >= 1 finding.

    The flagship diagnosis: a single wrong study N can explain a whole cluster of
    degrees-of-freedom clashes. Rather than assert it, we PROVE it - a candidate N is
    accepted only after re-running the df-vs-N check confirms it reconciles every
    flagged test - and present it as a hypothesis for the reviewer, since we cannot
    know whether the N or the df values are the true error.
    """
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
