#!/usr/bin/env bash
# stop_dashboard.sh — Stop the Task Dashboard server
# Usage: bash ~/agents/agent-services/system/scripts/stop_dashboard.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/../dashboard.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "Dashboard is not running (no PID file found)."
  exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  sleep 1
  if kill -0 "$PID" 2>/dev/null; then
    echo "Process $PID still running — sending SIGKILL."
    kill -9 "$PID"
  fi
  rm -f "$PID_FILE"
  echo "✅ Dashboard stopped (PID $PID)."
else
  echo "Process $PID not found — cleaning up stale PID file."
  rm -f "$PID_FILE"
fi
