# P6 — Robot Framework Extraction Support

Status: **Done** (2026-07-02)
Priority: **P1** — same class of gap as P2 (YAML): 0 nodes for an entire real, in-use test suite, not a ranking problem
Owner surface: new `graphify/extractors/robot.py`
Created: 2026-07-02
Depends on: none

---

## Why

Comprehensive extension audit across the session's real projects (Company +
Personal, same method used to find the YAML gap) turned up `.robot`
(Robot Framework) as a second major format with zero extraction support —
125 files found by raw count (98 of those in `.claude/worktrees/` duplicate
branches; 12 real files in harness-terminal's actual `Tests/robot/` and
`Tests/HarnessRobotTests/suites/` directories). Directly relevant to the
user's own QA stack (Robot Framework is a distinct, named category in their
skill-routing rules), arguably higher priority than YAML for their day-to-day
work even though YAML has a larger raw file count.

Unlike YAML, this isn't just declarative config — Robot Framework has real
test-case and reusable-keyword *definitions* with names, bodies, and calls
between them, closer in shape to a real programming language than to a
markup/config format.

## Non-goals

- ~~Resource file (`.resource`) cross-file keyword resolution~~ — **reopened
  and closed 2026-07-02.** `extract_robot` now walks `*** Settings ***` for
  `Resource` statements and emits a real `imports_from` edge to the resolved
  target file (same convention as every path-based import in `extract.py`).
  Keyword calls not defined in the current file are no longer dropped —
  they're deferred as `raw_calls` entries and picked up by the shared
  cross-file `calls` resolver in `extract()`, the same mechanism every other
  language extractor uses (no bespoke resolver written). Also added
  `.robot`/`.resource` to `_CASE_INSENSITIVE_EXTS` (#1581's fold mechanism),
  since Robot Framework keyword names are case-insensitive by spec — a
  `log message` invocation now resolves to a `Log Message` definition in
  another file. Validated on harness-terminal's real suite: 9 `imports_from`
  edges (one per suite importing `harness.resource`), 53 real cross-file
  `calls` edges into `harness.resource`'s shared keywords that were
  previously invisible (0 before this fix — the graph simply had no
  representation of "this test uses that shared keyword").
- `Library` setting imports — left unresolved (most name an installed
  package like `SeleniumLibrary`, not a project-relative file); a local `.py`
  keyword library is a Python file already covered by `extract_python`'s own
  node, and the cross-file `raw_calls` deferral resolves calls into it by
  name without needing an explicit import edge.
- `*** Test Templates ***` / `[Template]` / `[Setup]` / `[Teardown]`
  keyword-reference resolution — real Robot Framework feature, out of scope
  for a first pass; the test case's `[Documentation]` and step-level
  `keyword_invocation` calls already cover the "find the right test/keyword"
  goal this plan targets.
- Variable (`${VAR}`) definition-to-usage edges — would mirror what
  `_search_tokens`/BM25 can already do via label text matching on variable
  names; not pursued unless a real query gap shows label matching isn't
  enough.

## What's done

- Installed `tree-sitter-robot==1.4.0` and inspected its real AST against an
  actual harness-terminal `.robot` file (not written blind against grammar
  docs) — confirmed `child_by_field_name` returns `None` for the fields this
  extractor needs (a grammar quirk, verified empirically before writing
  around it), so `graphify/extractors/robot.py` matches children by `.type`
  throughout, same as the non-field-based branches in `zig.py`.
- New self-contained `extract_robot` (not routed through `_extract_generic`
  — Robot Framework's `*** Section ***` shape has no equivalent in the
  shared config-driven walker, same reasoning as YAML/Zig). Node types:
  `test_case_definition` and `keyword_definition` each produce a node (label
  = the human-readable name, e.g. `"Bug 1 - Browser Pane Reuse On Rebuild"`,
  not a mangled identifier) connected to the file via `contains`.
- **Calls edges**, not just node extraction: a test case or keyword whose
  body contains a `keyword_invocation` referencing another *locally-defined*
  keyword gets a `calls` edge to it — same value proposition as call-graph
  tracking in every other language extractor (find what a keyword is used
  by). Calls to library/built-in keywords (`Open Browser`, `Should Contain`,
  etc. — no matching local definition) are deliberately dropped rather than
  fabricating a phantom node, matching the cross-file-resolution convention
  used everywhere else in the codebase.
- Registered in `extractors/__init__.py`, re-exported from `extract.py`,
  wired into `_DISPATCH` for `.robot`.
- `tree-sitter-robot` added as an **optional extra** (`robot = [...]` in
  `pyproject.toml`), not a hard dependency — unlike YAML (found in nearly
  every repo), Robot Framework is audience-specific (QA automation), which
  matches the existing convention for `sql`/`terraform`/`dm` extras rather
  than the core `dependencies` list. Also added to the dev
  `dependency-group` (matching how `tree-sitter-hcl` is handled) so it's
  actually installed and tested in this environment, not silently skipped.
- 7 tests in `tests/test_robot_extraction.py`: test-case node, keyword node,
  calls edge to a locally-defined keyword, *no* calls edge for a
  builtin/library keyword call (the phantom-node guard), file->contains
  edges for both node types, Settings/Variables-only file doesn't crash or
  spuriously produce nodes, and dispatch through the real
  `graphify.extract.extract()` entrypoint (not just the standalone function
  in isolation — same "prove it's actually wired in" test P2 used).
- Full suite: 2811 passed, 0 failures (2804 -> 2811, +7 new).
- Real-file validation: extracted all 12 real `.robot` files in
  harness-terminal (98 duplicate worktree copies correctly excluded) — 131
  nodes, 0 errors, 0.01s. Ran the full search pipeline end-to-end (again, no
  changes needed to `serve.py`): query `"memory leak guard test"` correctly
  surfaces `memory_leak_guards.robot` as a seed and reaches the specific
  test case `"Leak C - Every Per-Surface Dict In Coordinator Has Retire
  Cleanup"` in the BFS traversal via the `contains` edge.
