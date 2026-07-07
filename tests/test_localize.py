"""Unit tests for error localization (minimum-repair over the constraint set)."""
from rigor.localize import localize


def test_shared_n_cluster_ranks_first():
    # Two tests whose df are both impossible for N=10 -> one N typo explains both.
    stats = [
        {"test": "t", "df1": 48, "statistic": 1.9, "reported_p": 0.001, "comparator": "<"},
        {"test": "r", "df1": 38, "statistic": 0.42, "reported_p": 0.007, "comparator": "="},
    ]
    hyps = localize(stats, [], stated_n=10)
    assert hyps
    top = hyps[0]
    assert top.kind == "shared-n"
    assert top.explains == 2
    assert "49" in top.repair  # needs N >= max(49, 40) = 49


def test_single_dfn_offers_both_repairs():
    stats = [{"test": "t", "df1": 48, "statistic": 1.9, "reported_p": 0.001, "comparator": "<"}]
    hyps = localize(stats, [], stated_n=10)
    assert len(hyps) == 1
    assert hyps[0].explains == 1
    assert "N >= 49" in hyps[0].repair
    assert "df <=" in hyps[0].repair  # the alternative repair is offered


def test_no_hypothesis_when_consistent():
    stats = [{"test": "t", "df1": 8, "statistic": 2.0, "reported_p": 0.05, "comparator": "="}]
    assert localize(stats, [], stated_n=30) == []


def test_no_stated_n_means_no_hypothesis():
    stats = [{"test": "t", "df1": 48, "statistic": 1.9, "reported_p": 0.001, "comparator": "<"}]
    assert localize(stats, [], stated_n=None) == []


def test_repairs_are_verified_not_guessed():
    # The shared-n repair value must actually resolve the checks (proved inside localize).
    from rigor.checks import check_df_vs_n
    stats = [
        {"test": "t", "df1": 60, "statistic": 2.0, "reported_p": 0.05, "comparator": "="},
        {"test": "r", "df1": 40, "statistic": 0.3, "reported_p": 0.05, "comparator": "="},
    ]
    hyps = localize(stats, [], stated_n=12)
    assert hyps[0].explains == 2
    # extract the needed N and confirm it truly resolves both
    needed = int(hyps[0].repair.split(">=")[1].strip())
    assert check_df_vs_n("t", 60, needed).consistent
    assert check_df_vs_n("r", 40, needed).consistent
