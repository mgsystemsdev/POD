# Investigation — Repository Analysis (Loop)

Run this in any coding agent (Cursor, Claude Code, Codex, etc.). Read-only. Reports facts only — feeds the Loop GPT.

```
Repository: [the repo path]

Inspect this repository and report facts only. Read-only audit feeding a tool that generates an execution prompt.

Hard rules:
- Do not modify, create, or delete any file.
- Do not commit, push, or change git state.
- Do not recommend, plan, or implement anything.
- If a fact cannot be determined, write "unknown" — never guess.

Report under these headings, in order. Quote exact lines where asked.

1. WHAT THIS IS
   - Language, framework, what the app does in one sentence.
   - Entry point file and the exact command that starts it.

2. RUNTIME
   - Language/runtime version and where it's declared (file + line), or "unpinned".
   - Package manager and whether a lockfile exists.
   - Any build step.

3. HOW IT RUNS & IS REACHED
   - Does it read its port from an env var? Quote the line, or state the hardcoded port.
   - Binds to all interfaces (0.0.0.0) or only localhost?
   - What URL/path returns a successful response when running (health route, "/", etc.)? Quote it, or "unknown".

4. DATA
   - Database type, if any, and how it connects (quote the line).
   - Files read/written on local disk that must persist (exact paths), or "none".
   - Migration or seed scripts.

5. CONFIG & SECRETS
   - Every env var the app reads, where used, default.
   - For each: REQUIRED to start/run, or optional?
   - Any hardcoded secret/key/password in source (file + line), or "none found".

6. GIT & HISTORY
   - Current branch; working tree clean?
   - Uncommitted changes (list files).
   - Any committed .env or secret file (yes/no, which).
   - How does the deploy host get new code — from git push, or a CLI upload? (So we know if updating it requires a push.)

7. DEPLOYMENT & INFRA FILES
   - Where it deploys today and the evidence (railway.toml, Procfile, vercel.json, etc.).
   - Whether the currently deployed version matches the current code, or looks stale.
   - Which exist: Dockerfile, .dockerignore, docker-compose.yml, .env.example, Makefile, README, CI/CD workflows.
   - What any existing CI/CD pipeline does.

Output as a plain list under these seven headings. Facts only.
```
