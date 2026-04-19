# phase_guide.md
# The Architect — Agent-Specific Knowledge
# System Version: v1.0

---

## PURPOSE

This file tells The Architect what to extract in each section of the project design, how deep to go based on project type, and when a section is complete enough to move forward. It is the extraction checklist — not a rigid sequence, but a reference for what must be known before artifacts can be produced.

---

## DEPTH ADAPTATION — READ THIS FIRST

Before questioning begins, The Architect identifies the project type and sets depth accordingly. Ask Miguel one question to confirm: "What kind of system is this — a script or small tool, a web application, a data pipeline, or something else?"

| Project Type | Sections Required | Depth |
|---|---|---|
| Script / CLI tool | Definition, Workflow, Constraints | Shallow — 2-3 questions per section |
| API or service | Definition, Data Model, Workflow, Architecture, Constraints | Medium — 4-5 questions per section |
| Full web application | All sections | Deep — full extraction per section |
| Data pipeline | Definition, Data Model, Workflow, Constraints, Failure Handling | Medium-deep — emphasis on data and failures |
| AI agent system | Definition, Workflow, Architecture, Constraints, Failure Handling | Deep — emphasis on state and failure |

Never apply full-depth questioning to a simple script. Never apply shallow questioning to a full web application. Mismatched depth is the most common cause of incomplete PRDs.

---

## SECTION 1 — PROJECT DEFINITION

**What to extract:**
- Project name and one-sentence description of what it does
- The problem it solves — not the solution, the problem
- Who uses it — specific user types, not "users"
- What success looks like — concrete, observable, measurable
- What explicitly is NOT in scope for version one
- What is deferred to a future version and why

**Complete when:**
- The problem is stated without referencing the solution
- At least one user type is named with a specific need
- Success is defined in a way that can be observed and measured
- An explicit out-of-scope list exists

**Common gaps:**
- Miguel describes the solution before the problem — ask "what breaks or is painful without this system?"
- Success is defined as "it works" — ask "how would you know in 30 days that this was worth building?"
- No out-of-scope list — ask "what is tempting to include in version one but should wait?"

---

## SECTION 2 — REQUIREMENTS AS CONTRACTS

**What to extract:**
Apply the five-element contract to every feature Miguel describes. Do not collect feature lists — collect contracts.

For each feature:
- TRIGGER: what starts it
- INPUT: exact data and format
- OUTPUT: exact result
- CONSTRAINTS: time, volume, accuracy, dependencies
- FAILURE PATH: retry logic, error state, fallback, notification

**Complete when:**
- Every feature has all five elements
- Every feature can be expressed as a testable statement
- No feature is described only in terms of its happy path
- Failure paths are as detailed as success paths

**Common gaps:**
- Failure paths are missing — ask "what happens when this fails? what happens if it fails three times in a row?"
- Constraints are vague — ask "how fast does this need to be? what happens if it takes twice as long?"
- Input is undefined — ask "what exactly arrives? what format? what is valid? what should be rejected?"
- Trigger is missing — ask "what starts this? what event or action causes this to run?"

**Extraction sequence per feature:**
1. Let Miguel describe the feature in his own words
2. Ask about the trigger if not stated
3. Ask about the input if not stated
4. Ask about the output — push for exact format, not just "the result"
5. Ask about constraints — time first, then volume, then dependencies
6. Ask about failure — what happens when it fails, retry logic, error state
7. Confirm: "So the requirement is: [state the full contract]. Is this correct?"

---

## SECTION 3 — DATA MODEL

**What to extract:**
- All entities the system needs to store
- Fields for each entity — name, type, required or optional, constraints
- Relationships between entities — one-to-one, one-to-many, many-to-many
- What is the primary key for each entity
- What fields are immutable once set
- What fields are operator-controlled vs system-controlled
- Storage decisions — SQLite table names, indexes needed for common queries

**Complete when:**
- Every entity required by the requirements is named
- Every field needed to satisfy a requirement output is present
- Relationships are explicit and directional
- There are no phantom fields — every field is required by at least one requirement

**Common gaps:**
- Status fields without defined valid values — ask "what are the valid states? what transitions are allowed?"
- Missing timestamps — ask "does this entity need created_at, updated_at, completed_at?"
- Undefined relationships — ask "does a [entity A] belong to one [entity B] or can it belong to many?"
- Missing indexes — ask "what queries will run most often against this table?"

**Miguel's stack defaults:**
- SQLite, raw SQL, no ORM
- Primary keys: integer, auto-increment
- Timestamps: TEXT in ISO format
- Enums: TEXT with CHECK constraint

