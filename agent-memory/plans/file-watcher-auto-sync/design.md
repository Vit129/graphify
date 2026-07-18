# File-Watcher Auto-Sync — Design

Source: P17 item 1 (`agent-memory/plans/p17-post-competitor-audit-roadmap.md`), PR #14.

## Orientation (before design — required by this doc's own P17 instruction)

Confirmed by reading the real code, not assumed:

- `graphify watch` (`graphify/watch.py:1010`, dispatched from `graphify/__main__.py:3539`) **already
  exists and is fully functional** — a real `watchdog`-based daemon (`Observer`/`PollingObserver`,
  `FileSystemEventHandler`, 3s debounce, `.graphifyignore`-aware, code/doc-change split, calls the same
  `_rebuild_code()` `update` uses). It is not a stub or partial implementation.
- It is **opt-in and foreground-blocking**: `watchdog` is an optional extra (`pyproject.toml:62`,
  `watch = ["watchdog"]`, not installed by default), and `watch()`'s main loop is `while True: time.sleep(0.5)`
  (`watch.py:1080`) — a human must run `graphify watch .` in a dedicated terminal and leave it running.
- **There is no hook that triggers a rebuild after an AI agent's own edits.** Grepped the whole codebase
  for `PostToolUse` — zero matches. The only installed Claude Code hook is `PreToolUse`
  (`_SETTINGS_HOOK`/`_READ_SETTINGS_HOOK`, `__main__.py:470-524`), which nudges the agent to *query* the
  graph before reading raw files — it says nothing about keeping the graph fresh after a write.
- **`_install_claude_hook`'s own printed message is currently false advertising**: `__main__.py:1980-1981`
  prints *"Claude Code will now check the knowledge graph before answering codebase questions and rebuild
  it after code changes"* — the second half describes a feature that doesn't exist. This design closes
  that gap for real, rather than just fixing the sentence.
- This session hit the resulting gap directly twice (Home-Assistant, Fitness-Tracker) and needed a manual
  `graphify update .` (once even needing a manual `graphify-out/cache` wipe, since the SHA256 cache tracks
  file content, not extractor-code version — a narrower issue, out of scope here, only affects people
  developing graphify's own extractors).

**Conclusion: the gap is not "missing rebuild engine," it's "nothing invokes it automatically for the
one workflow graphify is actually built around — an AI agent editing files in the same session that
queries the graph."** This reframes the fix from "port a competitor's file-watcher" to "wire up a
capability graphify already built and already claims to have."

## Strategic Design

This is a CLI/tooling feature, not a business-domain model — bounded-context/aggregate/domain-event
vocabulary doesn't map cleanly onto it, so this section states that plainly rather than forcing a fit.
The one real strategic decision is **which of two competing mechanisms** closes the gap:

| | **A. Auto-start the existing daemon** | **B. Hook-triggered incremental update** |
|---|---|---|
| Mechanism | A `SessionStart` hook spawns `graphify watch <project> &` (detached) once per project per machine, if not already running | A `PostToolUse` hook (matcher `Edit\|Write\|MultiEdit`) runs `graphify update <project> &` (detached) after every agent write |
| New dependency | Requires `watchdog` installed (optional extra) — must degrade gracefully when absent | None — reuses the same `update` path CLAUDE.md already documents running manually |
| New failure modes | Daemon lifecycle: orphaned processes across session restarts/crashes, needs a PID file + liveness check, needs cleanup on the *last* session for a project to end (not obvious when that is with multiple concurrent agent sessions) | None new — a background `update` call is a fire-and-forget subprocess, same shape as `webbrowser.open`'s pattern already in this codebase (P14) |
| Solves | Both agent edits AND a human editing the same repo in an IDE in parallel | Only edits the agent itself makes through its own tool calls |
| Redundant work | None (event-driven on real filesystem changes) | Could double-fire on `MultiEdit` (N file edits in one call) or fire once per `Edit` in a rapid sequence — needs the SAME debounce discipline `watch.py` already has, just reimplemented at the hook layer |

**Decision: B (hook-triggered incremental update), not A.** Reasoning:
1. B closes the *exact* gap this session hit — an agent forgetting to rebuild after its own edits — with
   zero new dependency and zero new process-lifecycle surface to get wrong. A solves a **different**,
   real-but-unconfirmed problem (a human editing in parallel) that no evidence from this session or the
   competitor audit specifically calls for.
2. B directly fixes `_install_claude_hook`'s existing false claim (a `PreToolUse`+`PostToolUse` pair,
   mirroring the two hooks that already exist for reads) rather than introducing a third, heavier
   mechanism alongside it.
3. A remains available as-is for the "human in an IDE" case — this design does not remove or change
   `graphify watch`, it just doesn't make it the default. Revisit A only if a real case surfaces where a
   human's parallel edits go unnoticed because no agent tool call touched that file.

