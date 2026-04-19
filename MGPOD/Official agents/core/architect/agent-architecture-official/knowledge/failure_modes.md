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
| Version conflict on PUT | Stale blueprint_id or version | GET blueprint again; re-attempt with current version + 1 |
