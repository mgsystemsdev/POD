#!/bin/bash
set -euo pipefail

SERVICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing agent-services cron jobs..."
echo ""

EXISTING=$(crontab -l 2>/dev/null || true)

read -r -d '' NEW_CRONS << 'CRON_EOF' || true
# --- agent-services managed crons ---
# Task worker: every 2 hours, pick highest-priority pending task and execute
0 */2 * * * cd ~/agents/agent-services && python3 workers/task_worker.py >> logs/task_worker.log 2>&1
# Decision reviewer: daily at 8:00 AM
0 8 * * * cd ~/agents/agent-services && python3 workers/decision_reviewer.py >> logs/decision_reviewer.log 2>&1
# Gmail triage: every 3 hours (activate after credentials are configured)
# 0 */3 * * * cd ~/agents/agent-services && python3 workers/gmail_triage.py >> logs/gmail_triage.log 2>&1
# --- end agent-services ---
CRON_EOF

if echo "$EXISTING" | grep -q "agent-services managed crons"; then
    echo "Agent-services crons already installed. To reinstall, remove the block from crontab -e first."
    exit 0
fi

echo "$EXISTING"$'\n'"$NEW_CRONS" | crontab -

echo "Installed cron jobs:"
echo "  - task_worker.py      every 2 hours"
echo "  - decision_reviewer.py daily at 8 AM"
echo "  - gmail_triage.py     DISABLED (uncomment after Gmail credentials are set)"
echo ""
echo "View with: crontab -l"
echo "Edit with: crontab -e"
echo ""
echo "API keys: edit ~/agents/agent-services/.env"
