# Rigor

**An AI research-integrity referee.** Rigor reads a scientific paper, recomputes
every p-value and mean with exact math, cross-checks the sample sizes, and flags
where the paper's claims overstate its own numbers. In seconds. Free and open
source.

Built for the **author** (grad students, early-career and non-native-English
researchers) who wants to catch honest mistakes *before* submission, not the
publishers with big budgets that existing integrity tools serve.

- **Hackathon:** Global AI Hackathon Series with Qwen Cloud, Track 4 (Autopilot Agent)
- **Powered by:** Qwen (Alibaba Cloud Model Studio) for extraction; exact statistics for every verdict

## Why it is not "just an AI wrapper"

The one question that separates a real tool from a wrapper: *if the LLM
hallucinates, does the product give a wrong answer?*

For Rigor, no. The language model's only job is **reading** messy prose and
pulling out structured numbers (`t(48) = 1.90, p < .001`). Every **verdict** is
produced by deterministic math and cannot be hallucinated. That is why Rigor
catches the errors *and leaves correct results alone*.

## What it checks

| Check | What it catches | Grounding |
|---|---|---|
| **p-value recomputation** | reported p disagrees with its test statistic (statcheck-style) | exact distributions (SciPy) |
| **GRIM** | arithmetically impossible means | pure arithmetic |
| **df vs N** | degrees of freedom that need more subjects than the study reports | pure arithmetic |
| **claim vs evidence** | conclusions that overstate the result (e.g. "significant" for a p that recomputed to n.s.) | grounded in the verified results |

Benchmark: **100% detection, 0% false positives** on a balanced 12-case set
(`python -m rigor.benchmark`). This is a proof-of-concept set, not a corpus;
scaling it to real papers is ongoing work.

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # add your DASHSCOPE_API_KEY + workspace endpoint

# the deterministic core, no API key needed:
python -m rigor.demo_checks

# the full pipeline on a built-in demo paper:
python -m rigor.audit

# the accuracy benchmark:
python -m rigor.benchmark

# the web app:
uvicorn web.app:app --port 8000   # then open http://localhost:8000
```

## Use Rigor from any AI agent (MCP)

Rigor ships an [MCP](https://modelcontextprotocol.io) server that exposes its
checks as tools, so any MCP client (Claude Desktop, an agent framework, another
Qwen agent) can fact-check statistics through Rigor and get a deterministic,
un-hallucinatable verdict.

```bash
python -m rigor.mcp_server        # stdio transport
```

Tools: `recompute_pvalue`, `grim_test`, `df_vs_n`, `audit_paper`. Example client
config (Claude Desktop):

```json
{ "mcpServers": { "rigor": { "command": "python", "args": ["-m", "rigor.mcp_server"] } } }
```

## Architecture

```mermaid
flowchart TD
    U["Researcher / reviewer (browser)"] --> FE["Frontend: landing + live tool"]
    AG["Any MCP agent (Claude Desktop, etc.)"] --> MCP["MCP server (rigor/mcp_server.py)"]
    FE --> API["FastAPI backend (web/app.py)"]

    API --> ING["ingest: text / PDF"]
    MCP --> ING
    ING --> EX["extract statistics (Qwen LLM)"]
    EX --> CK["deterministic checks: statcheck, GRIM, df-vs-N"]
    CK --> CM["claim vs evidence: grounded spin detection"]
    CM --> RP["scored, plain-language report"]
    RP --> API

    EX -->|DashScope API| Q["Qwen models (Alibaba Model Studio)"]
    CM -->|DashScope API| Q
    API -.runs on.-> ECS["Alibaba Cloud ECS (Singapore)"]
```

```
paper text / PDF
  -> ingest        (rigor/ingest.py)      text, PDF via PyMuPDF
  -> extract       (rigor/extract.py)     Qwen LLM -> structured stats/means/claims
  -> checks        (rigor/checks/)        statcheck + GRIM + df-vs-N (deterministic)
  -> claims        (rigor/claims.py)      claim-vs-evidence, grounded in the checks
  -> report        (rigor/report.py)      scored integrity report
web app            (web/app.py)           FastAPI + static landing page
```

## Tech stack

Python, FastAPI, SciPy, PyMuPDF, and Qwen via the OpenAI-compatible DashScope
endpoint. Deployable to Alibaba Cloud with the included `Dockerfile`.

## License

MIT. See [LICENSE](LICENSE).
