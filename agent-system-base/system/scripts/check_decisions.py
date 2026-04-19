#!/usr/bin/env python3
"""
Daily checker: flags any decision whose review_date has arrived.
Run from any directory — uses the path of this script to locate decisions.csv.
"""

import csv
import sys
from datetime import date
from pathlib import Path

CSV_PATH = Path.home() / ".claude" / "decisions.csv"

FIELDS = ["date", "decision", "reasoning", "expected_outcome", "review_date", "status"]


def main() -> None:
    if not CSV_PATH.exists():
        print(f"[check_decisions] No decisions.csv found at {CSV_PATH}")
        sys.exit(0)

    today = date.today()
    flagged = 0
    rows = []

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            review_str = row.get("review_date", "").strip()
            status = row.get("status", "").strip()
            if review_str and status != "REVIEW DUE":
                try:
                    review_date = date.fromisoformat(review_str)
                    if review_date <= today:
                        row["status"] = "REVIEW DUE"
                        flagged += 1
                except ValueError:
                    pass  # malformed date — leave row untouched
            rows.append(row)

    if flagged:
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"[check_decisions] {flagged} decision(s) flagged as REVIEW DUE.")
    else:
        print("[check_decisions] No new reviews due today.")


if __name__ == "__main__":
    main()
