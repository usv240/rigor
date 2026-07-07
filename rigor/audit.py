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

from rigor.checks import check_df_vs_n, check_pvalue, grim, grimmer
from rigor.claims import analyze_claims
from rigor.explain import explain_claim, explain_dfn, explain_grim, explain_grimmer, explain_pvalue
from rigor.extract import extract
from rigor.ingest import load_text
from rigor.localize import localize
from rigor.report import AuditReport, Finding, Severity

# Built-in demo paper: planted errors (bad p-value, impossible mean, impossible SD,
# df-vs-N clash, overclaim) alongside a correct control result the math leaves alone.
SAMPLE_PAPER = """
In Study 1 (N = 10), participants rated the target on a 1-5 scale. Those in the
treatment condition rated it higher (M = 3.45, SD = 0.82) than controls
(M = 2.90, SD = 0.75). A paired-samples t-test confirmed a significant effect,
t(48) = 1.90, p < .001.

A one-way ANOVA testing the three groups revealed no significant differences,
F(2, 57) = 3.20, p = .35.

Separately, baseline enjoyment ratings averaged M = 3.30 (SD = 0.50) on the same
1-5 scale (N = 10).

Finally, attitude correlated with behavior, r(38) = .42, p = .007.

In sum, this brief intervention significantly and reliably improves evaluations,
demonstrating that the manipulation causes more favorable judgments across the
general population.
""".strip()


def _pval_method(s: dict) -> str:
    """A short, human-readable description of exactly how the p-value was recomputed."""
    t = str(s.get("test", "")).lower()
    stat, df1, df2 = s.get("statistic"), s.get("df1"), s.get("df2")
    if t == "t":
        return f"two-tailed t: p = 2 x P(T > |{stat}|), df = {df1}"
    if t == "f":
        return f"F: p = P(F > {stat}), df = ({df1}, {df2})"
    if t in ("chi2", "chisq", "x2"):
        return f"chi-square: p = P(X^2 > {stat}), df = {df1}"
    if t == "r":
        return f"r to t: t = r x sqrt(df / (1 - r^2)), df = {df1}, then two-tailed t"
    if t == "z":
        return "two-tailed z: p = 2 x P(Z > |z|)"
    return ""


