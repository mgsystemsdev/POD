# requirement_contract.md
# System Version: v1.0
# Shared across: The Architect, Execution Spec Gate, Pipeline Strategist, The Operator

---

## WHAT A REQUIREMENT IS

A requirement is a testable contract between the system and the person who uses it.

If you cannot write a test that passes when it works and fails when it does not — it is not a requirement. It is a wish. Wishes do not enter the PRD. Contracts do.

Every feature Miguel describes starts as a wish. The Architect's job is to turn it into a contract. The Execution Spec Gate's job is to encode that contract into tasks. The Operator's job is to verify the contract is satisfied. The Pipeline Strategist's job is to reason from the contract when decisions need to be made.

The requirement contract is the spine of the entire system. Break it anywhere and the system produces untestable code that works in the happy path and fails silently at the edges.

---

## THE FIVE ELEMENTS

All five are required. No exceptions. A requirement missing any element is incomplete and does not enter the PRD until the missing element is defined.

### TRIGGER
What starts this? What event, action, or condition initiates the behavior?
- A user action (button click, form submit, API call)
- A system event (cron job, file arrival, database state change)
- An external event (webhook, email received, timer)

If there is no trigger, the requirement has no entry point and cannot be built or tested.

### INPUT
What exact data arrives when the trigger fires?
- What fields are present?
- What format is each field (string, integer, enum, JSON object)?
- What is the valid range or set of values?
- What is explicitly invalid and must be rejected?

If the input is undefined, the implementation will invent its own interpretation. That interpretation will be wrong under conditions the developer did not anticipate.

### OUTPUT
What exact result is produced when the requirement executes successfully?
- What is returned, stored, or sent?
- What format?
- What does the recipient of that output receive?
- What does success look like in a way that can be observed and measured?

If the output is undefined, there is no done condition. The task cannot be verified. "It works" is not an output definition.

### CONSTRAINTS
What limits apply to this requirement?
- Time: must complete within X milliseconds or seconds
- Volume: must handle X records or concurrent users
- Accuracy: must produce correct results X percent of the time
- Dependencies: requires Y to be complete or available
- Cost: must not exceed X API calls or compute units

If constraints are undefined, the implementation will make its own choices. Those choices will cause problems at scale or under load.

### FAILURE PATH
What happens when the requirement cannot complete successfully?
- What is the retry logic? How many times? What interval?
- What is the error state? Where is it stored?
- What is the fallback behavior if all retries fail?
- Who or what is notified?
- Does the failure affect other parts of the system?

If the failure path is undefined, failures will be silent. Silent failures are the most expensive kind. They compound. They produce inconsistent state. They are discovered weeks after they first occurred.

---

## THE CONTRACT TEST

Before any requirement enters the PRD, apply this test:

Can I write a test that:
- Fires the trigger with a valid input
- Checks that the output matches the defined output specification
- Checks that the constraint is satisfied (timing, volume, accuracy)
- Fires the trigger with an invalid input and checks the failure path executes correctly

If yes → it is a requirement. It enters the PRD.
If no → identify which element is missing and ask the question that fills it. Do not proceed until all five elements are present.

---

## BAD VERSUS GOOD — THREE EXAMPLES

### Example 1 — Task classification

BAD: "The system handles support tickets."

GOOD:
```
TRIGGER:      A new ticket row is inserted into the tickets table with status = 'unclassified'.
INPUT:        ticket_id (integer), subject (string, max 200 chars), body (string, max 5000 chars).
OUTPUT:       tickets row updated with category field set to one of: billing, technical, account, feedback, other. classification_confidence field set to float 0.0-1.0.
CONSTRAINTS:  Must complete within 2 seconds of insert. Must not fail if body is empty — default to category 'other' with confidence 0.0.
FAILURE PATH: On classification error, retry up to 3 times with 500ms interval. If all retries fail, set category = 'unclassified_error', log error to runs table with error_message, alert via dashboard flag.
```

### Example 2 — Job search

BAD: "Users can search for jobs."

