"""
Proof that Rigor is NOT an AI wrapper.

Run:  python -m rigor.demo_checks

No API key. No LLM. Just math catching fabricated / mistyped statistics - the
same verdicts Rigor's engine produces after the LLM extracts the numbers.
"""
from __future__ import annotations

from rigor.checks import check_pvalue, grim


def line(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def main() -> None:
    line("p-value recomputation (statcheck-style)")

    # A real-looking but WRONG result: claims p < .001, but t(48)=1.9 gives p ~ .06
    r = check_pvalue("t", 1.9, 0.001, df1=48, comparator="<")
    print(f"  t(48) = 1.9, reported p < .001")
    print(f"    -> {r.message}")

    # A CONSISTENT result: t(30)=2.5 -> p ~ .018, matches reported .018
    r = check_pvalue("t", 2.5, 0.018, df1=30, comparator="=")
    print(f"  t(30) = 2.5, reported p = .018")
    print(f"    -> {r.message}")

    # A chi-square that doesn't support its 'significant' claim
    r = check_pvalue("chi2", 2.1, 0.02, df1=1, comparator="=")
    print(f"  chi2(1) = 2.1, reported p = .02")
    print(f"    -> {r.message}")

    line("GRIM test (impossible means)")

    # 3.45 cannot be the mean of 10 integer responses
    g = grim(3.45, n=10, decimals=2)
    print(f"  mean = 3.45, N = 10")
    print(f"    -> {g.message}")

    # 3.40 can (34/10)
    g = grim(3.40, n=10, decimals=2)
    print(f"  mean = 3.40, N = 10")
    print(f"    -> {g.message}")

    print("\nEvery verdict above came from arithmetic, not a language model.")


if __name__ == "__main__":
    main()
