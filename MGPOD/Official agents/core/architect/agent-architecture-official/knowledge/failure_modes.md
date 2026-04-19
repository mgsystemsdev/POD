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
