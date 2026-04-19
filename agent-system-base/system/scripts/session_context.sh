#!/bin/bash
# Session context bootstrap — prints active project and task queue summary.
# Called by ~/.claude/hooks/load-memory.sh once per session.
# Always exits 0. Never outputs errors. Never blocks.

DB="$HOME/agents/agent-system-base/system/db/database.sqlite"
AGENTS_MD="$HOME/agents/agent-system-base/AGENTS.md"

# Require sqlite3 CLI
if ! command -v sqlite3 &>/dev/null; then
  exit 0
fi

if [ ! -f "$DB" ]; then
  exit 0
fi

# ── Detect active project from $PWD ──────────────────────────────────────────
# Match $PWD against projects.root_path (exact or parent prefix match).
ACTIVE_PROJECT=$(sqlite3 "$DB" "
  SELECT name
  FROM   projects
  WHERE  root_path != ''
    AND  root_path IS NOT NULL
    AND  (
      '${PWD}' = root_path
      OR '${PWD}' LIKE root_path || '/%'
    )
  LIMIT 1;
" 2>/dev/null || true)

if [ -z "$ACTIVE_PROJECT" ]; then
  ACTIVE_PROJECT="(no project matched current directory)"
  PROJECT_ID=""
else
  PROJECT_ID=$(sqlite3 "$DB" "
    SELECT id FROM projects
    WHERE root_path != ''
      AND root_path IS NOT NULL
      AND (
        '${PWD}' = root_path
        OR '${PWD}' LIKE root_path || '/%'
      )
    LIMIT 1;
  " 2>/dev/null || true)
fi

# ── Task queue summary ────────────────────────────────────────────────────────
if [ -n "$PROJECT_ID" ]; then
  PENDING_COUNT=$(sqlite3 "$DB" "
    SELECT count(*) FROM tasks
    WHERE project_id = $PROJECT_ID AND status = 'pending';
  " 2>/dev/null || echo "0")

  NEXT_TASK=$(sqlite3 "$DB" "
    SELECT '#' || id || ' — ' || title || ' (' || priority || ')'
    FROM tasks
    WHERE project_id = $PROJECT_ID AND status = 'pending'
    ORDER BY CASE priority
      WHEN 'urgent' THEN 4
      WHEN 'high'   THEN 3
      WHEN 'normal' THEN 2
      WHEN 'low'    THEN 1
      ELSE 0
    END DESC, created_at ASC
    LIMIT 1;
  " 2>/dev/null || true)
else
  PENDING_COUNT="?"
  NEXT_TASK="(unknown)"
fi

echo "ACTIVE PROJECT: $ACTIVE_PROJECT | PENDING: $PENDING_COUNT | NEXT: $NEXT_TASK"

# ── Agent roster (first 12 lines of Agent Roster section) ─────────────────────
if [ -f "$AGENTS_MD" ]; then
  awk '
    /^## Agent Roster/ { found=1; count=0; next }
    found && /^## /    { exit }
    found              { print; count++; if (count >= 12) exit }
  ' "$AGENTS_MD" 2>/dev/null || true
fi

exit 0
