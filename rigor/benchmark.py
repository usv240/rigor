"""
End-to-end benchmark - the accuracy number.

Runs the FULL pipeline (LLM extraction + deterministic checks) over a balanced,
labelled set: half the snippets contain a known error, half are correct. We
measure whether Rigor flags the bad ones (recall) and - just as important -
whether it leaves the good ones alone (false-positive rate). Extraction is the
only non-deterministic part, so this really tests extraction reliability.

Run:  python -m rigor.benchmark
"""
from __future__ import annotations

from rigor.audit import audit_text

# (snippet, should_be_flagged, note). Verdicts are ground truth by construction.
CASES: list[tuple[str, bool, str]] = [
    # --- should be flagged (known errors) ---
    ("A paired t-test showed a significant effect, t(48) = 1.90, p < .001.", True, "t decision error (~.06)"),
    ("A one-way ANOVA found no difference, F(2, 57) = 3.20, p = .35.", True, "F decision error (~.048)"),
    ("The groups differed, chi2(1) = 2.1, p = .02.", True, "chi2 decision error (~.15)"),
    ("The manipulation worked, t(20) = 1.50, p = .03.", True, "t decision error (~.15)"),
    ("Participants scored M = 3.45 (SD = 0.8) on the 1-5 scale (N = 10).", True, "GRIM impossible"),
    ("Mean rating was M = 4.28 across the seven judges (N = 7).", True, "GRIM impossible"),
    # --- should NOT be flagged (correct) ---
    ("The effect was reliable, t(30) = 2.50, p = .018.", False, "t consistent"),
    ("Attitude correlated with behavior, r(38) = .42, p = .007.", False, "r consistent (df not n)"),
    ("There was an effect, F(3, 96) = 4.10, p = .009.", False, "F consistent"),
    ("The association held, chi2(2) = 9.50, p = .009.", False, "chi2 consistent"),
    ("Using a normal approximation, z = 2.33, p = .02.", False, "z consistent"),
    ("Average score was M = 3.40 on the 1-5 scale (N = 10).", False, "GRIM possible"),
]


def run() -> None:
    tp = fp = tn = fn = 0
    print(f"Running {len(CASES)} cases through the full pipeline...\n")
    print(f"  {'expected':<10}{'rigor':<10}{'ok?':<5}note")
    print("  " + "-" * 60)
    for text, should_flag, note in CASES:
        flagged = len(audit_text(text).errors) > 0
        correct = flagged == should_flag
        tp += should_flag and flagged
        fn += should_flag and not flagged
        fp += (not should_flag) and flagged
        tn += (not should_flag) and not flagged
        print(f"  {'ERROR' if should_flag else 'clean':<10}"
              f"{'flagged' if flagged else 'clean':<10}"
              f"{'yes' if correct else 'NO':<5}{note}")

    total = len(CASES)
    recall = tp / (tp + fn) if (tp + fn) else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    fpr = fp / (fp + tn) if (fp + tn) else 0
    print("\n  " + "=" * 60)
    print(f"  accuracy            : {(tp + tn) / total:.0%}  ({tp + tn}/{total})")
    print(f"  recall (errors caught): {recall:.0%}  ({tp}/{tp + fn})")
    print(f"  precision           : {precision:.0%}")
    print(f"  false-positive rate : {fpr:.0%}  ({fp}/{fp + tn})")
    print("  " + "=" * 60)


if __name__ == "__main__":
    run()
