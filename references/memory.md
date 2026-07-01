# Persistent Memory Protocol

Godcoder's memory is the mechanism that makes the harness self-optimizing.
Without memory, each iteration is independent. With memory, iteration N is
informed by everything iterations 1 through N-1 learned.

---

## Memory Store

The ResearchSwarm bridge exposes four memory operations:

| Operation | When to call | What it does |
|---|---|---|
| `memory_log(entry)` | End of every iteration (LOG step) | Persists structured outcome |
| `memory_recall(query, tags)` | Start of ROUTE step | Retrieves relevant past outcomes |
| `memory_route(context)` | ROUTE step | Returns ranked next-change candidates |
| `memory_optimize(result)` | OPTIMIZE step | Updates routing weights |

---

## Log Entry Schema

Every iteration MUST produce exactly one log entry:

```json
{
  "iteration": 12,
  "mode": "harness",
  "timestamp": "2026-06-29T14:32:00Z",
  "change": "Added error recovery to the file-write tool wrapper",
  "outcome": "success",
  "verification": "pytest tools/test_file_write.py → 4 passed",
  "lesson": "Wrapping tool calls in try/except with checkpoint restore prevents cascade failures",
  "tags": ["harness:", "tools", "error-handling"],
  "cost": {
    "tokens_in": 1240,
    "tokens_out": 380
  }
}
```

Fields:
- `iteration`: monotonically increasing integer per session
- `mode`: "harness" | "cowork" | "freestyle"
- `change`: one sentence, past tense, specific
- `outcome`: "success" | "failure"
- `verification`: exact command run + output summary
- `lesson`: one sentence, generalized — useful to a future iteration that may not
  remember the specifics
- `tags`: always include the mode prefix tag (`harness:`, `cowork:`) plus
  semantic tags for the domain touched
- `cost`: token counts for the iteration (enables cost-per-improvement tracking)

---

## Tag Namespaces

Use consistent tags so `memory_recall` can filter precisely:

| Namespace | Purpose |
|---|---|
| `harness:` | Harness mode entries |
| `cowork:` | CoWork mode entries |
| `tools` | Changes to tool wrappers or tool logic |
| `loop` | Changes to the harness loop itself |
| `routing` | Changes to route/prioritization logic |
| `scaffold` | Changes to sandbox setup or scaffolding |
| `memory` | Changes to memory/recall logic |
| `eval` | Changes to evaluation/verification logic |
| `error` | Error-recovery related |
| `perf` | Performance improvements |

---

## Recall Pattern (ROUTE step)

At the start of every ROUTE step, run:

```
successes = memory_recall(
    query="what kinds of changes succeeded",
    tags=["harness:"],
    limit=10
)
failures = memory_recall(
    query="what changes failed and why",
    tags=["harness:"],
    limit=10
)
```

Then pass both to `memory_route(context)` along with the current harness state
(a brief description of what exists now and what seems weakest).

The route call returns a ranked list of candidate changes. Take the top candidate
unless there's a strong reason to override it (e.g., you just tried it and it failed).

---

## Human-Readable Log

In addition to the structured store, append to `harness-build/HARNESS_LOG.md`:

```markdown
## Iteration 12 — 2026-06-29 14:32
**Change:** Added error recovery to the file-write tool wrapper
**Outcome:** ✅ SUCCESS
**Verification:** `pytest tools/test_file_write.py` → 4 passed
**Lesson:** Wrapping tool calls in try/except with checkpoint restore prevents cascade failures
---
```

This file is the human-readable audit trail. It opens automatically with the sandbox.

---

## Memory Across Sessions

The ResearchSwarm bridge persists memory to a local SQLite store in the app data
directory (same location as session SQLite). Memory survives:
- Session restarts
- App restarts
- New sessions in the same project

Memory does NOT cross:
- Different sandbox directories
- Different mode namespaces (harness: entries don't pollute cowork: recalls)

---

## Cost Tracking

The `cost` field in every log entry enables:
- Total tokens spent per session
- Average tokens per successful improvement
- ROI: improvements per 1K tokens

Emit a cost summary every 10 iterations:
```
📊 Cost snapshot: 10 iterations, 8 successes, ~18K tokens total (~2.2K/improvement)
```
