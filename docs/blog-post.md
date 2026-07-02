# Building Rigor: a spell-checker for statistics, powered by Qwen

*My journey building an AI research-integrity referee for the Global AI Hackathon with Qwen Cloud.*

## The problem that started it

About half of published psychology papers contain at least one statistical
inconsistency, and roughly one in seven of those would flip the paper's
conclusion. That is not fraud, mostly. It is honest human error: a mistyped
p-value, a mean that cannot exist for the sample size, a "significant" claim that
the numbers do not actually support.

Here is the uncomfortable part: peer reviewers almost never catch these, because
they read for ideas and argument, not arithmetic. Nobody sits down and recomputes
a p-value by hand. The tools that do exist are closed, expensive, and sold to
publishers to run after submission. The person who most needs the help, the
author about to submit, has nothing.

So I built Rigor: paste a paper, and it recomputes every p-value and mean with
exact math, cross-checks the sample sizes, and flags where the words overstate the
numbers. In seconds. Free and open source.

## The insight: not an AI wrapper

The doubt I kept circling back to was: is this just an LLM with a nice UI? That
question kills most AI projects, and it deserved an honest answer.

The answer is no, and the reason is the whole design. The language model only
*reads*. Its single job is to turn messy prose like `t(48) = 1.90, p < .001` into
structured data. Every *verdict* is produced by deterministic math: exact
statistical distributions and arithmetic. If the model hallucinates, the worst
case is a missed or spurious flag on one statistic. It can never invent a wrong
verdict, because it never produces a verdict.

That separation is what makes Rigor trustworthy. It catches the errors *and leaves
correct results alone*, which a hallucinating wrapper cannot do.

## Where Qwen Cloud came in

I used Qwen (via Alibaba Cloud Model Studio, over the OpenAI-compatible DashScope
endpoint) for the one thing only a strong language model can do: read arbitrary,
free-form scientific text and extract the statistics, means, and claims as clean
structured data. This is the step that was simply impossible before modern LLMs.
statcheck, the tool that pioneered p-value recomputation, only works on rigidly
formatted statistics. Qwen's extraction generalizes the whole idea to any paper,
in any format, including full PDFs.

I also used Qwen for the feature I am proudest of: claim-vs-evidence detection.
Given the paper text and the results the math already verified, Qwen finds
sentences whose wording overstates the evidence, and Rigor grounds the hard flags
in the recomputed numbers so they are provable, not opinions.

## The four checks

1. **p-value recomputation** (statcheck-style): the true p-value is fixed by the
   test statistic and its degrees of freedom.
2. **GRIM**: the mean of whole-number responses can only land on certain values.
3. **df vs N**: a test's degrees of freedom imply a minimum sample size.
4. **claim vs evidence**: does the conclusion actually follow from the numbers?

The first two are established science. The last two go further than any tool I
know of.

## The moment it got real

A benchmark is nice (Rigor hits 100% detection with zero false positives on a
balanced set), but the moment I believed in it was running it on real, published,
open-access papers. On one real psychology paper it flagged a summary sentence
presented as an established finding, and pointed out that the underlying test was
t(63) = 1.868, p = .066, not significant, and that the paper itself admitted the
effect was "slightly above the threshold." A published overclaim, caught
automatically, in seconds.

That run also taught me humility. An early version wrongly applied the GRIM check
to continuous measurements in micrometres. Testing on real data forced me to make
the extraction conservative, so it only flags what it can defend. Robustness turned
out to matter as much as detection.

## Making it a capability, not just an app

To go beyond a single website, I wrapped Rigor's checks in an MCP server. Now any
AI agent can call `recompute_pvalue`, `grim_test`, `df_vs_n`, or `audit_paper` as
tools and fact-check statistics on its own. Rigor becomes a reusable building block.

## Deploying on Alibaba Cloud

The backend runs on Alibaba Cloud, containerized, with Qwen doing the reading and
exact math doing the judging. Everything is open source under the MIT license.

## What I would tell anyone building with Qwen

Use the model for what only it can do (reading and understanding messy human text),
and let deterministic code own anything that must be correct. That division is what
turns "an LLM demo" into a tool people can actually trust.

Rigor is free and open source: https://github.com/usv240/rigor

*Catch the statistical errors before the reviewers do.*
