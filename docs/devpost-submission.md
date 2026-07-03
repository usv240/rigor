# Devpost submission - Rigor

Copy-paste ready. Fill the two bracketed links (video, blog) once recorded/posted.

---

## Project name
Rigor

## Elevator pitch (tagline)
An AI research-integrity referee that catches the statistical errors before the reviewers do. The AI reads the paper; exact math renders every verdict.

## Track
Track 4: Autopilot Agent

## Inspiration
About half of published psychology papers contain at least one statistical
inconsistency, and roughly one in seven of those would flip the paper's
conclusion. These are mostly honest mistakes - a mistyped p-value, an impossible
mean, a "significant" claim the numbers do not support. Peer reviewers rarely
catch them, because they read for ideas, not arithmetic. The tools that do exist
are closed, expensive, and sold to publishers to run after submission. The person
who most needs the help - the author about to submit - has nothing. We built Rigor
for them.

## What it does
Paste a paper (or drop a PDF) and Rigor:
- **Recomputes every p-value** from its test statistic (statcheck-style) and flags
  decision-flipping errors.
- **Runs the GRIM test** to catch arithmetically impossible means.
- **Cross-checks degrees of freedom against the sample size** - a check no other
  tool does.
- **Detects "spin"** - claims whose wording overstates the numbers, grounded in the
  results the math already verified.
- Explains each finding in **plain language** with concrete correction options, and
  lets the user **dismiss false positives** before finalising a downloadable report.

It runs as a website, a JSON API, an **MCP server** (so any AI agent can call the
checks as tools), and a genuine **Qwen tool-calling agent** that decides what to
check, calls the deterministic tools itself, reasons about the results, and
synthesises whether the errors are systematic.

## How we built it
- **Qwen (Alibaba Cloud Model Studio)** via the OpenAI-compatible DashScope endpoint
  does the one thing only a strong LLM can: read arbitrary, free-form scientific
  prose and extract the statistics via **native function/tool calling**.
- A **deterministic engine** (SciPy exact distributions + arithmetic) renders every
  verdict, so nothing can be hallucinated. If the model misreads a number, the worst
  case is a flag a human dismisses; it can never invent a wrong verdict.
- An **agentic loop** (rigor/agent.py) runs Qwen in multi-turn tool use for reasoning
  and pattern synthesis, with a human-in-the-loop review checkpoint.
- **FastAPI** backend + a premium static frontend, containerised with Docker and
  **deployed on Alibaba Cloud ECS** (Singapore), with per-IP rate limiting and audit
  logging.
- An **MCP server** exposes the checks as reusable agent tools.

## Challenges we ran into
- Proving it is not "an AI wrapper": we solved this architecturally - the LLM only
  extracts; math judges.
- Robustness on real papers: an early version wrongly applied GRIM to continuous
  measurements. We hardened extraction so GRIM only fires on integer scales, added
  guards against malformed p-values, and de-duplicated findings.
- Turning a pipeline into a real agent for Track 4, with tool use and reasoning.

## Accomplishments we are proud of
- **100% detection, 0% false positives** on a 32-case benchmark spanning t, F,
  chi-square, r, z, GRIM, and df-vs-N.
- A **verified real-world catch**: on a published Geology paper (Eppes et al., 2018),
  Rigor flagged a correlation across only four rock types claiming p < .05 that
  recomputes to about .08 - confirmed against the paper's own methods.
- A genuine **Qwen tool-calling agent**, an **MCP server**, and a **live deployment
  on Alibaba Cloud**.

## What we learned
Use the model for what only it can do - reading messy human text - and let
deterministic code own anything that must be correct. That division is what turns an
LLM demo into a tool people can trust.

## What's next
Scale the validation to a large corpus of retracted/corrected papers; add
recompute-from-summary-stats; support more test types and one-tailed detection.

## Built with
python, qwen, alibaba-cloud, model-studio, dashscope, fastapi, scipy, pymupdf, mcp,
docker, ecs, uvicorn

## Links
- **Code repository:** https://github.com/usv240/rigor
- **Live demo (Alibaba Cloud ECS):** http://47.236.166.20:8000
- **Proof of Alibaba Cloud services/APIs (code file):** https://github.com/usv240/rigor/blob/main/rigor/llm.py
- **Demo video:** [YouTube/Vimeo link - add after recording]
- **Blog post (optional bonus):** [Medium/Dev.to link - add after posting]

## Proof of Alibaba Cloud deployment
- Backend running on Alibaba Cloud ECS (Singapore); a short screen recording shows
  the instance in the console and the live URL functioning.
- Code file demonstrating use of Alibaba Cloud services/APIs: rigor/llm.py (calls
  Qwen via the DashScope / Model Studio endpoint).
