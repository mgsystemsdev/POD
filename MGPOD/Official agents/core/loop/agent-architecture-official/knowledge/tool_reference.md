# LOOP — TOOL REFERENCE

The Loop knowledge doc holds the *rules*; this doc holds the *facts* about each tool, so the GPT can write accurate execution prompts and translate handoffs correctly.

Path: `Official agents/core/loop/agent-architecture-official/knowledge/tool_reference.md`

---

# GITHUB

**What it is.** Version control and the home for the code. It is the safety net for everything downstream — every later step (deps, env, Docker, deploy, CI/CD) changes files, and GitHub is what lets the user see diffs and roll back.

**Why it's first.** It's the cheapest, lowest-risk step, and it surfaces the worst hazard early: secrets already committed to history.

**Key facts.**
- A secret committed to git history is exposed even after it's deleted from the latest commit — it lives in history. The fix is rotation (replace the secret), not just removal.
- `.gitignore` should cover `.env`, secret files, build artifacts, and dependency folders (`node_modules`, `.venv`).
- Branch protection rules can block force-pushes and direct commits to `main`; a restructuring change can violate them.
- Renaming or moving files can break existing clone URLs, deploy hooks, or import paths.

**Common Loop work.** Add `.gitignore`, README, license; clean a messy repo; confirm no secrets in history; set up a sane branch structure.

---

# DEPENDENCY & LOCKFILE MANAGEMENT

**What it is.** Pinning exact versions and producing a lockfile so builds are reproducible.

**Key facts.**
- A lockfile (`package-lock.json`, `poetry.lock`, `requirements.txt` with pins) records exact versions; without it, two installs can differ.
- Use the lockfile-respecting install command — `npm ci` (not `npm install`) for Node, a locked install for Python — so the build matches the lockfile exactly.
- Removing a dependency can break an import or a feature that relied on it indirectly (a transitive dependency).
- Native/binary dependencies (things compiled for a specific OS or runtime) can break when the container or runtime changes.

**Common Loop work.** Generate a missing lockfile, pin floating versions, remove unused packages — each checked against the closed blocker list first.

---

# ENV VARS & SECRETS

**What it is.** Configuration and secrets the app reads at runtime, kept out of the code.

**Key facts.**
- A local `.env` file does **not** travel to a hosting platform. Required vars must be set in the platform's own settings (e.g. Railway → service → Variables). This is the single most common deploy confusion.
- `.env.example` documents required vars with placeholder values and is safe to commit; the real `.env` is never committed.
- A var the app silently needs with no default will fail at runtime in a way that's hard to diagnose — these must be surfaced.
- Some secrets are needed at build time, others at runtime; they're set in different places.
- A committed `.env` in history is an exposed-secret incident — rotate, don't just delete.

**Common Loop work.** Find hardcoded secrets, build `.env.example`, document required vs optional vars and where each is used.

---

# DOCKER

**What it is.** Containerization — pinning *how* the app runs: runtime version, dependencies, port, start command, into a reproducible image.

**Why it sits where it does.** Containerize the plain app before adding fragile layers (deploy, auth). A known-good container makes everything above it easier to debug.

**Key facts.**
- The app must read its port from an env var (e.g. `process.env.PORT`) — a hardcoded port won't bind correctly in a container.
- The app must bind to all interfaces (`0.0.0.0`), not just `localhost`, or the container won't be reachable.
- The DB connection must come from a connection-string env var (e.g. `DATABASE_URL`), not be hardcoded.
- Local-disk state (uploads, SQLite files, on-disk sessions) vanishes when a container restarts — flag it.
- Use a standard slim base image matching the detected runtime (Node slim, Python slim); pin the version.
- Use the lockfile install command in the build; run as non-root where practical; add a simple healthcheck.
- A multi-service local setup (app + Postgres) uses Compose, with the local DB behind a profile and a named volume.

**Files Docker work touches.** `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `.env.example`, `Makefile`, README (Docker section) — and nothing else without confirmation.

---

# RAILWAY

**What it is.** A managed deploy platform for smaller, quick-to-the-internet apps. Deploys from git; provides managed Postgres and HTTPS.

**Key facts.**
- Railway deploys from a git push (or `railway up`). New code only reaches it by deploying — a config change against an old deploy fails confusingly.
- Env vars are set in the platform dashboard (service → Variables), **not** read from a local `.env`. Vars set on the wrong service (e.g. on Postgres instead of the app) silently don't reach the app.
- Variables only take effect on the next deploy — set them, then redeploy.
- It injects `DATABASE_URL` when a Postgres plugin is attached.
- It terminates TLS, so the app should trust the proxy and treat the platform as production for secure-cookie behavior even if `NODE_ENV` is unset.
- It can detect the platform via an env marker (e.g. `RAILWAY_ENVIRONMENT`).
- The CLI supports machine-readable output (`--json`) for reading real platform state instead of guessing, and `--yes`/`-y` to skip confirmations — which must **not** be used on destructive commands (`down`, `delete`).

**Common Loop work (Railway review).** Confirm the start command matches the entry point, the DB is attached, required vars are present, the port is routable, and the deployed version isn't stale.

---

# CI/CD (GITHUB ACTIONS)

**What it is.** Automating build, test, and deploy so they run on push/merge instead of by hand.

**Why it's near the end.** You can only automate a path that already works manually — so it comes after the app deploys cleanly by hand.

**Key facts.**
- Secrets a pipeline needs (deploy tokens, API keys) live in the repo/host secret store, never in the workflow file.
- An existing pipeline can be silently overwritten — check before writing one.
- A deploy step can fire automatically on merge; that's a real consequence to flag, not assume.
- If there are no tests or build steps yet, there may be nothing to wire up.
- Hosted runners and external services a pipeline triggers can cost money.

**Common Loop work.** Wire a build/test workflow; add a deploy step (gated so it doesn't fire unexpectedly); keep runner cost in view.

---

# NODE.JS / PYTHON PACKAGING

**What it is.** How the app's runtime and dependencies are declared so any environment can reproduce them.

**Key facts.**
- **Node** — `package.json` declares scripts and deps; `engines` can pin the Node version; `package-lock.json` locks exact versions; `npm ci` installs from the lock.
- **Python** — runtime pinned via the environment/base image; deps via `requirements.txt` (pinned) or `poetry.lock`/`pyproject.toml`; a virtual environment isolates them.
- Pin the runtime version explicitly somewhere the build reads, or it's "unpinned" and can drift.
- A build step (transpile, bundle, compile) must be reproducible from the repo, or the deploy can't reproduce it.
