from __future__ import annotations

import json
import re
from typing import Any


_FENCE = re.compile(r"^```(?:json)?\s*", re.MULTILINE)
_FENCE_END = re.compile(r"\s*```\s*$", re.MULTILINE)


def strip_markdown_fences(text: str) -> str:
    t = text.strip()
    t = _FENCE.sub("", t, count=1)
    t = _FENCE_END.sub("", t, count=1)
    return t.strip()


def extract_json_object(text: str) -> Any:
    """Parse first JSON object from text (after fence strip)."""
    t = strip_markdown_fences(text)
    start = t.find("{")
    if start < 0:
        raise ValueError("no JSON object start")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                blob = t[start : i + 1]
                return json.loads(blob)
    raise ValueError("unbalanced braces in JSON object")


def parse_model_json(text: str) -> dict[str, Any]:
    obj = extract_json_object(text)
    if not isinstance(obj, dict):
        raise ValueError("root must be object")
    return obj