## Tactical Design

No entities/aggregates in the DDD sense — the "thing being modified" is a JSON file on disk
(`graph.json`), already modeled by the existing `_rebuild_code()` pipeline, not a new domain concept.
The only new "event" is procedural: **AgentWroteFile → debounced background graph update**, described
as a state machine rather than a domain event stream (this is infrastructure, not a bounded context with
its own lifecycle):

```
Edit/Write/MultiEdit tool call completes
  -> PostToolUse hook fires, matcher "Edit|Write|MultiEdit"
  -> parse tool_input.file_path (or file_path list for MultiEdit) from stdin JSON (same
     python3 -c "..." pattern _SETTINGS_HOOK/_READ_SETTINGS_HOOK already use)
  -> bail (fail open, exit 0) if: graphify-out/graph.json doesn't exist, OR file_path is
     under graphify-out/ (avoid a self-triggered rebuild loop), OR the extension isn't in
     a watched set (mirror watch.py's _WATCHED_EXTENSIONS)
  -> touch a debounce marker file under graphify-out/.pending-update (mtime = now); if a
     background updater for this project is already running (PID file check, same
     _rebuild_lock() pattern watch.py:93 already uses for its own concurrency guard),
     do nothing further - it will pick up the new marker
  -> else spawn `graphify update <project-root> &` detached (setsid/nohup-equivalent,
     stdout/stderr to graphify-out/.update.log so failures are inspectable, never
     surfaced as hook output - this must never block or fail the agent's turn)
```

Debounce reuses `watch.py`'s own constants/thresholds (3s) rather than inventing new ones, so the two
code paths (persistent `watch`, hook-triggered `update`) behave identically if a user runs both.

## Logical Design

**New CLI surface**: none required — this wires the hook installer to an *existing* command
(`graphify update <path>`), it does not add a new subcommand.

**Changed files**:
- `graphify/__main__.py` — add `_POST_EDIT_HOOK` (or similarly-named constant, matching
  `_SETTINGS_HOOK`/`_READ_SETTINGS_HOOK`'s existing naming) with `"matcher": "Edit|Write|MultiEdit"`, a
  `PostToolUse` hook body following the same `python3 -c "..."` stdin-parsing convention. Register it in
  `_install_claude_hook` alongside the two existing `PreToolUse` entries (add a `hooks["PostToolUse"]`
  key). Update `_uninstall_claude_hook` symmetrically. Fix the now-true printed claim at lines 1980-1981
  (no wording change needed once this actually ships — currently false, becomes true).
- `graphify/watch.py` — expose the debounce-and-spawn logic as an importable function (e.g.
  `trigger_background_update(project_root: Path, debounce: float = 3.0)`) rather than duplicating
  `_rebuild_lock`'s PID-file logic inline in a shell one-liner; the hook's shell command calls
  `python3 -m graphify.watch --trigger <path>` (or similar thin CLI entry) which imports and calls it —
  keeps the actual logic in Python (testable) rather than growing the shell-embedded hook string.
- Docs: README's install/hook section (mentions `PreToolUse` hooks already) gets a line for the new
  `PostToolUse` behavior; CHANGELOG entry under `## Unreleased`.

**Config surface**: none new by default (auto-installed alongside the existing hooks on `graphify
install`/`graphify claude install`). If real usage shows false positives (rebuild firing on files that
don't matter, e.g. scratch files), add an opt-out flag then — not speculatively now.

**Test plan** (mirrors this session's own verification discipline — real repo, not just synthetic):
1. Unit: hook JSON structure (matcher, command presence) — same shape as existing tests for
   `_SETTINGS_HOOK`/`_READ_SETTINGS_HOOK` if any exist (check `tests/test_*hook*.py` first).
2. Unit: `trigger_background_update`'s debounce/PID-lock logic in isolation (tmp_path graph, monkeypatched
   subprocess spawn — do NOT actually spawn a real background process in the test suite).
3. Live validation: install the hook in a real scratch project, make an Edit-tool-shaped change (or
   simulate via the same stdin-JSON the hook parses), confirm `graph.json`'s mtime/node count actually
   changes without a manual `graphify update` call — same "validate against the real failing case, not
   just a synthetic test" standard this session held itself to for the query/affected/HTML fixes.

## Non-goals (restated from P17, now with reasoning grounded in the orientation above)

- No Merkle-tree/network sync (Cursor's design) — solves a cloud-embedding-consistency problem graphify
  doesn't have.
- No change to `graphify watch` itself — it stays as the correct answer for "a human wants a live-updating
  graph while editing in an IDE," a different use case from what this design closes.
- No new optional dependency — deliberately avoided `watchdog` for this path so the fix ships for every
  install, not just ones that opted into the `watch` extra.
