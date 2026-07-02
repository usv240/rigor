"""
Rigor MCP server - exposes the integrity checks as tools any AI agent can call.

This turns Rigor from a single app into a reusable capability: any MCP client
(Claude Desktop, an agent framework, another Qwen agent) can fact-check a
p-value, a mean, or a df/N pair, or audit a whole paper, and get back a
deterministic, un-hallucinatable verdict.

Run:
    python -m rigor.mcp_server        # stdio transport

Register it with an MCP client, e.g. Claude Desktop config:
    {
      "mcpServers": {
        "rigor": { "command": "python", "args": ["-m", "rigor.mcp_server"] }
      }
    }
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from rigor.audit import audit_text
from rigor.checks import check_df_vs_n, check_pvalue, grim

mcp = FastMCP("rigor")


@mcp.tool()
def recompute_pvalue(
    test: str,
    statistic: float,
    reported_p: float,
    df1: float | None = None,
    df2: float | None = None,
    n: int | None = None,
    comparator: str = "=",
) -> dict:
    """Recompute a p-value from a reported test statistic and compare it to what was
    printed. `test` is one of t/f/chi2/r/z. Provide df1 (and df2 for F, or n for r).
    Returns the recomputed p, whether it is consistent, and whether the significance
    decision flips at .05. Pure math - no model."""
    r = check_pvalue(test, statistic, reported_p, df1=df1, df2=df2, n=n, comparator=comparator)
    return {
        "reported_p": r.reported_p,
        "computed_p": r.computed_p,
        "consistent": r.consistent,
        "decision_error": r.decision_error,
        "verdict": r.message,
    }


@mcp.tool()
def grim_test(mean: float, n: int, n_items: int = 1, decimals: int = 2) -> dict:
    """Check whether a reported mean is arithmetically possible for `n` integer
    responses (GRIM test). Returns whether it is possible and the nearest achievable
    means."""
    g = grim(mean, n, n_items, decimals)
    return {"possible": g.possible, "nearest_possible": g.nearest_possible, "verdict": g.message}


@mcp.tool()
def df_vs_n(test: str, df: float, stated_n: int) -> dict:
    """Check whether a test's degrees of freedom are possible for the stated sample
    size N. Applies to t-tests and correlations."""
    d = check_df_vs_n(test, df, stated_n)
    if d is None:
        return {"applicable": False, "note": "df-vs-N applies to t and r tests only"}
    return {
        "applicable": True,
        "consistent": d.consistent,
        "implied_min_n": d.implied_min_n,
        "verdict": d.message,
    }


@mcp.tool()
def audit_paper(text: str) -> dict:
    """Full integrity audit of a paper's text: extracts the statistics with Qwen, then
    runs every deterministic check plus the claim-vs-evidence analysis. Returns a
    scored report with all findings. Requires DASHSCOPE_API_KEY in the environment."""
    return audit_text(text).to_dict()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
