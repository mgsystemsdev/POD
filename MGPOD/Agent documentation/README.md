# MGPOD documentation

Map of core roles and tiered topics. The [Master document](tier-1/master-document.md) entry points here as the canonical index.

## Agent prompts (repository)

- [Official agents README](../Official%20agents/README.md) — canonical prompts under `Official agents/`; archived material under `Legacy agents/`
- [GPT layer index](tier-1/gpt-layer-index.md) — entrypoint path for every pipeline and auxiliary GPT role
- [Vertical data flow (Mermaid)](../Official%20agents/core/architect/vertical-data-flow.md) — full 7-layer stack diagram

## Core roles (narrative)

Role-specific narrative pages may live in tier docs and legacy archives. **System prompts** for ChatGPT load from `Official agents/` (see GPT layer index).

## Tier 1 — Specs, registry, framework

- [Master document](tier-1/master-document.md)
- [This framework outlines](tier-1/this-framework-outlines.md)
- [The Configuration Format system](tier-1/configuration-format.md)
- [The Registry (projects_index.json)](tier-1/registry-projects-index.md)
- [Version Control (Layer 7)](tier-1/version-control-layer-7.md)
- [The Execution Spec Gate](execution-spec-gate/execution-spec-gate.md)

## Tier 2 — Platform, data plane, integrations

- [The Dashboard and FastAPI backend](tier-2/dashboard-fastapi-backend.md)
- [The SQLite Database (Operational Mirror)](tier-2/sqlite-operational-mirror.md)
- [The Sync Layer](tier-2/sync-layer.md)
- [The Workers layer (Operational Bridge)](tier-2/workers-operational-bridge.md)
- [The Anthropic API Key](tier-2/anthropic-api-key.md)
- [The three versions (V1, V2, and V3) of the Personal D](tier-2/personal-d-versions-v1-v2-v3.md)

## Tier 3 — Environment and tooling

- [Operating System](tier-3/operating-system.md)
- [4 ChatGPT agents (thinking layer)](tier-3/chatgpt-agents-thinking-layer.md)
- [Blueprint](tier-3/blueprint.md)

## Tier 4 — CLI agents

Terminal execution tools. Each page uses structured Markdown (`##` sections, tables, lists) like tiers 1–3.

- [Claude Code](tier-4/claude-code.md)
- [Codex](tier-4/codex.md)
- [Gemini](tier-4/gemini.md) (Gemini CLI)
- [Kiro](tier-4/kiro.md)
- [OpenCode](tier-4/opencode.md)
