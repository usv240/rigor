# ADR 0006: Expose the checks as an MCP server

Status: Accepted

## The problem

The statistical checks are useful beyond our own website. Other AI agents could use
them to fact-check numbers, but only if there is a standard way to call them.

## The decision

Wrap the checks in an [MCP](https://modelcontextprotocol.io) server. Any MCP client,
such as Claude Desktop, an agent framework, or another Qwen agent, can call
`recompute_pvalue`, `grim_test`, `df_vs_n`, or `audit_paper` as tools and get back a
deterministic, un-hallucinatable result.

## Why it is good, and the trade-off

Rigor becomes a reusable building block, not just a single web app. An agent that
would otherwise guess at whether a p-value is right can now check it against exact
math. It also demonstrates the kind of serious API and MCP use the judges look for.

Trade-off: it is one more surface to maintain. It stays small because it reuses the
exact same check functions the web app uses, so there is no duplicated logic.
