Here is the full analysis. Every pattern you repeat, named and explained.

---

## MIGUEL'S AGENT DESIGN PATTERNS

---

### PATTERN 1 — ONE QUESTION AT A TIME, NEVER TWO

This is the most consistent rule across every agent you built. The Architect never asks two questions in one message. The Operator asks one thing per step. The Strategist restates the problem before asking anything. The Execution Spec Gate reads Section B fully before asking a single clarifying question.

The rule behind this pattern is that you do not want to overwhelm the person in the conversation — which is often you on your phone. One question forces a complete answer. Two questions let the user answer the easy one and skip the hard one.

When the user is stuck, the pattern shifts slightly — three options with a recommendation — but even then it is still one prompt, one response, one decision. Never a branching conversation that requires the user to hold multiple threads.

---

### PATTERN 2 — READ EVERYTHING BEFORE ASKING ANYTHING

Every agent starts by reading what it was given before it speaks. The Architect reads the mode response before questioning. The Execution Spec Gate reads all of Section B before flagging any gap. The Operator reads Section B and session.md before running the system state check. The Strategist reads Section B and decisions.md before restating the problem.

The pattern is: receive first, understand second, speak third. No agent ever asks a question that the input already answered. This comes from your frustration with agents that ask you to repeat yourself or that start advising before they understand the context.

---

### PATTERN 3 — NAMED HARD STOPS WITH EXPLICIT BLOCKING CONDITIONS

Every agent has specific situations where it stops completely and will not proceed. These are not soft suggestions. They are hard blocks.

The Architect blocks on unresolved conflicts between requirements. It will not produce an artifact until the conflict is resolved. The Execution Spec Gate blocks when a requirement is missing an element — it sends it back to The Architect by name. The Operator blocks when the user is on main branch — no execution starts, full stop. The Strategist blocks when proceeding would lock in a decision the system cannot support.

Every block names the exact reason and names the exact resolution. Never vague. Never "something seems off." Always specific: "REQ-003 has no failure path. I need the failure path before generating tasks for this requirement."

---

### PATTERN 4 — EXPLICIT ECOSYSTEM POSITION

Every agent knows where it sits in the pipeline, who feeds it, and who it feeds. This is not implied — it is stated explicitly in the prompt under ECOSYSTEM POSITION.

The Architect says it is GPT 1 of 4 and that nothing else runs until it produces project.md. The Execution Spec Gate says it receives from The Architect and feeds The Operator. The Strategist says it is on-call and that it does not feed anything — it advises and returns. The Operator says it is GPT 4 of 4 and that design problems go back to GPT 1.

The pattern behind this is that no agent should ever wonder what to do when it hits the edge of its role. The answer is always named. Stuck goes to The Strategist. Design wrong goes to The Architect. New scope goes to the Execution Spec Gate. No agent tries to do another agent's job.

---

### PATTERN 5 — HONEST BOUNDARIES NAMED EXPLICITLY

Every agent states what it does NOT do. Not implied — explicitly stated in the prompt.

The Architect does not write code. It does not generate tasks. It does not advise on implementation. The Execution Spec Gate does not design systems or make architectural decisions. The Strategist does not execute tasks or write code. The Operator does not design, plan, or think out loud.

This pattern comes from your principle that a two-sentence role description means the agent is doing too much. One sentence for what it does. Explicit statement of what it does not do. The boundary is as important as the role.

---

### PATTERN 6 — THE FIVE-ELEMENT REQUIREMENT CONTRACT APPLIED EVERYWHERE

Trigger, input, output, constraints, failure path. This framework appears in every agent in every context.

The Architect extracts it from conversations. The Execution Spec Gate verifies that every requirement in Section B has all five before generating tasks. The Operator verifies that every implementation satisfies all five before accepting it. The Strategist grounds every recommendation in the contract — "this option satisfies the output constraint but fails the failure path requirement."

You invented this contract as a tool for The Architect and then applied it to every other agent retroactively. It became the universal quality standard for the entire system. If something cannot be expressed in five elements, it is not ready.

---

### PATTERN 7 — PLAIN ENGLISH TRANSLATIONS, NO CODE IN EXPLANATIONS

Every agent that produces technical output also produces a plain English translation. The Architect translates architectural decisions: "this means X for how the system behaves." The Operator has a dedicated TRANSLATE step — Step 4 — where it explains what was built in plain English with no code blocks before the review step. The Strategist presents tradeoffs in plain English, never in technical terms.

The pattern comes from your awareness that you are learning to work like a professional developer and you do not want to be dependent on understanding code to make decisions. Every agent treats the plain English explanation as a first-class output, not an afterthought.

---

### PATTERN 8 — DRIFT CONTROL AS AN EXPLICIT SECTION

Every agent has a DRIFT CONTROL section that maps specific user behaviors to specific agent responses. The patterns are exhaustive — not just general guidance but exact if-then rules.

Miguel describes implementation instead of requirement → exact response. Miguel adds scope mid-requirement → exact response. Miguel says it is obvious → exact response. Miguel is on main branch → exact response. Miguel skips the diff check → exact response.

This pattern exists because you observed in practice that the same deviations happen repeatedly. Rather than letting agents handle drift inconsistently, you codified every known deviation and its correction. The agent never has to improvise a response to a drift situation — it has the exact words to use.

---

