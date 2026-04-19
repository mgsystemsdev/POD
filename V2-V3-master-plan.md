# ⚡ V2 → V3 — Claude Code Master Plan

## What this is

A complete Claude Code execution plan to take the agent system from v1 (local only) to v2 (ngrok + authenticated API) to v3 (Raspberry Pi 24/7 server). Run each phase as a separate Claude Code session. Human approval required between phases.

---

## CONTEXT — What exists today

- **Blueprint repo:** `~/agents/agent-system-base`
- **Runtime:** `~/agents/agent-services`
- **Database:** `~/agents/agent-system-base/system/db/database.sqlite`
- **Server:** `~/agents/agent-system-base/system/dashboard/server.py`
- **CLI:** `agents` alias pointing to `agentctl.sh`
- **API runs at:** `http://127.0.0.1:8765`
- **Current auth state:** No API key enforcement (returns 200 without key)
- **ngrok:** Installed, authenticated, v3.22.1
- **Git state:** Dirty — 19 modified files, unchecked

---

## INVARIANTS — Must never break

1. Dashboard loads at `http://127.0.0.1:8765` and shows correct data
2. `GET /api/projects` returns all 5 projects as valid JSON
3. Import worker writes to SQLite correctly — no silent failures
4. `agents push --dry-run` completes with no errors
5. All API routes under `/api/*` keep their current behavior — only authentication changes

---

## PHASE 1 — API Key Security (Block 1)

**Goal:** Lock the API so only requests with the correct key get through.
**Time:** 30 minutes
**Risk:** Wrong middleware placement breaks the dashboard before tests run.

### Claude Code prompt — paste this exactly:

```
Read ~/agents/agent-system-base/system/dashboard/server.py completely.
Do not modify anything yet.

First, map and return:
1. Exact line where FastAPI app is created
2. Any existing middleware code (add_middleware, APIKeyMiddleware, X-API-Key)
3. Any line reading AGENTS_API_KEY from environment
4. The route serving GET / (root, serves index.html)
5. Any .env loading (load_dotenv or similar)

Then make exactly these changes:

Change 1 — Add to ~/agents/agent-services/.env:
AGENTS_API_KEY=[generate with: python3 -c "import secrets; print(secrets.token_hex(32))"]

Change 2 — In server.py, immediately after the imports
and BEFORE app = FastAPI(...), add:

import os
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/api/"):
            api_key = os.environ.get("AGENTS_API_KEY", "")
            if api_key:
                request_key = request.headers.get("X-API-Key", "")
                if request_key != api_key:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid API key"}
                    )
        return await call_next(request)

Change 3 — Immediately after app = FastAPI(...) add:
app.add_middleware(APIKeyMiddleware)

Change 4 — Add dotenv loading if not present:
from dotenv import load_dotenv
load_dotenv()

Then:
1. Sync: bash ~/agents/agent-system-base/init.sh ~/agents/agent-system-base
2. Restart dashboard: agents dashboard
3. Run verification:
   curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8765/api/projects
   Expected: 401
   curl -sS -o /dev/null -w "%{http_code}" -H "X-API-Key: [your-key]" http://127.0.0.1:8765/api/projects
   Expected: 200
4. Commit:
   cd ~/agents/agent-system-base
   git add system/dashboard/server.py
   git commit -m "feat: add API key middleware for v2 security"

Done when: 401 without key. 200 with key. Committed.
If either test fails — stop and report. Do not continue.
```

### Phase 1 done when:
- [ ] 401 without key confirmed
- [ ] 200 with correct key confirmed
- [ ] Middleware committed to git

---

## PHASE 2 — Knowledge Files (Block 2)

**Goal:** Find, package, and verify all agent knowledge files on disk.
**Time:** 1 hour
**Note:** Uploading to ChatGPT is manual — Claude Code handles the disk side only.

### Claude Code prompt — paste this exactly:

```
Search everywhere under ~/agents/agent-system-base/ and ~/.claude/
for these exact filenames. Show full path for each found.
Confirm missing for each not found.

Files to find:
phase_guide.md
artifact_templates.md
questioning_patterns.md
schema.json
tasks_schema.json
scope_guide.md
principles.md
tools_guide.md
decision_framework.md
stack_guide.md
swarm_patterns.md
terminal_hygiene.md
user_profile.md
requirement_contract.md
system_contract.md

Then:
1. Create directory: mkdir -p ~/agents/agent-system-base/docs
2. Copy every found file into docs/ keeping original filename
3. For user_profile.md — also check ~/.claude/memory/user.md
   and copy it if found
4. List what is now in docs/ with file sizes
5. List what is still missing (not found anywhere on disk)

Do not create or generate any missing files.
Report only what exists and what is missing.

Commit what was found:
   cd ~/agents/agent-system-base
   git add docs/
   git commit -m "docs: package agent knowledge files into docs/"
```

### After Claude Code runs — manual step:

