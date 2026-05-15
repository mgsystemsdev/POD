# Invariants (high confidence only)

Format: **Invariant — Why required — What breaks without it**

1. **Section B complete and schema-stable** — Spec Gate ingests it as the primary baton; gaps force block or invention — **Invalid or missing `tasks.json`; execution drift.**

2. **Every REQ implies verification modality** — Evidence must be deducible from Output + Done when — **Subjective “it works”; false PASS or blocked commits.**

3. **Architect output enables description-only execution** — Task `description` is the execution prompt — **Stop-and-ask loops; rework.**

4. **`requirement_ref` stability** — REQ-IDs stable per scope unless PRD versioned — **Traceability and dashboard sync break.**

5. **Persistence REQs need explicit model + migration intent in Section A** — Infra-first ordering — **Wrong migrations; bad task order.**

6. **Confirmed assumption only substitute for fact** — No silent fill — **Contract violations downstream.**

7. **One task → one requirement** — Traceability and scope control — **Untestable bundles; audit failure.**

8. **Architect = validator, not designer of implementation** — Boundaries separate Spec Gate / Operator / Execution — **Tactics leak into PRD; Gate confusion.**

9. **Persistence must succeed or emit is blocked** — Dashboard write is part of emit; a silent failure leaves Spec Gate without the baton — **Spec Gate reads stale or missing blueprint; execution drift.**

10. **project_id required before emit** — All blueprint writes need a resolved project_id — **Write to wrong project or 404 error breaks traceability.**

11. **No duplicate version on PUT** — Version field must be incremented from the last GET — **Data overwrite; version history collapse; Spec Gate reads wrong version.**
