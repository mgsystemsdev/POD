# Investigation — Terraform Config & State (Infra)

Run this in any coding agent (Cursor, Claude Code, Codex, etc.). Read-only. Reports facts only — feeds the Infra GPT.

```
Repository / Terraform directory: [the path]

Inspect this Terraform setup and report facts only. STRICTLY read-only audit feeding a planning conversation.

Hard rules — READ CAREFULLY:
- You may ONLY run read-only commands: terraform validate, terraform fmt -check, terraform state list, terraform show, terraform providers, terraform plan (plan changes nothing).
- NEVER run: terraform apply, destroy, import, state mv/rm, taint, or ANY cloud CLI command that creates/changes/deletes resources. If one seems needed, STOP and say so.
- Do not modify any file, .tfstate, or .tfvars. Do not commit, push, or change git state.
- If a fact can't be determined, write "unknown." NEVER guess cost or what a resource does — say "unknown, verify before applying."

Report under these headings. Quote exact lines where asked.

1. WHAT THIS IS
   - Real Terraform? Which provider(s) (AWS, GCP, Azure, other)? Quote the provider block.
   - One sentence: what infrastructure is this meant to create?
   - Tied to a specific app/repo, or standalone infra?

2. TARGET HOST CONTEXT
   - Provisions AWS/another real cloud, or local/learning only?
   - If AWS: which region(s)? Quote it.
   - Any sign the app also runs on Railway or elsewhere today (so we don't assume this replaces a working deploy)?

3. CURRENT STATE
   - State file location (local vs remote backend like S3)? Quote the backend block, or "local state."
   - terraform state list — what does Terraform believe exists? List, or "nothing provisioned yet."
   - State empty, or populated with real resources?

4. WHAT A PLAN WOULD DO (run terraform plan)
   - The summary line ("X to add, Y to change, Z to destroy").
   - Plain-language list of what would be CREATED.
   - Plain-language list of what would be CHANGED.
   - LOUDLY and separately: what would be DESTROYED — name each; flag as data-loss/irreversibility risk.
   - If plan can't run (missing vars/credentials/init), report exactly why — don't force it.

5. COST EXPOSURE (best-effort, never guess)
   - Which resources cost money while running? Plain terms (RDS, NAT gateway, load balancer, EC2).
   - Which are effectively free/pay-per-use.
   - Anything that costs money even when idle? Flag it — the "left it running" trap.
   - Unclear cost → "cost unknown, verify before apply." Never assert a cost you're unsure of.

6. TEARDOWN
   - Would terraform destroy cleanly remove everything, or do resources persist (manual things, deletion-protected buckets, snapshots)?
   - Note anything that survives a destroy and keeps costing money.

7. CREDENTIALS & INPUTS REQUIRED
   - What credentials/auth this needs to run. Quote where referenced.
   - Required variables with no default — what I must supply.
   - Any secret hardcoded in a .tf/.tfvars (file + line), or "none found."
   - Any committed .tfstate/.tfvars with real values — yes/no, which.

8. RISKS & BLOCKERS
   - Anything destructive, costly, or irreversible in the current plan.
   - Anything requiring a human decision before apply.
   - State/backend risks (local state that could be lost, no locking).
   - Anything that would create billable infra for what's only a learning exercise.

Output as a plain list under these headings. Facts only. Do not apply or change anything.
```
