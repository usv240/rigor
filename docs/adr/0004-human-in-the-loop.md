# ADR 0004: Keep a human in the loop

Status: Accepted

## The problem

On messy, real-world papers, extraction can occasionally produce a wrong flag. A
tool that shows a false positive and gives you no way to correct it is not something
a researcher can trust for real work.

## The decision

Show every finding, and let the reviewer dismiss any false positive. The integrity
score recomputes live as findings are dismissed, and the exported report contains
only what the human chose to keep.

## Why it is good, and the trade-off

The human stays in control. The final report reflects their judgment, not a black
box. This matches how real review already works: a tool surfaces candidates, a
person decides. It also makes the occasional extraction miss harmless.

Trade-off: the score is not a single automated verdict, it depends on the reviewer.
That is the honest and correct behavior for this kind of tool.
