"""Build system + user prompts from a task row and ``context_loader`` context dict."""

from __future__ import annotations

from typing import Any


def build_prompts(
    task: dict[str, Any],
    ctx: dict[str, Any],
    *,
    rules: str | None = None,
) -> tuple[str, str]:
    """
    Deterministic sections: project block (system), task block (user).

    ``ctx`` must be the dict returned by ``context_loader.load_project_context``.
    ``rules`` is optional condensed AGENTS.md content from ``context_loader.load_rules_context``.
    """
    project = ctx.get("project") or {}
    root_exists = ctx.get("root_exists")
    root_path = project.get("root_path")

    system_lines = [
        "You are a coding assistant executing a single queued task from a project task system.",
        "Produce a concise, actionable response. Prefer concrete steps or code when appropriate.",
        "",
        "## Project",
        f"- name: {project.get('name', '')}",
        f"- slug: {project.get('slug', '')}",
        f"- root_path: {root_path!r}",
        f"- root_exists: {root_exists}",
    ]

    if rules:
        system_lines += ["", "## Behavioral Rules", rules]

    pmd = ctx.get("project_md")
    if pmd:
        system_lines += ["", "## Project blueprint (.claude/project.md)", pmd[:4000]]

    slog = ctx.get("session_log")
    if isinstance(slog, dict) and slog:
        system_lines += [
            "",
            "## Latest session log",
            f"- session_date: {slog.get('session_date', '')}",
            f"- notes: {slog.get('notes') or '(none)'}",
            f"- next_task: {slog.get('next_task') or '(none)'}",
        ]

    rdec = ctx.get("recent_decisions") or []
    if rdec:
        system_lines += ["", "## Recent decisions (project)"]
        for d in rdec:
            system_lines.append(f"- {d.get('title', '')}: {(d.get('content') or '')[:200]}")

    lbs = ctx.get("latest_blueprints") or []
    if lbs:
        b0 = lbs[0]
        system_lines += [
            "",
            "## Latest blueprint",
            f"- title: {b0.get('title', '')}",
            f"- type: {b0.get('type', '')}",
            (b0.get("content") or "")[:3000],
        ]

    user_lines = [
        "## Task",
        f"- id: {task.get('id')}",
        f"- title: {task.get('title', '')}",
        f"- description: {task.get('description') or '(none)'}",
        f"- type: {task.get('type')}",
        f"- priority: {task.get('priority')}",
        f"- source: {task.get('source')}",
        f"- status: {task.get('status')}",
        "",
        "Respond to this task now.",
    ]

    return "\n".join(system_lines), "\n".join(user_lines)
