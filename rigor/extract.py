"""
LLM extraction layer - turns messy paper prose into structured statistics.

Uses Qwen's native function/tool-calling API (Alibaba Cloud Model Studio): the
model is given a typed `submit_extraction` function schema and returns structured
arguments, rather than free text we regex-parse. This is more reliable and is a
first-class use of the Qwen tool-use API. The model still only *reads*; it makes
no judgement about correctness (that is the deterministic engine's job).
"""
from __future__ import annotations

import json
import os
from collections import Counter

from rigor.llm import LLM_MODEL, SEED, client, log_usage

SYSTEM = """You are a meticulous extraction engine for scientific papers. Call the \
submit_extraction function with everything you find. Rules:

- For each null-hypothesis test (t, F, chi-square, r, z): give the test statistic,
  the degrees of freedom (df1 for t and chi2; df1 AND df2 for F; for a correlation
  r the number in parentheses IS the df, put it in df1), the reported p-value and
  its comparator. reported_p must be a number strictly between 0 and 1 (use 0.001
  for "p < .001"); never 0 or negative. "claim" is the exact sentence THIS statistic
  appears in, not a later summary or conclusion.
- "means": ONLY include a mean when the responses are WHOLE NUMBERS on a bounded
  rating scale (e.g. 1-5 Likert) or simple counts. NEVER include means of physical
  measurements, times, distances, weights, percentages, or any continuous quantity.
  Include "sd" (the reported standard deviation for that mean) when it is printed,
  else null.
- "sample_size": the overall N of the study if clearly stated, else null.

Extract faithfully what is printed; do not judge correctness."""

EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_extraction",
        "description": "Submit the statistics, means, and sample size extracted from the paper.",
        "parameters": {
            "type": "object",
            "properties": {
                "stats": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "test": {"type": "string", "enum": ["t", "f", "chi2", "r", "z"]},
                            "statistic": {"type": "number"},
                            "df1": {"type": ["number", "null"]},
                            "df2": {"type": ["number", "null"]},
                            "n": {"type": ["integer", "null"]},
                            "reported_p": {"type": "number"},
                            "comparator": {"type": "string", "enum": ["=", "<", ">"]},
                            "claim": {"type": "string"},
                        },
                        "required": ["test", "statistic", "reported_p", "comparator", "claim"],
                    },
                },
                "means": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "number"},
                            "n": {"type": "integer"},
                            "sd": {"type": ["number", "null"]},
                            "n_items": {"type": "integer"},
                            "decimals": {"type": "integer"},
                            "scale": {"type": "string"},
                            "context": {"type": "string"},
                        },
                        "required": ["value", "n"],
                    },
                },
                "sample_size": {"type": ["integer", "null"]},
            },
            "required": ["stats", "means"],
        },
    },
}


def _extract_json(raw: str) -> dict:
    """Robustly pull a JSON object out of a model's text reply (used by claims.py)."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("{") :]
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return {}


def _extract_once(paper_text: str) -> dict:
    """A single Qwen tool-calling extraction pass."""
    resp = client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": paper_text},
        ],
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "function", "function": {"name": "submit_extraction"}},
        temperature=0,
        seed=SEED,
    )
    log_usage(resp, tag="extract")
    msg = resp.choices[0].message
    data: dict = {}
    if msg.tool_calls:
        try:
            data = json.loads(msg.tool_calls[0].function.arguments)
        except (json.JSONDecodeError, TypeError):
            data = {}
    elif msg.content:  # fallback if the model replied in text
        data = _extract_json(msg.content)

    data.setdefault("stats", [])
    data.setdefault("means", [])
    data.setdefault("sample_size", None)
    return data


def _num(x):
    try:
        return round(float(x), 4)
    except (TypeError, ValueError):
        return None


def _canon_stat(s: dict) -> tuple:
    return (str(s.get("test", "")).lower(), _num(s.get("statistic")), _num(s.get("df1")),
            _num(s.get("df2")), _num(s.get("reported_p")), s.get("comparator", "="))


def _canon_mean(m: dict) -> tuple:
    return (_num(m.get("value")), m.get("n"), _num(m.get("sd")), m.get("n_items", 1))


def _reconcile(runs: list[dict], key_fn, list_name: str) -> tuple[list[dict], list[float]]:
    """Majority-vote items across runs; attach each survivor's support ratio."""
    k = len(runs)
    majority = k // 2 + 1
    buckets: dict[tuple, dict] = {}
    for run in runs:
        seen = set()
        for item in run.get(list_name, []) or []:
            key = key_fn(item)
            if key in seen:  # don't let one run's duplicate inflate support
                continue
            seen.add(key)
            b = buckets.setdefault(key, {"count": 0, "item": item})
            b["count"] += 1
    kept, supports = [], []
    for b in buckets.values():
        if b["count"] >= majority:
            support = round(b["count"] / k, 3)
            item = dict(b["item"])
            item["_support"] = support
            kept.append(item)
            supports.append(support)
    return kept, supports


def extract(paper_text: str, samples: int | None = None) -> dict:
    """Return {"stats": [...], "means": [...], "sample_size": int|None, "extraction": {...}}.

    With samples > 1, Rigor extracts several times and reconciles the results by
    majority vote: an item is kept only if it appears in most runs, which filters out
    one-off misreads, and each survivor carries a `_support` ratio (its reproducibility
    across runs). The `extraction.agreement` field is the mean support - a live,
    honest measure of how reliably the model read THIS paper. Extraction is the only
    non-deterministic part of Rigor, so this turns that uncertainty into a number.
    """
    if samples is None:
        samples = int(os.getenv("RIGOR_EXTRACT_SAMPLES", "1"))
    samples = max(1, samples)

    if samples == 1:
        data = _extract_once(paper_text)
        data["extraction"] = {"samples": 1, "agreement": 1.0}
        return data

    runs = [_extract_once(paper_text) for _ in range(samples)]
    stats, s_sup = _reconcile(runs, _canon_stat, "stats")
    means, m_sup = _reconcile(runs, _canon_mean, "means")

    ns = [r.get("sample_size") for r in runs if r.get("sample_size") is not None]
    sample_size = Counter(ns).most_common(1)[0][0] if ns else None

    supports = s_sup + m_sup
    agreement = round(sum(supports) / len(supports), 3) if supports else 1.0
    return {
        "stats": stats,
        "means": means,
        "sample_size": sample_size,
        "extraction": {"samples": samples, "agreement": agreement},
    }
