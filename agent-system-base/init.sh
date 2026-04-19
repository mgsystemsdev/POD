#!/bin/bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:?usage: $0 <target-project-dir>}"
# Doc placeholders like /REAL/PATH/TO/YOUR/PROJECT try to create /REAL — fails on macOS (read-only root).
case "$TARGET" in
  /REAL/*)
    echo "error: '$TARGET' is a documentation placeholder, not a real path." >&2
    echo "  usage: $0 /path/to/your-actual-project" >&2
    exit 1
    ;;
esac
GLOBAL="$HOME/.claude"
SERVICES="$HOME/agents/agent-services"

# 0. Sync global tools to ~/.claude/ (orchestrator, agents, schemas, system)
mkdir -p "$GLOBAL"
rsync -a --exclude='__pycache__' --exclude='*.pyc' --delete "$BASE_DIR/orchestrator/" "$GLOBAL/orchestrator/"
rsync -a --delete "$BASE_DIR/agents/"  "$GLOBAL/agents/"
rsync -a --delete "$BASE_DIR/schemas/" "$GLOBAL/schemas/"
echo "  Synced global tools → $GLOBAL"

# 1. Sync runtime layer to ~/agents/agent-services/
mkdir -p "$SERVICES/workers" "$SERVICES/logs" "$SERVICES/state" "$SERVICES/config"
rsync -a --exclude='__pycache__' --exclude='*.pyc' "$BASE_DIR/workers/" "$SERVICES/workers/"
rsync -a --exclude='__pycache__' --exclude='*.pyc' "$BASE_DIR/system/"  "$SERVICES/system/"
rsync -a "$BASE_DIR/config/" "$SERVICES/config/"
chmod +x "$SERVICES/system/scripts/start_dashboard.sh"
echo "  Synced runtime → $SERVICES/ (workers + system + config)"

# 2. Create per-project runs directory
mkdir -p "$TARGET/runs/ephemeral"

# 3. Create .claude/skills/swarm/ (project-locked skill)
mkdir -p "$TARGET/.claude/skills/swarm"
cp "$BASE_DIR/.claude/skills/swarm/SKILL.md" "$TARGET/.claude/skills/swarm/SKILL.md"

# --- Standard .claude/ document structure ---
echo "Seeding .claude/ document structure for $TARGET..."

if [ ! -f "$TARGET/.claude/project.md" ]; then
  cat > "$TARGET/.claude/project.md" << 'PROJECTMD'
# Project Name — Blueprint

## Overview


## Problem


## Stack
- Language: Python
- Framework: FastAPI
- Database: SQLite (raw SQL, no ORM)

## Architecture


## Critical Constraints


## Current State
Greenfield.

## Next Scope

PROJECTMD
  echo "  Created .claude/project.md"
fi

if [ ! -f "$TARGET/.claude/tasks.json" ]; then
  echo "[]" > "$TARGET/.claude/tasks.json"
  echo "  Created .claude/tasks.json"
fi

if [ ! -f "$TARGET/.claude/session.md" ]; then
  cat > "$TARGET/.claude/session.md" << 'SESSIONMD'
# Session Log

---
SESSIONMD
  echo "  Created .claude/session.md"
fi

if [ ! -f "$TARGET/.claude/decisions.md" ]; then
  cat > "$TARGET/.claude/decisions.md" << 'DECISIONSMD'
# Decisions Log

---
DECISIONSMD
  echo "  Created .claude/decisions.md"
fi

# 3b. Seed project context files (copy templates, don't overwrite existing)
if [ ! -f "$TARGET/CLAUDE.md" ]; then
    cp "$BASE_DIR/CLAUDE.md" "$TARGET/CLAUDE.md"
    echo "  Created $TARGET/CLAUDE.md"
fi
if [ ! -f "$TARGET/.env.template" ]; then
    cp "$BASE_DIR/config/.env.template" "$TARGET/.env.template"
    echo "  Created $TARGET/.env.template"
fi

# 4. Create global data stubs if not present
if [ ! -f "$GLOBAL/tasks.json" ]; then
    echo "[]" > "$GLOBAL/tasks.json"
    echo "  Created ~/.claude/tasks.json"
fi

echo ""
echo "Seeded $TARGET:"
echo "  ~/.claude/          (orchestrator + agents + schemas + system — global)"
echo "  ~/agents/agent-services/   (workers synced — runtime layer)"
echo "  runs/               (per-project run outputs)"
echo "  .claude/skills/swarm/SKILL.md"
echo "  .claude/{project.md,tasks.json,session.md,decisions.md}"
echo ""
echo "To run the orchestrator:"
echo "  cd ~/.claude && python3 -m orchestrator --runs-dir $TARGET/runs/ephemeral --plan swarm_research --goal 'test' --mode simulate"
echo ""
echo "To install cron jobs (first time only):"
echo "  bash ~/agents/agent-services/install.sh"
