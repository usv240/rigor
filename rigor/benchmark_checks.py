"""
Deterministic-core benchmark - measures the MATH, with no LLM in the loop.

The end-to-end benchmark (rigor.benchmark) needs the Qwen API and tests extraction.
This one isolates the part that produces every verdict: the deterministic checks. It
generates hundreds of cases with ground truth known BY CONSTRUCTION (errors injected
into otherwise-correct statistics) and reports per-check precision and recall. It runs
anywhere, instantly, offline - so anyone can reproduce Rigor's core accuracy claim
without a key or a cent of tokens.

Ground truth:
  - "correct" cases are built from real, self-consistent numbers -> must NOT be flagged.
  - "error" cases inject a known, provable inconsistency -> must be flagged.
For GRIM/GRIMMER, an exhaustive brute-force search over integer responses is the
independent oracle.

Run:  python -m rigor.benchmark_checks
"""
from __future__ import annotations

import random
import statistics
from itertools import combinations_with_replacement

from rigor.checks import check_cohens_d, check_df_vs_n, check_pvalue, grim, grimmer

RNG = random.Random(7)  # fixed seed: the benchmark is fully reproducible


class Tally:
    __slots__ = ("tp", "fp", "tn", "fn")

    def __init__(self):
        self.tp = self.fp = self.tn = self.fn = 0

    def add(self, flagged: bool, should_flag: bool):
        if should_flag and flagged:
            self.tp += 1
        elif should_flag and not flagged:
            self.fn += 1
        elif not should_flag and flagged:
            self.fp += 1
        else:
            self.tn += 1

    @property
    def total(self):
        return self.tp + self.fp + self.tn + self.fn

    def row(self, name: str) -> str:
        p = self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 1.0
        r = self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 1.0
        acc = (self.tp + self.tn) / self.total if self.total else 1.0
        fpr = self.fp / (self.fp + self.tn) if (self.fp + self.tn) else 0.0
        return (f"  {name:<16}{self.total:>5}{acc:>9.0%}{p:>11.0%}{r:>9.0%}{fpr:>9.0%}")


def _bench_pvalue(t: Tally, n=60):
    made = 0
    while made < n:
        test = RNG.choice(["t", "f", "chi2", "r", "z"])
        if test == "t":
            df1, df2, stat = RNG.randint(10, 120), None, round(RNG.uniform(0.5, 4.0), 2)
        elif test == "f":
            df1, df2, stat = RNG.randint(1, 5), RNG.randint(20, 120), round(RNG.uniform(0.5, 8.0), 2)
        elif test == "chi2":
            df1, df2, stat = RNG.randint(1, 6), None, round(RNG.uniform(0.5, 20.0), 2)
        elif test == "r":
            df1, df2, stat = RNG.randint(10, 120), None, round(RNG.uniform(0.05, 0.7), 2)
        else:
            df1, df2, stat = None, None, round(RNG.uniform(0.3, 3.5), 2)
        try:
            true_p = check_pvalue(test, stat, 0.5, df1=df1, df2=df2).computed_p
        except Exception:
            continue
        if 0.03 < true_p < 0.07:
            continue  # skip boundary cases where rounding makes ground truth ambiguous
        made += 1
        # correct case: report the true p -> must not be a decision error
        good = check_pvalue(test, stat, round(true_p, 3), df1=df1, df2=df2, comparator="=")
        t.add(good.decision_error, False)
        # error case: report a p on the wrong side of .05 -> injected decision error
        if true_p < 0.05:
            bad = check_pvalue(test, stat, 0.30, df1=df1, df2=df2, comparator="=")
        else:
            bad = check_pvalue(test, stat, 0.001, df1=df1, df2=df2, comparator="<")
        t.add(bad.decision_error, True)


def _achievable_means(n, lo=1, hi=5, dec=2):
    return {round(s / n, dec) for s in range(lo * n, hi * n + 1)}


