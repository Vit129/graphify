# P4 — test()/describe() Block Extraction (spec.ts)

Status: **Done** (2026-07-02)
Priority: **P1** — same "find the edit spot" impact class as P3/P5, but a different layer: an extraction gap, not a search-ranking gap
Owner surface: `graphify/extract.py` (`_js_extra_walk`, JS/TS-only)
Created: 2026-07-02
Depends on: none

---

## Why

Extracted a real spec file from `cpi-qa-automation`
(`territory-so-type.spec.ts`, which contains several `test('[TS-169476-01]
Territory Level 2 -> code=22, name=WholeSales', ...)`-style blocks) and
inspected the output:

```
territory_so_type_spec | territory-so-type.spec.ts
territory_so_type_spec_createmaster | createMaster()
```

Two nodes: the file, and one helper function defined in it. **Zero nodes
for the `test(...)` blocks themselves.** A query like "fix the WholeSales
Territory Level 2 test" has nothing to find — not a ranking failure (P3/P5's
class of problem), but a structural gap: the extractor never turns
`test(...)`/`describe(...)` calls into nodes at all. No amount of search
improvement fixes this; the target simply doesn't exist in the graph.

## Architecture (from session research, 2026-07-02)

- `_extract_generic`'s main `walk()` is an imperative, config-driven
  type-dispatch chain (`graphify/extract.py`, function starts ~3039). It
  never visits `call_expression`/`new_expression` for node creation —
  `config.call_types` is only consulted by a separate, later pass
  (`walk_calls`) that emits `calls` **edges**, never nodes. No existing
  language does "a call becomes a node" anywhere in the codebase — this is
  a new pattern, not an extension of one.
- JS/TS has an existing, already-wired, **JS/TS-only** extension point:
  `_js_extra_walk` (line 2409), called from inside the shared `walk()`
  for every node that fell through the config's declared type checks.
  Adding a `call_expression` branch here does **not** touch the shared
  `class_types`/`function_types`/`import_types` dispatch other languages
  (Python, Go, Rust, Swift, C#, ...) depend on.
- Confirmed by reading the real control flow (not just the research
  report): `_js_extra_walk` is invoked, and if it returns `True`, `walk()`
  returns immediately *without* falling through to the default
  "recurse into children" case (`extract.py` ~4292-4298, ~4327-4329). If a
  `test()`/`describe()` handler returned `True`, nested `describe`/`it`
  calls inside the callback body would never be visited and would
  silently vanish. **Fix: the new branch creates its node/edge as a side
  effect and returns `False`** (not `True`) so the existing default
  recursion naturally walks into the callback's body and reaches nested
  calls — no manual re-recursion needed, confirmed against the function's
  actual control flow rather than assumed from the research summary alone.
- ID generation (`ids.make_id`/`normalize_id`) NFKC-normalizes and
  collapses non-word runs to `_` — handles an arbitrary description
  string fine (`"should login with valid credentials!"` ->
  `should_login_with_valid_credentials`). Real risk: two `test("same
  text", ...)` calls in one file would collide to the identical id, and
  `add_node` (confirmed at `extract.py:3122-3126`) silently drops the
  second on a `seen_ids` hit. **Fix: include the 1-based line number in
  the id** (`_make_id(stem, description, str(line))`) — two calls can't
  start on the same line in practice, so this is a cheap, sufficient
  disambiguator without needing a running counter.
- `graphify/extractors/` (the newer per-language directory) is *not* a
  uniformly more-isolated architecture — `zig.py` is fully self-contained,
  but `csharp.py` still routes through `_extract_generic`. Migrating JS/TS
  there to build this feature would mean reimplementing everything JS/TS
  currently gets from the shared engine (arrow functions, CJS/prototype
  assignment handling, dynamic imports, tsconfig aliases, cross-file
  resolution) — an order-of-magnitude larger, separate project. Not
  warranted for this feature; stay inside `_js_extra_walk`.
- Existing convention (`tests/test_extract.py:678-818`): functions get
  label `"name()"`; nested/owned methods get `.name()"`; file-owns-thing
  edges use relation `"contains"`. A test-block node isn't a callable
  symbol, so its label is the raw description string with **no**
  trailing `()`; the file -> test edge reuses the existing `"contains"`
  relation rather than inventing a new one (no other tooling in the graph
  currently branches on relation type in a way a new relation would need
  to be taught to).

## Scope (v1 — deliberately narrow)

1. In `_js_extra_walk`, add a `node.type == "call_expression"` branch:
   - Callee must be a bare `identifier` (`test`, `it`, `describe`) — not
     `test.only`/`test.skip`/`describe.each`/other member-expression
     forms (non-goal below).
   - First positional argument must be a `"string"` node (tree-sitter JS/TS
     string literal) — skip template literals/expressions/variables
     (dynamic test names are out of scope; the file/helper-function nodes
     already extracted still give *some* grounding for those).
   - Node: `id = _make_id(stem, description, str(line))`, `label =
     description` (raw string content, quotes stripped via the same
     `_read_text(node, source).strip("'\"\` ")` pattern already used for
     `require(...)` args at `extract.py:2303`).
   - Edge: `file_nid -> new_nid`, relation `"contains"` (flat — see
     non-goals on nesting).
   - Returns `False` (not `True`) so default recursion continues into the
     callback body and reaches nested `test`/`describe`/`it` calls.
2. Tests in `tests/test_extract.py` (or a new
   `tests/test_js_test_block_extraction.py`) matching the existing
   JS/TS extraction test shape — flat file, nested `describe(() =>
   { it(...) })`, non-string dynamic name (must NOT produce a node),
   duplicate description text on different lines (must produce two
   distinct nodes, not a silent drop).
3. Real-file validation: re-run extraction on the exact
   `territory-so-type.spec.ts` file from this session's investigation,
   confirm the `test('[TS-169476-01] Territory Level 2 -> code=22,
   name=WholeSales', ...)` block now produces a node, and a natural-
   language query for "WholeSales Territory Level 2" surfaces it.

## Non-goals (v1)

- `test.only`/`test.skip`/`describe.each`/`test.describe`/any
  member-expression callee form — bare identifiers only. Revisit if a
  real project's spec files predominantly use these (Playwright's
  `test.describe` groups are common enough that this may become a fast
  follow, but adding it now would double the callee-matching surface for
  a case not yet confirmed to matter in practice).
