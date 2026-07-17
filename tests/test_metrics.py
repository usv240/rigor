"""Unit tests for the per-paper metrics (this paper measured against the field baseline)."""
from rigor.baseline import FIELD_BASELINE
from rigor.report import AuditReport, Finding, Severity


def _f(kind, sev, w=0.0):
    return Finding(kind, sev, "claim", "detail", "reported", "recomputed", weight=w)


def test_metrics_rates_and_counts():
    r = AuditReport(n_tests=5, n_means=1)
    r.findings = [
        _f("pvalue", Severity.ERROR, 2.0),
        _f("pvalue", Severity.WARNING, 0.8),
        _f("pvalue", Severity.OK),
        _f("pvalue", Severity.OK),
        _f("pvalue", Severity.OK),
        _f("grim", Severity.ERROR, 1.5),
    ]
    m = r.metrics()
    assert m["results_checked"] == 5
    assert m["inconsistent"] == 2
    assert m["inconsistent_rate"] == 0.4
    assert m["decision_errors"] == 1
    assert m["impossible_values"] == 1
    assert "above" in m["verdict"]  # 40% is above the ~10% field average


def test_metrics_clean_paper_reads_below_average():
    r = AuditReport(n_tests=3)
    r.findings = [_f("pvalue", Severity.OK) for _ in range(3)]
    m = r.metrics()
    assert m["inconsistent"] == 0
    assert m["inconsistent_rate"] == 0.0
    assert "below" in m["verdict"].lower()


def test_metrics_no_tests_is_honest():
    r = AuditReport(n_tests=0)
    m = r.metrics()
    assert m["results_checked"] == 0
    assert m["inconsistent_rate"] is None
    assert "no recomputable" in m["verdict"].lower()


def test_baseline_is_cited():
    # An integrity tool must never show an unsourced number.
    assert "Nuijten" in FIELD_BASELINE["citation"]
    assert 0 < FIELD_BASELINE["pvalues_inconsistent"] < 1


def test_metrics_present_in_report_dict():
    r = AuditReport(n_tests=1)
    r.findings = [_f("pvalue", Severity.ERROR, 2.0)]
    assert "metrics" in r.to_dict()
    assert r.to_dict()["metrics"]["decision_errors"] == 1
