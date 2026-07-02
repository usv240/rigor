"""
Rigor web app - premium landing page + live integrity checker.

Serves a static single-page site (web/static/) and a small JSON API that runs the
audit pipeline, with per-IP rate limiting and structured audit logging.

Run:
    uvicorn web.app:app --reload --port 8000
Open http://localhost:8000
"""
from __future__ import annotations

import json
import logging
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from rigor.audit import SAMPLE_PAPER, audit_text
from rigor.ingest import load_text

logging.basicConfig(level=logging.INFO, format="%(message)s")
_log = logging.getLogger("rigor.audit")

app = FastAPI(title="Rigor", description="AI research-integrity referee")

# Per-IP rate limiting protects the (paid) Qwen API from being hammered.
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class AuditIn(BaseModel):
    text: str


def _log_audit(source: str, chars: int, result: dict, seconds: float) -> None:
    _log.info(json.dumps({
        "event": "audit", "ts": round(time.time(), 3), "source": source,
        "chars": chars, "score": result.get("score"),
        "errors": result.get("errors"), "warnings": result.get("warnings"),
        "seconds": round(seconds, 2),
    }))


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/sample")
def sample() -> dict:
    return {"text": SAMPLE_PAPER}


@app.post("/api/audit")
@limiter.limit("10/minute")
def api_audit(request: Request, body: AuditIn) -> JSONResponse:
    t0 = time.time()
    try:
        result = audit_text(body.text).to_dict()
    except Exception as exc:  # noqa: BLE001 - surface a real message to the UI
        return JSONResponse(status_code=502, content={"error": f"{type(exc).__name__}: {exc}"})
    result["source"] = "pasted text"
    _log_audit("text", len(body.text), result, time.time() - t0)
    return JSONResponse(result)


@app.post("/api/audit/pdf")
@limiter.limit("10/minute")
async def api_audit_pdf(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    t0 = time.time()
    try:
        data = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or ".pdf").suffix) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        text = load_text(tmp_path)
        result = audit_text(text).to_dict()
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=502, content={"error": f"{type(exc).__name__}: {exc}"})
    result["source"] = file.filename
    _log_audit(file.filename or "pdf", len(text), result, time.time() - t0)
    return JSONResponse(result)
