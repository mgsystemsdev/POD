from __future__ import annotations

import os
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class ToolReport:
    name: str
    available: bool
    detail: str


def _env_override() -> dict[str, bool] | None:
    raw = os.environ.get("DMRB_AGENT_TOOLS")
    if not raw:
        return None
    out: dict[str, bool] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if part.endswith("=0") or part.lower() == "false":
            out[part.split("=", 1)[0].strip()] = False
        elif part.endswith("=1") or part.lower() == "true":
            out[part.split("=", 1)[0].strip()] = True
        else:
            out[part] = True
    return out


def check_bash() -> ToolReport:
    if shutil.which("bash"):
        return ToolReport("Bash", True, "bash on PATH")
    return ToolReport("Bash", False, "bash not found; use Read/Grep only")


def check_web_fetch() -> ToolReport:
    override = _env_override()
    if override and "WebFetch" in override:
        ok = override["WebFetch"]
        return ToolReport("WebFetch", ok, "DMRB_AGENT_TOOLS override")
    try:
        urllib.request.urlopen("https://example.com", timeout=3)
        return ToolReport("WebFetch", True, "network fetch to example.com succeeded")
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return ToolReport("WebFetch", False, f"fetch failed: {e!s}")


def check_web_search() -> ToolReport:
    override = _env_override()
    if override and "WebSearch" in override:
        ok = override["WebSearch"]
        return ToolReport("WebSearch", ok, "DMRB_AGENT_TOOLS override")
    # No portable WebSearch without Claude Code or external API.
    return ToolReport(
        "WebSearch",
        False,
        "not available from Python orchestrator; use repo docs + Grep or set DMRB_AGENT_TOOLS=WebSearch=1 if your session has it",
    )


def assess_tools(preferred: list[str]) -> tuple[list[ToolReport], list[str]]:
    """Returns reports and a fallback strategy summary."""
    checks = {
        "Bash": check_bash,
        "WebFetch": check_web_fetch,
        "WebSearch": check_web_search,
    }
    reports: list[ToolReport] = []
    fallbacks: list[str] = []
    for name in preferred:
        fn = checks.get(name)
        if fn:
            r = fn()
            reports.append(r)
            if not r.available:
                fallbacks.append(f"{name}: {r.detail}")
    return reports, fallbacks


def resolve_tool_strategy(
    preferred: list[str], fallback: list[str]
) -> dict[str, object]:
    reports, failed = assess_tools([x for x in preferred if x in ("Bash", "WebFetch", "WebSearch")])
    use_network = any(r.name == "WebFetch" and r.available for r in reports)
    use_search = any(r.name == "WebSearch" and r.available for r in reports)
    strategy = {
        "effective_tools": [r.name for r in reports if r.available]
        + [t for t in preferred if t not in ("WebFetch", "WebSearch", "Bash")],
        "use_web_fetch": use_network,
        "use_web_search": use_search,
        "fallback_notes": failed,
        "read_grep_glob_always": True,
    }
    # Always allow read-only repo tools in Claude; orchestrator only validates what it can.
    if not use_search and "WebSearch" in preferred:
        strategy["fallback_notes"] = list(strategy["fallback_notes"]) + [
            "WebSearch unavailable → confine to AGENTS.md, CLAUDE.md, memory/, and Grep."
        ]
    if not use_network and "WebFetch" in preferred:
        strategy["fallback_notes"] = list(strategy["fallback_notes"]) + [
            "WebFetch unavailable → use local docs only."
        ]
    return strategy


def smoke_subprocess_bash() -> bool:
    try:
        subprocess.run(
            ["bash", "-c", "exit 0"],
            check=True,
            capture_output=True,
            timeout=5,
        )
        return True
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        return False