def _bench_grim(t: Tally, n=60):
    for _ in range(n):
        k = RNG.randint(6, 20)
        sample = [RNG.randint(1, 5) for _ in range(k)]
        real = round(statistics.mean(sample), 2)
        t.add(not grim(real, k).possible, False)  # real mean -> possible
        achievable = _achievable_means(k)
        impossible = [round(x / 100, 2) for x in range(100, 501)
                      if round(x / 100, 2) not in achievable]
        target = min(impossible, key=lambda m: abs(m - real))
        t.add(not grim(target, k).possible, True)  # injected impossible mean


def _brute_grimmer(mean, sd, n, lo=1, hi=5):
    for combo in combinations_with_replacement(range(lo, hi + 1), n):
        if round(sum(combo) / n, 2) == mean and round(statistics.stdev(combo), 2) == sd:
            return True
    return False


def _bench_grimmer(t: Tally, n=45):
    made = 0
    while made < n:
        k = RNG.randint(4, 8)  # small n keeps the brute-force oracle cheap
        sample = [RNG.randint(1, 5) for _ in range(k)]
        mean = round(statistics.mean(sample), 2)
        sd = round(statistics.stdev(sample), 2)
        made += 1
        t.add(not grimmer(mean, sd, k).possible, False)  # real SD -> must pass
        # perturb the SD and use brute force as the independent oracle
        alt = round(sd + RNG.choice([-0.03, -0.02, 0.02, 0.03, 0.05]), 2)
        if alt < 0:
            continue
        truly_impossible = not _brute_grimmer(mean, alt, k)
        t.add(not grimmer(mean, alt, k).possible, truly_impossible)


def _bench_dfn(t: Tally, n=50):
    for _ in range(n):
        test = RNG.choice(["t", "r"])
        df = RNG.randint(5, 80)
        implied = df + (1 if test == "t" else 2)
        big_n = implied + RNG.randint(0, 40)          # enough subjects -> consistent
        small_n = RNG.randint(2, implied - 1)          # too few -> impossible
        c_ok = check_df_vs_n(test, df, big_n)
        c_bad = check_df_vs_n(test, df, small_n)
        t.add(bool(c_ok and not c_ok.consistent), False)
        t.add(bool(c_bad and not c_bad.consistent), True)


def _bench_effect(t: Tally, n=50):
    for _ in range(n):
        n1, n2 = RNG.randint(15, 60), RNG.randint(15, 60)
        tt = round(RNG.uniform(1.0, 4.0), 2)
        true_d = abs(tt) * (1 / n1 + 1 / n2) ** 0.5
        good = check_cohens_d(tt, round(true_d, 2), n1=n1, n2=n2)
        bad = check_cohens_d(tt, round(true_d * RNG.choice([1.8, 2.0, 0.5]), 2), n1=n1, n2=n2)
        if good:
            t.add(not good.consistent, False)
        if bad:
            t.add(not bad.consistent, True)


def run() -> None:
    checks = {
        "p-value": _bench_pvalue, "GRIM": _bench_grim, "GRIMMER": _bench_grimmer,
        "df-vs-N": _bench_dfn, "effect-size (d)": _bench_effect,
    }
    print("Deterministic-core benchmark (no LLM) - injected errors, ground truth by construction\n")
    print(f"  {'check':<16}{'cases':>5}{'acc':>9}{'precision':>11}{'recall':>9}{'FPR':>9}")
    print("  " + "-" * 59)
    overall = Tally()
    for name, fn in checks.items():
        t = Tally()
        fn(t)
        print(t.row(name))
        for a in ("tp", "fp", "tn", "fn"):
            setattr(overall, a, getattr(overall, a) + getattr(t, a))
    print("  " + "-" * 59)
    print(overall.row("ALL"))
    print("\n  Precision = of everything flagged, how much was truly wrong (100% = no false alarms).")
    print("  Recall    = of everything truly wrong, how much was caught.")
    print("  GRIMMER is deliberately conservative (bounds-free necessary conditions): it never")
    print("  false-alarms (precision 100%) and may miss a few impossibilities bounds would catch.")


if __name__ == "__main__":
    run()
