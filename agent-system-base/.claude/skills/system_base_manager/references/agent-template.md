# Agent + Skill Creation Template

Use this template when creating new agents via Path B (direct creation).
For complex skills, delegate to Skill Creator instead (Path A).

This is also the **quality bar** that System Base Manager uses when auditing existing skills.
Every skill in the system should meet the principles embedded here. If one doesn't, that's
a quality gap.

---

## The Principles (Why This Template Exists)

Most skill templates are just structure — fill in the blanks, ship it. That produces skills
that technically exist but don't actually work well. These four principles separate skills
that perform from skills that sit there:

### 1. The description is a hiring decision

Claude reads the description and decides "do I need this?" Most templates treat descriptions
like labels. This template treats them like job postings — the description has to answer
*why* this skill exists, *when* to use it, and *when not to*. If the description doesn't
do this, the skill either never fires or fires on the wrong things.

### 2. Explain the why, not just the what

Every instruction should have a "because" attached. Claude is smart enough to generalize
from reasoning — if you give it rules without context, it follows them literally and breaks
on anything unexpected. If you explain *why* a rule exists, Claude can handle novel situations
the rule-writer never anticipated.

### 3. Name the failure modes explicitly

Without this, Claude reproduces whatever its default behavior is when things go sideways.
You have to name the bad pattern to override it. "Don't do X" is weak. "You'll be tempted
to do X because [reason], but that fails because [consequence]. Instead, do Y." — that
actually works.

### 4. Define the exit condition

Most skills have no ending. Claude either keeps going when it should stop, or stops when
it should keep going. Defining "done" with checkable conditions makes the skill behave
predictably. Every skill needs a clear answer to: "How does Claude know it's finished?"

---

## Agent JSON Template

Save to `~/.claude/agents/<name>.json`:

```json
{
  "name": "<name>",
  "skill": "<name>",
  "role": "<One sentence: what this agent does and when to use it>",
  "tools_preferred": ["<tool1>", "<tool2>"],
  "tools_fallback": ["<tool1>"],
  "inputs_schema": "schemas/agent_output.schema.json",
  "output_schema": "schemas/agent_output.schema.json",
  "reads_prior_outputs": false,
  "notes": "<Key behavioral constraints — keep to 1-2 sentences>"
}
```

### Field guidance

- **name**: lowercase, underscores. Must match the skill directory name exactly.
- **skill**: same as name. This is how the orchestrator finds the SKILL.md.
- **role**: one sentence that tells another agent (or the swarm) what this agent contributes. Think "elevator pitch for a machine."
- **tools_preferred**: the tools the agent needs to do its job well. Must match what SKILL.md declares in `allowed-tools`.
- **tools_fallback**: subset that still allows partial function if preferred tools aren't available.
- **reads_prior_outputs**: set to `true` only if this agent needs output from a previous step in a swarm plan. Most standalone agents are `false`.
- **notes**: constraints that matter for orchestration — things like "never writes files" or "requires network access."

---

## SKILL.md Template

Save to `~/.claude/skills/<name>/SKILL.md`:

````markdown
---
name: your-skill-name
description: >
  [THE MOST IMPORTANT FIELD. Claude decides to use your skill based on this alone.

  Answer these three things in plain language:
  1. What does this skill make Claude do that it couldn't do (or wouldn't do consistently) on its own?
  2. What does the user SAY when they need this? (not what they mean — what do they actually type)
  3. What are the near-misses that should NOT trigger this? (name them so Claude can distinguish)

  Then make it slightly pushy: end with "Use this skill whenever [X], even if the user
  doesn't explicitly ask for it."

  Bad: "Helps with Python code."
  Good: "Guides the user through building Streamlit apps using clean service-layer architecture,
  raw parameterized SQL, and optimistic concurrency. Use this skill whenever the user mentions
  Streamlit, dashboards, or data apps — even if they just say 'I want to display this data
  somewhere.' Do NOT trigger for general Python questions or FastAPI/Flask backends."]
---

# [Skill Name]

