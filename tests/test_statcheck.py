"""Unit tests for p-value recomputation against known values."""
import pytest

from rigor.checks import check_pvalue


def test_t_reported_significant_but_is_not():
    # t(48)=1.90 two-tailed -> p ~ .063, so "p < .001" is a decision error.
    r = check_pvalue("t", 1.90, 0.001, df1=48, comparator="<")
    assert r.computed_p == pytest.approx(0.0634, abs=0.002)
    assert not r.consistent
    assert r.decision_error


def test_t_consistent():
    r = check_pvalue("t", 2.50, 0.018, df1=30, comparator="=")
    assert r.computed_p == pytest.approx(0.0181, abs=0.001)
    assert r.consistent
    assert not r.decision_error


def test_f_reported_ns_but_is_significant():
    # F(2,57)=3.20 -> p ~ .048, so "p = .35" is a decision error the other way.
    r = check_pvalue("f", 3.20, 0.35, df1=2, df2=57, comparator="=")
    assert r.computed_p == pytest.approx(0.0482, abs=0.002)
    assert r.decision_error


def test_chi2_decision_error():
    r = check_pvalue("chi2", 2.1, 0.02, df1=1, comparator="=")
    assert r.computed_p == pytest.approx(0.1473, abs=0.002)
    assert r.decision_error


def test_r_consistent_uses_df_not_n():
    # r(38): the 38 is df (= n-2), so N=40. p should be ~ .007.
    r = check_pvalue("r", 0.42, 0.007, df1=38, comparator="=")
    assert r.computed_p == pytest.approx(0.0070, abs=0.001)
    assert r.consistent


def test_z_two_tailed():
    r = check_pvalue("z", 1.96, 0.05, comparator="=")
    assert r.computed_p == pytest.approx(0.05, abs=0.005)


def test_unsupported_test_raises():
    with pytest.raises(ValueError):
        check_pvalue("wilcoxon", 1.0, 0.05)
