"""
Unit tests for the GRIMMER SD-granularity check.

The critical property is SOUNDNESS: whenever the analytic check says a
(mean, SD, N) triple is IMPOSSIBLE, an exhaustive brute-force search over integer
responses must also find no witness. A false "impossible" would be a false positive
- exactly what Rigor promises never to do - so we hammer that direction hard.
"""
import statistics
from itertools import combinations_with_replacement

import pytest

from rigor.checks import grimmer


def _brute(mean, sd, n, lo=1, hi=7, decimals=2, sd_decimals=2):
    """True iff SOME multiset of n integers in [lo, hi] has the reported mean and SD."""
    tm, ts = round(mean, decimals), round(sd, sd_decimals)
    for combo in combinations_with_replacement(range(lo, hi + 1), n):
        if round(sum(combo) / n, decimals) != tm:
            continue
        if round(statistics.stdev(combo), sd_decimals) == ts:
            return True
    return False


def test_known_possible():
    # {2,3,4}: mean 3.00, sample SD 1.00 -> must be possible.
    assert grimmer(3.00, 1.00, 3).possible


def test_parity_catches_what_integrality_misses():
    # mean 3.00, N=3, SD 0.71 -> Q=28 is a whole number but wrong parity (S=9 is odd).
    r = grimmer(3.00, 0.71, 3)
    assert not r.possible
    assert r.reason == "sd"
    assert not _brute(3.00, 0.71, 3)  # confirm truly impossible


def test_non_integer_sum_of_squares():
    # mean 3.00, N=3, SD 0.50 -> implied Q ~ 27.5, no integer in range.
    r = grimmer(3.00, 0.50, 3)
    assert not r.possible
    assert not _brute(3.00, 0.50, 3)


def test_grim_impossible_mean_reported():
    # 3.45 can't be a mean of 3 integers at 2dp -> flagged at the mean stage.
    r = grimmer(3.45, 0.50, 3)
    assert not r.possible
    assert r.reason == "mean"


def test_multi_item_declined():
    # composite scores are ambiguous; GRIMMER declines (possible=True, not applicable).
    assert grimmer(3.45, 0.5, 10, n_items=2).possible


def test_soundness_over_a_grid():
    """Every analytic IMPOSSIBLE must be confirmed impossible by brute force."""
    checked = 0
    for n in range(3, 8):
        for s in range(1 * n, 7 * n + 1):          # every reachable integer sum
            mean = s / n
            for sd_x100 in range(0, 300, 7):        # a spread of SDs, 2 decimals
                sd = sd_x100 / 100
                r = grimmer(round(mean, 2), sd, n)
                if not r.possible and r.reason == "sd":
                    checked += 1
                    assert not _brute(round(mean, 2), sd, n), (
                        f"false positive: mean={round(mean,2)} sd={sd} n={n}")
    assert checked > 50  # the grid actually exercised the impossible branch


@pytest.mark.parametrize("n", [3, 4, 5, 6])
def test_real_data_never_flagged(n):
    """A real integer sample's own mean+SD must always survive the check."""
    sample = [((i * 3 + 1) % 7) + 1 for i in range(n)]  # arbitrary integers in 1..7
    m = round(statistics.mean(sample), 2)
    sd = round(statistics.stdev(sample), 2)
    assert grimmer(m, sd, n).possible
