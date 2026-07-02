"""
Rigor end-to-end: read a paper -> extract stats (LLM) -> verify (deterministic)
-> integrity report.

Run:
    python -m rigor.audit                 # built-in demo paper
    python -m rigor.audit paper.txt       # your own paper (text)
    python -m rigor.audit paper.pdf       # your own paper (PDF)

The LLM reads the prose; the MATH renders every verdict. Watch it catch planted
errors while leaving correct results alone.
"""
from __future__ import annotations

import sys

from rigor.checks import check_df_vs_n, check_pvalue, grim
from rigor.claims import analyze_claims
from rigor.extract import extract
from rigor.ingest import load_text
from rigor.report import AuditReport, Finding, Severity

# Built-in demo paper: THREE planted errors + ONE correct result (control).
SAMPLE_PAPER = """
In Study 1 (N = 10), participants rated the target on a 1-5 scale. Those in the
treatment condition rated it higher (M = 3.45, SD = 0.82) than controls
(M = 2.90, SD = 0.75). A paired-samples t-test confirmed a significant effect,
t(48) = 1.90, p < .001.

A one-way ANOVA testing the three groups revealed no significant differences,
F(2, 57) = 3.20, p = .35.

Finally, attitude correlated with behavior, r(38) = .42, p = .007.

In sum, this brief intervention significantly and reliably improves evaluations,
demonstrating that the manipulation causes more favorable judgments across the
general population.
""".strip()


def audit_text(text: str) -> AuditReport:
    data = extract(text)
    stats, means = data["stats"], data["means"]
    report = AuditReport(n_tests=len(stats), n_means=len(means))
    try:
        stated_n = int(data["sample_size"]) if data.get("sample_size") is not None else None
    except (TypeError, ValueError):
        stated_n = None

    for s in stats:
        try:
            r = check_pvalue(
                s["test"],
                float(s["statistic"]),
                float(s["reported_p"]),
                df1=s.get("df1"),
                df2=s.get("df2"),
                n=s.get("n"),
                comparator=s.get("comparator", "="),
            )
        except Exception:  # noqa: BLE001 - malformed extraction; count and move on
            report.skipped += 1
            continue
        sev = (
            Severity.OK if r.consistent
            else Severity.ERROR if r.decision_error
            else Severity.WARNING
        )
        report.findings.append(
            Finding(
                kind="pvalue",
                severity=sev,
                claim=(s.get("claim") or "").strip(),
                detail=r.message,
                reported=f"p {r.comparator} {r.reported_p:g}",
                recomputed=f"p = {r.computed_p:.4g}",
            )
        )

    for m in means:
        try:
            g = grim(float(m["value"]), int(m["n"]), int(m.get("n_items", 1)), int(m.get("decimals", 2)))
        except Exception:  # noqa: BLE001
            report.skipped += 1
            continue
        report.findings.append(
            Finding(
                kind="grim",
                severity=Severity.OK if g.possible else Severity.ERROR,
                claim=(m.get("context") or "").strip(),
                detail=g.message,
                reported=f"M = {m['value']:g}, N = {m['n']}",
                recomputed="achievable" if g.possible else f"nearest {g.nearest_possible}",
            )
        )

    # df-vs-N cross-consistency: does a test's df fit the stated sample size?
    if stated_n is not None:
        for s in stats:
            dfn = check_df_vs_n(str(s.get("test", "")), s.get("df1"), stated_n)
            if dfn is not None and not dfn.consistent:
                report.findings.append(
                    Finding(
                        kind="sample",
                        severity=Severity.ERROR,
                        claim=(s.get("claim") or "").strip(),
                        detail=dfn.message,
                        reported=f"df = {s.get('df1')}, stated N = {stated_n}",
                        recomputed=f"needs N >= {dfn.implied_min_n}",
                    )
                )

    # Claim vs. evidence ("spin") - grounded in the results the math just verified.
    verified = [
        f"{f.claim or '(stat)'}: reported {f.reported}, recomputed {f.recomputed} -> {f.severity.value}"
        for f in report.findings if f.kind == "pvalue"
    ]
    for c in analyze_claims(text, verified):
        grounded = bool(c.get("grounded"))
        issue = str(c.get("issue", "OVERCLAIM"))
        report.findings.append(
            Finding(
                kind="claim",
                severity=Severity.ERROR if grounded else Severity.WARNING,
                claim=(c.get("claim") or "").strip(),
                detail=(c.get("explanation") or "").strip(),
                reported=f"claim: {issue.lower()}",
                recomputed="contradicts a verified result" if grounded else "AI-flagged - needs review",
            )
        )

    return report


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    except Exception:
        pass
    if argv:
        text, source = load_text(argv[0]), argv[0]
    else:
        text, source = SAMPLE_PAPER, "built-in demo paper (3 planted errors, 1 correct)"
    print(f"Reading: {source}")
    report = audit_text(text)
    print(report.pretty(source=source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
