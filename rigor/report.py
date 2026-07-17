"""
Integrity report - turns raw check results into a shareable referee report.

An overall integrity score, findings grouped by severity, and both a pretty text
view (for the demo/CLI) and a dict (for the web API / JSON output).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from rigor.baseline import FIELD_BASELINE, MANUAL_MIN_PER_CHECK


class Severity(str, Enum):
    ERROR = "ERROR"      # decision-flipping inconsistency or impossible value
    WARNING = "WARNING"  # inconsistent, but the significance decision is unchanged
    OK = "OK"


@dataclass
class Finding:
    kind: str            # "pvalue" | "grim" | "grimmer" | "sample" | "claim"
    severity: Severity
    claim: str
    detail: str
    reported: str
    recomputed: str
    plain: str = ""      # what it means, in plain language
    fix: str = ""        # what to do about it
    weight: float = 0.0  # severity weight used in scoring (e.g. decision error = 2.0)
    method: str = ""     # the exact computation used (transparency)
    confidence: float = 1.0  # how reliably the underlying numbers were extracted (0-1)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["severity"] = self.severity.value
        return d


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)
    n_tests: int = 0
    n_means: int = 0
    skipped: int = 0
    extraction: dict = field(default_factory=lambda: {"samples": 1, "agreement": 1.0})
    hypotheses: list = field(default_factory=list)  # root-cause hypotheses (see rigor/localize.py)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.WARNING]

    def score(self) -> int:
        """0-100 integrity score: points off per issue, weighted by severity. A
        decision-flipping error (2.0) hurts more than a harmless typo (0.8), which
        hurts more than a soft AI flag (0.4). A clean paper stays at 100."""
        penalty = sum(f.weight for f in self.findings)
        return max(0, round(100 - penalty * 5))

    def metrics(self) -> dict:
        """This paper's numbers measured against the published field baseline, so the
        result has a reference point. Everything here is COMPUTED from this audit or
        CITED from Nuijten 2016 - never asserted."""
        pvals = [f for f in self.findings if f.kind == "pvalue"]
        checked = self.n_tests
        inconsistent = [f for f in pvals if f.severity is not Severity.OK]
        decision = [f for f in pvals if f.severity is Severity.ERROR]
        impossible = [
            f for f in self.findings
            if f.kind in ("grim", "grimmer") and f.severity is Severity.ERROR
        ]
        rate = (len(inconsistent) / checked) if checked else None
        base = FIELD_BASELINE["pvalues_inconsistent"]

        if rate is None:
            verdict = "No recomputable p-values were found to compare against the field."
        elif not inconsistent:
            verdict = (f"Clean: 0 of {checked} p-values inconsistent, below the field "
                       f"average of about 1 in 10 (Nuijten 2016).")
        else:
            cmp = "above" if rate > base else "in line with"
            verdict = (f"{len(inconsistent)} of {checked} p-values inconsistent ({rate:.0%}), "
                       f"{cmp} the field average of about 1 in 10 (Nuijten 2016).")

        # Time a manual recheck would take: every recomputable stat and every mean is a
        # value a human would have to find and recompute by hand.
        checks_run = self.n_tests + self.n_means
        manual_minutes = checks_run * MANUAL_MIN_PER_CHECK

        return {
            "results_checked": checked,
            "inconsistent": len(inconsistent),
            "inconsistent_rate": round(rate, 3) if rate is not None else None,
            "decision_errors": len(decision),
            "impossible_values": len(impossible),
            "checks_run": checks_run,
            "manual_minutes": manual_minutes,
            "min_per_check": MANUAL_MIN_PER_CHECK,
            "baseline": FIELD_BASELINE,
            "verdict": verdict,
        }

    def to_dict(self) -> dict:
        return {
            "score": self.score(),
            "n_tests": self.n_tests,
            "n_means": self.n_means,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "skipped": self.skipped,
            "extraction": self.extraction,
            "metrics": self.metrics(),
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "findings": [f.to_dict() for f in self.findings],
        }

    def pretty(self, source: str = "") -> str:
        score = self.score()
        bar = "#" * (score // 5) + "." * (20 - score // 5)
        lines = [
            "",
            "=" * 68,
            f"  RIGOR - research integrity report",
            f"  source: {source}" if source else "",
            "=" * 68,
            f"  integrity score : {score}/100  [{bar}]",
            f"  checked         : {self.n_tests} test(s), {self.n_means} mean(s)"
            + (f"  ({self.skipped} skipped)" if self.skipped else ""),
            f"  findings        : {len(self.errors)} error(s), {len(self.warnings)} warning(s)",
        ]
        if self.extraction.get("samples", 1) > 1:
            lines.append(
                f"  extraction      : {self.extraction['samples']} runs reconciled, "
                f"{self.extraction['agreement']:.0%} agreement")
        m = self.metrics()
        if m["results_checked"]:
            lines.append(f"  vs field        : {m['verdict']}")
        if m["checks_run"]:
            lines.append(
                f"  time            : a hand recheck of {m['checks_run']} value(s) would take "
                f"about {m['manual_minutes']} min")
        lines.append("=" * 68)

        def block(title: str, items: list[Finding]) -> None:
            if not items:
                return
            lines.append(f"\n  {title}")
            for f in items:
                lines.append(f"    [{f.severity.value}] {f.claim}".rstrip())
                lines.append(f"           reported {f.reported}  |  recomputed {f.recomputed}")
                lines.append(f"           {f.detail}")

        block("ERRORS (likely wrong)", self.errors)
        block("WARNINGS (inconsistent)", self.warnings)

        if self.hypotheses:
            lines.append("\n  LIKELY ROOT CAUSES (which number to fix first)")
            for h in self.hypotheses:
                lines.append(f"    * explains {h.explains} finding(s): {h.summary}")
                lines.append(f"           fix: {h.repair}")

        ok = [f for f in self.findings if f.severity is Severity.OK]
        lines.append(f"\n  {len(ok)} result(s) checked out clean.")
        lines.append("")
        return "\n".join(line for line in lines if line is not None)