def audit_text(text: str) -> AuditReport:
    data = extract(text)
    stats, means = data["stats"], data["means"]
    report = AuditReport(n_tests=len(stats), n_means=len(means))
    report.extraction = data.get("extraction", {"samples": 1, "agreement": 1.0})
    try:
        stated_n = int(data["sample_size"]) if data.get("sample_size") is not None else None
    except (TypeError, ValueError):
        stated_n = None

    for s in stats:
        try:
            rp = float(s["reported_p"])
        except (TypeError, ValueError, KeyError):
            report.skipped += 1
            continue
        if not (0 < rp <= 1):  # a p-value must be in (0, 1]; skip garbage extractions
            report.skipped += 1
            continue
        try:
            r = check_pvalue(
                s["test"],
                float(s["statistic"]),
                rp,
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
        plain, fix = explain_pvalue(r)
        report.findings.append(
            Finding(
                kind="pvalue",
                severity=sev,
                claim=(s.get("claim") or "").strip(),
                detail=r.message,
                reported=f"p {r.comparator} {r.reported_p:g}",
                recomputed=f"p = {r.computed_p:.4g}",
                plain=plain,
                fix=fix,
                weight=2.0 if r.decision_error else 0.0 if r.consistent else 0.8,
                method=_pval_method(s),
                confidence=float(s.get("_support", 1.0)),
            )
        )

    for m in means:
        conf = float(m.get("_support") or 1.0)
        # The model can emit an explicit null for these; .get(key, default) keeps the None,
        # so coerce it here rather than let int(None) crash the whole audit.
        ni, dec = m.get("n_items"), m.get("decimals")
        n_items = 1 if ni is None else int(ni)
        decimals = 2 if dec is None else int(dec)
        try:
            g = grim(float(m["value"]), int(m["n"]), n_items, decimals)
        except Exception:  # noqa: BLE001
            report.skipped += 1
            continue
        plain, fix = explain_grim(g)
        report.findings.append(
            Finding(
                kind="grim",
                severity=Severity.OK if g.possible else Severity.ERROR,
                claim=(m.get("context") or "").strip(),
                detail=g.message,
                reported=f"M = {m['value']:g}, N = {m['n']}",
                recomputed="achievable" if g.possible else f"nearest {g.nearest_possible}",
                plain=plain,
                fix=fix,
                weight=0.0 if g.possible else 1.5,
                method=f"a mean of {m['n']} whole-number responses must be an integer sum / {m['n']}",
                confidence=conf,
            )
        )

        # GRIMMER: if an SD is reported for this mean, check the SD's granularity too.
        sd = m.get("sd")
        if sd is not None and n_items == 1:
            try:
                gm = grimmer(float(m["value"]), float(sd), int(m["n"]), n_items, decimals)
            except Exception:  # noqa: BLE001
                gm = None
            # Only surface SD-level results (the mean itself is already covered by GRIM above).
            if gm is not None and gm.reason != "mean" and "NOT APPLICABLE" not in gm.message:
                plain, fix = explain_grimmer(gm)
                report.findings.append(
                    Finding(
                        kind="grimmer",
                        severity=Severity.OK if gm.possible else Severity.ERROR,
                        claim=(m.get("context") or "").strip(),
                        detail=gm.message,
                        reported=f"M = {m['value']:g}, SD = {float(sd):g}, N = {m['n']}",
                        recomputed="achievable" if gm.possible else "impossible SD",
                        plain=plain,
                        fix=fix,
                        weight=0.0 if gm.possible else 1.5,
                        method=f"sum of squares SD^2*(N-1)+S^2/N must be a whole number with the "
                               f"same parity as the sum S (GRIMMER)",
                        confidence=conf,
                    )
                )

    # df-vs-N cross-consistency: does a test's df fit the stated sample size?
    if stated_n is not None:
        for s in stats:
            dfn = check_df_vs_n(str(s.get("test", "")), s.get("df1"), stated_n)
            if dfn is not None and not dfn.consistent:
                plain, fix = explain_dfn(dfn)
                report.findings.append(
                    Finding(
                        kind="sample",
                        severity=Severity.ERROR,
                        claim=(s.get("claim") or "").strip(),
                        detail=dfn.message,
                        reported=f"df = {s.get('df1')}, stated N = {stated_n}",
                        recomputed=f"needs N >= {dfn.implied_min_n}",
                        plain=plain,
                        fix=fix,
                        weight=1.5,
                        method=f"{s.get('test')}(df={s.get('df1')}) requires N >= {dfn.implied_min_n} (df = N - 1 or N - 2)",
                        confidence=float(s.get("_support", 1.0)),
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
        explanation = (c.get("explanation") or "").strip()
        plain, fix = explain_claim(issue, explanation)
        report.findings.append(
            Finding(
                kind="claim",
                severity=Severity.ERROR if grounded else Severity.WARNING,
                claim=(c.get("claim") or "").strip(),
                detail=explanation,
                reported=f"claim: {issue.lower()}",
                recomputed="contradicts a verified result" if grounded else "AI-flagged - needs review",
                plain=plain,
                fix=fix,
                weight=1.5 if grounded else 0.4,
            )
        )

    # De-duplicate identical findings (e.g. one sentence reporting several identical stats).
    seen, unique = set(), []
    for f in report.findings:
        key = (f.kind, f.claim, f.reported, f.recomputed, f.detail)
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)
    report.findings = unique

    # Error localization: which single reported number, if corrected, resolves the most
    # findings? A novel step beyond detection - see rigor/localize.py.
    report.hypotheses = localize(stats, means, stated_n)

    return report


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    except Exception:
        pass
    if argv:
        text, source = load_text(argv[0]), argv[0]
    else:
        text, source = SAMPLE_PAPER, "built-in demo paper (planted errors + 1 correct control)"
    print(f"Reading: {source}")
    report = audit_text(text)
    print(report.pretty(source=source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
