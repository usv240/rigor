"""Unit tests for the df-vs-N cross-check."""
from rigor.checks import check_df_vs_n


def test_t_impossible():
    d = check_df_vs_n("t", 48, 10)
    assert d is not None
    assert not d.consistent
    assert d.implied_min_n == 49


def test_r_impossible():
    d = check_df_vs_n("r", 38, 10)
    assert not d.consistent
    assert d.implied_min_n == 40


def test_t_consistent():
    d = check_df_vs_n("t", 8, 20)
    assert d is not None
    assert d.consistent


def test_not_applicable_tests_return_none():
    assert check_df_vs_n("chi2", 3, 100) is None
    assert check_df_vs_n("f", 2, 100) is None


def test_missing_df_returns_none():
    assert check_df_vs_n("t", None, 100) is None
