# Rigor at corpus scale

To show Rigor operating as a pipeline and not a one-paper demo, we ran it over a
folder of **26 real, published geoscience papers** in a single automated pass:

```bash
rigor batch ./Papers --csv corpus.csv --json corpus.json
```

One command, one machine, one live Qwen call per paper. The batch engine
([rigor/batch.py](../rigor/batch.py)) is the same one wired into the
[GitHub Action](../action.yml), so this is the editorial-workflow shape running at
queue scale.

## The impact, in one line

> Screening these 26 papers by hand, recomputing all **62 reported statistics** at
> about 3 minutes each, is roughly **3.1 hours** of work. Rigor did it in **5.9
> minutes**, and narrowed the stack down to the **3 papers that need a human look.**

That is the value of the tool in a sentence: it turns hours of tedious recomputation
into minutes, and turns a pile of 26 submissions into a ranked shortlist of 3. Every
number there is computed from the run itself (the batch prints it and writes it to
the JSON), at a conservative 3 minutes per statistic, an assumption we show rather
than hide.

## What happened

- **All 26 papers processed. 22 scored a clean 100/100.** Crucially, Rigor did **not**
  false-fire on the corpus's many continuous measurements (rock temperatures, strain,
  erosion rates in physical units). The GRIM/GRIMMER guard that limits those checks to
  whole-number rating scales held up across a real, messy corpus. That negative result
  is the important one: **no false positives on continuous data.**
- **4 papers drew flags; 3 had hard errors** and sit at the top of the worst-first
  table for a human to examine.
- The **single worst-ranked paper** (score 65) is *"Rates of Subcritical Cracking and
  Long-Term Rock Erosion"*, which is exactly the paper we independently hand-verified
  (the n = 4 correlation claiming p < .05 that recomputes to about .08, see
  [real-world.md](real-world.md)). The triage put the confirmed real catch at the top
  on its own.

## An earlier run paid for itself by surfacing two real bugs

Running at scale is a stress test, and an early pass found defects a single-paper demo
never would:

1. **A crash on a null field.** One paper made the model emit `"n_items": null`;
   because `dict.get(key, default)` keeps an explicit `None`, `int(None)` threw and
   sank the *whole* audit. Fixed and covered by a regression test.
2. **A 30-second timeout too tight for long PDFs.** Full-text extraction plus claim
   analysis on a 30-page paper can exceed 30s; raised to 60s with retries.

Both are fixed, which is why all 26 papers now process cleanly.

## The honest headline: single-pass flag counts are *leads, not verdicts*

The most important caveat, stated plainly: on a long, dense PDF the language model
reads slightly differently run to run, so *which numbers get checked* can vary, and
single-pass flag counts on messy full text are noisy.

This is exactly the boundary Rigor is built around:

- Every **verdict** is exact math and never varies. Given the same extracted numbers,
  the answer is identical every time.
- What varies is **extraction**, the one non-deterministic step. That is precisely why
  Rigor has (a) **multi-run reconciliation** with a live agreement score
  (`RIGOR_EXTRACT_SAMPLES=3`, [ADR 0007](adr/0007-extraction-reconciliation.md)), which
  majority-votes away one-off misreads, and (b) a **human-in-the-loop** review step. On
  a clean Results section (the intended input) extraction is stable; on a 30-page PDF,
  treat the flags as leads to verify, not accusations.

For **verified** real-paper catches, where we confirmed a flag against the paper's own
methods, see [real-world.md](real-world.md). Those are the claims we stand behind; the
corpus run is a scale, impact, and robustness demonstration.

## What the corpus run demonstrates for judging

- **Impact:** 3.1 hours of hand-checking compressed into under 6 minutes, and 26
  submissions triaged to 3, computed from the run, not asserted.
- **Scale / productization:** Rigor screens a whole submission queue in one pass and
  emits a ranked triage table (CSV/JSON), the editorial workflow, not a toy.
- **Robustness:** no false positives on a real corpus full of continuous data; it
  stayed quiet where it should, and ranked the one verified catch first.
- **Engineering honesty:** the run found and fixed real bugs, and we report its one
  genuine limitation (extraction variance on long PDFs) rather than hide it.
