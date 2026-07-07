# ADR 0008: Localize the error, don't just detect it

Status: Accepted

## The problem

statcheck, GRIM, and Rigor's own checks all answer one question: *are these numbers
inconsistent?* When several checks fail on the same paper, the author is still left
guessing *which* reported number is the actual mistake. That is the expensive part of
fixing a manuscript, and no tool in this space helps with it.

## The decision

Add a step after detection that answers *which number to fix first*. A paper's
statistics are an over-determined constraint system — the sample size N, a test's
degrees of freedom, its statistic and p-value, and a group's mean and SD all
constrain each other. So Rigor runs a **minimum-repair search**: it looks for the
single reported value whose correction resolves the largest number of findings.

The flagship case: a whole cluster of degrees-of-freedom clashes is more
parsimoniously explained by *one* wrong sample size than by many wrong df values.
Rigor reports that hypothesis — "N=10 is the likely typo; every flagged test's df is
consistent once N ≥ 49."

## Why it is good, and the trade-off

It is a genuinely new capability in this domain, and it fits the project's core
discipline: every proposed repair is **verified by re-running the deterministic
checks** with the substituted value, so it is provable, not guessed. It is deliberately
framed as a parsimony-ranked *hypothesis* for the human reviewer ([0004](0004-human-in-the-loop.md)),
never a certainty — because Rigor cannot know whether the N or the df values are the
true error, only which explanation is simplest.

Trade-off: the search is deliberately conservative. It only proposes repairs it can
prove resolve real findings (today, the shared-N cluster), rather than speculating
about every possible edit. Correctness and credibility over coverage — the same
principle as the checks themselves.