GOOD:
```
TRIGGER:      User submits search form with at least one filter field populated.
INPUT:        JSON object — keywords (string, optional), location (string, optional), status (enum: pending/applied/rejected/offer, optional), date_range (object with from/to ISO dates, optional). At least one field must be non-null.
OUTPUT:       Array of job records matching ALL active filters, sorted by created_at descending, maximum 50 results. Each record contains: id, title, company, location, status, created_at. Empty array if no matches — never null.
CONSTRAINTS:  Must return within 1 second for datasets up to 10,000 records. If zero filters are active, reject the request — do not return all records.
FAILURE PATH: If query exceeds 3 seconds, return partial results with a timeout:true flag in the response envelope. Log the slow query to the decisions table. Never return a 500 — always return a structured response.
```

### Example 3 — Task execution worker

BAD: "The worker runs tasks."

GOOD:
```
TRIGGER:      Operator runs python system/services/task_worker.py --mode manual from agent-services directory.
INPUT:        No direct input. Worker reads from SQLite tasks table. Selects one task where status = 'pending', ordered by priority desc, created_at asc.
OUTPUT:       Task row updated to status = 'in_progress'. Run row created with status = 'pending_input' and input_prompt populated. Terminal prints: READY task_id=[id] run_id=[id]. Worker exits.
CONSTRAINTS:  Must claim exactly one task per invocation. Must not claim a task already claimed by another process. Must exit cleanly if no pending tasks exist — no error, no exception.
FAILURE PATH: If prompt build fails due to missing context files, set task status = 'blocked', run status = 'failed', error_message = specific file path that was missing. Print diagnostic to terminal. Exit with code 1.
```

---

## HOW EACH AGENT USES THIS CONTRACT

### The Architect
Uses the five elements as a gate. Every feature Miguel describes is questioned through the contract template before entering the PRD. The Architect asks about the trigger, then the input, then the output, then the constraints, then the failure path — one element at a time if Miguel does not volunteer them. When all five are present and testable, the requirement enters the PRD. Not before.

When Miguel does not know an answer, The Architect presents three concrete options with tradeoffs and recommends one. Miguel reacts. The contract gets filled. The Architect never leaves a gap empty.

### Execution Spec Gate
Reads every requirement in the PRD and derives task content directly from the contract elements.

- Done condition → derived from OUTPUT element
- Task constraints → derived from CONSTRAINTS element
- Failure behavior field → derived from FAILURE PATH element
- Scope and order → derived from dependency relationships between requirements

Every task produced by the Execution Spec Gate must trace back to a specific requirement. Tasks without a requirement reference are rejected — they indicate scope that was never formally defined.

### The Pipeline Strategist
When advising on an implementation decision, always reads the relevant requirement contract first. Decisions must not violate any contract element. If a proposed solution cannot satisfy the CONSTRAINTS element or cannot implement the FAILURE PATH element, the Pipeline Strategist says so explicitly and offers alternatives that can.

When new scope is identified during execution, the Pipeline Strategist does not formalize new requirements itself. New scope without a contract goes back to The Architect, not to the Execution Spec Gate.

### The Operator
Verification step checks the requirement contract, not just the task description.

After implementation, the Operator verifies:
- TRIGGER: is the trigger correctly handled in code?
- INPUT: is input validated as defined? Invalid inputs rejected as defined?
- OUTPUT: does the output match the exact specification?
- CONSTRAINTS: are timing, volume, and accuracy constraints met?
- FAILURE PATH: is the failure path implemented? Does it retry as defined? Does it produce the correct error state?

"It works" is never sufficient. The contract is sufficient.

---

## WHEN THE CONTRACT IS INCOMPLETE

If a requirement enters the PRD with missing elements — this should not happen if The Architect ran correctly, but it can happen when requirements change mid-execution — any agent that detects an incomplete contract stops and surfaces it immediately.

The agent does not try to infer the missing element. It does not make an assumption. It says: "Requirement [name] is missing its [element]. I cannot proceed until this is defined. Take this back to The Architect."

Missing contract elements are always upstream problems. They are fixed upstream, not patched downstream.

---

## CONTRACT VERSIONING

When a requirement changes, the change is logged. The PRD is updated with the new contract. The Execution Spec Gate is re-run for affected tasks. Tasks already completed against the old contract are reviewed — do they still satisfy the new contract or do they need to be redone?

A changed requirement is not a small thing. It potentially invalidates work already done. This is surfaced explicitly. Miguel decides whether to update existing implementation or accept the delta. The decision is logged to decisions.md.
