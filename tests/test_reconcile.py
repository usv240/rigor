"""Unit tests for the multi-run extraction reconciliation (no API needed)."""
from rigor.extract import _canon_mean, _canon_stat, _reconcile


def _stat(test="t", statistic=1.9, df1=48, p=0.001, comp="<"):
    return {"test": test, "statistic": statistic, "df1": df1, "reported_p": p, "comparator": comp}


def test_majority_keeps_agreed_items():
    a = _stat()
    runs = [{"stats": [a]}, {"stats": [a]}, {"stats": [a]}]
    kept, sup = _reconcile(runs, _canon_stat, "stats")
    assert len(kept) == 1
    assert kept[0]["_support"] == 1.0
    assert sup == [1.0]


def test_minority_item_dropped():
    a, b = _stat(), _stat(statistic=2.5, p=0.018, comp="=")
    runs = [{"stats": [a, b]}, {"stats": [a, b]}, {"stats": [a]}]  # b in 2/3
    kept, _ = _reconcile(runs, _canon_stat, "stats")
    keys = {_canon_stat(k) for k in kept}
    assert _canon_stat(a) in keys          # unanimous -> kept, support 1.0
    assert _canon_stat(b) in keys          # 2/3 is a majority of 3 -> kept
    a_item = next(k for k in kept if _canon_stat(k) == _canon_stat(a))
    b_item = next(k for k in kept if _canon_stat(k) == _canon_stat(b))
    assert a_item["_support"] == 1.0
    assert b_item["_support"] == round(2 / 3, 3)


def test_below_majority_removed():
    a, c = _stat(), _stat(statistic=9.9, p=0.5, comp="=")
    runs = [{"stats": [a, c]}, {"stats": [a]}, {"stats": [a]}, {"stats": [a]}]  # c in 1/4
    kept, _ = _reconcile(runs, _canon_stat, "stats")
    assert {_canon_stat(k) for k in kept} == {_canon_stat(a)}


def test_intra_run_duplicate_not_double_counted():
    a = _stat()
    runs = [{"stats": [a, a]}, {"stats": []}, {"stats": []}]  # duplicated in one run only
    kept, _ = _reconcile(runs, _canon_stat, "stats")
    assert kept == []  # 1 real run of 3 is below majority


def test_mean_reconcile_uses_sd():
    m1 = {"value": 3.4, "n": 10, "sd": 0.8}
    m2 = {"value": 3.4, "n": 10, "sd": 0.9}  # different SD -> different item
    runs = [{"means": [m1]}, {"means": [m1]}, {"means": [m2]}]
    kept, _ = _reconcile(runs, _canon_mean, "means")
    assert len(kept) == 1
    assert kept[0]["sd"] == 0.8
