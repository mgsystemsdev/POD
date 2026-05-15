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

# --- Standard .claude/ document structure (copied from templates/project/.claude/) ---
echo "Seeding .claude/ document structure for $TARGET..."

TEMPLATES="$BASE_DIR/templates/project/.claude"
if [ ! -d "$TEMPLATES" ]; then
  echo "error: templates directory missing: $TEMPLATES" >&2
  exit 1
fi

# Copy every template file, but never overwrite existing files in the target.
# Structure: pipeline/, governance/, specialists/, config.json
mkdir -p "$TARGET/.claude/pipeline" "$TARGET/.claude/governance" "$TARGET/.claude/specialists"

copy_template() {
  local rel="$1"
  local src="$TEMPLATES/$rel"
  local dest="$TARGET/.claude/$rel"
  if [ ! -f "$src" ]; then
    echo "  [skip] template missing: $rel" >&2
    return 0
  fi
  if [ -f "$dest" ]; then
    return 0  # never overwrite
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo "  Created .claude/$rel"
}

copy_template "config.json"
copy_template "pipeline/tasks.json"
copy_template "pipeline/blueprints.md"
copy_template "pipeline/session_log.md"
copy_template "pipeline/execution_trace.md"
copy_template "governance/decisions.md"
copy_template "governance/requirements.md"
copy_template "governance/memory.md"
copy_template "governance/approvals.md"
copy_template "governance/backlog.md"
copy_template "governance/audit_trail.md"
for role in strategist system_design backend_spec db_spec schema_spec ui_spec senior_dev; do
  copy_template "specialists/$role.md"
done

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
echo "  .claude/{config.json,pipeline/,governance/,specialists/}  (from templates/project/.claude/)"
echo ""
echo "To run the orchestrator:"
echo "  cd ~/.claude && python3 -m orchestrator --runs-dir $TARGET/runs/ephemeral --plan swarm_research --goal 'test' --mode simulate"
echo ""
echo "To install cron jobs (first time only):"
echo "  bash ~/agents/agent-services/install.sh"
