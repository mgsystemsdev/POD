# Database Specialist — failure modes

| Mistake | Why it breaks PDOS | Avoid |
|--------|---------------------|--------|
| Hidden denorm vs schema tension | Conflicting contracts | **Decisions** with Schema Specialist |
| Fake workload numbers | Wrong index advice | **Open Questions** or label assumptions |
| Procedural migration checklist | Task smuggling | Declarative invariants |