[One sentence. What problem does this skill solve, and why does Claude need explicit
instructions to solve it well? If you can't answer "why does Claude need instructions
for this", your skill might not need to exist.]

---

## What This Skill Is For

[Describe the job to be done. Not the steps — the *outcome*. What does the world look
like after this skill runs successfully?

Also answer: what does failure look like? What does Claude do without this skill that
makes you need it?]

---

## When to Use This (and When Not To)

**Use this skill when:**
- [Specific trigger condition — the more concrete the better]
- [Another trigger — include phrasing cues, file types, contexts]
- [Edge case that should still trigger]

**Do NOT use this skill when:**
- [Near-miss that looks similar but needs different handling]
- [Context where a different skill or no skill is better]

[This section exists because Claude sometimes over-triggers OR under-triggers.
Be explicit about the boundaries.]

---

## Core Workflow

[The heart of the skill. Write it as a sequence of steps Claude should take.

Rules for writing good steps:
- Use imperative voice ("Do X" not "Claude should X")
- Explain WHY, not just WHAT — give reasoning and Claude generalizes; give only rules and it gets brittle
- If a step requires a decision, write out the decision logic explicitly
- If order matters, say why it matters]

### Phase 1: [Name — e.g., "Understand the situation"]

[What should Claude do first, and why does it need to happen before anything else?]

1. [Step — include reasoning. "Do X because without it, Y will break downstream."]
2. [Step]
3. [Step]

**Decision point:** If [condition], go to Phase 2. If [other condition], skip to Phase 3
because [reason].

### Phase 2: [Name — e.g., "Build the thing"]

[What happens here? What should Claude have in hand before starting?]

1. [Step]
2. [Step]

**Common mistake to avoid:** [What does Claude typically get wrong here without guidance?
Name it explicitly.]

### Phase 3: [Name — e.g., "Verify and hand off"]

[How does Claude know it's done? What does "done" look like?]

1. [Step]
2. [Step]

---

## Output Format

[If your skill produces consistent outputs, define them here. Be specific.

If the output is a file: name the format, the naming convention, where it should be saved.
If the output is text: show a template or example.
If the output is a decision: show the format and how Claude should communicate it.]

**Template:**
```
[Paste an actual example of good output. Not a description — a real example.
The model learns from examples better than from descriptions.]
```

---

## What "Good" Looks Like

[Describe a successful execution. Walk through an example.

This is where you encode your taste and judgment. Don't just describe mechanics —
describe the *quality bar*.]

**Example:**
- Input: "[realistic user message]"
- Claude does: [key steps, decisions made]
- Output: [concrete result]

---

## What "Bad" Looks Like (and How to Recover)

[Name the failure modes. For each:
1. How to recognize it
2. Why it happens
3. What to do instead]

**Failure: [name it]**
Signs: [how you'd notice]
Cause: [why Claude does this without the instruction]
Fix: [what to do instead]

**Failure: [name it]**
Signs: [how you'd notice]
Cause: [why]
Fix: [what to do]

---

## Edge Cases

[Situations that don't fit the happy path. Don't enumerate every case — focus on the ones
where the wrong instinct is likely.]

- **If [edge case]:** Do [X] instead of [Y] because [reason].
- **If [edge case]:** Stop and ask the user for [specific thing] before proceeding.
- **If [edge case]:** This skill doesn't apply — tell the user [what they actually need].

---

## Bundled Resources

[Only include this section if you have scripts, reference docs, or assets.
Delete it entirely if you don't.]

| Resource | Location | When to use it |
|---|---|---|
| [script name] | `scripts/[filename]` | [Specific situation] |
| [reference doc] | `references/[filename]` | [When to read it] |

[Don't load everything upfront. Tell Claude when to load each resource — loading everything
wastes context.]

---

## How to Know You're Done

[Define the exit condition. What signal tells Claude — and the user — that the skill
has done its job?]

This skill is complete when:
- [ ] [Concrete, checkable condition]
- [ ] [Another condition]
- [ ] The user has [what they need to move forward]

If any condition isn't met, [what should Claude do — loop back to which phase? Ask the
user for what?]
````

---

## Quality Checklist

Use this when creating a new skill AND when auditing existing skills. Every skill in the
system should pass these checks.

### Must-have (fail the audit without these)

- [ ] **Description answers the three questions** — what does it do, what does the user say, what are the near-misses? A description that's just a label ("Helps with X") fails.
- [ ] **Explains why it exists** — the opening section answers "why does Claude need explicit instructions for this?" If it can't, the skill might not need to exist.
- [ ] **Has an exit condition** — defines "done" with checkable conditions. A skill with no ending is unpredictable.
- [ ] **Names failure modes** — explicitly describes what bad looks like and how to recover. Without this, Claude falls back to defaults.
- [ ] **Reasoning over rules** — instructions explain *why*, not just *what*. If you see more than 2 bare ALWAYS/NEVER without explanation, that's a flag.
- [ ] **No overlap** — the description doesn't collide with other skills' trigger surfaces.
- [ ] **Tools match** — `allowed-tools` in SKILL.md matches `tools_preferred` in agent JSON.
- [ ] **Synced** — both files exist in `~/.claude/` and `~/agents/agent-system-base/`.

### Should-have (flag but don't fail)

- [ ] **When-to and when-not-to section** — explicit boundaries prevent over/under-triggering.
- [ ] **Output format defined** — with a real example, not an abstract description.
- [ ] **"Good" example** — at least one walkthrough of successful execution.
- [ ] **Under 500 lines** — if longer, overflow into `references/`.
- [ ] **Progressive disclosure** — doesn't front-load everything; references are loaded on demand.

### Nice-to-have

- [ ] **Edge cases** — covers 3-5 realistic non-happy-path situations.
- [ ] **Bundled resources** — scripts or references for deterministic/repetitive subtasks.
- [ ] **Decision points** — workflow branches are explicit, not left to vibes.

---

## Common Mistakes

- **Description too vague**: "Helps with code" — nobody triggers this. Be specific: "Reviews Python code for performance issues, memory leaks, and anti-patterns. Use when..."
- **Description too narrow**: "Converts CSV files to JSON" — misses cases where users say "transform this data" or "parse this spreadsheet." Include adjacent phrasings.
- **Tools mismatch**: SKILL.md says `allowed-tools: Read, Write` but agent JSON says `tools_preferred: ["Read", "Grep", "Write"]`. Pick one source of truth (SKILL.md) and make the JSON match.
- **No activation step**: The skill jumps straight into action without reading current state. This leads to stale assumptions. Always read real files first.
- **Rules without reasons**: "NEVER use more than 3 bullet points" — why? What breaks? If you can't explain it, the rule probably doesn't need to exist.
- **No failure modes**: The skill only describes the happy path. Claude will encounter edge cases and fall back to its defaults — which is exactly what the skill was supposed to override.
- **No exit condition**: The skill never says when it's done. Claude either loops indefinitely or stops at an arbitrary point.
- **Wall-of-text instructions**: 800 lines of undifferentiated prose. Break it up with phases, decision points, and reference files. If Claude can't quickly find what it needs, it'll ignore half of it.
