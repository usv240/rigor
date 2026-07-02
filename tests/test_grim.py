"""Unit tests for the GRIM check."""
from rigor.checks import grim


def test_impossible_mean():
    g = grim(3.45, 10)
    assert not g.possible
    assert 3.4 in g.nearest_possible or 3.5 in g.nearest_possible


def test_possible_means():
    assert grim(3.40, 10).possible   # 34 / 10
    assert grim(2.90, 10).possible   # 29 / 10


def test_large_n_makes_more_possible():
    # With N=100, any 2-decimal mean is achievable.
    assert grim(3.45, 100).possible


def test_multi_item_scale():
    # Averaging several items changes the granularity.
    g = grim(3.45, 10, n_items=2)
    assert g.possible  # 69 / 20 = 3.45
