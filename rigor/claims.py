"""
Claim vs. evidence ("spin") detection - the feature no deterministic tool has.

statcheck / GRIM check whether the *numbers* are internally consistent. They say
nothing about whether the paper's *words* match those numbers. This module does:
given the paper text and the results Rigor already VERIFIED with math, it flags
claims whose wording overstates the evidence - especially claims of a significant
effect for a result that recomputed as non-significant.

Grounding matters: a flag is "grounded" only when it directly contradicts a
math-verified verdict (un-hallucinatable). Softer issues (causal language from
correlational data, over-generalisation) are labelled as AI-flagged for human
review - honestly separated from the hard, provable findings.
"""
from __future__ import annotations

from rigor.extract import _extract_json
from rigor.llm import chat

SYSTEM = """You audit scientific CLAIMS against their statistical evidence.

You are given (a) a paper's text and (b) a list of statistical results that have
already been VERIFIED with exact math, each with a verdict. Identify places where
the paper's WORDING overstates what the statistics support. Look for:

- OVERCLAIM: asserting a significant effect / improvement / difference when the
  cited result is NOT significant, or was flagged inconsistent.
- CAUSAL: causal wording ("causes", "leads to", "improves", "boosts") drawn from
  a correlational or observational result.
- GENERALIZATION: extending the conclusion well beyond the sample studied.

Output ONLY a JSON object:
{"claims": [
  {"claim": "<the exact overstated sentence/phrase>",
   "issue": "OVERCLAIM" | "CAUSAL" | "GENERALIZATION",
   "grounded": true | false,
   "explanation": "<why it overstates the evidence, in one plain sentence>"}
]}

Set "grounded": true ONLY when the claim directly contradicts a verified result
(e.g. it claims significance for a result recomputed as non-significant). Use
false for judgement calls. If the claims fairly match the evidence, return an
empty array. Do NOT invent problems."""


def analyze_claims(paper_text: str, verified_results: list[str]) -> list[dict]:
    evidence = "\n".join(f"- {r}" for r in verified_results) or "(no test statistics verified)"
    user = f"PAPER TEXT:\n{paper_text}\n\nVERIFIED RESULTS:\n{evidence}"
    raw = chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
    data = _extract_json(raw)
    claims = data.get("claims", [])
    return claims if isinstance(claims, list) else []
