# ⚡ Godcoder

> A self-optimizing AI agent skill that auto-builds a task-specific harness on every message, discovers relevant installed skills, and loops until the job is done.

---

## 🧠 What it does

Godcoder fires **automatically on every message** — no invocation phrase needed. For each request it:

1. 🔍 **Classifies** the task (code / write / file / research / plan / debug / creative / pipeline)
2. 🛰️ **Scans** all installed skills and loads the relevant ones
3. 🏗️ **Scaffolds** a task-specific sandbox at `harness-build/{task_id}/`
4. 🔁 **Runs the loop** until the task is complete

```
ROUTE → PLAN → EXECUTE → EVALUATE → LOG → OPTIMIZE → repeat
```

5. 🧠 **Persists lessons** to SQLite memory — every task makes future tasks smarter

---

## 🔌 Skill Awareness

Godcoder auto-detects and combines whichever installed skills are relevant:

| Skill | Activates when |
|---|---|
| `superpowers-aio` | Any coding, debugging, or architecture task |
| `meta-skills-aio` | Every task — decomposition + assumption audit |
| `github-push` | Task produces files to commit |
| `product-optimizer` | Improving a product, app, or workflow |
| `docx / pdf / pptx / xlsx` | Document or file output tasks |
| `frontend-design` | UI, HTML, React, or visual design |
| `file-reading / pdf-reading` | User uploads a file |
| `product-self-knowledge` | Questions about Claude's own capabilities |

Skill conflicts are resolved by priority order — Godcoder's loop always wins on iteration structure.

---

## 📁 Structure

```
godcoder/
├── SKILL.md                   # Main skill — auto-triggers on every message
├── references/
│   ├── loop.md                # Scaffold → Route → Plan → Execute → Evaluate → Log → Optimize
│   ├── memory.md              # Log schema, recall patterns, cost tracking
│   ├── tools.md               # Tool inventory, approval model, mode matrix
│   ├── modes.md               # Harness / CoWork / Freestyle mechanics
│   └── cowork.md              # GUI actuation protocol
└── tools/
    ├── scaffold.py            # Creates task-scoped sandbox (harness-build/{task_id}/)
    ├── skill_scanner.py       # Discovers + scores installed skills for this task
    ├── memory.py              # SQLite log / recall / route / optimize
    ├── checkpoint.py          # File snapshot save / restore / diff
    ├── state.py               # Reads/writes harness.json per task
    └── context_engine.py      # Optional semantic+graph search (Qdrant + FalkorDB)
```

---

## 🔄 The Loop

Each iteration is **one decisive, verifiable change**:

```
🏗️  SCAFFOLD   create sandbox, load memory, scan skills
🗺️  ROUTE      pick highest-value next action (informed by past outcomes)
📋  PLAN       design the change + define verification before touching files
⚙️  EXECUTE    checkpoint → apply → verify
✅  EVALUATE   pass → keep | fail → restore checkpoint + re-route
📝  LOG        persist structured entry to SQLite + HARNESS_LOG.md
🔁  OPTIMIZE   update routing weights → check completion → repeat
```

Every sandbox gets a human-readable `HARNESS_LOG.md`:

```markdown
## Iteration 3 — 2026-06-30 10:41
**Change:** Added error recovery to file-write wrapper
**Outcome:** ✅ SUCCESS
**Verification:** pytest tools/test_write.py → 4 passed
**Lesson:** try/except + checkpoint restore prevents cascade failures
```

---

## 💾 Persistent Memory

Memory lives at `~/.godcoder/memory.db` (SQLite, zero setup). It survives session restarts and compounds across tasks.

```bash
# Recall what worked on similar tasks
python tools/memory.py recall --query "what changes succeeded" --tags "harness:"

# See stats across all tasks
python tools/memory.py stats
```

Each entry stores: `task_id`, `change`, `outcome`, `lesson`, `tags`, `token cost`.

---

## 🛡️ Hard Rules

- ❌ Never writes outside the active sandbox
- ❌ Never asks "should I continue?" — just continues
- ❌ Never announces that it's running
- ✅ First tool call per session requires confirmation — all subsequent are auto-approved
- ✅ Checkpoint before every file write
- ✅ One change per iteration, always verifiable before the next begins

---

## 📦 Install

```bash
npx skills add ./godcoder
```

Or upload the zip via **Claude.ai → Settings → Features → Custom Skills**.

---

## 🧰 Tools (dependency-free)

| Tool | Purpose |
|---|---|
| `scaffold.py` | Creates `harness-build/{task_id}/` with `harness.json` + log |
| `skill_scanner.py` | Parses frontmatter of all skills, scores relevance to current task |
| `memory.py` | SQLite-backed log / recall / route / optimize |
| `checkpoint.py` | Snapshot + restore files before risky edits |
| `state.py` | Read/write `harness.json` state during iteration |
| `context_engine.py` | Optional semantic search via Qdrant — fails gracefully if offline |

---

## 🌐 Inspired by

[eli-labz/Godcoder](https://github.com/eli-labz/Godcoder) — extended with task-scoped sandboxing, persistent SQLite memory, automatic skill discovery, and skill composition rules.

---

<p align="center">Built to run on every message. Stops when the job is done.</p>
