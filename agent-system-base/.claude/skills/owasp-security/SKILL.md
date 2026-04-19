---
name: owasp-security
version: "1.0.0"
description: >
  OWASP Top 10:2025 + ASVS 5.0 + Agentic AI
  security audit with language-specific code
  review checklists. Deeper and more structured
  than the security-reviewer agent. Use for full
  security audits of any codebase, before any
  feature ships that handles auth, payments,
  user data, or file uploads. Trigger: "security
  audit", "owasp check", "full security review",
  "is this secure", "audit for vulnerabilities"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

# OWASP Security Audit

Full security audit. CRITICAL/HIGH/MEDIUM/LOW.
Nothing ships with a CRITICAL unresolved.

## OWASP Top 10:2025

A01 — Broken Access Control
- Every endpoint checks authorization
- IDOR vulnerabilities (can user A access
  user B's data by changing an ID?)
- For DMRB: RLS policies on all tables
- Missing function-level access control
- CORS misconfiguration

A02 — Cryptographic Failures
- Passwords: bcrypt or argon2id, never plain
- Sensitive data encrypted at rest
- HTTPS enforced, no HTTP fallback
- Weak hashing algorithms (MD5, SHA1) absent
- API keys not in source code or logs

A03 — Injection
- SQL: parameterized queries everywhere
- No f-string SQL construction
- Command injection via subprocess
- XSS: user input sanitized before render
- For DMRB: all psycopg3 queries use %s

A04 — Insecure Design
- Threat modeling done?
- Rate limiting on auth endpoints
- Account lockout after failed attempts
- Sensitive operations require re-auth

A05 — Security Misconfiguration
- Debug mode OFF in production
- Default credentials changed
- Unnecessary features disabled
- CORS: specific origins, not wildcard
- CSP headers present

A06 — Vulnerable Components
- Dependencies have known CVEs?
- requirements.txt / package.json pinned?
- Outdated packages with security patches?

A07 — Auth Failures
- Session tokens: secure, httponly, samesite
- Token expiry enforced
- Logout invalidates server-side session
- MFA available for admin accounts
- For DMRB: Supabase Auth used, not custom

A08 — Data Integrity Failures
- Unsigned data not trusted
- CI/CD pipeline integrity
- Deserialization of untrusted data

A09 — Logging + Monitoring Failures
- Auth failures logged
- No sensitive data in logs (passwords, tokens)
- Log injection prevented
- Audit trail for admin actions

A10 — SSRF
- User-supplied URLs validated
- Internal network not reachable via user input
- Allowlist for external requests

## Agentic AI Security (ASI01-ASI10)
For any AI-powered feature in the codebase:
- Prompt injection defense present
- Tool permission boundaries enforced
- Agent output sanitized before use
- Rate limiting on AI endpoints
- No sensitive data in prompts sent to LLMs

## Python-Specific Checks
- No eval() or exec() on user input
- No pickle.loads() on untrusted data
- No os.system() with user input
- subprocess calls use list args, not shell=True
- Temp files use tempfile module

## SQL-Specific Checks (DMRB focus)
- Zero f-string SQL queries
- All queries use %s parameterization
- No raw user input in ORDER BY clauses
- Stored procedures validated

## Failure Modes

**Codebase is large** — Audit by surface area, not line by line. Start with:
auth endpoints → data endpoints → file upload → external integrations.
Flag what was NOT audited explicitly.

**No auth layer visible** — Don't assume it's elsewhere. Flag as CRITICAL:
"Auth layer not found in scope. Either it's in a separate service (confirm)
or this is a CRITICAL gap."

**False positive risk** — If a finding requires context to confirm (e.g., "this
SQL looks parameterized but I can't see the caller"), flag as MEDIUM with
"Needs verification" rather than CRITICAL. Don't over-alarm.

## Output Format
CRITICAL: [finding] at [file:line] — [fix]
HIGH:     [finding] at [file:line] — [fix]
MEDIUM:   [finding] at [file:line] — [fix]
LOW:      [finding] at [file:line] — [fix]

Summary: X critical, Y high, Z medium, W low
Verdict: PASS / WARN / BLOCK

BLOCK if any CRITICAL found.
Nothing ships with CRITICAL unresolved.
