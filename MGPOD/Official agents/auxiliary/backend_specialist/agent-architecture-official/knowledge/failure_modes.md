# Backend Specialist — failure modes

| Mistake | Why it breaks PDOS | Avoid |
|--------|---------------------|--------|
| Silent UI vs server state authority | Conflicting REQs later | **Decisions** / **Risks** explicit tension |
| Illustrative API without “non-normative” | Treated as contract | Label + Architect owns final |
| Procedural deploy/migrate steps | Task smuggling | Declarative **invariants** for migrations |
| Invented stack | False **Constraints** | **Open Questions** |
