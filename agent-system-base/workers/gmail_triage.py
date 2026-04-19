#!/usr/bin/env python3
"""
Gmail inbox triage — scans inbox, classifies emails into
URGENT / NEEDS_REPLY / FYI / JUNK, auto-labels, and drafts replies
for URGENT and NEEDS_REPLY. Never auto-sends.

Requires: Gmail API OAuth credentials in ~/agents/agent-services/.env
State:    ~/agents/agent-services/state/emails_processed.json
Logs:     ~/agents/agent-services/logs/gmail_triage.log

STATUS: SCAFFOLD — Gmail API integration not yet wired.
        Fill in authenticate() and the Gmail API calls when credentials are ready.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path.home() / "agents" / "agent-services" / "state"
STATE_PATH = STATE_DIR / "emails_processed.json"
LOG_DIR = Path.home() / "agents" / "agent-services" / "logs"
LOG_PATH = LOG_DIR / "gmail_triage.log"


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts}  {msg}\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="")


def load_processed() -> set[str]:
    if not STATE_PATH.exists():
        return set()
    with STATE_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("processed_ids", []))


def save_processed(ids: set[str]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump({"processed_ids": sorted(ids), "last_run": datetime.now(timezone.utc).isoformat()}, f, indent=2)


def authenticate():
    """
    TODO: Load OAuth credentials from ~/agents/agent-services/.env or credentials.json
    and return an authenticated Gmail API service object.

    Expected env vars in .env:
      GMAIL_CREDENTIALS_PATH=~/agents/agent-services/credentials.json
      GMAIL_TOKEN_PATH=~/agents/agent-services/state/gmail_token.json
    """
    log("ERROR: Gmail authentication not configured. Add credentials to ~/agents/agent-services/.env")
    sys.exit(1)


def fetch_new_emails(service, processed_ids: set[str]) -> list[dict]:
    """
    TODO: Use Gmail API to fetch unread inbox messages not in processed_ids.
    Return list of dicts with: id, subject, sender, body_preview, received_at
    """
    return []


def classify_email(email: dict) -> str:
    """
    TODO: Use Claude API to classify email into: URGENT / NEEDS_REPLY / FYI / JUNK
    Consider sender history, subject keywords, body content.
    """
    return "FYI"


def draft_reply(service, email: dict, category: str) -> None:
    """
    TODO: For URGENT and NEEDS_REPLY, use Claude API to generate a tone-matched
    draft reply (based on user's last 20 sent emails). Save as Gmail draft.
    Never send automatically.
    """
    pass


def apply_label(service, email_id: str, category: str) -> None:
    """
    TODO: Apply the corresponding Gmail label (URGENT, NEEDS_REPLY, FYI, JUNK).
    Create labels if they don't exist.
    """
    pass


def main() -> None:
    log("GMAIL_TRIAGE START")

    service = authenticate()
    processed = load_processed()

    emails = fetch_new_emails(service, processed)
    if not emails:
        log("No new emails. Exiting.")
        return

    log(f"Found {len(emails)} new email(s)")

    for email in emails:
        category = classify_email(email)
        apply_label(service, email["id"], category)

        if category in ("URGENT", "NEEDS_REPLY"):
            draft_reply(service, email, category)
            log(f"  {category}: {email.get('subject', '?')[:60]} — draft created")
        else:
            log(f"  {category}: {email.get('subject', '?')[:60]}")

        processed.add(email["id"])

    save_processed(processed)
    log(f"GMAIL_TRIAGE END — processed {len(emails)} email(s)")


if __name__ == "__main__":
    main()