- Nesting hierarchy (`describe` -> child `test` edges) — v1 connects every
  test/describe node flatly to the file via `"contains"`, matching how
  functions are already connected. A real describe/test parent-child
  edge would need threading a "current test-block parent" id through
  `_js_extra_walk`'s call signature (it currently only threads
  `parent_class_nid`), a larger change than this plan's stated problem
  (make a specific test findable) requires. Revisit only if a query
  genuinely needs "find all tests under this describe block" and flat
  containment can't answer it.
- Jest/Mocha-specific globals beyond `test`/`it`/`describe`
  (`beforeEach`, `afterAll`, etc.) — these aren't test *cases*, extracting
  them as findable nodes doesn't serve the "find the test I need to edit"
  goal this plan targets.
- Extraction for non-JS/TS test frameworks (pytest, RSpec, Go's
  `testing.T`, ...) — scoped to the concrete gap found (Playwright/Jest
  TS spec files), not a general "extract test cases in every language"
  effort.

## Verification

- Unit tests covering: flat test() extraction, describe()-wrapped nested
  test()/it() extraction (confirms the `return False` fix actually
  preserves recursion — this is the one regression this plan could
  introduce if gotten wrong), non-string dynamic name is skipped, two
  same-text tests on different lines both produce nodes.
- Real-file validation against `territory-so-type.spec.ts` (session's
  original investigation file) — before: 2 nodes (file + one helper);
  after: file + helper + one node per `test(...)` block, each findable by
  its description text.
- Full suite green: `uv run pytest -q` — must not regress any existing
  JS/TS extraction test (arrow functions, CJS exports, prototype methods,
  the `describe(() => { const set = new Set(...) })` case already
  referenced in a comment at `extract.py:2484`, which depends on the
  *existing* recursion-into-callback-body behavior this plan must not
  break).

## What's done

- New `call_expression` branch added to `_js_extra_walk`
  (`graphify/extract.py`, right before the existing `expression_statement`
  branch) — bare `test`/`it`/`describe` callee, first positional arg must
  be a `"string"` node, id = `_make_id(stem, description, str(line))`,
  label = raw description (quotes stripped via the same
  `_read_text(...).strip("'\"\` ")` pattern already used for `require()`
  args), edge `file -> test` with relation `"contains"`. Returns `False`
  so default recursion still reaches the callback body — confirmed this
  is what actually preserves nested-call visibility (not an assumption
  from the research report) by writing
  `test_extract_ts_nested_it_inside_describe_produces_node` against it
  directly.
- 8 new tests in `tests/test_js_test_block_extraction.py`: flat
  extraction, nested `describe(() => it(...))`, dynamic (non-string) name
  correctly produces no node, duplicate description text on different
  lines produces two distinct nodes (id collision guard), file->test
  `"contains"` edge shape, `.js` (not just `.ts`) support, an unrelated
  call (`console.log(...)`) doesn't spuriously produce a node, and
  existing helper-function extraction is unaffected when test() blocks
  are also present in the same file.
- Full suite: 2784 passed, 0 failures — including the full existing
  JS/TS extraction suite (arrow functions, CJS exports, prototype
  methods, the `describe(() => { const set = new Set(...) })` case the
  plan flagged as the regression risk).
- Real-file validation against the exact file from the original
  investigation (`territory-so-type.spec.ts`, `cpi-qa-automation`):
  went from 2 nodes (file + one helper function) to 15 (file + helper +
  13 individual test-case nodes) — including Thai-language test
  descriptions (`ตรวจสอบข้อมูลถูกลบแล้ว` etc.), confirming
  `_make_id`/`normalize_id`'s Unicode handling works unmodified for this
  new node type. Confirmed the query `_score_nodes(G, ["wholesales",
  "territory", "level", "2"])` against the freshly-extracted graph ranks
  `[TS-169476-01] Territory Level 2 -> code=22, name=WholeSales` #1 — the
  exact target this plan set out to make findable.
