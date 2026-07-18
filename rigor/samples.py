"""Example papers users can load with one click in the web tool.

All three are SYNTHETIC, written for this demo. We deliberately do not host real
published papers, which are copyrighted; those are referenced by DOI in the docs
instead. Each example is built to exercise a different behaviour: planted errors,
a genuinely clean paper, and correct numbers wrapped in an overstated claim.
"""
from __future__ import annotations

from rigor.audit import SAMPLE_PAPER

# Correct statistics throughout, hedged conclusion: Rigor should leave this alone.
CLEAN_PAPER = """
In a randomized study (N = 62), the treatment group reported higher motivation than
the control group on a continuous 0-100 scale. An independent-samples t-test found a
significant difference, t(60) = 2.90, p = .005.

A follow-up one-way ANOVA across the three conditions was also significant,
F(2, 59) = 5.40, p = .007.

These results indicate that, in this sample, the intervention was associated with
higher reported motivation. Further work is needed to test whether the effect
generalizes.
""".strip()

# Every number is internally consistent, but the conclusion oversells them: this is
# the claim-vs-evidence check's moment.
OVERCLAIM_PAPER = """
In a pilot study (N = 18), users of the new app reported higher satisfaction
(M = 5.5, SD = 1.1) than a comparison group on a 1-7 scale. The difference reached
significance, t(16) = 2.20, p = .043.

We conclude that the app dramatically and reliably increases satisfaction for
everyone, and recommend it be rolled out to all users nationwide.
""".strip()

SAMPLES = [
    {
        "id": "planted",
        "label": "Planted errors",
        "note": "Several planted mistakes plus one correct control result.",
        "text": SAMPLE_PAPER,
    },
    {
        "id": "clean",
        "label": "A clean paper",
        "note": "Correct statistics throughout. Rigor should leave it alone.",
        "text": CLEAN_PAPER,
    },
    {
        "id": "overclaim",
        "label": "Overstated claim",
        "note": "The numbers are fine, but the conclusion oversells them.",
        "text": OVERCLAIM_PAPER,
    },
]
