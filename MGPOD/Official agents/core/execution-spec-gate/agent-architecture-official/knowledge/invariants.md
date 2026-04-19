# Inferred invariants (Spec Gate)

Only high-confidence pipeline invariants. Format: **Invariant — Why — What breaks**

1. **Section B complete and ordered** — Spec Gate ingests machine handoff; gaps force invention or BLOCK churn — **Invalid or empty `tasks.json`; rework with Architect.**

2. **Every REQ implies a verification modality** — Observable Output + Done when are the only lawful source for `success_criteria` — **Subjective PASS/FAIL; blocked commits or false confidence.**

3. **`description`-only execution** — Operator/tools treat `description` as the prompt — **Stop-and-ask; session waste if template incomplete.**

4. **`requirement_ref` stability** — REQ-IDs are the traceability key — **Orphan dashboard rows; audit trail breaks if IDs drift mid-scope.**

5. **Persistence changes need explicit story** — Infra-first ordering depends on stated model/migration intent — **Migrations out of order; broken DB state if Gate guesses DDL.**

6. **No silent assumptions** — PDOS forbids guessed facts in contracts — **Downstream violates real constraints; legal/security/ops risk.**

7. **DAG task graph** — Parallel eligibility and merge order depend on acyclic `depends_on` — **Deadlock interpretation; impossible execution order if cycles.**

8. **Failure path is mandatory for tasks** — `failure_behavior` is legally sourced only from Failure path — **Undefined error handling; production incidents if invented.**
