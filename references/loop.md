# The Harness Loop

This is the self-optimizing loop that runs in HARNESS and FREESTYLE modes.
In HARNESS mode it runs fully autonomously. In FREESTYLE mode it runs on a
user-specified goal and pauses to report after each iteration.

```
START
  │
  ▼
🏗️  SCAFFOLD
  Create sandbox directory (harness-build/ or cowork-build/).
  Open it in the file explorer.
  Confine all writes there.
  Load memory: recall past outcomes tagged for this mode.
  │
  ▼
🗺️  ROUTE
  Select the highest-value next change.
  Criteria (in order):
    1. Recall past failures — avoid repeating them.
    2. Recall past successes — bias toward patterns that worked.
    3. Identify the weakest link in the current harness state.
    4. Pick ONE change with a clear, verifiable success condition.
  Output: a one-sentence change description + success condition.
  │
  ▼
📋  PLAN
  Design the change in detail before touching any file.
  Output:
    - Exact files to create/edit (paths within sandbox)
    - Exact edits (diffs or full content)
    - How to verify it worked (test command or observable output)
    - Rollback: what to restore if it fails
  │
  ▼
⚙️  EXECUTE
  Checkpoint: snapshot any files about to be modified.
  Apply the plan: write, edit, create files in sandbox only.
  Run the verification command.
  │
  ▼
✅  EVALUATE
  Did verification pass?
    YES → mark as SUCCESS, keep the change.
    NO  → mark as FAILURE, restore checkpoint, discard change.
  Capture: what happened, why it succeeded/failed, what was learned.
  │
  ▼
📝  LOG
  Write to memory store:
    {
      "iteration": N,
      "mode": "harness|cowork|freestyle",
      "change": "one-sentence description",
      "outcome": "success|failure",
      "lesson": "one-sentence generalizable insight",
      "tags": ["harness:", ...]
    }
  Append to harness-build/HARNESS_LOG.md (human-readable).
  │
  ▼
🔁  OPTIMIZE
  Update routing bias:
    - Successful patterns → increase weight in future ROUTE decisions.
    - Failed patterns → add to avoidance list for future ROUTE decisions.
  Check terminal condition:
    - Has the harness reached a stable, high-quality state? (3 consecutive
      successes with no remaining weak links) → emit completion signal.
    - Otherwise → return to ROUTE.
  │
  └──────────────────────────────────────► repeat
```

---

## Iteration Discipline

**One change per iteration.** This is non-negotiable.
A change that "also fixes a few other things" is a bundled change — split it.

Verifiable means: there is a specific command or observable output that
proves the change worked before the next iteration begins. If you can't
define verification before executing, go back to PLAN.

---

## Compounding

The loop gets better because:
- Past successes raise the probability of the next change succeeding.
- Past failures are never repeated.
- The ROUTE step reads the full memory log before choosing — so iteration 50
  is informed by everything iterations 1–49 learned.

---

## Harness Log Format (harness-build/HARNESS_LOG.md)

```markdown
## Iteration N — [timestamp]
**Change:** [one-sentence]
**Outcome:** SUCCESS | FAILURE
**Verification:** [command run] → [output]
**Lesson:** [one-sentence generalizable insight]
---
```

---

## Sandbox Constraint

The EXECUTE step MUST:
1. Resolve all target paths to absolute paths.
2. Verify each path is under the sandbox root before writing.
3. Refuse any write outside the sandbox, log it as a constraint violation,
   and continue with the next iteration.

Reading files outside the sandbox (for reference) is allowed.
Writing outside the sandbox is a hard failure — discard and re-route.