For each file confirmed missing — retrieve from Claude conversation outputs and save to `~/agents/agent-system-base/docs/` manually.

Then upload to ChatGPT agents:

| Agent | Required files |
|---|---|
| The Architect | requirement_contract.md, system_contract.md, user_profile.md, phase_guide.md, artifact_templates.md, questioning_patterns.md, schema.json |
| Execution Spec Gate | requirement_contract.md, system_contract.md, user_profile.md, tasks_schema.json, scope_guide.md |
| The Strategist | requirement_contract.md, system_contract.md, user_profile.md, principles.md, tools_guide.md, decision_framework.md |
| The Operator | requirement_contract.md, system_contract.md, user_profile.md, stack_guide.md, swarm_patterns.md, terminal_hygiene.md |

### Phase 2 done when:
- [ ] All files found or manually retrieved
- [ ] All files in docs/ and committed
- [ ] The Architect — all files uploaded to ChatGPT
- [ ] Execution Spec Gate — all files uploaded
- [ ] The Strategist — all files uploaded
- [ ] The Operator — all files uploaded

---

## PHASE 3 — Complete One Full V1 Cycle (Block 3)

**Goal:** Prove the pipeline works end to end. One real task from design to merged PR.
**Time:** 2 to 3 hours
**This phase is mostly manual — Claude Code assists with git only.**

### Pick one task from the dashboard that is pending and clearly scoped.

The Operator drives this. Run The Operator in ChatGPT.
Paste Section B from the project's project.md as the opening message.

### Claude Code assists with — paste this when you reach STEP 2:

```
I am executing a task through the Operator protocol.
Task: [paste task title and description]
Project: [paste project name]

I have just run the implementation in Cursor.
Now run git diff and show me:
1. Every file that was changed
2. The exact changes in each file
3. Whether any file was changed that should not have been
4. Confirm the changes match the task description

Do not commit anything yet. Report only.
```

### The full 10-step checklist:

- [ ] STEP 0: Branch created — `git checkout -b feature/[task-name]`
- [ ] STEP 1: Prompt built and run in Claude Code or Cursor
- [ ] STEP 2: `git diff` checked — nothing unexpected touched
- [ ] STEP 3: Verified against requirement contract — all 5 elements
- [ ] STEP 4: Translated in plain English — no code blocks
- [ ] STEP 5: Reviewed and accepted
- [ ] STEP 6: `git add -A && git commit -m "[task-id]: description"`
- [ ] STEP 7: Pushed, PR opened on GitHub UI, reviewed, merged
- [ ] STEP 7: Branch deleted on GitHub, main pulled
- [ ] STEP 8: session.md written with real entry and committed
- [ ] Task marked done in dashboard

### Phase 3 done when:
- [ ] session.md has real filled entry (not the template)
- [ ] GitHub shows one merged PR
- [ ] Dashboard shows task status = done

---

## PHASE 4 — Git Hygiene

**Goal:** Clean baseline commit before any structure changes.
**Time:** 20 minutes

### Claude Code prompt — paste this exactly:

```
In ~/agents/agent-system-base:

1. Read the current .gitignore
2. Add these lines if not already present:
   .DS_Store
   system/db/*.sqlite
   *.pyc
   __pycache__/
   logs/
   state/
   .env
   *.bak
   system/dashboard/ui/
   *.db-shm
   *.db-wal

3. Run git status and show me everything that is:
   - Modified tracked files
   - Untracked files that should be committed
   - Untracked files that should be ignored

4. Commit all files that belong in the repo:
   git add -A
   git commit -m "feat: v1.0 complete - pre-v2 baseline"

5. Run git log --oneline -5 and show output
6. Run git status and confirm clean working tree

Done when: git status shows nothing to commit.
```

### Phase 4 done when:
- [ ] .gitignore updated
- [ ] Clean baseline commit on main
- [ ] `git status` shows nothing to commit

---

## PHASE 5 — V2 Launch (ngrok)

**Goal:** Expose the authenticated API through ngrok and connect ChatGPT agents.
**Time:** 1 hour
**Prerequisite:** Phases 1 through 4 all complete.

### Claude Code prompt — paste this exactly:

```
In ~/agents/agent-system-base/system/dashboard/server.py:

1. Verify the APIKeyMiddleware is correctly placed and wired
2. Confirm AGENTS_API_KEY loads from environment
3. Add this new route if it does not exist:

@app.get("/api/projects/by-slug/{slug}")
def get_project_by_slug(slug: str):
    project = project_service.get_project_by_slug(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

4. Check if get_project_by_slug exists in project_service.py
   If not, add it:
   def get_project_by_slug(slug: str):
       with connect() as conn:
           row = conn.execute(
               "SELECT * FROM projects WHERE slug = ?", (slug,)
           ).fetchone()
           return dict(row) if row else None

5. Sync to agent-services:
   bash ~/agents/agent-system-base/init.sh ~/agents/agent-system-base

6. Restart dashboard and verify:
   agents dashboard
   curl -sS -H "X-API-Key: [key]" http://127.0.0.1:8765/api/projects/by-slug/dmrb
   Expected: DMRB project JSON

7. Commit:
   git add system/dashboard/server.py system/services/project_service.py
   git commit -m "feat: add by-slug route for v2 agent API calls"
```

