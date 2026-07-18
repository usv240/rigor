# Devpost submission - Rigor

Copy-paste ready. Fill the two bracketed links (video, blog) once recorded/posted.

---

## Project name
Rigor

## Elevator pitch (tagline)
An agent that automates the statistical-integrity screening step of manuscript submission - reading the paper and recomputing every number with exact math. The AI reads; the math renders every verdict, so nothing can be hallucinated.

## Track
Track 4: Autopilot Agent

## Team
Ujwal Suresh Vanjare and Arpita Madhukar Kalburgi

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
Paste a paper (or drop a PDF, or point it at a whole submission folder) and Rigor:
- **Recomputes every p-value** from its test statistic (statcheck-style) and flags
  decision-flipping errors.
- **Runs GRIM and GRIMMER** to catch arithmetically impossible means AND standard
  deviations.
- **Cross-checks degrees of freedom against the sample size**, and **checks reported
  effect sizes** (Cohen's d against its t) - cross-checks no other tool does.
- **Detects "spin"** - claims whose wording overstates the numbers, grounded in the
  results the math already verified.
- **Localizes the likely error** - a minimum-repair search over the paper's numeric
  constraint graph that names the single value to fix first (e.g. "N=10 is the likely
  typo; every flagged df is consistent once N >= 49"), verified by re-running the checks.
- Runs extraction several times and **reconciles by majority vote**, reporting a live
  extraction-agreement score and a per-finding confidence.
- Explains each finding in **plain language** with concrete correction options, and
  lets the user **dismiss false positives** before finalising a downloadable report.

It runs as a website, a JSON API, an installable `rigor` **CLI**, a **batch tool**
that triages a whole submission queue to CSV/JSON, a drop-in **GitHub Action** that
screens manuscripts on every commit, an **MCP server** (so any AI agent can call the
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
- **100% precision and recall on 530 injected-error cases** in a deterministic-core
  benchmark that runs offline with no API key, plus 100% detection / 0% false
  positives end-to-end on a 32-case pipeline benchmark.
- Six independent, provable checks - including **GRIMMER**, which almost no tool
  implements - each using only necessary conditions so a flag is never a false alarm.
- **Error localization**: a minimum-repair search that goes beyond detection to name
  the single number most likely at fault - a capability no other integrity tool has.
- A **verified real-world catch**: on a published Geology paper (Eppes et al., 2018),
  Rigor flagged a correlation across only four rock types claiming p < .05 that
  recomputes to about .08 - confirmed against the paper's own methods.
- **Scale impact on a real corpus**: screened 26 published papers in one automated
  pass, roughly 3.1 hours of hand-checking (62 statistics) compressed into under 6
  minutes and triaged down to the 3 that need a human look - and the paper it ranked
  worst was the one we had independently verified.
- A genuine **Qwen tool-calling agent**, an **MCP server**, and a **live deployment
  on Alibaba Cloud**.

## What we learned
Use the model for what only it can do - reading messy human text - and let
deterministic code own anything that must be correct. That division is what turns an
LLM demo into a tool people can trust.

## What's next
Scale the validation to a large corpus of retracted/corrected papers; add
recompute-from-summary-stats; support more test types and one-tailed detection;
integrate the batch tool into a submission-portal webhook so screening runs on upload.

## Built with
python, qwen, alibaba-cloud, model-studio, dashscope, fastapi, scipy, pymupdf, mcp,
docker, ecs, uvicorn

## Links
- **Code repository:** https://github.com/usv240/rigor
- **Live demo (Alibaba Cloud ECS):** http://47.236.166.20:8000
- **Proof of Alibaba Cloud services/APIs (code file):** https://github.com/usv240/rigor/blob/main/rigor/llm.py
- **Demo video:** [YouTube/Vimeo link - add after recording]
- **Blog post (optional bonus):** https://dev.to/ujwal240/i-built-a-spell-checker-for-the-statistics-in-research-papers-3a9m

## Proof of Alibaba Cloud deployment
- Backend running on Alibaba Cloud ECS (Singapore); a short screen recording shows
  the instance in the console and the live URL functioning.
- Code file demonstrating use of Alibaba Cloud services/APIs: rigor/llm.py (calls
  Qwen via the DashScope / Model Studio endpoint).
