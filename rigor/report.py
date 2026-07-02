"""
Integrity report - turns raw check results into a shareable referee report.

An overall integrity score, findings grouped by severity, and both a pretty text
view (for the demo/CLI) and a dict (for the web API / JSON output).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    ERROR = "ERROR"      # decision-flipping inconsistency or impossible value
    WARNING = "WARNING"  # inconsistent, but the significance decision is unchanged
    OK = "OK"


@dataclass
class Finding:
    kind: str            # "pvalue" | "grim" | "sample" | "claim"
    severity: Severity
    claim: str
    detail: str
    reported: str
    recomputed: str
    plain: str = ""      # what it means, in plain language
    fix: str = ""        # what to do about it
    weight: float = 0.0  # severity weight used in scoring (e.g. decision error = 2.0)

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

    def to_dict(self) -> dict:
        return {
            "score": self.score(),
            "n_tests": self.n_tests,
            "n_means": self.n_means,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "skipped": self.skipped,
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
            "=" * 68,
        ]

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
        ok = [f for f in self.findings if f.severity is Severity.OK]
        lines.append(f"\n  {len(ok)} result(s) checked out clean.")
        lines.append("")
        return "\n".join(line for line in lines if line is not None)