### Then manual steps:

**Start the tunnel:**
```
ngrok http 8765
```
Copy the public URL — example: `https://abc123.ngrok-free.app`

**Test from terminal:**
```
curl -sS -H "X-API-Key: your-key" \
  https://abc123.ngrok-free.app/api/projects
```
Expected: your projects returned. If yes — tunnel is live and secure.

**Configure custom actions in each ChatGPT agent:**
Settings → Configure → Actions → Create new action
- Authentication: API Key, header `X-API-Key`, paste your key
- Server URL: your ngrok URL
- Start with The Operator

**Test The Operator end to end:**
Open The Operator in ChatGPT.
Ask it to read your latest session log.
It should call the API and return real data.

### Phase 5 done when:
- [ ] by-slug route working
- [ ] ngrok tunnel live
- [ ] curl through tunnel returns 200
- [ ] Custom actions in all 4 agents
- [ ] The Operator reads real data from database
- [ ] V2 confirmed live

---

## PHASE 6 — V3 Raspberry Pi Setup

**Goal:** Move the system from Mac to Raspberry Pi for 24/7 operation.
**Time:** One focused Saturday
**Prerequisite:** Pi purchased and arrived. V2 confirmed stable for at least one week.

### Step 1 — Flash the Pi

```
On your Mac:
1. Download Raspberry Pi Imager
2. Select: Ubuntu Server 24.04 LTS (64-bit)
3. Configure before flashing:
   - Hostname: agentpi
   - Username: miguel
   - WiFi: your network credentials
   - Enable SSH with your Mac's public key
4. Flash to SD card or SSD
5. Boot the Pi
```

### Step 2 — SSH in and install dependencies

```
ssh miguel@agentpi.local

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx curl
pip3 install fastapi uvicorn python-dotenv starlette --break-system-packages
```

### Step 3 — Deploy your system

```
On the Pi:
git clone https://github.com/your-username/agent-system-base.git \
  ~/agents/agent-system-base

mkdir -p ~/agents/agent-services
bash ~/agents/agent-system-base/init.sh ~/agents/agent-system-base

# Create .env
cat > ~/agents/agent-services/.env << EOF
AGENTS_API_KEY=same-key-as-your-mac
EOF
```

### Step 4 — Create systemd service

### Claude Code prompt for generating the service file:

```
Create a systemd service file for the agent dashboard.

File path: /etc/systemd/system/agent-dashboard.service

Requirements:
- Runs: python3 system/dashboard/server.py
- Working directory: /home/miguel/agents/agent-services
- User: miguel
- Loads .env from: /home/miguel/agents/agent-services/.env
- Restarts on failure with 5 second delay
- Starts after network is online
- Logs to journald

Also create the nginx config at:
/etc/nginx/sites-available/agent-dashboard

Requirements:
- Listens on port 80 (HTTP first, add HTTPS after)
- Proxies to localhost:8765
- Passes X-API-Key header through
- Sets appropriate proxy headers

After creating both files provide exact commands to:
1. Enable and start the systemd service
2. Enable the nginx site
3. Test the service is running
4. Test nginx is proxying correctly
```

### Step 5 — Point agents at the Pi

Replace your ngrok URL in all four ChatGPT agent custom actions with:
`http://agentpi.local` (local network only)
or your Pi's external IP if you set up port forwarding.

For true 24/7 access from anywhere:
- Get a free domain from DuckDNS
- Set up Let's Encrypt with Certbot
- Configure port forwarding on your router

### Phase 6 done when:
- [ ] Pi boots and SSH works
- [ ] System deployed and running on Pi
- [ ] Systemd service auto-starts on boot
- [ ] Dashboard accessible from Mac browser at Pi address
- [ ] All 4 agents pointing at Pi URL
- [ ] The Operator reads session log from Pi database
- [ ] Mac laptop can be closed and system still works
- [ ] V3 confirmed live

---

## EXECUTION ORDER SUMMARY

| Phase | What | Time | Gate |
|---|---|---|---|
| 1 | API key middleware | 30 min | 401/200 tests pass |
| 2 | Knowledge files | 1-2 hrs | All files in docs/, agents updated |
| 3 | Full V1 cycle | 2-3 hrs | Merged PR, filled session.md |
| 4 | Git hygiene | 20 min | Clean working tree |
| 5 | V2 ngrok launch | 1 hr | Agents read live data |
| 6 | V3 Pi setup | 1 day | Laptop closed, system runs |
| **Total** | | **~6-8 hrs + 1 day** | |

**Rule: Each phase gate must be verified before starting the next phase.**
**No exceptions. No partial credit.**
