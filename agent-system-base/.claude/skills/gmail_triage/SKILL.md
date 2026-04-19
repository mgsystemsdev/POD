---
name: gmail_triage
version: "1.0.0"
description: >
  Gmail inbox triage and review skill. Use when you want to review what the gmail_triage
  worker classified, approve or reject staged draft replies, configure triage rules, or
  manually run a triage session. Triggers on: "check my email", "review inbox", "what's
  in my email", "triage my gmail", "approve email drafts", "review email drafts",
  "what got labeled", "check gmail", "email catchup". Also trigger when the user wants
  to see what the overnight triage did or adjust how emails are categorized.
allowed-tools: Read, Bash
---

# Gmail Triage

The `gmail_triage.py` worker runs automatically (every 3 hours when enabled via cron)
and classifies incoming email. This skill helps you review its output and manage drafts.

---

## Four Categories

| Category | Meaning | Worker Action |
|----------|---------|---------------|
| `URGENT` | Needs response today; time-sensitive or from key contact | Creates draft reply |
| `NEEDS_REPLY` | Needs response but not urgent | Creates draft reply |
| `FYI` | Informational; no reply needed | Labels and archives |
| `JUNK` | Promotional, automated, or irrelevant | Labels for deletion |

---

## Reviewing Worker Output

The worker logs to `~/agents/agent-services/logs/gmail_triage.log`.
State is stored in `~/agents/agent-services/state/emails_processed.json`.

To see what the worker triaged:
```bash
tail -50 ~/agents/agent-services/logs/gmail_triage.log
```

To see draft replies staged (awaiting your review):
- Open Gmail
- Go to Drafts
- Drafts created by the worker are prefixed with `[TRIAGE]`

---

## Reviewing and Approving Drafts

1. Open Gmail Drafts
2. For each `[TRIAGE]` draft:
   - Read the original email
   - Read the staged reply
   - **Approve**: edit if needed, remove `[TRIAGE]` prefix, send when ready
   - **Reject**: delete the draft
3. The worker NEVER auto-sends. Every draft requires your explicit send action.

---

## Manual Triage Session

To manually run a triage session (requires Gmail credentials in `~/agents/agent-services/.env`):
```bash
cd ~/agents/agent-services && python3 workers/gmail_triage.py
```

Add `--dry-run` to see what would happen without writing any drafts or labels.

---

## Configuring Triage Rules

Triage rules are in the worker's prompt, not in a config file (v1).
To change how emails are classified:
1. Open `~/agents/agent-services/workers/gmail_triage.py`
2. Find the classification prompt (look for `URGENT`, `NEEDS_REPLY`, `FYI`, `JUNK`)
3. Edit the criteria — be specific about senders, subject patterns, keywords

Common customizations:
- Add specific senders to always mark URGENT
- Add domains to always mark JUNK
- Adjust what counts as "time-sensitive"

---

## Enabling the Cron Worker

The gmail_triage cron is disabled by default in `~/agents/agent-services/install.sh`.
To enable:
1. Set `GMAIL_CREDENTIALS_PATH` in `~/agents/agent-services/.env`
2. Run `python3 ~/agents/agent-services/workers/gmail_triage.py --dry-run` to verify auth works
3. Edit `~/agents/agent-services/install.sh` — uncomment the gmail_triage cron line
4. Run `bash ~/agents/agent-services/install.sh`

---

## Credentials Setup

Gmail OAuth requires a one-time setup:
1. Go to Google Cloud Console → create a project → enable Gmail API
2. Create OAuth 2.0 credentials (Desktop App type)
3. Download `credentials.json`
4. Set `GMAIL_CREDENTIALS_PATH=~/path/to/credentials.json` in `.env`
5. Run the worker once — it will open a browser for OAuth approval
6. Token is cached at `GMAIL_TOKEN_PATH` for subsequent runs
