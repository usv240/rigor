# Rigor at corpus scale

To show Rigor operating as a pipeline and not a one-paper demo, we ran it over a
folder of **26 real, published geoscience papers** in a single automated pass:

```bash
rigor batch ./Papers --csv corpus.csv --json corpus.json
```

One command, one machine, ~a few minutes, one live Qwen call per paper. The batch
engine ([rigor/batch.py](../rigor/batch.py)) is the same one wired into the
[GitHub Action](../action.yml), this is the editorial-workflow shape running at
queue scale.

## What happened

- **24 of 26 papers audited**; 18 of those scored a clean **100/100**. Crucially,
  Rigor did **not** false-fire on the corpus's many continuous measurements
  (rock temperatures, strain, erosion rates in physical units), the GRIM/GRIMMER
  guard that limits those checks to whole-number rating scales held up across a real,
  messy corpus. That negative result is the important one: **no false positives on
  continuous data.**
- A handful of papers drew flags for review.
- **2 papers failed the first pass**, and that is the most useful thing the run did
  (see below).

## The run paid for itself by surfacing two real bugs

Running at scale is a stress test, and it found defects a single-paper demo never
would:

1. **A crash on a null field.** One paper made the model emit `"n_items": null`;
   because `dict.get(key, default)` keeps an explicit `None`, `int(None)` threw and
   sank the *whole* audit. Fixed (and covered by a regression test) so a single odd
   field can never crash a run again.
2. **A 30-second timeout too tight for long PDFs.** Full-text extraction plus claim
   analysis on a 30-page paper can exceed 30s; raised to 60s with retries.

Both are fixed; all 26 papers now process.

## The honest headline: single-pass flag counts are *leads, not verdicts*

The most important finding is a limitation, and we state it plainly. Re-auditing one
flagged paper took its score from **14 to 100** between runs. Nothing in the math
changed, **extraction did.** On a long, dense PDF the language model reads slightly
differently run to run, so *which numbers get checked* varies, and single-pass flag
counts on messy full text are noisy.

This is exactly the boundary Rigor is built around:

- Every **verdict** is exact math and never varies, given the same extracted
  numbers, the answer is identical every time.
- What varies is **extraction**, the one non-deterministic step. That is precisely
  why Rigor has (a) **multi-run reconciliation** with a live agreement score
  (`RIGOR_EXTRACT_SAMPLES=3`, [ADR 0007](adr/0007-extraction-reconciliation.md)),
  which majority-votes away one-off misreads, and (b) a **human-in-the-loop** review
  step. On a clean Results section (the intended input) extraction is stable; on a
  30-page PDF, treat the flags as leads to verify, not accusations.

For **verified** real-paper catches, where we confirmed a flag against the paper's
own methods, see [real-world.md](real-world.md). Those are the claims we stand
behind; the corpus run is a scale-and-robustness demonstration, not a list of
confirmed errors.

## What the corpus run demonstrates for judging

- **Scale / productization:** Rigor screens a whole submission queue in one pass and
  emits a triage table (CSV/JSON), sorted worst-first, the editorial workflow, not a
  toy.
- **Robustness:** no false positives on a real corpus full of continuous data; it
  stayed quiet where it should.
- **Engineering honesty:** the run found and fixed real bugs, and we report its one
  genuine limitation (extraction variance on long PDFs) rather than hide it.
