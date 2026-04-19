# Audit Schema

Audit snapshots are saved to `~/.claude/system-audits/audit-YYYY-MM-DD.json`.
This schema defines the structure so audits are comparable across time.

## Full Schema

```json
{
  "date": "2026-03-22",
  "version": 1,

  "counts": {
    "agents": 10,
    "skills": 9,
    "plans": 2
  },

  "agents": [
    {
      "name": "system_base_manager",
      "skill": "system_base_manager",
      "status": "healthy",
      "issues": []
    },
    {
      "name": "research",
      "skill": "research-v2",
      "status": "broken",
      "issues": ["skill 'research-v2' does not exist — actual skill is 'research'"]
    }
  ],

  "skills": [
    {
      "name": "system_base_manager",
      "has_agent_json": true,
      "quality_grade": "A",
      "quality_issues": [],
      "description_length": 52,
      "allowed_tools": ["Read", "Grep", "Glob", "Write"],
      "issues": []
    },
    {
      "name": "research",
      "has_agent_json": true,
      "quality_grade": "C",
      "quality_issues": ["no failure modes", "bare rules without reasoning", "no exit condition"],
      "description_length": 30,
      "allowed_tools": ["Read", "Grep", "Glob", "WebSearch"],
      "issues": ["description too short"]
    }
  ],

  "plans": [
    {
      "name": "swarm_research",
      "agents_used": ["context", "research", "create", "merge"],
      "issues": []
    }
  ],

  "health_checks": [
    {
      "check": "all_agent_jsons_reference_existing_skills",
      "passed": false,
      "details": "research.json references 'research-v2' which does not exist"
    },
    {
      "check": "all_skills_have_agent_jsons",
      "passed": true,
      "details": null
    },
    {
      "check": "no_sync_drift",
      "passed": true,
      "details": null
    },
    {
      "check": "tool_consistency",
      "passed": true,
      "details": null
    },
    {
      "check": "no_description_overlap",
      "passed": true,
      "details": null
    }
  ],

  "gaps": [
    {
      "id": "gap-001",
      "type": "structural",
      "severity": "broken",
      "title": "Orphaned agent: research.json → research-v2",
      "evidence": "research.json skill field is 'research-v2', but skill directory is 'research'",
      "recommendation": "Update research.json skill field to 'research'",
      "status": "open"
    }
  ],

  "recommendations": [
    {
      "id": "rec-001",
      "action": "Fix research.json skill reference",
      "severity": "broken",
      "effort": "trivial",
      "related_gap": "gap-001",
      "status": "open"
    }
  ],

  "parking_lot": {
    "total_items": 3,
    "by_type": {
      "idea": 1,
      "skill_gap": 1,
      "agent_need": 1
    },
    "oldest_item_date": "2026-02-15",
    "clusters": []
  },

  "comparison": {
    "previous_audit": "2026-03-15",
    "new_gaps": ["gap-001"],
    "resolved_gaps": [],
    "ignored_recommendations": [],
    "count_changes": {
      "agents_added": 1,
      "agents_removed": 0,
      "skills_added": 1,
      "skills_removed": 0
    }
  }
}
```

## Field Reference

### Top-level

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | ISO date of the audit |
| `version` | number | Schema version (currently 1) |
| `counts` | object | Quick counts for agents, skills, plans |

### Agent entry

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent name from JSON filename |
| `skill` | string | Skill name from the `"skill"` field in agent JSON |
| `status` | enum | `healthy`, `warning`, `broken` |
| `issues` | string[] | List of specific issues found (empty if healthy) |

### Skill entry

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Skill directory name |
| `has_agent_json` | boolean | Whether a matching agent JSON exists |
| `quality_grade` | enum | `A`, `B`, `C`, `D` — see Skill Quality Audit in SKILL.md |
| `quality_issues` | string[] | Failed quality checklist items (empty if grade A) |
| `description_length` | number | Word count of frontmatter description |
| `allowed_tools` | string[] | Tools declared in frontmatter |
| `issues` | string[] | List of specific structural issues found |

### Gap entry

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique gap identifier (gap-NNN) |
| `type` | enum | `structural`, `quality`, `coverage` |
| `severity` | enum | `broken`, `stale`, `missing`, `nice-to-have` |
| `title` | string | Short description |
| `evidence` | string | What was found and where |
| `recommendation` | string | Specific action to take |
| `status` | enum | `open`, `dismissed`, `resolved` |

### Recommendation entry

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique recommendation identifier (rec-NNN) |
| `action` | string | What to do |
| `severity` | enum | `broken`, `stale`, `missing`, `nice-to-have` |
| `effort` | enum | `trivial`, `small`, `medium` |
| `related_gap` | string | Gap ID this addresses (if any) |
| `status` | enum | `open`, `in_progress`, `done`, `dismissed` |
