#!/bin/bash
# install_crons.sh — Wire autonomous worker cron jobs
# Run once: bash ~/agents/agent-system-base/install_crons.sh
#
# Workers run from ~/agents/agent-services/ (runtime layer).
# ANTHROPIC_API_KEY is sourced at cron runtime from .env — no reinstall needed on key rotation.
# gmail_triage is DISABLED until Gmail OAuth credentials are configured.

set -euo pipefail

SERVICES=~/agents/agent-services
ENV_FILE="$SERVICES/.env"
LOGS="$SERVICES/logs"

# Ensure logs directory exists
mkdir -p "$LOGS"

# Guard — do not double-install
EXISTING=$(crontab -l 2>/dev/null || true)
if echo "$EXISTING" | grep -q "autonomous-workers"; then
  echo "Cron jobs already installed."
  echo "To reinstall: remove the '# --- autonomous-workers ---' block from crontab -e, then re-run."
  exit 0
fi

# Verify .env exists (ANTHROPIC_API_KEY must be in it for task_worker)
if [ ! -f "$ENV_FILE" ]; then
  echo "⚠️  WARNING: $ENV_FILE not found."
  echo "   task_worker.py requires ANTHROPIC_API_KEY — add it to $ENV_FILE before crons run."
fi

NEW_CRONS=$(cat <<CRONEOF

# --- autonomous-workers ---
# task_worker — every hour (sources .env for ANTHROPIC_API_KEY at runtime)
0 * * * * bash -c 'set -a; source $ENV_FILE; set +a; cd $SERVICES && python3 workers/task_worker.py' >> $LOGS/task_worker.log 2>&1

# decision_reviewer — daily at 9am (no API key required)
0 9 * * * cd $SERVICES && python3 workers/decision_reviewer.py >> $LOGS/decision_reviewer.log 2>&1

# gmail_triage — DISABLED: scaffold only (authenticate() exits immediately)
# Activate after Gmail OAuth credentials are configured in $ENV_FILE:
# GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH must be set.
# 30 * * * * bash -c 'set -a; source $ENV_FILE; set +a; cd $SERVICES && python3 workers/gmail_triage.py' >> $LOGS/gmail_triage.log 2>&1
# --- end autonomous-workers ---
CRONEOF
)

printf '%s\n%s\n' "$EXISTING" "$NEW_CRONS" | crontab -

echo "✅ Cron jobs installed:"
echo "   task_worker       — 0 * * * *   (every hour)"
echo "   decision_reviewer — 0 9 * * *   (daily 9am)"
echo "   gmail_triage      — DISABLED    (scaffold, needs Gmail OAuth)"
echo ""
echo "Logs → $LOGS/"
echo ""
echo "Current crontab:"
crontab -l
