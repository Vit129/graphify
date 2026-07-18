# Dev Task Progress — File-Watcher Auto-Sync (P17 item 1)

Last updated: 2026-07-18 22:50
Status: In Progress

## Context
- System: graphify
- Feature: file-watcher-auto-sync
- Workflow: Dev
- Complexity: Lightweight (single-repo Python CLI feature, no DB/no client app — see Category Mapping)
- Test Root: `tests/` (flat pytest, no per-feature subtree — matches this repo's existing convention,
  not the QA `tests/{api,web,mobile}-testing/` layout)

## Category Mapping (this project has no DB/no client app — task-design.md's default categories don't
apply as-is; mapped to what this repo actually has)
- Infrastructure → N/A (no schema/broker/env vars — reuses `graph.json`/`graphify-out/cache` already there)
- Data Storage → N/A (no new persistent state; debounce state is an in-memory/PID-file concern, folded
  into Server Logic below)
- Server Logic → the actual unit: `trigger_background_update()` in `watch.py`, the `PostToolUse` hook
  constant + install/uninstall wiring in `__main__.py`
- Client Application → N/A (no UI)
- Integration → hook registration end-to-end + live validation against a real repo

## Artifacts
- Design: `agent-memory/plans/file-watcher-auto-sync/design.md`
- Test Scripts: N/A (no TDD skeleton pre-created — tasks below each end with a real pytest file,
  following this repo's existing convention of writing the test alongside the change, not a separate
  RED-first skeleton phase; `tests/test_hooks.py`/`tests/test_read_hook.py` are the precedent to mirror)
- Published: PR #14 (draft), https://github.com/Vit129/graphify/pull/14

## Summary
- Total tasks: 6
- Completed: 1
- Remaining: 5

## Server Logic

- [x] **Task 1 — `trigger_background_update()` in `graphify/watch.py`** — Done (2026-07-18)
  **Deviated from the original plan on implementation, for the better — documented here since the plan
  text above described a different mechanism than what shipped:** no new `.pending-update` marker file
  and no reimplemented PID/lock check. `_rebuild_code` (called by the spawned child) already has its own
  non-blocking `_rebuild_lock` + `_queue_pending`/`_drain_pending` coalescing (confirmed by reading
  `watch.py:459-480` during implementation) — a burst of rapid triggers already collapses into the fewest
  rebuilds necessary without any new debounce state. What actually shipped: `trigger_background_update
  (project_root, changed_paths=None)` spawns `[sys.executable, "-c", _TRIGGER_BODY, str(project_root),
  *changed_paths]` fully detached — POSIX `start_new_session=True`, Windows `DETACHED_PROCESS |
  CREATE_NEW_PROCESS_GROUP` (+ `CREATE_BREAKAWAY_FROM_JOB` attempt first) — mirroring `hooks.py`'s
  `_LAUNCHER_TEMPLATE` flags exactly (proven cross-platform there already), but as plain Python since
  this isn't shell-embedded. Paths travel as argv (immune to quoting issues), not templated into source
  text. stdout/stderr to `graphify-out/.update.log`; spawn failures logged, never raised — verified via a
  mocked-Popen `OSError` test.
  - Verify: **5 new tests** in `tests/test_watch.py` (all passing) — `_TRIGGER_BODY` parses as standalone
    Python; Popen called with the right cmd shape + detach kwargs; changed_paths land as argv; log dir
    gets created; a spawn failure doesn't raise. **Plus a real (non-mocked) end-to-end smoke test**: spawned
    against a real 2-function scratch corpus, confirmed the detached child actually ran and produced a
    correct `graph.json` (3 nodes/3 edges) within 3s, with the parent call returning instantly — not just
    validated against mocks. Full suite: 3003 passed, 0 failed, 0 regressions.

- [ ] **Task 2 — thin CLI entry point to invoke it**
  A way for a shell hook one-liner to call Task 1's function without importing Python inline in the hook
  string (keeps the hook string short and the logic testable/importable) — e.g.
  `python3 -m graphify.watch --trigger <path>` in `watch.py`'s existing `if __name__ == "__main__":`
  block (currently only wires the full `watch()` daemon — add a `--trigger` flag alongside `--debounce`
  that calls `trigger_background_update()` and exits immediately instead of entering the `while True` loop).
  - Blocked by Task 1.
  - Verify: extend the same test file — `python -m graphify.watch --trigger <tmp_path>` subprocess call,
    assert it returns fast (non-blocking) and doesn't hang.

