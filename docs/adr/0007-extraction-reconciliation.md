# ADR 0007: Reconcile several extractions, and report the agreement

Status: Accepted

## The problem

Rigor's verdicts are exact math and cannot be hallucinated ([0001](0001-model-reads-math-judges.md)).
But *what* gets checked depends on the one non-deterministic step: the model reading
the paper. On a clean Results section this is reliable; on a long, messy PDF the
model can occasionally misread or miss a number, and the same paper can vary a
little between runs. That single weak link deserved to be measured and hardened,
not just disclaimed.

## The decision

Make extraction optionally *self-checking*. With `RIGOR_EXTRACT_SAMPLES > 1`, Rigor
extracts the paper several times and reconciles the runs by majority vote:

- an extracted statistic or mean is kept only if it appears in a majority of runs,
  which filters out one-off misreads;
- each surviving item carries a **support** ratio (how many runs agreed on it),
  surfaced in the UI as a per-finding confidence;
- the report shows an overall **extraction agreement**, the mean support, a live,
  honest number for how reliably the model read *this* paper.

The verdicts are still exact math either way; this only concerns which numbers reach
them. Default is a single pass (cheapest); the deployed demo uses three.

## Why it is good, and the trade-off

It turns Rigor's one source of uncertainty into a measured, visible quantity instead
of a caveat, and majority voting genuinely improves precision on noisy PDFs. It also
keeps faith with the project's honesty principle: the tool tells you how confident it
is that it read the paper correctly, separately from the (always exact) math.

Trade-off: N samples cost roughly N times the extraction tokens. Because it is a
single env var, an operator picks the point on the cost/reliability curve that suits
them, and single-pass mode keeps the default cheap and the tests fast.
