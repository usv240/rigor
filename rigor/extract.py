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

from rigor.llm import LLM_MODEL, client

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


def extract(paper_text: str) -> dict:
    """Return {"stats": [...], "means": [...], "sample_size": int|None} via Qwen tool-calling."""
    resp = client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": paper_text},
        ],
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "function", "function": {"name": "submit_extraction"}},
        temperature=0,
    )
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
