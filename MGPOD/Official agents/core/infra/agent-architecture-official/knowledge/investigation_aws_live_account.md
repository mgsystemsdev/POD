# Investigation — AWS Live Account (Infra)

Run this in any coding agent (Cursor, Claude Code, Codex, etc.). Read-only. Reports facts only — feeds the Infra GPT.

```
AWS account context: [profile / region, or "default"]

Inspect this AWS account and report what is ACTUALLY running and costing money right now. STRICTLY read-only. Purpose: I'm learning AWS and spin up resources to experiment — the biggest risk is forgetting something running and getting billed.

Hard rules — READ CAREFULLY:
- ONLY read-only commands (aws ... describe-*, list-*, get-*, Cost Explorer reads).
- NEVER run anything that creates, changes, starts, stops, or deletes — no run-*, create-*, delete-*, terminate-*, modify-*, mutating put-*. If one seems needed, STOP and say so.
- Do not modify any file, commit, push, or change git state.
- If a value (especially cost) can't be confirmed, write "unknown, verify in the AWS console." NEVER guess a dollar amount.
- Check the named region AND flag that resources can hide in OTHER regions.

Report under these headings.

1. ACCOUNT & SCOPE
   - Which account/profile and region (sts get-caller-identity, configured region).
   - State clearly: covers ONLY this region unless checked otherwise — beginners leave things running in forgotten regions; flag this.

2. WHAT'S RUNNING RIGHT NOW (bill drivers)
   For each, list what exists and whether it bills while idle. "none found" if none.
   - EC2 instances (running vs stopped — stopped still bills for storage)
   - RDS / databases (bill hourly even unused — flag loudly)
   - NAT gateways (hourly + per GB — classic forgotten cost; flag loudly)
   - Load balancers (hourly)
   - Elastic IPs allocated but NOT attached (bill when unattached — flag)
   - EBS volumes not attached (storage cost — flag)
   - Anything else billable (EKS, ElastiCache, OpenSearch, etc.)

3. STORAGE & DATA
   - S3 buckets (names, rough size).
   - RDS/EBS snapshots left behind (persist and bill after source is gone — classic leftover).
   - Anything holding data a teardown might miss.

4. COST SNAPSHOT (best-effort, never guess)
   - Month-to-date spend if Cost Explorer is accessible.
   - Top services by cost.
   - Anything billing that looks like a forgotten experiment.
   - If cost data isn't accessible, say so and point me to Billing — don't invent numbers.

5. WHO/WHAT CREATED IT (Terraform vs manual)
   - Resources tagged Terraform-managed vs created by hand?
   - Flag MANUAL/untracked resources — terraform destroy will NOT clean these; I'd remove them myself.

6. SECURITY QUICK-LOOK (flag, don't fix)
   - Any S3 bucket publicly readable/writable? Flag, don't change.
   - Any security group open to 0.0.0.0/0 on SSH 22 or DB ports? Flag, don't change.
   - Access keys that look long-unused (note only).

7. RISKS & WHAT NEEDS ME
   - The "you're paying for this right now" list, plainest terms.
   - Likely-forgotten leftovers to consider tearing down.
   - Anything I must remove by hand (not Terraform-managed).
   - Anything I can't see from here (other regions, no billing access) to check myself.

Output as a plain list under these headings. Facts only. Do not change, stop, start, or delete anything.
```
