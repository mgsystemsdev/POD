from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunResult:
    raw_text: str
    parsed: dict[str, Any] | None
    token_usage: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0})
    error: str | None = None
