# The Anthropic API Key

## System purpose

The Anthropic API key authorizes **Layer 4 (execution)** and **Layer 5 (automation)**—e.g. `/swarm` loops and `task_worker.py`. It provides a **billed API channel** for high-reasoning work outside browser OAuth subscription limits.

> Do **not** commit real keys to the repo. Store them in environment or secret managers only.

---

## Inputs

| Input | Description |
| :--- | :--- |
| **Source** | [Anthropic Console](https://console.anthropic.com/) (or your org’s key issuance flow). |
| **Format** | String prefix `sk-ant-…`. |
| **Storage** | e.g. `export ANTHROPIC_API_KEY=…` in `~/.zshrc`; project `.env` (gitignored). |
| **Account limits** | TPM/RPM per tier (Build, Scale, etc.). |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **Authorized model calls** | Opus / Sonnet-class models for execution. |
| **Billed usage** | Per-token cost in Console; optional `/cost`-style reporting. |
| **Agent outputs** | Plans, code, verification logs from autonomous runs. |

---

## Key entities

| Entity | Role |
| :--- | :--- |
| **`ANTHROPIC_API_KEY`** | Primary auth token for API calls. |
| **Workspace** | Console workspace tracking aggregate usage. |
| **Usage stats** | Input/output tokens, thinking tokens, cache hits. |
| **Rate limits** | TPM/RPM caps per org/user tier. |

---

## Workflow

1. **Generate** key in Anthropic Console (project-scoped if available).
2. **Scaffold** — `agents init` / project setup expects the key in the environment.
3. **Inject** — `export ANTHROPIC_API_KEY=…` in shell profile; `.env` for workers/cron.
4. **Precedence** — Claude Code may prefer API key over OAuth in non-interactive (`-p`) flows when key is set.
5. **Autonomous runs** — `task_worker.py` reads from `.env` for queued tasks.
6. **Monitoring** — Optional reporting to Dashboard Health / cost views.

---

## Constraints

- **No hardcoding** — Never embed the key in source (e.g. `db.py`, services).
- **Gitignore** — `.env`, local profile snippets with secrets must stay out of version control.
- **One key per session context** — Avoid ambiguous billing from mixed keys.
- **Approval gates** — Dangerous actions still require explicit approval unless running with dangerous skip flags (use rarely).

---

## Edge cases

| Case | Behavior |
| :--- | :--- |
| **Key missing** | Swarm / workers may halt or fail closed; Health should show problem. |
| **Invalid / revoked** | 401/403 → block further execution attempts; surface error. |
| **Disabled org** | Old org key may error even if personal subscription exists. |
| **Thinking token overrun** | Long “thinking” may hit `MAX_THINKING_TOKENS`; handle gracefully. |

---

## State handling

- **Persistence** — Shell env + project `.env` (e.g. under `~/agents/agent-services/` or your layout).
- **Dashboard** — Health shows key **present/absent**, never the secret string.
- **Precedence** — `/status` (or equivalent) can show API key vs OAuth.

---

## Failure handling

- **`agents doctor`** — Verifies key presence/shape where implemented.
- **Dashboard** — Red alert if worker cannot find the key.
- **Halt on 401** — Exit with clear code instead of infinite retry on the same task.

---

## Examples

- **Setup** — User creates key, appends `export ANTHROPIC_API_KEY=sk-ant-…` to `~/.zshrc`, opens new shell → `echo $ANTHROPIC_API_KEY` shows value; Claude terminal may show API-key auth path.
- **Cron without env** — `task_worker` run without sourcing profile → log `ANTHROPIC_API_KEY not set`; task stays pending; failed run recorded.
