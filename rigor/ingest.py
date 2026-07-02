"""
Paper ingest - load plain text or extract text from a PDF.

Keeps Rigor usable on real papers, not just pasted snippets. The extracted text
is (optionally) capped so a very long paper doesn't blow up token usage; the
statistics almost always live in the Results section, well within the cap.
"""
from __future__ import annotations

from pathlib import Path

MAX_CHARS = 60_000


def _pdf_text(path: Path) -> str:
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24 exposes `pymupdf`
    except ImportError:
        import fitz  # older PyMuPDF
    doc = fitz.open(path)
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def load_text(path: str | Path, max_chars: int = MAX_CHARS) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    text = _pdf_text(p) if p.suffix.lower() == ".pdf" else p.read_text(encoding="utf-8")
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[...truncated for length...]"
    return text
