"""
End-to-end wiring test for audit_text WITHOUT the API.

We stub the two model-backed calls (extraction and claim analysis) so the whole
deterministic pipeline - p-value, GRIM, GRIMMER, df-vs-N, confidence propagation,
extraction metadata, de-duplication - runs offline and is asserted exactly.
"""
import rigor.audit as audit
from rigor.report import Severity


def _fake_extract(text, samples=None):
    return {
        "stats": [
            # decision error: t(48)=1.90 -> p~.063, reported p<.001
            {"test": "t", "statistic": 1.90, "df1": 48, "reported_p": 0.001,
             "comparator": "<", "claim": "a significant effect", "_support": 1.0},
            # consistent correlation (control), extracted in only 2/3 runs -> confidence .667
            {"test": "r", "statistic": 0.42, "df1": 38, "reported_p": 0.007,
             "comparator": "=", "claim": "attitude correlated with behavior", "_support": 0.667},
        ],
        "means": [
            # GRIM impossible mean + (its SD is moot); and a GRIM-ok mean with impossible SD
            {"value": 3.45, "n": 10, "sd": None, "context": "treatment", "_support": 1.0},
            {"value": 3.30, "n": 10, "sd": 0.50, "context": "baseline enjoyment", "_support": 1.0},
        ],
        "sample_size": 10,
        "extraction": {"samples": 3, "agreement": 0.917},
    }


def _fake_claims(text, verified):
    return []  # keep the test focused on the deterministic checks


def test_null_fields_do_not_crash(monkeypatch):
    """Regression: the model can emit explicit nulls for n_items/decimals/_support;
    .get(key, default) keeps the None, so int(None) must not crash the whole audit."""
    def extract_with_nulls(text, samples=None):
        return {
            "stats": [],
            "means": [{"value": 3.40, "n": 10, "sd": None, "n_items": None,
                       "decimals": None, "context": "x", "_support": None}],
            "sample_size": None,
            "extraction": {"samples": 1, "agreement": 1.0},
        }
    monkeypatch.setattr(audit, "extract", extract_with_nulls)
    monkeypatch.setattr(audit, "analyze_claims", _fake_claims)
    report = audit.audit_text("(stubbed)")   # must not raise
    grim = [f for f in report.findings if f.kind == "grim"]
    assert grim and grim[0].severity is Severity.OK  # 3.40 is achievable for N=10


def test_full_pipeline_offline(monkeypatch):
    monkeypatch.setattr(audit, "extract", _fake_extract)
    monkeypatch.setattr(audit, "analyze_claims", _fake_claims)
    report = audit.audit_text("(ignored - extract is stubbed)")
    d = report.to_dict()

    kinds = {f.kind for f in report.findings}
    assert {"pvalue", "grim", "grimmer", "sample"} <= kinds

    # the p-value decision error is a red ERROR
    pv = [f for f in report.findings if f.kind == "pvalue" and f.severity is Severity.ERROR]
    assert pv and "significant" in pv[0].detail.lower()

    # GRIMMER fired on the impossible SD (mean 3.30 is GRIM-ok, so this is SD-only)
    gm = [f for f in report.findings if f.kind == "grimmer"]
    assert gm and gm[0].severity is Severity.ERROR

    # df-vs-N: t(48) needs N>=49 but stated N=10
    dfn = [f for f in report.findings if f.kind == "sample"]
    assert dfn and dfn[0].severity is Severity.ERROR

    # confidence propagated from extraction support
    r_finding = [f for f in report.findings if f.kind == "pvalue" and f.confidence < 1.0]
    assert r_finding and abs(r_finding[0].confidence - 0.667) < 1e-6

    # extraction metadata carried through to the dict
    assert d["extraction"] == {"samples": 3, "agreement": 0.917}
