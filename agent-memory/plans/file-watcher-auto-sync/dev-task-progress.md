# Dev Task Progress — File-Watcher Auto-Sync (P17 item 1)

Last updated: 2026-07-18 23:13
Status: Done

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
- Completed: 6
- Remaining: 0

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

- [x] **Task 2 — thin CLI entry point to invoke it** — Done (2026-07-18)
  Added a `--trigger` flag to `watch.py`'s existing `if __name__ == "__main__":` argparse block. When `--trigger <path>` is passed, it calls `trigger_background_update(Path(args.trigger))` and exits immediately (sys.exit(0)), without entering the foregound `while True` watchdog thread block.
  - Verify: Added `test_cli_trigger_flag_returns_fast` in `tests/test_watch.py` asserting that calling `python -m graphify.watch --trigger <tmp_path>` as a subprocess exits immediately (under 3.0s) and does not hang.

- [x] **Task 3 — `_POST_EDIT_HOOK` constant in `graphify/__main__.py`** — Done (2026-07-18)
  Added a `_POST_EDIT_HOOK` constant mapping to tool type matcher `"Edit|Write|MultiEdit"`. The hook runs a Python one-liner that reads `tool_input` from `sys.stdin`, handles potential variations of the key (`file_path`, `path`, `target_file`, `TargetFile`), bails early if `graphify-out/graph.json` doesn't exist, if the edited file is inside `graphify-out/` or hidden `.directories`, or if the file suffix is not in `_WATCHED_EXTENSIONS`. If validated, it spawns `python -m graphify.watch --trigger .` fully detached.
  - Verify: Added `test_post_edit_hook_structure_and_syntax` to `tests/test_install_strings.py` asserting the hook structure, matcher, and checking via `ast.parse` that the embedded python body is syntactically valid Python code.

## Integration

- [x] **Task 4 — wire into `_install_claude_hook`/`_uninstall_claude_hook`** — Done (2026-07-18)
  Wired the hook into `_install_claude_hook` to dynamically add the `PostToolUse` hook alongside the `PreToolUse` hook in `.claude/settings.json`, and deduplicate it on re-install. Updated `_uninstall_claude_hook` to symmetrically remove both PreToolUse and PostToolUse hook registrations.
  - Verify: Confirmed zero existing test coverage on `_install_claude_hook`/`_uninstall_claude_hook`. Wrote a new test file `tests/test_install_claude_hook.py` that installs the hooks in a `tmp_path` settings file, asserts the hooks keys, verifies re-installation is idempotent, and asserts uninstallation removes all graphify hooks cleanly.

- [x] **Task 5 — ✅ Run test scripts (verify GREEN)** — Done (2026-07-18)
  Ran the full test suite in the virtual environment to ensure zero regressions.
  - Verify: All 3006 passed, 28 skipped, 0 failed.

- [x] **Task 6 — live validation against a real repo** — Done (2026-07-18)
  Performed end-to-end live validation using a real python environment and a real throwaway workspace in `/tmp`.
  - Verify: Created a validation script `/Users/supavit.cho/.gemini/antigravity-cli/brain/cacc4ce5-2996-4a57-a04f-2864070e1178/scratch/live_validate.py` that sets up a throwaway project in `/tmp/graphify_validation_scratch/`, creates a file, builds the graph, updates the file, and runs the simulated JSON stdin payload to trigger the hook. Confirmed `graph.json`'s mtime updated and node count increased within 5 seconds. Also verified that editing files under `graphify-out/` or editing non-watched extension files (e.g. `.xyz`) did not trigger updates, confirming all guards work correctly.

## Next Step
- Complete! Ready for local git commit.

