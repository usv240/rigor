# Rigor on real papers

Rigor is not only validated on a curated benchmark; it was run on real, published,
open-access papers (PLOS, CC-BY). These findings are **inconsistencies to review,
not accusations** - the point is that Rigor surfaces them automatically, in seconds,
where a human reviewer would not have recomputed anything.

## Example 1: a genuine overclaim (real psychology paper)

Running Rigor on a real PLOS ONE cognitive-psychology paper (36 reported tests), it
flagged, among other things, a **claim-vs-evidence** issue:

> The paper's summary states *"Experiment 1 showed that humans switch more when
> foraging in large immersive navigational environments..."* as an established
> finding. Rigor flagged that the critical test was **t(63) = 1.868, p = .066** -
> **not significant** - and that the paper itself notes the effect is "slightly
> above the threshold of statistical significance."

A non-significant result (p = .066) presented in the summary as an established
finding. Rigor caught it automatically, grounded in the recomputed value.

It also flagged a **df-vs-N inconsistency**: correlations reported as `r(66)` (which
require 68 data points) against a stated sample of **N = 64**. Worth a human check -
either the df, the N, or the unit of analysis is mislabeled.

## Example 2: clean on a legitimate paper (no false positives)

On a real PLOS ONE engineering paper, after hardening extraction, Rigor scored it
**91/100** with **zero false positives** - it did not misfire on the paper's many
continuous measurements (e.g. surface-roughness values in micrometres), which an
earlier version wrongly flagged with GRIM. GRIM now only applies to whole-number
rating scales, as it should.

## What this shows

- Rigor produces **credible results on messy, real-world PDFs**, not just clean
  toy inputs.
- The robustness matters as much as the detection: it **leaves legitimate papers
  alone** and reserves flags for genuine inconsistencies.
- Every flag is a lead for a human to verify, with the exact recomputed numbers
  attached.

*Papers used are open-access (CC-BY) PLOS articles, referenced by DOI in the
project's evaluation notes. Findings are reported as inconsistencies for review.*
