# ADR 0009: Ship an adoption surface - CLI, batch, and a GitHub Action

Status: Accepted

## The problem

A research-integrity tool only has impact if people can actually fold it into how
they work. A single web demo proves the idea but does not travel: an author checking
one paper, a lab screening a backlog, and a journal gating submissions are three
different workflows, and "clone the repo and run a Python module" is friction that
stops adoption before it starts.

## The decision

Wrap the same core (`audit_text`) in the surfaces each of those users already lives in:

- **An installable CLI.** `pip install .` exposes one `rigor` command
  (`audit` / `batch` / `agent` / `demo` / `benchmark` / `serve`), packaged via
  `pyproject.toml`. One obvious entry point instead of six `python -m` invocations.
- **Batch mode** (`rigor/batch.py`). Point it at a folder of papers and it returns a
  worst-first triage table as CSV and JSON, with a `--min-score` flag that exits
  non-zero - so it can gate a pipeline.
- **A GitHub Action** (`action.yml`). A composite action that installs Rigor and runs
  the batch tool on a repo's papers on every push, uploads the report as an artifact,
  and fails the build if any paper scores below a threshold.

All three are thin shells over the identical deterministic core; none forks the logic.

## Why it is good, and the trade-off

It turns Rigor from a demo into infrastructure and directly serves the
editorial-submission workflow it targets: the same engine screens one paper, a queue,
or every commit. It also strengthens the open-source-adoption story - the path from
"saw it" to "using it in my repo" is a few lines of YAML.

Trade-off: more surfaces to keep working, so each is covered by the same tests and a
CI job installs the package and runs `rigor` to catch packaging regressions. The core
stays single-sourced, so the maintenance cost is packaging, not duplicated logic.
