"""
Field baselines, so a paper's result can be measured against something real instead
of asserted in a vacuum. Every number here is from published data and is cited, which
is the only honest way for an integrity tool to show a benchmark.

Source: Nuijten, M. B., Hartgerink, C. H. J., van Assen, M. A. L. M., Epskamp, S., &
Wicherts, J. M. (2016). "The prevalence of statistical reporting errors in psychology
(1985-2013)." Behavior Research Methods, 48, 1205-1226. The statcheck tool was run over
roughly 250,000 p-values in about 16,700 papers.

These are approximate, rounded to how they are usually quoted, and labelled as such
wherever shown.
"""
from __future__ import annotations

# A conservative estimate of how long it takes a person to locate one statistic in a
# paper and recompute it by hand: find the test, read off the degrees of freedom, look
# up the distribution, compute the p-value, and compare. Used only to estimate time
# saved, and always displayed WITH this assumption visible so the number is honest.
MANUAL_MIN_PER_CHECK = 3

FIELD_BASELINE = {
    "source": "Nuijten et al. 2016 (statcheck over ~250,000 p-values in ~16,700 papers)",
    "citation": "Nuijten et al. 2016, Behavior Research Methods 48:1205-1226",
    # about half of papers had at least one p-value inconsistent with its statistic
    "papers_with_inconsistency": 0.50,
    # about one in eight papers had an inconsistency large enough to change the conclusion
    "papers_with_decision_error": 0.125,
    # about one in ten reported p-values was inconsistent
    "pvalues_inconsistent": 0.10,
}
