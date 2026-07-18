"""
Thin Qwen (DashScope, OpenAI-compatible) client for Rigor.

The LLM's ONLY job in Rigor is reading messy paper prose and returning structured
data. All verdicts come from the deterministic engine in rigor/checks/. This file
is the sandbox around the model, nothing more.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
LLM_MODEL = os.getenv("QWEN_LLM_MODEL", "qwen-plus")
SEED = 7  # fixed seed + temperature 0 for reproducible extraction where supported

_usage_log = logging.getLogger("rigor.usage")


@dataclass
class Usage:
    """Process-level running token total, so cost is observable in the demo and in prod."""
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


USAGE = Usage()


def log_usage(resp, tag: str = "") -> None:
    """Accumulate and log the token usage from a chat-completions response."""
    u = getattr(resp, "usage", None)
    if u is None:
        return
    pt = getattr(u, "prompt_tokens", 0) or 0
    ct = getattr(u, "completion_tokens", 0) or 0
    USAGE.calls += 1
    USAGE.prompt_tokens += pt
    USAGE.completion_tokens += ct
    _usage_log.info(
        '{"event": "qwen_usage", "tag": "%s", "prompt_tokens": %d, "completion_tokens": %d, '
        '"cumulative_total": %d}', tag, pt, ct, USAGE.total_tokens)


def client() -> OpenAI:
    if not API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY not set - add it to your .env")
    # 60s timeout + up to 3 retries with exponential backoff (built into the SDK) so a
    # transient Qwen hiccup (429 / 5xx / network) does not crash the request. 60s (not
    # 30s) gives long, full-text papers room to finish extraction and claim analysis.
    return OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=60.0, max_retries=3)


def chat(messages: list[dict], model: str | None = None, temperature: float = 0.0) -> str:
    resp = client().chat.completions.create(
        model=model or LLM_MODEL,
        messages=messages,
        temperature=temperature,
        seed=SEED,
    )
    log_usage(resp, tag="chat")
    return resp.choices[0].message.content or ""


def strip_dashes(s: str) -> str:
    """House style: no em dashes anywhere Rigor renders, including model-written prose.
    The LLM sometimes emits em/en dashes in its explanations; normalise them before the
    text ever reaches the report. Em dash becomes a comma; en dash becomes a hyphen."""
    if not s:
        return s
    s = s.replace(" - ", " - ")  # keep spaced hyphens as-is
    s = s.replace(" — ", ", ").replace("—", ", ")   # em dash
    s = s.replace(" – ", ", ").replace("–", "-")     # en dash
    return s.replace("  ", " ").replace(" ,", ",")


def ping() -> str:
    """Quick connectivity check: returns the model's reply to a trivial prompt."""
    return chat([{"role": "user", "content": "Reply with exactly: pong"}])
