"""
LLM extraction layer - turns messy paper prose into structured statistics.

This is the part that was impossible before modern LLMs: reading arbitrary,
free-form scientific text and pulling out every `t(48) = 1.90, p < .001` (and the
claim it supports) as clean structured data. It makes NO judgement about
correctness - that is the deterministic engine's job (rigor/checks/).
"""
from __future__ import annotations

import json

from rigor.llm import chat

SYSTEM = """You are a meticulous extraction engine for scientific papers. From the \
text, extract two things and output ONLY a single JSON object (no prose, no code \
fences):

1. "stats": every null-hypothesis significance test reported. For each:
   - "test": one of "t", "f", "chi2", "r", "z"
   - "statistic": the numeric test-statistic value
   - "df1": degrees of freedom for t and chi2; the FIRST df for F; and for a
     correlation r the number in parentheses IS the df (df = n - 2), so put it here
   - "df2": the SECOND df for F; else null
   - "n": sample size if explicitly stated; else null (for r, prefer df1, not n)
   - "reported_p": the numeric p-value as printed. For "p < .001" use 0.001 with
     comparator "<". It must be a number strictly between 0 and 1; never 0 or negative.
   - "comparator": "=", "<", or ">" as printed with the p-value
   - "claim": the exact sentence in which THIS statistic is reported (the sentence
     that contains it), NOT a later summary, abstract, or conclusion sentence

2. "means": ONLY include a reported mean when the underlying responses are WHOLE
   NUMBERS on a bounded rating scale (e.g. a 1-5 or 1-7 Likert scale) or are simple
   counts. The GRIM check only applies to integer responses. DO NOT include means
   of physical measurements, times, distances, weights, currency, temperatures,
   percentages, or any continuous quantity (e.g. "6.07 micrometres" or "3.4 seconds").
   If you are not certain the responses are whole numbers on a small scale, OMIT it.
   For each included mean:
   - "value": the reported mean
   - "n": the sample size the mean is based on
   - "n_items": number of items averaged (default 1 if unclear)
   - "decimals": number of decimal places the mean was reported to
   - "scale": the integer scale or count it comes from (e.g. "1-7 Likert"); required
   - "context": the snippet it came from

3. "sample_size": the overall number of participants/observations in the study, as
   an integer, if it is clearly stated (e.g. "N = 10"); otherwise null.

Extract faithfully what is printed. Do NOT judge correctness. If none are found,
return empty arrays. Output must be valid JSON."""


def _extract_json(raw: str) -> dict:
    """Robustly pull the JSON object out of the model's reply."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("{") :]
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return {"stats": [], "means": []}
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return {"stats": [], "means": []}


def extract(paper_text: str) -> dict:
    """Return {"stats": [...], "means": [...]} extracted from the paper text."""
    raw = chat(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": paper_text},
        ]
    )
    data = _extract_json(raw)
    data.setdefault("stats", [])
    data.setdefault("means", [])
    data.setdefault("sample_size", None)
    return data