- [ ] **Task 3 — `_POST_EDIT_HOOK` constant in `graphify/__main__.py`**
  New hook constant, `"matcher": "Edit|Write|MultiEdit"`, following `_SETTINGS_HOOK`/
  `_READ_SETTINGS_HOOK`'s exact style (`__main__.py:470-524`): a `python3 -c "..."` one-liner parses
  `tool_input` from stdin, extracts `file_path` (or the file-path list for `MultiEdit` — check its
  actual `tool_input` shape first, don't assume it matches single-`Edit`'s), bails (exit 0, fail open) if
  `graphify-out/graph.json` doesn't exist, the path is under `graphify-out/` (avoid a self-triggered
  rebuild loop — same guard `watch.py`'s `Handler.on_any_event` already has), or the extension isn't
  code/doc/paper/image (mirror `watch.py`'s `_WATCHED_EXTENSIONS`); otherwise calls Task 2's CLI entry.
  - Blocked by Task 2.
  - Verify: `tests/test_install_strings.py`-style test (or new `tests/test_post_edit_hook.py`) —
    assert the hook JSON structure, the matcher, and (mirroring `test_hooks_use_cross_platform_detach`/
    `test_launcher_and_rebuild_body_are_valid_python` in `tests/test_hooks.py`) that the embedded
    `python3 -c "..."` body is syntactically valid Python on its own (parse it standalone in the test,
    same technique that file already uses for the git-hook bodies).

## Integration

- [ ] **Task 4 — wire into `_install_claude_hook`/`_uninstall_claude_hook`**
  Add `hooks.setdefault("PostToolUse", [])` alongside the existing `PreToolUse` list in
  `_install_claude_hook` (`__main__.py:1985`), append `_POST_EDIT_HOOK`, dedupe on re-install (same
  `"graphify" in str(h)` filter pattern the `PreToolUse` list already uses at line 2000). Mirror in
  `_uninstall_claude_hook`. Correct the printed message at `__main__.py:1980-1981` — it already claims
  this happens; once this task lands, the claim becomes true (verify wording still reads correctly,
  adjust only if needed).
  - Blocked by Task 3.
  - Verify: **confirmed `_install_claude_hook`/`_uninstall_claude_hook` have zero existing test coverage**
    (grepped `tests/*.py` — no hits) — a real pre-existing gap, closed as a side effect here rather than
    a separate cleanup task. New `tests/test_install_claude_hook.py` (or add to `test_read_hook.py` if
    it turns out to share enough setup — check its fixtures first): install into a `tmp_path`
    `.claude/settings.json`, assert `PostToolUse` key present with the new hook, assert idempotent
    re-install doesn't duplicate, assert uninstall removes it cleanly.

- [ ] **Task 5 — ✅ Run test scripts (verify GREEN)**
  Full `pytest tests/` run — the standard this session held itself to throughout (2900+ passed baseline,
  zero regressions expected since every change here is additive: a new function, a new CLI flag, a new
  hook constant, new hook-list entries — nothing existing is modified in a way that changes prior
  behavior).
  - Blocked by Tasks 1-4.

- [ ] **Task 6 — live validation against a real repo**
  Same discipline this session used for the query/affected/HTML fixes: don't stop at synthetic tests.
  Install the hook in a real scratch project (or one of this session's known real repos — kouen-terminal/
  Fitness-Tracker/Home-Assistant, all already graphified), simulate an Edit-tool-shaped stdin payload (or
  make a real edit through an actual agent session if feasible), confirm `graph.json`'s mtime/node count
  changes automatically within debounce+rebuild time, with no manual `graphify update` call. Confirm
  the self-triggered-loop guard actually holds (editing a file, the hook fires once, not repeatedly).
  - Blocked by Task 5.

## Next Step

All tasks done + verified GREEN + live-validated → continue with `/build` (or implement directly given
the scope is small and already fully specified above — user's call, not assumed here).