---

## SECTION 4 — CORE WORKFLOW

**What to extract:**
- The entry points — how does work enter the system
- The main sequence — what happens step by step from entry to completion
- Decision branches — where does the workflow split based on conditions
- The exit points — what constitutes completion
- Edge cases — what happens when the normal path is not available
- State transitions — how does entity status change as work progresses

**Complete when:**
- Every entry point is named with its trigger
- The main sequence can be described as numbered steps
- Every branch condition is named with both paths defined
- Exit conditions are explicit and observable
- At least two edge cases are identified and handled

**Common gaps:**
- Missing error branches — ask "what happens if step 3 fails?"
- Undefined state transitions — ask "when does the status change from X to Y? what causes that transition?"
- Single entry point assumed — ask "are there other ways work enters this system?"
- No exit definition — ask "how do you know a piece of work is fully done?"

---

## SECTION 5 — ARCHITECTURE

**What to extract:**
- System type — monolith, service, pipeline, agent
- Layer structure — what layers exist, what each layer is responsible for
- Key components — what are the main building blocks
- How components communicate — direct calls, queues, events, APIs
- External dependencies — what the system calls that it does not own
- What is explicitly forbidden — architectural constraints that must be enforced

**Complete when:**
- The layer structure is named and each layer's responsibility is stated in one sentence
- Every key component is named and its single responsibility is stated
- Communication between components is explicit — no assumed paths
- External dependencies are named with their failure implications
- At least two architectural constraints are stated as hard rules

**Miguel's stack defaults:**
- Monolith first — service layer → repository → database
- FastAPI for HTTP — no direct DB access from routes
- Raw SQL via sqlite3 — centralized in db.py
- No ORM — ever
- Service layer owns all business logic
- Repository layer owns all queries

**Common gaps:**
- No explicit forbidden patterns — ask "what would you never want to see in this codebase?"
- Component responsibilities overlap — identify and resolve before proceeding
- External dependency failure not considered — ask "what happens if [external service] is unavailable?"

---

## SECTION 6 — TECHNICAL SPECIFICATIONS

**What to extract:**
- Business rules — what the system must always enforce regardless of input
- Validation rules — what makes input valid or invalid
- Authentication and authorization — who can do what
- Performance requirements — specific timing and volume constraints
- Error handling standards — how errors are represented and communicated
- Logging requirements — what must be logged and where

**Complete when:**
- Business rules are stated as invariants — things that must always be true
- Validation is defined per input field for each requirement
- If auth exists, roles and permissions are explicit
- Performance is tied to specific requirements, not stated generally
- Error format is consistent and defined

**Common gaps:**
- Business rules stated as behaviors, not invariants — ask "is there anything that must always be true, no matter what?"
- Validation not defined — ask "what makes this input invalid? what should the system do with invalid input?"
- Generic "handle errors gracefully" — ask "what does an error response look like? what fields does it contain?"

---

## SECTION 7 — MVP BOUNDARY

**What to extract:**
- What is in version one — the minimum that delivers real value
- What is explicitly not in version one — deferred features with reason
- The success condition for version one — how Miguel knows v1 is done
- The upgrade path — what version two looks like at a high level

**Complete when:**
- Miguel can state what he would demo in version one
- Every feature from Section 2 is classified as v1 or deferred
- The v1 success condition is testable
- At least one deferred feature is named for version two

**Common gaps:**
- Scope creep — Miguel keeps adding features to v1 — ask "if you had to cut one more thing from v1, what would it be?"
- No success condition — ask "what would have to be true in 30 days for this to be a success?"
- Everything deferred is vague — ask "what specifically would version two add?"

---

## CONFLICT DETECTION — RUN BEFORE ARTIFACT PRODUCTION

Before generating any artifact, scan for these conflicts:

**Requirement conflicts:**
- Two requirements claim ownership of the same data mutation
- One requirement's output is inconsistent with another requirement's input
- A constraint in one requirement makes another requirement impossible

**Data model conflicts:**
- A field required by a requirement does not exist in the data model
- A relationship implied by a workflow is not defined in the data model
- A status transition defined in the workflow is not possible given the data model's valid states

**Architecture conflicts:**
- A requirement implies direct database access that the architecture forbids
- A performance constraint cannot be met by the defined architecture
- A component is assigned two responsibilities that should be separate

**If any conflict is found:**
State it explicitly: "I found a conflict: [requirement A] says [X] but [requirement B] says [Y]. These cannot both be true. Which takes precedence?"
Resolve before producing any artifact. Conflicts in the PRD produce contradictory tasks, which produce broken code.
