"""Unit tests for the Cohen's d effect-size consistency check."""
from rigor.checks import check_cohens_d


def test_independent_consistent():
    # n1=n2=25 -> d = t*sqrt(1/25+1/25) = 2.5*0.2828 = 0.707; reported .71 matches.
    r = check_cohens_d(2.5, 0.71, n1=25, n2=25)
    assert r is not None
    assert r.consistent


def test_independent_inconsistent():
    # same t and groups, but d reported ~2x too large.
    r = check_cohens_d(2.5, 1.40, n1=25, n2=25)
    assert r is not None
    assert not r.consistent


def test_paired_consistent():
    # paired, N=30 -> d = t/sqrt(30) = 2.5/5.477 = 0.456; reported .46 matches.
    r = check_cohens_d(2.5, 0.46, n=30, design="paired")
    assert r is not None
    assert r.consistent


def test_declines_without_group_sizes():
    assert check_cohens_d(2.5, 0.7) is None
    assert check_cohens_d(2.5, 0.7, n1=25) is None
    assert check_cohens_d(2.5, 0.7, n=None, design="paired") is None


def test_sign_insensitive():
    # a negative t or d (direction) should not by itself cause an inconsistency.
    r = check_cohens_d(-2.5, 0.71, n1=25, n2=25)
    assert r is not None and r.consistent
