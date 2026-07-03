# ADR 0003: Make it an agent, not a pipeline

Status: Accepted

## The problem

A fixed extract, check, report pipeline works well and is fast. But it is not really
an agent, and Track 4 (Autopilot Agent) rewards genuine agentic behavior: a system
that decides what to do and uses tools on its own.

## The decision

Give Qwen the checks as tools and let it run a multi-turn loop. The agent decides
what to check, calls the deterministic verification tools itself, reasons about each
result, decides whether the problems are systematic or isolated, then writes a
plain-language verdict. We stream the whole thing live so you can watch it work.

## Why it is good, and the trade-off

It is a real agent (tool use plus reasoning), and the live stream makes that obvious
to anyone watching. The tools it calls are still the deterministic checks, so the
final verdict still cannot be hallucinated ([0001](0001-model-reads-math-judges.md)).

Trade-off: the agent uses more tokens and is a little slower than the straight
pipeline. So we keep the fast pipeline as the main check and offer the agent as an
optional deeper analysis.