### PATTERN 9 — EVERY SESSION PRODUCES A COMMITTED ARTIFACT

No agent closes a session without producing something that gets committed. The Architect produces project.md and tells you exactly where to save it and what the commit message should be. The Strategist produces a decisions.md entry and tells you to append and commit. The Operator produces session.md and commits it as the final step before stopping.

The pattern is that a session that produces only conversation is a session that disappears. Everything must land on disk, committed to Git, before the session is considered complete. You built this rule because you experienced the pain of losing context between sessions and having to re-explain your system to an agent that had no memory of what was decided.

---

### PATTERN 10 — THE HANDOFF IS EXPLICIT AND NAMED

Every agent ends by telling you exactly what to do next and exactly which agent receives it. The Architect tells you the exact message to send to the Execution Spec Gate — including what to paste and what to say. The Execution Spec Gate tells you to save tasks.json and run the import worker with the exact command. The Operator tells you to mark the task complete in the dashboard.

No agent leaves you wondering what comes next. The handoff is part of the output, not an assumption. This comes from your principle that a vague handoff breaks the pipeline — the user has to make a decision they should not have to make, and they often make the wrong one.

---

### PATTERN 11 — KNOWLEDGE FILES LOAD AT SESSION START, ACKNOWLEDGED EXPLICITLY

Every agent loads its knowledge files at session start and acknowledges them out loud. "Loaded: requirement_contract.md, system_contract.md, user_profile.md..." This is not optional behavior — it is the first action of every session.

The pattern ensures that the agent is never operating from memory alone. The knowledge files are the ground truth. If user_profile.md changes, all agents that load it get the update automatically. The acknowledgment is a signal to you that the agent is oriented correctly before it starts asking questions.

---

### PATTERN 12 — HUMAN GATE BEFORE ANYTHING EXECUTES

No agent in your system executes anything autonomously without a human approval step. The Operator does not start a task until you have reviewed the scope map and confirmed. The orchestrator plans pause between phases for your approval. The proposed_action_service requires your approval before any internal agent write lands in SQLite. The review_wave produces a SHIP/REVISE/BLOCK verdict — BLOCK means full stop, nothing proceeds.

This is your most fundamental design principle. The agents advise and prepare. You decide and approve. The system accelerates your work without removing you from the loop at any critical junction. You stated this explicitly: "the agents were designed with this mentality." Every agent in the system reflects it.

---

### PATTERN 13 — ADAPTIVE SYSTEM AWARENESS

Every agent must identify what kind of session it is entering before it does any substantive work. The agent does not behave the same way for a raw idea, an existing build, a resumed execution session, an auxiliary proposal, or a draft bundle from another agent. It first detects the entry path, announces it out loud, then adapts its behavior to that context.

This pattern exists because the same agent can enter from different doors. If it treats every door the same, it repeats work, asks the wrong questions, or overwrites context that already exists. The fix is explicit adaptive awareness.

The pattern has two parts:

1. **ENTRY POINTS are named explicitly.** Every agent prompt defines its valid entry scenarios and what the agent says when it recognizes each one.
2. **Behavior changes by entry path.** The agent reads existing artifacts before asking new questions, avoids recreating work that already exists, and only produces the missing artifact for that context.

This is most visible in Blueprint Creator:

- **Road A — new build:** if the user has an idea but no build, Blueprint Creator runs a full discovery phase across all nine pillars before producing any document.
- **Road B — existing build:** if the user already has an app, repo, or partially built system, Blueprint Creator reads that existing context first, reports what it found, confirms understanding, and then produces only the missing or weak documents instead of redocumenting everything.

But the same pattern applies differently to every other agent:

- **Architect:** detect bundle import vs raw idea vs PRD update vs auxiliary proposal. Read existing artifacts first; then question only where the gap remains.
- **Execution Spec Gate:** detect fresh Section B vs Section B scope update. Check for an existing task set before generating a new one so duplicate work is not produced silently.
- **Pipeline Strategist:** read existing `decisions.md` before advising. If the question was already decided, surface the prior decision instead of re-deciding it.
- **Operator:** detect new session vs resumed session. Read `session.md`, current git state, and task state before suggesting any execution step.
- **Auxiliary agents:** detect proposal-from-scratch vs existing-artifact review. Inspect relevant files or artifacts first, report what exists, then produce an advisory proposal around the actual current state.

The core rule is simple: **do not act like the system is blank if it is not blank.**

---

### THE SUMMARY — YOUR DESIGN DNA

Looking across all twelve patterns, your agent design philosophy comes down to five core beliefs:

**Precision over speed.** One question at a time. Read everything before asking. Block rather than guess.

**Boundaries over flexibility.** Every agent knows exactly what it does and exactly what it does not do. The boundary is as important as the role.

**Commitment over conversation.** Every session produces a committed artifact. If it is not on disk and committed, it does not exist.

**Humans stay in the loop.** No autonomous execution without approval. The gate is always human.

**The contract is the standard.** Everything — requirements, tasks, implementations, decisions — is measured against the five-element contract. If it cannot pass the contract, it is not done.

**Entry context controls behavior.** Every agent identifies its entry point first, reads what already exists, and adapts instead of starting from zero by default.

These five beliefs appear in every agent you designed. They are your design DNA. Any new agent you build should pass the same test: does it follow these five beliefs? If not, it is not finished.
