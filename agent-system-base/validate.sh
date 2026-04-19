#!/bin/bash
# Local quality gate — run before committing changes to agent-system-base.
# Checks: skill frontmatter, agent JSON pairing, plan agent references.
# Prints PASS or FAIL for each check and exits 1 if any fail.

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$BASE_DIR/.claude/skills"
AGENTS_DIR="$BASE_DIR/agents"
PLANS_DIR="$AGENTS_DIR/plans"

PASS=0
FAIL=0

ok()   { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1"; FAIL=$((FAIL + 1)); }

echo ""
echo "=== Validate agent-system-base ==="
echo ""

# ── Check 1: All SKILL.md files have required frontmatter ────────────────────
echo "--- Skill frontmatter ---"
for skill_md in "$SKILLS_DIR"/*/SKILL.md; do
    skill_name="$(basename "$(dirname "$skill_md")")"
    missing=""
    for field in name version description; do
        if ! grep -q "^${field}:" "$skill_md" 2>/dev/null; then
            missing="$missing $field"
        fi
    done
    if [ -z "$missing" ]; then
        ok "$skill_name: name/version/description present"
    else
        fail "$skill_name: missing frontmatter fields:$missing"
    fi
done

echo ""

# ── Check 2: All agent JSONs are valid JSON with required fields ──────────────
echo "--- Agent JSON validity ---"
for agent_json in "$AGENTS_DIR"/*.json; do
    agent_name="$(basename "$agent_json" .json)"
    if python3 -c "
import json, sys
data = json.load(open('$agent_json'))
required = ['name']
missing = [f for f in required if f not in data]
if missing:
    print('missing: ' + ', '.join(missing))
    sys.exit(1)
" 2>/dev/null; then
        ok "$agent_name: valid JSON"
    else
        fail "$agent_name: invalid JSON or missing 'name' field"
    fi
done

echo ""

# ── Check 3: Agents with 'skill' field have a matching SKILL.md ──────────────
echo "--- Skill-agent pairing ---"
for agent_json in "$AGENTS_DIR"/*.json; do
    agent_name="$(basename "$agent_json" .json)"
    skill_name="$(python3 -c "import json; d=json.load(open('$agent_json')); print(d.get('skill',''))" 2>/dev/null || echo "")"
    if [ -z "$skill_name" ]; then
        continue
    fi
    # Check both base and global skill dirs
    if [ -f "$SKILLS_DIR/$skill_name/SKILL.md" ] || \
       [ -f "$HOME/.claude/skills/$skill_name/SKILL.md" ]; then
        ok "$agent_name → skill '$skill_name' found"
    else
        fail "$agent_name → skill '$skill_name' not found in .claude/skills/ or ~/.claude/skills/"
    fi
done

echo ""

# ── Check 4: All plan JSONs reference agents that exist in agents/ ────────────
echo "--- Plan agent references ---"
for plan_json in "$PLANS_DIR"/*.json; do
    plan_name="$(basename "$plan_json" .json)"
    invalid="$(python3 -c "
import json, os, sys
data = json.load(open('$plan_json'))
agents_dir = '$AGENTS_DIR'
invalid = []
for step in data.get('steps', []):
    agent = step.get('agent', '')
    if agent == 'merge':
        continue  # builtin
    agent_file = os.path.join(agents_dir, agent + '.json')
    if not os.path.exists(agent_file):
        invalid.append(agent)
print(' '.join(invalid))
" 2>/dev/null || echo "parse_error")"
    if [ "$invalid" = "parse_error" ]; then
        fail "$plan_name: could not parse JSON"
    elif [ -z "$invalid" ]; then
        ok "$plan_name: all agent references valid"
    else
        fail "$plan_name: unknown agents: $invalid"
    fi
done

echo ""

# ── Summary ──────────────────────────────────────────────────────────────────
echo "=== Results: $PASS passed, $FAIL failed ==="
echo ""

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
