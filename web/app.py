"""
Rigor web app - premium landing page + live integrity checker.

Serves a static single-page site (web/static/) and a small JSON API that runs the
audit pipeline.

Run:
    uvicorn web.app:app --reload --port 8000
Open http://localhost:8000
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rigor.audit import SAMPLE_PAPER, audit_text
from rigor.ingest import load_text

app = FastAPI(title="Rigor", description="AI research-integrity referee")

STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class AuditIn(BaseModel):
    text: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/sample")
def sample() -> dict:
    return {"text": SAMPLE_PAPER}


@app.post("/api/audit")
def api_audit(body: AuditIn) -> JSONResponse:
    result = audit_text(body.text).to_dict()
    result["source"] = "pasted text"
    return JSONResponse(result)


@app.post("/api/audit/pdf")
async def api_audit_pdf(file: UploadFile = File(...)) -> JSONResponse:
    data = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or ".pdf").suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    text = load_text(tmp_path)
    result = audit_text(text).to_dict()
    result["source"] = file.filename
    return JSONResponse(result)
