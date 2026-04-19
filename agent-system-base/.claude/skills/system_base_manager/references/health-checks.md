# Health Checks

Run these checks during every audit. Each check is a specific, verifiable condition.
Report pass/fail with details for any failures.

## Structural Checks

### 1. All agent JSONs reference existing skills

For each `~/.claude/agents/<name>.json`:
- Read the `"skill"` field
- Verify `~/.claude/skills/<skill>/SKILL.md` exists

**Pass**: every agent JSON points to a real skill directory with a SKILL.md
**Fail**: list each broken reference — `<agent>.json → skill '<skill>' not found`

### 2. All skills have agent JSONs

For each `~/.claude/skills/<name>/SKILL.md`:
- Check if `~/.claude/agents/<name>.json` exists

**Pass**: every skill has a matching agent JSON
**Fail**: list orphaned skills

**Exception**: skills marked as "project-locked" or standalone in their header
(e.g., `swarm`) are excluded from this check. Note them as intentional exclusions.

### 3. No sync drift between ~/.claude/ and ~/agents/agent-system-base/

Compare each file pair:
- `~/.claude/agents/<name>.json` vs `~/agents/agent-system-base/agents/<name>.json`
- `~/.claude/skills/<name>/SKILL.md` vs `~/agents/agent-system-base/.claude/skills/<name>/SKILL.md`

**Pass**: all files are identical (or agent-system-base is a subset of ~/.claude/)
**Fail**: list each file with differences — note which version is newer if detectable

**Note**: `~/.claude/` may contain skills not in agent-system-base (user-local or
plugin-installed skills). Only compare files that exist in both locations.

### 4. Tool consistency

For each agent JSON:
- Read `tools_preferred` from the JSON
- Read `allowed-tools` from the corresponding SKILL.md frontmatter
- Compare the two lists

**Pass**: they match (order doesn't matter)
**Fail**: list mismatches — `<agent>: JSON has [X, Y, Z], SKILL.md has [X, Y]`

**Note**: SKILL.md `allowed-tools` is optional. If absent, skip this check for that skill
but note it as a minor issue (the field should exist for clarity).

## Quality Checks

### 5. Description quality

For each skill's frontmatter description:
- **Length check**: between 20 and 100 words (too short = vague, too long = noisy)
- **Trigger phrases**: contains at least 2 concrete trigger phrases or user-facing keywords
- **Action clarity**: description states what the skill *does*, not just what it *is*

**Pass**: all skills meet the criteria
**Fail**: list skills with issues — `<skill>: description is [N] words (too short/long)`
or `<skill>: no trigger phrases detected`

### 6. No description overlap

Compare every pair of skill descriptions:
- Look for skills whose descriptions would both trigger on the same user input
- Focus on trigger phrases and keywords, not general topic area

**Pass**: each skill has a distinct trigger surface
**Fail**: list overlapping pairs — `<skill-a> and <skill-b> both trigger on "[phrase]"`

This check requires judgment, not just keyword matching. Two skills can share a word
(like "research") and still have distinct triggers if the surrounding context differs.

### 7. Skill quality bar

For each skill, run it against the quality checklist in `references/agent-template.md`.

**Pass**: all skills grade A or B (pass all must-have checks)
**Fail**: any skill grades C or D (fails must-have checks)

Focus on the must-have checks:
- Description answers what/when/when-not (not just a label)
- Explains why it exists
- Has an exit condition
- Names failure modes
- Reasoning over bare rules
- No overlap with other skills
- Tools match between SKILL.md and agent JSON

Report each skill's grade and list specific failed checks for C/D skills.

### 8. Plan integrity

For each plan in `~/.claude/agents/plans/<plan>.json`:
- Every agent referenced in the plan has a corresponding agent JSON
- Dependency chains are valid (no circular dependencies, no missing steps)

**Pass**: all plans reference valid agents with valid dependency chains
**Fail**: list broken references or invalid dependencies

## Reporting

Summarize results as a table:

```
| # | Check | Result | Details |
|---|-------|--------|---------|
| 1 | Agent → Skill references | ✅ Pass | All 10 agents reference existing skills |
| 2 | Skill → Agent references | ⚠️ Warn | 1 orphaned skill: 'swarm' (intentional) |
| 3 | Sync drift | ❌ Fail | 2 files differ between ~/.claude/ and agent-system-base |
| 4 | Tool consistency | ✅ Pass | All tools match |
| 5 | Description quality | ⚠️ Warn | 1 skill has short description: 'context' (15 words) |
| 6 | Description overlap | ✅ Pass | No overlapping triggers |
| 7 | Skill quality bar | ⚠️ Warn | 2 skills grade C: 'research', 'context' |
| 8 | Plan integrity | ✅ Pass | Both plans reference valid agents |
```

Use ✅ for pass, ⚠️ for warnings (non-blocking issues), ❌ for failures (needs action).
