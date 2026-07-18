"""Unit tests for the batch aggregate scale-impact (pure function, no API)."""
from rigor.batch import impact_summary


def test_impact_aggregates_only_ok_rows():
    rows = [
        {"status": "ok", "values": 6, "errors": 8, "seconds": 15.0},
        {"status": "ok", "values": 4, "errors": 0, "seconds": 9.0},
        {"status": "error: Timeout", "values": None, "errors": None, "seconds": 5.0},
    ]
    imp = impact_summary(rows)
    assert imp["papers_screened"] == 2          # failed row excluded
    assert imp["papers_flagged"] == 1           # only the 8-error paper
    assert imp["statistics_checked"] == 10      # 6 + 4
    assert imp["manual_minutes"] == 30          # 10 * 3
    assert imp["rigor_seconds"] == 29.0         # runtime counts every attempt


def test_impact_handles_empty():
    imp = impact_summary([])
    assert imp["statistics_checked"] == 0
    assert imp["manual_hours"] == 0.0
