"""
Unified `rigor` command - the single entry point once the package is installed.

    pip install .          # or: pip install git+https://github.com/usv240/rigor
    rigor audit paper.pdf
    rigor batch ./submissions --csv out.csv --min-score 70
    rigor demo             # deterministic checks, no API key
    rigor benchmark        # deterministic-core accuracy (530 cases, no API key)
    rigor serve            # launch the web app

Frictionless install + one obvious command is what turns an open-source project into
one people actually adopt.
"""
from __future__ import annotations

import sys

USAGE = """rigor - statistical-integrity screening for research papers

usage: rigor <command> [args]

commands:
  audit <path>            audit one paper (text or PDF)
  batch <folder> [opts]   audit a whole folder -> triage table (+ --csv/--json/--min-score)
  agent [path]            run the Qwen tool-calling agent on a paper
  demo                    deterministic checks, no API key needed
  benchmark               deterministic-core accuracy benchmark (no API key)
  serve [--port N]        launch the web app
  help                    show this message
"""


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "help"
    rest = argv[1:]

    if cmd == "audit":
        from rigor.audit import main as audit_main
        return audit_main(rest)
    if cmd == "batch":
        from rigor.batch import main as batch_main
        return batch_main(rest)
    if cmd == "agent":
        from rigor.agent import main as agent_main
        return agent_main(rest)
    if cmd == "demo":
        from rigor.demo_checks import main as demo_main
        demo_main()
        return 0
    if cmd == "benchmark":
        from rigor.benchmark_checks import run
        run()
        return 0
    if cmd == "serve":
        port = 8000
        if "--port" in rest:
            try:
                port = int(rest[rest.index("--port") + 1])
            except (IndexError, ValueError):
                pass
        import uvicorn
        uvicorn.run("web.app:app", host="0.0.0.0", port=port)
        return 0
    if cmd in ("help", "-h", "--help"):
        print(USAGE)
        return 0

    print(f"unknown command: {cmd}\n")
    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
