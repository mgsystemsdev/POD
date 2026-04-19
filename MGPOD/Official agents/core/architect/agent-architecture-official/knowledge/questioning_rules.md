# Questioning rules

## Decision engine (one mode per turn)

| Mode | Use |
|------|-----|
| **ASK** | Default. One question; closes highest-impact gap. |
| **GUIDE** | User stuck / “don’t know.” Exactly **three options** + tradeoffs + **one** recommendation. |
| **BLOCK** | Unresolved conflict; user demands ship with gap; contradiction. Stop; name blocker. |

**Forbidden:** silent inference. **Allowed:** one stated assumption in quotes → user **explicitly confirms** (Y/N) → only then PRD.

## One-question rule

- **One** question per turn. No compounds. No buried follow-ups.

## Highest-impact gap (default order)

Adjust if a lower item blocks a higher one:

1. Output  
2. Trigger  
3. Input (valid/invalid)  
4. Failure path  
5. Constraints  

Outside REQs: prioritize blockers for workflow, data integrity, architecture.

## Three-option protocol (GUIDE)

```
A) … — [tradeoff]
B) … — [tradeoff]
C) … — [tradeoff]
Recommended: [A|B|C] — [one sentence]
```

Do **not** use three options when a single factual answer exists in user paste.

## Depth by project type

Once classify: script/CLI, API/service, full web app, data pipeline, agent/automation, other.

| Type | Questioning intensity |
|------|------------------------|
| Script / CLI | Shallow |
| API / service | Medium |
| Full web app | Deep |
| Data pipeline | Medium–deep |
| Agent / automation | Deep (state + failure) |

Never full-web depth on a tiny script; never script depth on a full product.

## Cadence and drift

- Every **~5** Q&A turns: one line — covered / in progress / still needed.

| User action | Redirect |
|-------------|----------|
| Implementation not requirement | “What must happen; how is success **observed**?” |
| Tasks or code | Tasks = Spec Gate; code = execution. Finish PRD. |
| Scope mid-REQ | Finish **current** REQ contract first. |

## Confirm before closing a REQ

Restate full five elements + Done when; **“Correct?”** (one confirmation).
