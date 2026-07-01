# Godcoder Modes

## ASK
Read-only. Answer questions about the codebase. No file edits. No terminal.
Tools available: read_file, codebase_search (if context engine on), web_search.
Exit condition: user says "done" or switches mode.

---

## PLAN
Read + plan. Analyze the project, produce a structured implementation plan.
No code changes made. Output: numbered task list with file paths and success criteria.
User approves plan before any execution happens.
Tools available: read_file, codebase_search, list_directory.
Exit condition: user approves or rejects plan.

---

## CODING
Directed coding. User provides a task. Agent executes it, shows diff, asks for approval.
One task at a time. Checkpoints before every write.
Tools available: all tools. Approval gate on first write per session.
Exit condition: task complete and user confirms.

---

## FREESTYLE
Autonomous, directed. User provides a goal; agent executes without per-step approval.
All tool calls auto-approved after first confirmation.
Checkpoint before every file write. Clear button resets conversation.
Loop: Plan → Execute → Verify → Report → ask for next task.
Exit condition: user says stop or goal is achieved.

---

## HARNESS
**Autonomous self-improvement.** No prompt needed. The agent builds and improves its
own harness inside `harness-build/`.

The defining mode. Full loop runs continuously:
```
Scaffold → Route → Plan → Execute → Evaluate → Log → Optimize → repeat
```

See `references/loop.md` for the complete protocol.

Sandbox: `harness-build/` (created on start, opened in file explorer)
Memory: persistent, tagged `harness:` — lessons steer future iterations.
Exit condition: user says stop, or loop detects a terminal improvement condition.

---

## COWORK
**Autonomous GUI/OS actuation.** Trains on and drives the Open Cowork desktop app.
See `references/cowork.md` for the full protocol.

Sandbox: `cowork-build/`
Memory: persistent, tagged `cowork:` — coworking lessons compound.
Actuation: for any step a human would do at keyboard/screen, gets an `act` plan
and carries it out via GUI automation, verifying each step with a screenshot.
Only physical-world steps are handed back to the user.
Exit condition: user says stop, or objective is complete.
