"""
Thin Qwen (DashScope, OpenAI-compatible) client for Rigor.

The LLM's ONLY job in Rigor is reading messy paper prose and returning structured
data. All verdicts come from the deterministic engine in rigor/checks/. This file
is the sandbox around the model, nothing more.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
LLM_MODEL = os.getenv("QWEN_LLM_MODEL", "qwen-plus")


def client() -> OpenAI:
    if not API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY not set - add it to your .env")
    # 30s timeout + up to 3 retries with exponential backoff (built into the SDK)
    # so a transient Qwen hiccup (429 / 5xx / network) does not crash the request.
    return OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=30.0, max_retries=3)


def chat(messages: list[dict], model: str | None = None, temperature: float = 0.0) -> str:
    resp = client().chat.completions.create(
        model=model or LLM_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def ping() -> str:
    """Quick connectivity check: returns the model's reply to a trivial prompt."""
    return chat([{"role": "user", "content": "Reply with exactly: pong"}])
