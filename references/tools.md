# Godcoder Tool Inventory

## Approval Model

- **First tool call per session**: requires user confirmation.
- **All subsequent calls**: auto-approved (no per-call gate).
- **Exception**: `bash` commands that are destructive outside the sandbox
  (rm -rf, git reset --hard, etc.) always require explicit confirmation.
- **Clear button**: resets session conversation and context. Does NOT delete
  sandbox files. Start fresh conversation, sandbox persists.

---

## File Tools

### read_file(path)
Read any file in the project (including outside sandbox — read-only reference).
Returns: file contents as string.

### write_file(path, content)
Write a file. MUST be within active sandbox. Checkpoints automatically before
first write to any given path per iteration.
Returns: confirmation + bytes written.

### edit_file(path, old_str, new_str)
In-place edit via string replacement. Unique match required — fails if old_str
appears 0 or 2+ times. Safer than write_file for surgical edits.
Returns: diff of the change.

### list_directory(path)
List files and directories up to 2 levels deep.
Returns: tree structure.

### delete_file(path)
Delete a file. MUST be within active sandbox.
Returns: confirmation.

---

## Search Tools

### file_search(pattern, root?)
Glob pattern search over the project tree.
Returns: matching paths.

### text_search(query, root?, file_glob?)
Grep-style text search. Supports regex.
Returns: matching lines with file:line references.

### codebase_search(query) [Context Engine required]
Semantic + structural search over the indexed repo.
Queries Qdrant (vectors) + FalkorDB (call graph) + BM25 (lexical).
Returns: ranked results with file:line references and relevance scores.

### codebase_graph(symbol) [Context Engine required]
Call-graph traversal. Returns callers, callees, and definition sites for a symbol.
Returns: graph nodes with file:line references.

---

## Execution Tools

### bash(command, cwd?)
Run a shell command. cwd defaults to sandbox root.
Returns: stdout, stderr, exit code.

Use for: running tests, compilers, linters, build tools, verification commands.
Avoid: destructive commands outside sandbox (always confirm those).

---

## Checkpoint Tools

### checkpoint_save(label?)
Snapshot all files modified so far this iteration into a checkpoint.
Returns: checkpoint ID.

### checkpoint_restore(checkpoint_id)
Restore files to the state captured in a checkpoint.
Called automatically on EVALUATE → FAILURE.
Returns: list of restored files.

### checkpoint_diff(checkpoint_id)
Show diff between checkpoint and current state.
Returns: unified diff.

### checkpoint_list()
List all checkpoints for the current session.
Returns: checkpoint IDs with timestamps and labels.

---

## Memory Tools (ResearchSwarm bridge)

### memory_log(entry)
Write a structured log entry to the persistent memory store.
Entry schema: `{iteration, mode, change, outcome, lesson, tags[]}`.
Also appends human-readable entry to `harness-build/HARNESS_LOG.md`.

### memory_recall(query, tags?, limit?)
Semantic recall from the persistent memory store.
Returns: ranked past entries matching the query, filtered by tags if provided.
Use in ROUTE step: `memory_recall("what changes succeeded", tags=["harness:"])`

### memory_route(context)
Ask the memory store for the highest-value next change given current context.
Returns: ranked candidate changes with confidence scores based on past outcomes.
Use this as the primary ROUTE mechanism in HARNESS mode.

### memory_optimize(iteration_result)
Update routing weights based on latest iteration outcome.
Called automatically in OPTIMIZE step.

---

## MCP Tools (user-configured)

Any MCP server configured in Settings is available as additional tools.
MCP tools follow the same approval model (first call confirmed, rest auto).
Common MCP extensions: web search, GitHub, file system, browser automation.

---

## Voice Tools (if configured)

### tts(text, voice?)
Text-to-speech. Speaks the text using the configured TTS provider.

### stt() 
Start speech-to-text capture. Returns transcribed text.

---

## Tool Availability by Mode

| Tool              | Ask | Plan | Coding | Freestyle | Harness | CoWork |
|---|---|---|---|---|---|---|
| read_file         | ✅  | ✅   | ✅     | ✅        | ✅      | ✅     |
| write_file        | ❌  | ❌   | ✅     | ✅        | ✅      | ✅     |
| edit_file         | ❌  | ❌   | ✅     | ✅        | ✅      | ✅     |
| bash              | ❌  | ❌   | ✅     | ✅        | ✅      | ✅     |
| checkpoint_*      | ❌  | ❌   | ✅     | ✅        | ✅      | ✅     |
| memory_*          | ❌  | ❌   | ❌     | ✅        | ✅      | ✅     |
| codebase_search   | ✅  | ✅   | ✅     | ✅        | ✅      | ✅     |
| cowork_act        | ❌  | ❌   | ❌     | ❌        | ❌      | ✅     |
| cowork_screenshot | ❌  | ❌   | ❌     | ❌        | ❌      | ✅     |
