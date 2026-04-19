from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from orchestrator.models import SCHEMA_VERSION
from orchestrator.runner.base import RunResult
from orchestrator.runner.json_extract import parse_model_json


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

_CLAUDE_DIR = Path.home() / ".claude"


def _load_skill_content(agent_name: str) -> str:
    """
    Load SKILL.md body for the given agent, if the agent has a 'skill' field
    in its agents/*.json definition. Returns empty string if not found.
    """
    agent_def_path = _CLAUDE_DIR / "agents" / f"{agent_name}.json"
    if not agent_def_path.exists():
        return ""
    try:
        agent_def = json.loads(agent_def_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""

    skill_name = agent_def.get("skill", "").strip()
    if not skill_name:
        return ""

    skill_path = _CLAUDE_DIR / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        return ""

    content = skill_path.read_text(encoding="utf-8")
    # Strip YAML frontmatter (--- ... ---) before injecting
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].strip()
    return content


def _build_system_prompt(skill_content: str = "") -> str:
    base = (
        "You are a structured output generator. Respond with exactly one JSON object, no markdown, "
        "no prose before or after. The JSON must include keys: agent, goal, status (success|failure), "
        "inputs, actions, outputs, decisions, artifacts, next_steps, meta. "
        f"meta must include run_id, step_id, schema_version ({SCHEMA_VERSION!r}), agent (same as top-level agent), "
        "timestamp (ISO-8601 UTC with Z suffix). "
        "For agent 'research' on success include non-empty sources_checked: string[]. "
        "For agent 'context' on success include non-empty docs_used: string[]. "
        "For agent 'create' on success include non-empty artifacts. "
        "On failure set status failure and non-empty decisions."
    )
    if skill_content:
        return base + "\n\n## Skill Instructions\n" + skill_content
    return base


def _build_user_prompt(context_path: Path, agent_name: str, extra: str) -> str:
    ctx = context_path.read_text(encoding="utf-8")
    return (
        f"Agent name: {agent_name}\n"
        f"Read this context JSON and produce the required output JSON object:\n\n{ctx}\n"
        f"{extra}"
    )


class AnthropicApiRunner:
    def __init__(self) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        self.model = os.environ.get("DMRB_ANTHROPIC_MODEL", "claude-sonnet-4-20250514").strip()
        self.max_tokens = int(os.environ.get("DMRB_ANTHROPIC_MAX_TOKENS", "8192"))

    def run_step(
        self,
        *,
        context_path: Path,
        agent_name: str,
        log_path: Path,
        retry_json_prompt: bool = True,
    ) -> RunResult:
        if not self.api_key:
            return RunResult(
                raw_text="",
                parsed=None,
                error="ANTHROPIC_API_KEY is not set",
            )

        skill_content = _load_skill_content(agent_name)

        def one_call(user_extra: str) -> tuple[str, dict[str, int]]:
            user = _build_user_prompt(context_path, agent_name, user_extra)
            body = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": _build_system_prompt(skill_content),
                "messages": [{"role": "user", "content": user}],
            }
            req = urllib.request.Request(
                ANTHROPIC_URL,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "content-type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            text_parts: list[str] = []
            for block in data.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(str(block.get("text", "")))
            text = "\n".join(text_parts)
            usage = data.get("usage") or {}
            tok = {
                "input": int(usage.get("input_tokens", 0) or 0),
                "output": int(usage.get("output_tokens", 0) or 0),
            }
            return text, tok

        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_chunks: list[str] = []
        total_tok = {"input": 0, "output": 0}
        last_err: str | None = None

        attempts = 2 if retry_json_prompt else 1
        for attempt in range(attempts):
            extra = ""
            if attempt == 1:
                extra = (
                    "\n\nYour previous reply was not valid JSON. Reply with ONLY one JSON object, "
                    "no markdown fences, matching the schema described in the system message."
                )
            try:
                text, tok = one_call(extra)
                total_tok["input"] += tok["input"]
                total_tok["output"] += tok["output"]
                log_chunks.append(f"--- attempt {attempt + 1} raw ---\n{text}")
                parsed = parse_model_json(text)
                with log_path.open("w", encoding="utf-8") as f:
                    f.write("\n\n".join(log_chunks))
                return RunResult(raw_text=text, parsed=parsed, token_usage=dict(total_tok), error=None)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")[:8000]
                last_err = f"HTTP {e.code}: {body}"
                log_chunks.append(last_err)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_err = str(e)
                log_chunks.append(last_err)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                last_err = str(e)
                log_chunks.append(f"[json] {last_err}")

        with log_path.open("w", encoding="utf-8") as f:
            f.write("\n\n".join(log_chunks))

        return RunResult(
            raw_text="\n\n".join(log_chunks),
            parsed=None,
            token_usage=dict(total_tok),
            error=last_err or "unknown",
        )
