"""
Rigor agent - a genuine Qwen tool-calling agent, not a linear pipeline.

Instead of a fixed extract -> check -> report flow, this runs Qwen in a multi-turn
loop where the model DECIDES what to check, CALLS the deterministic verification
tools itself (it never computes a verdict), REASONS about each result, and then
SYNTHESISES a judgement about the pattern of findings (systematic vs isolated).

The deterministic tools guarantee the verdicts are un-hallucinatable; the agent
supplies the reasoning and narrative on top. This is the Track 4 "Autopilot Agent"
shape: ambiguous input in, tool use + reasoning + a human-readable verdict out.

Run:  python -m rigor.agent            # on the built-in demo paper
      python -m rigor.agent paper.txt
"""
from __future__ import annotations

import json
import sys

from rigor.checks import check_df_vs_n, check_pvalue, grim
from rigor.ingest import load_text
from rigor.llm import LLM_MODEL, SEED, client

SYSTEM = """You are Rigor, a research-integrity auditor AGENT. You are given a \
paper's text. Work in steps:

1. Find every reported statistical test (t, F, chi-square, r, z) and every reported
   mean of a whole-number rating scale.
2. For EACH one, CALL the matching tool with the exact numbers you read:
   - recompute_pvalue for any test with a p-value,
   - grim_test for a mean on an integer scale,
   - check_df_vs_n when a test's df can be compared to the study's stated N.
   You must NEVER decide a verdict yourself - only the tools decide. Call tools.
3. After a tool returns, reason briefly about what it means (a decision-flipping
   error is serious; a tiny rounding mismatch is minor).
4. When you have checked everything, STOP calling tools and write a final
   assessment with these parts:
   OVERALL: <one-line integrity judgement>
   PATTERN: <are the problems systematic - e.g. many overstated p-values - or isolated?>
   KEY ISSUES: <the 1-3 most important findings, each in one plain sentence>
   Base every statement only on tool results."""

TOOLS = [
    {"type": "function", "function": {
        "name": "recompute_pvalue",
        "description": "Recompute a p-value from a test statistic and compare to the reported value.",
        "parameters": {"type": "object", "properties": {
            "test": {"type": "string", "enum": ["t", "f", "chi2", "r", "z"]},
            "statistic": {"type": "number"},
            "reported_p": {"type": "number"},
            "df1": {"type": ["number", "null"]},
            "df2": {"type": ["number", "null"]},
            "n": {"type": ["integer", "null"]},
            "comparator": {"type": "string", "enum": ["=", "<", ">"]},
        }, "required": ["test", "statistic", "reported_p"]}}},
    {"type": "function", "function": {
        "name": "grim_test",
        "description": "Check whether a reported mean is possible for N integer responses.",
        "parameters": {"type": "object", "properties": {
            "mean": {"type": "number"}, "n": {"type": "integer"},
            "n_items": {"type": "integer"}, "decimals": {"type": "integer"},
        }, "required": ["mean", "n"]}}},
    {"type": "function", "function": {
        "name": "check_df_vs_n",
        "description": "Check whether a test's degrees of freedom fit the stated sample size N.",
        "parameters": {"type": "object", "properties": {
            "test": {"type": "string"}, "df": {"type": "number"}, "stated_n": {"type": "integer"},
        }, "required": ["test", "df", "stated_n"]}}},
]


def _run_tool(name: str, a: dict) -> dict:
    if name == "recompute_pvalue":
        r = check_pvalue(a["test"], a["statistic"], a["reported_p"], df1=a.get("df1"),
                         df2=a.get("df2"), n=a.get("n"), comparator=a.get("comparator", "="))
        return {"consistent": r.consistent, "decision_error": r.decision_error,
                "computed_p": round(r.computed_p, 5), "verdict": r.message}
    if name == "grim_test":
        g = grim(a["mean"], a["n"], a.get("n_items", 1), a.get("decimals", 2))
        return {"possible": g.possible, "verdict": g.message}
    if name == "check_df_vs_n":
        d = check_df_vs_n(a["test"], a["df"], a["stated_n"])
        return {"note": "not applicable"} if d is None else {"consistent": d.consistent, "verdict": d.message}
    return {"error": f"unknown tool {name}"}


def audit_agent_stream(paper_text: str, max_turns: int = 10):
    """Yield events AS the agent works: status, each tool call, and the final
    narrative. This is what powers the live activity log in the web UI."""
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": paper_text},
    ]
    yield {"type": "status", "msg": "Reading the paper and deciding what to check..."}
    for turn in range(max_turns):
        yield {"type": "status", "msg": f"Turn {turn + 1}: asking Qwen which checks to run..."}
        resp = client().chat.completions.create(
            model=LLM_MODEL, messages=messages, tools=TOOLS, temperature=0, seed=SEED)
        msg = resp.choices[0].message

        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or ""})
            yield {"type": "narrative", "text": msg.content or ""}
            yield {"type": "done", "turns": turn + 1}
            return

        messages.append({
            "role": "assistant", "content": msg.content or "",
            "tool_calls": [{"id": tc.id, "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                           for tc in msg.tool_calls],
        })
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
                result = _run_tool(tc.function.name, args)
            except Exception as exc:  # noqa: BLE001
                args, result = {}, {"error": str(exc)}
            yield {"type": "tool", "tool": tc.function.name, "args": args, "result": result}
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

    yield {"type": "narrative", "text": "(agent reached the turn limit)"}
    yield {"type": "done", "turns": max_turns}


def audit_agent(paper_text: str, max_turns: int = 10, verbose: bool = False) -> dict:
    """Non-streaming wrapper (CLI + /api/agent): collects the stream into a result."""
    narrative, trace, turns = "", [], 0
    for ev in audit_agent_stream(paper_text, max_turns):
        if ev["type"] == "tool":
            trace.append(ev)
            if verbose:
                print(f"  [tool] {ev['tool']}({ev['args']}) -> {ev['result'].get('verdict', ev['result'])}")
        elif ev["type"] == "narrative":
            narrative = ev["text"]
        elif ev["type"] == "done":
            turns = ev["turns"]
    return {"narrative": narrative, "trace": trace, "turns": turns}


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    from rigor.audit import SAMPLE_PAPER
    text = load_text(argv[0]) if argv else SAMPLE_PAPER
    print("Running the Rigor agent (Qwen tool-calling loop)...\n")
    out = audit_agent(text, verbose=True)
    print(f"\nAgent finished in {out['turns']} turns, {len(out['trace'])} tool calls.\n")
    print("=" * 68)
    print(out["narrative"])
    print("=" * 68)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
