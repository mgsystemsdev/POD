# Investigation — Auth (Security)

Run this in any coding agent (Cursor, Claude Code, Codex, etc.). Read-only. Reports facts only — feeds the Security GPT.

```
Repository: [the repo path]

Inspect this repository and report the full picture of authentication, authorization, administration, and the app's shape — including lifecycle edges (how the first admin comes to exist, how recovery works, what data already exists). Read-only audit feeding a security design conversation.

Hard rules:
- Do not modify, create, or delete any file.
- Do not commit, push, or change git state.
- Do not recommend, plan, or implement anything.
- If something cannot be determined, write "unknown" — never guess.

Report under these headings. Quote exact lines where asked.

1. WHAT THIS APP IS
   - Language, framework, what it does in one sentence.
   - Frontend type (server-rendered, SPA, static, none) and where it lives.
   - Backend/API separate from frontend, or one combined server?
   - Rough size (routes or pages).

2. AUTH PRESENT? — Yes / No / Partial. One sentence on what exists.

3. CREDENTIALS
   - Email+password login? Quote where handled.
   - If passwords exist: how stored/hashed? Quote the line. "plaintext" if none.
   - Any password length/format rules already enforced? Quote them.
   - Any shared/single password (e.g. Basic Auth)? Quote it.

4. EXTERNAL PROVIDERS — Google/Apple/other OAuth? Which, where configured?

5. IDENTITY STORAGE
   - Users table or user records? Quote the schema.
   - Or delegated to a provider? "no user storage found" if neither.

6. SESSIONS / TOKENS
   - How a login persists (server session, JWT/token, cookie, none)? Quote it.
   - Any logout or session-expiry logic? Quote it, or "none found."

7. AUTHORIZATION — roles/permissions beyond logged-in/not? Quote where enforced, or "none found."

8. ADMINISTRATION
   - Any admin area/route/console today? Frontend or backend? Quote where.
   - Any separate entry point, internal tool, or script to manage the app?
   - "no admin surface found" if none.

9. BOOTSTRAP & RECOVERY (lifecycle edges)
   - How does the FIRST admin/user come to exist? Seed script, env var, manual insert, first-run/setup screen, hardcoded, unknown? Quote evidence.
   - Any password reset/recovery flow? Quote where, or "none found."
   - Does recovery depend on email sending? Note any email service/config.

10. EXISTING DATA
   - Does it store user-owned/generated data? Quote schema/tables.
   - If auth were added, what existing data would need an owner or be affected?

11. TRANSPORT — HTTPS/TLS assumptions, secure-cookie flags, host/proxy config? Quote it, or "unknown."

12. SECRETS & CONFIG
   - Every auth/admin env var read, where used.
   - Any auth/admin secret hardcoded in source (file + line), or "none found."
   - Any committed .env or secret file (yes/no, which).

13. WHAT TOUCHES SECURITY
   - Files involved in auth/admin/bootstrap today (or "none").
   - Database/schema/migration files, so we know what's at risk.

14. DEPLOY & STALE-CODE CHECK
   - How does the deploy host receive new code (git push + redeploy, CLI upload)?
   - Does the currently deployed version appear to match the current code, or stale? (A stale deploy makes correct keys/passwords fail confusingly.)

Output as a plain list under these fourteen headings. Facts only.
```
