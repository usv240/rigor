"""
Plain-language explanations - turn each finding into "what it means" + "what to do".

Rigor is built for authors, not only statisticians, so every finding gets a
human-readable meaning and a concrete next step. These are deterministic
templates (no LLM, no cost, always consistent), filled from the exact numbers the
math produced.
"""
from __future__ import annotations


def explain_pvalue(r) -> tuple[str, str]:
    p = r.computed_p
    if r.consistent:
        return ("The reported p-value matches its test statistic. No issue here.", "")
    if r.decision_error:
        if p >= 0.05:  # reported as significant, but it is not
            plain = (f"Reported as significant, but recomputing from the test statistic gives "
                     f"p = {p:.3g}, which is above .05 and therefore NOT significant. "
                     f"The claimed effect is not statistically supported.")
            fix = "Recheck the test statistic and degrees of freedom, or revise the claim of a significant effect."
        else:  # reported as non-significant, but it is significant
            plain = (f"Reported as non-significant, but recomputing gives p = {p:.3g}, which is "
                     f"below .05 and IS significant. A real effect may have been missed.")
            fix = "Re-examine this result; the effect appears to be significant after all."
        return (plain, fix)
    plain = (f"The reported p-value does not match its test statistic (recomputed p = {p:.3g}). "
             f"The overall conclusion likely stands, but a number is off.")
    return (plain, "Check for a typo in the test statistic, the degrees of freedom, or the p-value.")


def explain_grim(g) -> tuple[str, str]:
    if g.possible:
        return ("This mean is achievable for the reported sample size. No issue here.", "")
    nearest = ", ".join(str(x) for x in g.nearest_possible)
    plain = (f"A mean of {g.reported_mean:g} is arithmetically impossible for {g.n} whole-number "
             f"responses. The nearest values that CAN occur are {nearest}.")
    return (plain, "Check for a typo in the mean, the sample size (N), or how the responses were recorded.")


def explain_dfn(d) -> tuple[str, str]:
    plain = (f"This result's degrees of freedom require at least {d.implied_min_n} participants, "
             f"but the study reports only {d.stated_n}. Both numbers cannot be correct.")
    return (plain, "Check whether the sample size, the degrees of freedom, or the test type is mislabeled.")


_CLAIM_FIX = {
    "OVERCLAIM": "Revise the sentence so it matches the actual (recomputed) result.",
    "CAUSAL": "Use associational wording unless the design supports causation, and review this yourself.",
    "GENERALIZATION": "Limit the claim to the sample studied, or justify the broader claim.",
}


def explain_claim(issue: str, detail: str) -> tuple[str, str]:
    # the LLM's explanation is already plain; pair it with a concrete, templated action.
    return (detail, _CLAIM_FIX.get(issue.upper(), "Review this claim against the evidence."))
