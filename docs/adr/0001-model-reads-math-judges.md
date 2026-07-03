# ADR 0001: The model reads, the math judges

Status: Accepted

## The problem

Most AI tools ask you to trust whatever the model says. For checking research
statistics, that is not good enough. If the model makes up an answer, you get a
wrong verdict and no way to know it was wrong.

## The decision

Split the work in two.

- The language model (Qwen) only **reads** the paper and pulls out the numbers,
  like `t(48) = 1.90, p < .001`.
- Every **verdict** comes from exact, deterministic math (SciPy distributions and
  plain arithmetic). The model never decides whether a number is right or wrong.

## Why it is good, and the trade-off

If the model misreads a number, the worst case is one flag you can dismiss. It can
never invent a wrong verdict, because it never gives a verdict. This is what makes
Rigor more than an AI wrapper, and it is why every result is reproducible: same
paper, same numbers, every time.

Trade-off: the quality of what gets checked depends on how well the model reads. We
handle that with strict extraction rules, guards against bad values, and a human
review step ([0004](0004-human-in-the-loop.md)).
