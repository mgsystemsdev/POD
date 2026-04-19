#!/usr/bin/env python3
"""
Daily decision reviewer — scans ~/.claude/decisions.csv, flags rows whose
review_date has arrived, and logs flagged items.

State: ~/.claude/decisions.csv (read/write)
Logs:  ~/agents/agent-services/logs/decision_reviewer.log
"""

import csv
import sys
from datetime import date
from pathlib import Path

CSV_PATH = Path.home() / ".claude" / "decisions.csv"
LOG_DIR = Path.home() / "agents" / "agent-services" / "logs"
LOG_PATH = LOG_DIR / "decision_reviewer.log"

FIELDS = ["date", "decision", "reasoning", "expected_outcome", "review_date", "status"]


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = date.today().isoformat()
    line = f"{ts}  {msg}\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="")


def main() -> None:
    if not CSV_PATH.exists():
        log(f"No decisions.csv at {CSV_PATH}")
        sys.exit(0)

    today = date.today()
    flagged = 0
    rows: list[dict] = []

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            review_str = row.get("review_date", "").strip()
            status = row.get("status", "").strip()
            if review_str and status not in ("REVIEW DUE", "reviewed", "closed"):
                try:
                    review_date = date.fromisoformat(review_str)
                    if review_date <= today:
                        row["status"] = "REVIEW DUE"
                        flagged += 1
                        log(f"FLAGGED: {row.get('decision', '?')[:80]} (due {review_str})")
                except ValueError:
                    pass
            rows.append(row)

    if flagged:
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        log(f"Total flagged: {flagged} decision(s)")
    else:
        log("No new reviews due today.")


if __name__ == "__main__":
    main()
