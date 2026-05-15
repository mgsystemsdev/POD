# Failure modes

| Failure | Cause | Prevention |
|---------|--------|------------|
| Spec Gate returns to Architect | Incomplete 5/5; vague Output/Failure; Section B incomplete | Contract test + ten-section Section B |
| Execution stop (“unclear”) | Thin `description` | [translation_rules.md](translation_rules.md) |
| Verification FAIL / subjective pass | Done when not observable | Output defines proof modality |
| Wrong context path | Legacy path | `.claude/context/project.md` only |
| Contradictory tasks | Unresolved REQ/model conflict | [validation.md](validation.md) before emit |
| Scope explosion in one task | Bundled REQs | Split REQs; hard MVP boundary |
| Silent production bugs | Generic Failure path | State + retry + visibility |
| User bypasses PRD | Emit with known gap | **BLOCK**; cite Gate/verification |
| Schema drift | `schema.json` ≠ Section A | Regenerate from final Section A |
| Missing infra ordering | DDL implicit | Infrastructure-first in Section A |
| 4xx from dashboard API | Bad input (missing project_id, malformed body) | BLOCK emit; fix input per `persistence_contract.md` |
| 5xx from dashboard API | Server error on write | Retry once; fallback to text emit with user warning |
| 401 Unauthorized | Missing or invalid X-API-Key | BLOCK; instruct user to verify ChatGPT Actions auth |
| 404 project not found | Wrong project_id or project not created | BLOCK; GET `/api/projects`; ask user to confirm project |
| Empty `GET /api/projects` but user insists data exists | Wrong API key/env, DB reset, or projects never persisted | Run GET again when asked; distinguish **401** (auth) vs **200 []** (empty registry); do not claim “already checked” instead of calling the API |
| User string mismatch vs name | Fuzzy match fail treated as empty | Separate “N projects, no match for ‘...’” from “0 projects” (true empty); fuzzy match on `name` and `slug` (substring OK) |
| Model claims “no API access” | Hallucinated refusal | Call `GET /api/projects` first; never skip Action unless a prior Action in the same turn returned a hard 4xx/5xx |
| Hello skips registry fetch | Ignored session start | **GET /api/projects** on Turn 1 (including "hello"); do not ask "what project?" until list/zero is shown |
| “Running GET…” then no tool body | Narration without tool call | **Tool-first**; emit Action immediately; retry once; BLOCK only on real 4xx/5xx after retry |
| Version conflict on PUT | Stale blueprint_id or version | GET blueprint again; re-attempt with current version + 1 |
