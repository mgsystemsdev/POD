"""Anthropic Messages API — no database imports."""

from __future__ import annotations

import os
import random
import time

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_TIMEOUT_S = 120.0
_DEFAULT_MAX_RETRIES = 3


def _require_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return key


def _default_model() -> str:
    return os.environ.get("ANTHROPIC_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw, 10)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def run_messages(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    timeout_s: float | None = None,
) -> str:
    """
    Call Claude Messages API; return assistant plain text.

    Uses the ``anthropic`` package (``pip install anthropic``).
    """
    _require_api_key()
    max_t = max_tokens if max_tokens is not None else _int_env("CLAUDE_MAX_TOKENS", _DEFAULT_MAX_TOKENS)
    timeout = timeout_s if timeout_s is not None else _float_env("CLAUDE_TIMEOUT_S", _DEFAULT_TIMEOUT_S)
    m = model if model is not None else _default_model()

    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=timeout)
    msg = client.messages.create(
        model=m,
        max_tokens=max_t,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts: list[str] = []
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts)


def _retryable(exc: BaseException) -> bool:
    try:
        from anthropic import APIConnectionError, APITimeoutError
        from anthropic import APIStatusError
    except ImportError:
        return False

    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError):
        code = getattr(exc, "status_code", None)
        if code is None:
            return False
        if code == 429:
            return True
        return code >= 500
    return False


def run_messages_with_retry(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    timeout_s: float | None = None,
    max_retries: int | None = None,
) -> str:
    """
    Same as ``run_messages`` with limited retries, backoff + jitter on transient errors.
    """
    n = max_retries if max_retries is not None else _int_env("CLAUDE_MAX_RETRIES", _DEFAULT_MAX_RETRIES)
    n = max(1, n)
    last: BaseException | None = None
    for attempt in range(n):
        try:
            return run_messages(
                system,
                user,
                model=model,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
            )
        except Exception as e:
            if isinstance(e, RuntimeError) and "ANTHROPIC_API_KEY" in str(e):
                raise
            last = e
            if not _retryable(e):
                raise
            if attempt == n - 1:
                raise last
            delay = (2**attempt) + random.uniform(0, 1.0)
            time.sleep(delay)
    raise AssertionError("unreachable")
