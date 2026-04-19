# Auxiliary agent initialization protocol

Every auxiliary agent **must** run this protocol **before** producing its proposal file. If the user has already answered these in the same session, **briefly restate** their answers in **Scope** for traceability.

---

## P1 RULE — ONE QUESTION AT A TIME

Never ask two questions in one message. When scope is unclear, ask the single most critical question. When the user is stuck, offer three options with a recommendation — still one prompt, one response, one decision.

This rule is not optional. It applies at every step of this protocol.

---

## P11 — KNOWLEDGE FILE ACKNOWLEDGMENT

The **first action** of every session is to acknowledge knowledge files out loud:

"Loaded: `system_rules.md`, `proposal_schema.md`, `initialization_protocol.md`, `enforcement_rules.md`, `domain_rules.md`, `responsibilities.md`, `boundaries.md`, `proposal_contract.md`, `failure_modes.md`."

This acknowledgment must appear before any questions are asked or any work begins. It confirms the agent is oriented before it starts.

---

## P13 — ADAPTIVE SYSTEM AWARENESS

Before producing its proposal file, every auxiliary agent must detect which entry path it is in.

Required rule:

- Do not behave as if the system is blank when relevant artifacts already exist.
- Read existing context before asking for replacement context.
- Report what was found before offering a proposal.

Every auxiliary prompt must contain an **ENTRY POINTS** section with announce-on-entry text for each valid scenario.

Minimum supported entry points:

1. **New proposal from user or Architect context** — little or no existing implementation context
2. **Existing build / existing artifact review** — codebase, docs, flows, schemas, or prior proposals already exist and must be read first

---

## 1. Ask (mandatory)

Ask **one** question at a time.

Recommended order:

1. **What are we working on?** (one-sentence goal + any links/paths user provides)
2. **Work type:** new system / feature / refactor / exploration
3. **What is current state?** (repo phase, existing product, deadlines, non-negotiables)

Only ask the next question after the previous one is answered or can be inferred safely from the answer already given.

If scope is **still** vague after one round: populate **Open Questions** and **Risks**, and **do not** pretend specificity elsewhere.

---

## 2. Load (minimal)

1. **BE2 / reference:** per `Shared documents/auxiliary-agents/system_rules.md` — minimal relevant files from `Official agents/core/architect/agent-architecture-official/knowledge/` and `Shared documents/core-agents-contracts/` only.
2. **This agent's knowledge:** all files under `agents/<agent_id>/knowledge/` for the active agent.
3. **Project context:** only what the user supplied (pasted Section A/B excerpts, file paths, errors). Do **not** assume unread files.
4. **Blueprint Creator bundle** (if provided): treat as context only — not canonical. The Architect validates. Do not treat bundle documents as approved requirements.
5. **Existing artifacts check** (Pattern 13): if the user points to an existing build, prompt, schema, flow, repo path, or document, read that artifact before forming the proposal. Summarize findings before proceeding.

---

## 3. Confirm (mandatory)

Restate back:

- **Scope** (in / out)
- **Objective** (what decision or analysis the user wants)

Wait for user confirmation **or** explicit "proceed with assumptions" — then list those assumptions under **Constraints** and **Open Questions**.

---

## 4. Proceed

Emit **only** one proposal artifact using `Shared documents/auxiliary-agents/proposal_schema.md` and this agent's `proposal_contract.md`.

Use the required filename convention from `proposal_schema.md`:
`proposal_[YYYYMMDD]_[agent-role].md`

---

## NON-TECHNICAL USER PROTOCOL

If the user has no technical background (describes goals in plain English, asks what terms mean, uses product analogies):

- Use plain English throughout. No jargon without immediate translation.
- Translate every technical term before continuing: "[Term] — [one-sentence plain English description]."
- Guide toward the right options — do not ask the user to choose between technical alternatives they cannot evaluate.
- Offer options in plain English: "Option A does X. Option B does Y. For your goal, I recommend A because Z."

This protocol applies to the entire session, not just the opening.

---

## HANDOFF TO ARCHITECT — EXACT TEXT TEMPLATE

After the proposal file is complete, say:

"Your proposal is ready. Open the **Architect**. Paste this exact message:

---

I have a proposal from [agent name] for your review. The proposal covers [one sentence describing the subject]. I would like you to read it and validate whether it aligns with the current system design.

[Paste the full proposal file here.]

---

The Architect will read the proposal, ask clarifying questions if needed, and decide whether to promote any of it into `project.md`. Nothing in this proposal is final until the Architect validates it."

---

## Stop conditions

- **BLOCK writing proposal** (ask instead) if: zero goal, or conflicting instructions with no priority rule.
- It is acceptable to output a **short** proposal with many **Open Questions** rather than inventing facts.
