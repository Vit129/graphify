# Dev Task Progress — IaC Indexing + HTTP Call-Site Linking

Last updated: 2026-07-24
Status: Done

## Context
- System: graphify
- Feature: iac-http-linking
- Workflow: Dev
- Complexity: Standard (new extractors + one prerequisite bug fix in shared `extractors/yaml_.py` +
  one new cross-file resolver — no changes to existing extractor output shapes for other languages)
- Test Root: `tests/` (flat pytest, matches this repo's existing convention)

## Category Mapping (no DB/no client app — same as `pagerank-ranking`/`file-watcher-auto-sync`)
- Infrastructure → N/A (no new storage/schema/broker; rides inside existing `graph.json`)
- Data Storage → N/A
- Server Logic → the actual units: `detect.py::classify_file`, `extract.py::_get_extractor` +
  new `LanguageResolver`, new `extractors/dockerfile.py`, new `extractors/kustomization.py`,
  changed `extractors/yaml_.py`
- Client Application → N/A
- Integration → full `uv run pytest -q` after each task, live smoke-test against real fixture
  repos at the end (My-Investment-Port for http_calls; a small local K8s/Dockerfile fixture dir
  for Feature 1, since no real project on disk has a Kustomize overlay to test against yet)

## Artifacts
- Design: `agent-memory/plans/iac-http-linking/design.md`
- LANGUAGE.md: `/Users/supavit.cho/Git/Personal/graphify/LANGUAGE.md`
- Related rejection record: `agent-memory/knowledge/architecture/feature-provenance.md` ("Rejected: TF-IDF Fallback Search Tier" — Feature 3, dropped, not part of this task list)

## Summary
- Total tasks: 9
- Completed: 9
- Remaining: 0

## Server Logic — Feature 1 (IaC indexing)

- [x] **Task 1 — multi-document YAML fix (prerequisite, blocks Task 2)** — Done (2026-07-24)
  `extractors/yaml_.py::extract_yaml()` — `_find_root_mapping()` currently descends via
  single-named-child only, silently keeping just the first `---`-separated document. Iterate
  `root.children` where `type == "document"` (verify actual tree-sitter-yaml node-type name against
  a real multi-doc fixture first — don't assume), run the existing per-document body once per
  document, offsetting `source_location` per document so nodes don't collide.
  Test: fixture with 2 `---`-separated plain-mapping documents → assert nodes exist for both
  top-level key sets, not just the first.
  **Done**: verified grammar shape directly (`stream` root, `document` children — confirmed via a
  throwaway parse script, not assumed). Fixed `extract_yaml()` to iterate `[c for c in
  root.children if c.type == "document"]` (falls back to `[root]` if none found). Also caught and
  fixed a second bug the design doc hadn't flagged: `key_nid = _make_id(stem, key_text)` collided
  across documents sharing key names (e.g. two K8s resources both having `kind`/`spec`) — added a
  `doc_idx`-qualified stem, only when `len(documents) > 1` (single-doc ID scheme untouched, zero
  regression risk). Added 2 tests: the reopen regression test above (RED confirmed before the fix,
  GREEN after) + a same-key-collision test (`kind`/`spec` repeated across 2 documents). All 10
  tests in `test_yaml_extraction.py` pass. Full suite: 21 pre-existing failures isolated as
  unrelated (env var `GRAPHIFY_VIZ_NODE_LIMIT=0` causes the same failures on unmodified `main`,
  confirmed via `git stash` compare) — no regressions from this change.

- [x] **Task 2 — K8s Resource node typing** (depends on Task 1) — Done (2026-07-24)
  `extractors/yaml_.py::extract_yaml()` — per document, if both `apiVersion` and `kind` are
  top-level keys (reuse `_mapping_pairs(root_mapping)`), emit an additional Resource node:
  `node_type="resource"`, `metadata={"kind": ..., "api_version": ..., "name": <metadata.name if
  present>}` — additive, alongside the existing generic per-key nodes for the same document.
  Test: single-doc K8s `Deployment` fixture → assert both the generic key-nodes AND one Resource
  node exist. Multi-doc `Deployment`+`Service` fixture → assert 2 Resource nodes (this is also the
  regression test proving Task 1 actually unblocks this).
  **Done**: extended `extractors/yaml_.py`'s `add_node()` to accept optional `node_type`/`metadata`
  (matching `extract.py`'s existing `add_node`/`add_node_fn` convention exactly — node dict key is
  `"type"`, not `"node_type"`; metadata runs through `sanitize_metadata`, imported from
  `graphify.security`, same as every other extractor). Detection: top-level `apiVersion` + `kind`
  both present → additive Resource node (`type="resource"`, `metadata={"kind", "api_version",
  "name"}`, name pulled from `metadata.name` if present), plus a `contains` edge from the file node.
  3 tests added: single-doc K8s manifest (Resource node + generic nodes both present, proving
  additive not replacing), non-K8s YAML (no Resource node, proving the gate doesn't false-positive),
  multi-doc K8s bundle (2 Resource nodes, one per document — the actual motivating case). All 13
  tests in `test_yaml_extraction.py` pass on first run. Full suite (excluding the 2 files with the
  pre-existing unrelated env-var failure): 2984 passed, 0 failed, 0 new regressions.

- [x] **Task 3 — Dockerfile extractor** — Done (2026-07-24)
  New `graphify/extractors/dockerfile.py::extract_dockerfile(path) -> dict`. Parse `FROM ... AS
  <stage>` lines (node per stage, anonymous index-numbered if unnamed) and `COPY --from=<stage>`
  lines (`depends_on` edge, confidence `EXTRACTED`). Base images not matching a local stage name get
  a plain external node, not walked further (matches existing "don't walk into a dependency's
  internals" pattern used for package manifests).
  Test: multi-stage fixture (`FROM node AS build`, `FROM nginx`, `COPY --from=build`) → assert 2
  stage nodes + 1 `depends_on` edge + 1 external node for the non-local base image.
  **Done**: new `extractors/dockerfile.py`, hand-rolled regex scanner (no tree-sitter-dockerfile
  grammar on PyPI, checked — same reasoning as `fish.py`). `FROM ... AS <stage>` → stage node
  (`type="stage"`); `COPY --from=<ref>` and a stage's own `FROM <ref>` resolve `<ref>` against
  already-seen stage names, then positional index (`--from=0`), then fall back to a new external
  image node — mirrors "don't chase a dependency's internals" pattern used elsewhere. 4 tests:
  single-stage external image, multi-stage named-stage `COPY --from=`, positional-index
  `COPY --from=0`, dispatch-wiring (this one intentionally RED until Task 4 landed — confirmed).

- [x] **Task 4 — wire Dockerfile into detection + dispatch** — Done (2026-07-24)
  `is_dockerfile_path(path)`: `path.name == "Dockerfile" or path.name.startswith("Dockerfile.")`.
  Add to `detect.py::classify_file()` before the suffix/shebang fallback (~line 397, same slot as
  `is_package_manifest_path`) → `FileType.CODE`. Add to `extract.py::_get_extractor()` before the
  final `_DISPATCH.get(path.suffix)` (~line 15449, same pattern as `is_mcp_config_path`) →
  `extract_dockerfile`.
  Test: a bare `Dockerfile` (no extension) in a fixture dir → assert `classify_file` returns CODE
  and `_get_extractor` returns `extract_dockerfile` (currently returns `None`/skips entirely).
  **Done**: `is_dockerfile_path()` added directly in `extractors/dockerfile.py` (same module-colocated
  convention as `is_mcp_config_path` living beside `extract_mcp_config` in `mcp_ingest.py`) — checked
  before the shebang fallback in `detect.py::classify_file` and before the suffix dispatch tail in
  `extract.py::_get_extractor`. All 4 dockerfile tests pass (the dispatch test now GREEN). No import
  cycle (`extract.py` importing `extractors.dockerfile` verified clean). Full suite (excluding the 2
  files with the pre-existing env-var failure): 2988 passed, 0 failed, 0 new regressions.

- [x] **Task 5 — Kustomize extractor + wiring** — Done (2026-07-24)
  New `graphify/extractors/kustomization.py::extract_kustomization(path) -> dict`, same
  `tree_sitter_yaml` parse pattern as `yaml_.py`. Read the `resources:` list, resolve each entry
  relative to `path.parent`, emit one Module node (`node_type="module"`,
  `metadata={"kind": "kustomize_overlay"}`) + one `imports` edge per resource (confidence
  `EXTRACTED`) to `_make_id(resolved_path)` — hook into the existing deferred/forward-reference
  resolution convention (`raw_calls` pattern, `extract.py:4734`+`16051`) rather than a new mechanism,
  since the target Resource node may not exist yet when this edge is emitted. Wire into
  `_get_extractor()`: `if path.name in ("kustomization.yaml", "kustomization.yml"): return
  extract_kustomization` (before generic `.yaml`/`.yml` dispatch).
  Test: fixture `kustomization.yaml` listing 2 `resources:` entries + the 2 target manifest files →
  assert Module node + 2 `imports` edges resolving to the right Resource node IDs (depends on
  Task 2 existing so the target actually is a Resource node, not just a generic file node).
  **Done, with a design simplification + a real bug caught before shipping**:
  - Simplified from the design doc: the Module node IS the kustomization file's own file node
    (`type="module"` set directly on it), not a separate node — a kustomization.yaml already only
    has one natural node to represent it. `imports` edges target the referenced manifest's *file*
    node (not its Resource node specifically) — full traceability still holds via the existing
    `file --contains--> Resource` edge from Task 2, so `Module --imports--> File --contains-->
    Resource` gives the same reachability without inventing a second resolution mechanism.
  - **Real bug caught via a failing test, not by inspection**: initial implementation used the
    `module_nid` id captured at `extract_kustomization()`'s own extraction time directly as the
    edge's `source`. Node ids get remapped after per-file extraction (confirmed by reading
    `_resolve_value_coupling`'s own docstring, which explicitly warns about this exact trap) — the
    edge silently pointed at a stale id that no longer matched the final node. Fixed by resolving
    the kustomization file's OWN current id fresh (via `source_file` lookup against `all_nodes`),
    exactly like the target is resolved — never trust a captured id from extraction time, same
    discipline `_resolve_value_coupling` already uses.
  - Deferred resolution implemented as a new `LanguageResolver` (`kustomize_imports`), registered
    right after `_resolve_value_coupling`'s definition (module-execution-order requirement, not a
    style choice — the resolver function must be defined before its `register_language_resolver`
    call runs at module import time) — reuses the exact-then-basename source_file matching
    strategy from `_resolve_value_coupling` for both endpoints, not just the target.
  - 4 tests: Module node shape, dispatch wiring, real edge resolution (source_file basename
    matching, since deep tmp_path fixtures get path-shortened - discovered mid-test, not assumed),
    missing-target produces no dangling edge. All pass. Full suite (excluding the 2 pre-existing
    env-var-failure files): 2992 passed, 0 failed, 0 new regressions.

## Server Logic — Feature 2 (HTTP call-site linking)

- [x] **Task 6 — action-branch parsing inside doGet/doPost** — Done (2026-07-24)
  Within the `.gs`/JS extraction path (`extract_js`, or a small new helper it calls), parse
  `if/else if (action === '<literal>')` arms inside functions named `doGet`/`doPost`, mapping each
  literal action value to whatever function that arm calls (resolve via the same local-call
  resolution the rest of the file already does — reuse, don't reimplement name→node lookup).
  Test: fixture `.gs` with `doGet` containing 2 action arms (`'holdings'` → `getHoldings()`,
  `'dividends'` → `getDividends()`) → assert a `{"holdings": <getHoldings node id>, "dividends":
  <getDividends node id>}`-shaped mapping is produced (internal to the extractor at this stage —
  no edges emitted yet, that's Task 8).
  **Done**: spawned an Explore agent first to map the real JS extraction pipeline before touching
  it (`_extract_generic`'s `walk()`, `extract.py:4291+`) — confirmed no reusable "walk statements,
  find calls" helper exists (had to write one), confirmed `function_bodies`/`label_to_nid` timing
  (body is available at node-creation time; same-file name→id resolution only exists AFTER the
  full `walk(root)` pass), and confirmed the exact tree-sitter-javascript grammar shape via a
  throwaway parse script before writing any matching code (`if_statement.condition/consequence/
  alternative` fields exist; `binary_expression` has NO named fields, positional access needed).
  Implementation: raw arms recorded at node-creation time into `gas_action_arms_raw` (deferred,
  same reason Kustomize's targets are deferred — same-file name→id map isn't built yet at that
  point in the walk), resolved right after `label_to_nid` is built, attached to the result dict as
  `gas_action_handlers` only when non-empty (matches the `swift_extensions`/`ts_type_table`
  conditional-attach convention already in this function). New helpers: `_gas_binary_string_literal`
  (identifier === literal shape, either operand order, non-literal/non-`===` skipped not guessed),
  `_find_first_call_expression` (stops at nested function boundaries), `_gas_collect_action_arms`
  (walks the if/else-if chain, stops at a final plain `else`). 3 tests: 2-arm resolution + correct
  `getHoldings()`/`getDividends()` node ids (final plain `else` correctly excluded), non-doGet/
  doPost function produces no handlers (name-gate works), unresolvable same-file callee produces
  no handler entry (not a dangling one). All pass. Full suite (excluding the 2 pre-existing
  env-var-failure files): 2995 passed, 0 failed — notable because this touches the shared
  `_extract_generic` used by every JS/TS file in the corpus, highest blast-radius change so far.

- [x] **Task 7 — fetch() call-site literal-action extraction** — Done (2026-07-24)
  New parsing in the JS/TS extraction path (confirmed no existing `fetch()` handling to reuse) —
  scan `fetch(...)` call expressions, extract a literal `action=<value>` segment from the URL
  argument when it's a literal/template-literal with only-literal segments. Skip (don't guess) when
  the action value comes from an interpolated variable.
  Test: fixture `.js` with `fetch(url + '?action=holdings')` (literal) and
  `` fetch(`${GAS_URL}?action=${action}`) `` (interpolated) → assert the first produces an extracted
  `action="holdings"` call-site record, the second produces none.
  **Done, with one scope addition beyond the original design line**: the design didn't explicitly
  say fetch call-sites need their own graph node (only that `gas_fetch_calls` facts get produced) —
  but Task 8's edge needs a real SOURCE node to point from, and none existed for a bare `fetch()`
  expression. Added one: `add_node(call_nid, f"fetch(action={literal})", line)` +
  `contains` edge from the owning function, same pattern as other synthetic nodes in this file
  (e.g. the Route-path nodes in the GoRouter/AutoRoute navigation handling).
  Value detection: `_js_flatten_string_segments()` flattens a `string`/`template_string`/`+`-chain
  into ordered literal/dynamic segments (verified `binary_expression` exposes NO named left/right
  fields in this grammar — positional access required, same finding as Task 6); combines them with
  a sentinel for dynamic parts, then regex-extracts `action=<value>` only when the matched span
  never touches a dynamic segment — correctly distinguishes `` `${GAS_URL}?action=all&...` ``
  (literal, real backup.js pattern) from `` `${GAS_URL}?action=${action}` `` and
  `GAS_URL + '?action=' + action + ...` (both interpolated, real api.js pattern) — skipped, not
  guessed, exactly matching the design's stated scope. 5 tests: template-literal capture,
  plain-string capture, string-concat interpolation skip, template interpolation skip, non-`fetch`
  call produces nothing. All pass. Full suite (excluding the 2 pre-existing env-var-failure files):
  3000 passed, 0 failed.

- [x] **Task 8 — `http_calls` LanguageResolver** — Done (2026-07-24)
  Register `LanguageResolver("http_calls_linking", frozenset({".js", ".jsx", ".ts", ".tsx", ".gs"}),
  _resolve_http_calls)` at `extract.py:~11745` (existing resolver-registration block).
  `_resolve_http_calls` correlates Task 7's call-site action values against Task 6's per-handler
  action→target maps, emitting `http_calls` edges (call-site node → matched arm's target node,
  confidence `INFERRED`). No-op if zero `.gs` handler nodes exist in the corpus (matches
  `resolver_registry`'s existing suffix-gate skip behavior).
  Test: wire Task 6 + Task 7 fixtures together end-to-end → assert the literal `fetch` call-site
  gets an `http_calls` edge to `getHoldings()` (not to `doGet` itself), and the interpolated
  call-site gets none.
  **Done, with a real bug found and fixed via two rounds of empirical (not assumed) debugging**:
  - **Structural rework before writing the resolver at all**: confirmed via a manual multi-file
    `extract()` probe (mimicking pytest's tmp_path depth) that ids captured during per-file
    extraction (both Task 6's `callee_nid` via `label_to_nid`, and Task 7's `call_nid`) go stale
    once the corpus has 2+ files — `_file_stem`'s own docstring names this exact mechanism
    ("the extract() id-remap post-pass re-derives the canonical repo-relative form from
    source_file"). Reworked Task 6/7 to carry `(source_file, label)` pairs forward
    (`actions_by_name`, `handler_source_file` on handlers; `source_file`/`label` on fetch calls)
    instead of trusting captured ids for cross-file resolution — existing Task 6/7 unit tests
    (single-file, no remap) still pass unchanged since the original resolved fields were kept too.
  - **First empirical failure**: exact `(source_file, label)` match alone produced zero edges —
    root-caused (not guessed) by dumping `all_nodes`' actual `source_file` values, which get
    shortened relative to the extraction-time absolute path for deep corpora. Added a
    basename-keyed fallback tier, matching `_resolve_value_coupling`/`_resolve_kustomize_imports`'s
    existing tolerance.
  - **Second empirical failure, after adding the fallback**: still zero edges. Root-caused by
    instrumenting the real function directly (not the registered copy - a first monkeypatch attempt
    didn't actually take effect) and discovering `.strip("()")` only trims from a string's *ends*:
    `"fetch(action=holdings)".strip("()")` → `"fetch(action=holdings"` (the opening paren after
    `fetch` is untouched, only the trailing `)` gets stripped) — so the label used to build
    `label_by_sf`'s keys didn't match the raw, unnormalized label used to query it. Fixed by
    normalizing inside `_resolve_label()` itself (single source of truth), not at each call site.
  - Cheap early exit confirmed: resolver returns immediately if no file in the corpus has any
    `gas_action_handlers` at all (no `.gs` doGet/doPost anywhere) - verified by its own test.
  - 3 tests: real link (literal call → `getHoldings()`, confirmed NOT to `doGet` itself, confidence
    `INFERRED`), interpolated call-site produces no edge, no-GAS-handlers-in-corpus is a no-op. All
    pass. Full suite (excluding the 2 pre-existing env-var-failure files): 3003 passed, 0 failed —
    the most invasive change so far (new cross-file resolver spanning 2 different file types).

## Integration

- [x] **Task 9 — full suite + live smoke test** — Done (2026-07-24)
  `uv run pytest -q` green after all 8 tasks, 0 regressions vs. current baseline. Live smoke test:
  run `graphify update` against a small local fixture directory covering Dockerfile + Kustomize +
  multi-doc K8s YAML (Feature 1 has no real project on disk yet — build the fixture dir here), and
  against My-Investment-Port for Feature 2 (real target, confirmed in design verification) —
  confirm the expected new nodes/edges actually appear in the real `graph.json` output, not just in
  isolated unit-test fixtures.
  **Done, with 2 real bugs found only because this was a genuine multi-file smoke test, not another
  unit fixture**:
  - Full suite: 3025 passed, 21 pre-existing unrelated failures (env var `GRAPHIFY_VIZ_NODE_LIMIT=0`,
    identical to the pre-feature baseline, confirmed via `git stash` compare back in Task 1) — 0
    regressions across all 8 implementation tasks.
  - **Feature 1 smoke test** (built fixture dir: multi-stage Dockerfile, `deployment.yaml`
    single-doc, `service.yaml` multi-doc bundling `Service`+`ConfigMap`, `kustomization.yaml`
    referencing both): every piece landed correctly together in ONE combined `extract()` run —
    2 Dockerfile stages + correct `depends_on` chain to `node:18`/`nginx`, 1 Resource node for the
    single-doc manifest, 2 correctly-separated Resource nodes for the multi-doc manifest (proving
    the Task 1 collision fix holds under a real combined run, not just its own isolated test), 2
    `imports` edges from the Kustomize Module node to both target files.
  - **Feature 2 smoke test against My-Investment-Port — 2 real bugs caught, not by unit tests**:
    1. **Cache root gotcha**: `extract()`'s `effective_root` is computed from the input paths'
       *common prefix* (`extract.py:16225-16244`), not cwd — repeated smoke-test runs kept reading
       a stale cached extraction (`.gs` isn't in `_JS_CACHE_BYPASS_SUFFIXES`, `extract.py:102`) from
       `My-Investment-Port/graphify-out/cache/`, not this repo's own cache dir. Cost real debugging
       time (multiple "why is this still empty" cycles) before finding it — cleared only the
       `cache/` subdirectory (regenerable build artifact), left that project's real `graph.json`/
       reports untouched.
    2. **Real multi-if-chain bug in Task 6's arm scan**: `doGet` in the real file has TWO separate
       top-level if-chains (an outer `if (payload) { if (action === 'save_x') ... }` write-dispatch
       block, then a separate `if (action === 'holdings') ...` read chain) - the original scan only
       checked the FIRST if_statement among the function body's direct children, silently missing
       the second chain entirely (where `holdings`/`dividends`/`all` actually live). Fixed with a
       new `_iter_nodes()` generator scanning every `if_statement` anywhere in the body (not
       crossing nested-function boundaries), collecting arms from each chain head found - redundant
       re-collection from a mid-chain else-if is harmless (idempotent dict writes).
    3. Also hardened `_find_first_call_expression` → `_find_first_bare_call_expression` (only
       matches identifier-called calls, skips `.split(',')`-shaped member calls in setup code) -
       fixed 2 of 3 originally-broken real arms (`getStockPrices`, `getCalendarAlerts`). The 3rd
       (`archived_dividends`) has a `ponytail:` comment on `_find_first_bare_call_expression`
       documenting the remaining ceiling (result flows through a local variable + `.filter()`, not
       a direct call) - confirmed narrow (1 unresolved arm out of 20 real ones), not chased further.
  - **Final real result**: `fetch(action=all) -> syncLocalStorageToGoogleSheets()`, confidence
    `INFERRED`, resolved end-to-end on the actual target repo that motivated this feature.
