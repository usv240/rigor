# Rigor on real papers

Rigor is validated on a curated benchmark (100% detection, 0% false positives on
32 cases) AND run on real, published papers. These are **inconsistencies to review,
not accusations** - the point is that Rigor surfaces them automatically, in seconds,
where a human reviewer would not have recomputed anything.

## Example 1 (VERIFIED): a fragile small-N correlation in a published paper

Running Rigor on a real, published *Geology* paper (Eppes et al., "Rates of
subcritical cracking and long-term rock erosion," 2018) it flagged this sentence:

> *"We find strong correlations - across the four rock types - between averaged
> erosion rates and the three subcritical cracking parameters (R2s > 0.85 and
> p-values < 0.05)."*

Rigor's flag: the correlation is across only **four rock types (n = 4, df = 2)**,
and at that sample size an **R² = 0.85 correlation recomputes to p ≈ 0.08, not
below 0.05.** Reaching p < 0.05 with four points needs R² ≈ 0.90+, so the blanket
"p < 0.05" claim is statistically fragile.

**We verified it against the paper's own methods:** the four rock types are named
(Old Rag Granite, Weverton, Harpers, Antietam quartzite), confirming n = 4. Rigor
inferred the sample size from "four rock types" and was correct. This is the kind
of small-sample significance overclaim that reviewers routinely miss - caught
automatically.

## Example 2: a genuine overclaim in a psychology paper

On a real PLOS ONE cognitive-psychology paper, Rigor flagged a summary sentence
presented as an established finding, and pointed out that the critical test was
**t(63) = 1.868, p = .066 - not significant** - and that the paper itself notes the
effect is "slightly above the threshold of statistical significance." A
non-significant result presented as established, caught automatically.

## Example 3: clean on a legitimate paper (no false positives)

On a real PLOS ONE engineering paper, after hardening extraction, Rigor scored it
**91/100 with zero false positives** - it did not misfire on the paper's many
continuous measurements (surface-roughness values in micrometres), which an earlier
version wrongly flagged with GRIM. GRIM now only applies to whole-number rating
scales, as it should.

## Honest scope

- Rigor is tuned for null-hypothesis significance reporting (t, F, chi-square, r, z
  tests; GRIM), which is common in psychology, social science, and biomedicine.
- On long, messy PDFs outside that format, extraction is noisier and can vary
  between runs. That is exactly what the **human-in-the-loop review step** is for:
  Rigor flags, a human verifies, and false positives are dismissed before the
  report is finalised. Every hard finding also carries the exact recomputed numbers
  so a human can check it in seconds.
- Verdicts are always deterministic math; only extraction is model-based. A fixed
  seed and temperature 0 are used to make extraction as reproducible as possible.
