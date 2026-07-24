# Design — IaC indexing + HTTP call-site linking

Feature scope per `LANGUAGE.md` (project root): Feature 1 (Dockerfile + Kustomize + K8s Resource
typing) and Feature 2 (`http_calls` edge, My-Investment-Port `fetch()` -> Apps Script `doGet`/`doPost`).
Feature 3 (TF-IDF search) dropped — see `agent-memory/knowledge/architecture/feature-provenance.md`
"Rejected: TF-IDF Fallback Search Tier".

Architecture pattern: graphify is a single Python package, one extraction pipeline
(`detect.py` classify -> `extract.py` dispatch -> per-file extractor -> `resolver_registry.py`
cross-file passes). No bounded-context split needed — this is monolith module-boundary design,
not DDD strategic design across services.

## Strategic Design — module boundaries

| New/changed file | Owns |
|---|---|
| `graphify/extractors/dockerfile.py` (new) | `extract_dockerfile()` — multi-stage build graph (stages, `FROM`, `COPY --from=`) |
| `graphify/extractors/yaml_.py` (changed) | multi-document YAML fix (prerequisite bug, see below) + K8s Resource-node typing layered onto existing generic nodes |
| `graphify/extractors/kustomization.py` (new) | `extract_kustomization()` — Module node + `imports` edges to referenced manifests |
| `graphify/detect.py` (changed) | `classify_file()` gains a filename check for Dockerfile, same slot/pattern as the existing `is_package_manifest_path` check (line ~397) |
| `graphify/extract.py` (changed) | `_get_extractor()` gains filename checks for Dockerfile and `kustomization.yaml`, same pattern as `is_mcp_config_path`/`is_package_manifest_path` (line ~15449); new `LanguageResolver` registered at the existing block (line ~11745) for `http_calls` |
| `graphify/resolvers/http_calls.py` (new — or inline in extract.py near the other `_resolve_*_member_calls` functions, match whichever convention holds for the newest-added resolver, check before creating a new file) | cross-file `http_calls` edge resolution: correlate `fetch()` call-sites against `doGet`/`doPost` handler nodes |

## Tactical Design — node/edge entities (see LANGUAGE.md for definitions)

**Prerequisite bug fix (blocks Resource-node typing, found during design):**
`extractors/yaml_.py`'s `_find_root_mapping()` descends from `tree.root_node` via
single-named-child only, stopping at the first `block_mapping` — for a multi-document YAML file
(`---`-separated, tree-sitter-yaml's `stream` root has multiple `document` children), this silently
extracts only the **first** document and drops the rest. Kubernetes manifests routinely bundle
multiple Resources per file this way (`Deployment` + `Service` in one `.yaml`). Must iterate
`root.children` where `type == "document"` and run extraction per-document before Resource typing
can see anything past the first Resource. Scoped as part of this feature, not a separate ticket —
Resource typing is meaningless without it.

**Resource node** — one per YAML document where both `apiVersion` and `kind` are top-level keys.
`node_type="resource"`, `metadata={"kind": <kind>, "api_version": <apiVersion>, "name": <metadata.name>}`
(matches existing `add_node_fn(..., node_type="namespace", metadata={"kind": ...})` convention,
`extract.py:2780`). Additive: emitted alongside the existing generic per-key structural nodes for
the same document, not replacing them.

**Module node** — one per `kustomization.yaml`/`.yml`. `node_type="module"`,
`metadata={"kind": "kustomize_overlay"}`.

**imports edge (Kustomize)** — Module node -> Resource node (or file node, if the target file's
Resource-typing hasn't resolved a Resource node yet). Confirmed a reusable deferred-resolution
mechanism exists — `raw_calls` (`extract.py:4734`, resolved at `extract.py:16051`) plus existing
dangling-edge repoint passes (`extract.py:10990`, `16025`) — hook into that same convention rather
than inventing a second one. `confidence: "EXTRACTED"` (the path is a literal string in
`resources:`, no ambiguity).

**Dockerfile stage graph** — one node per build stage (`FROM ... AS <stage>`, or an anonymous
index-numbered stage if unnamed). `depends_on` edge from a stage to the stage/image named in its
`FROM`; `depends_on` edge from a stage to the stage named in any `COPY --from=<stage>` within it.
Base images from a registry (not a local stage name) get a plain external node, not walked further
(YAGNI — resolving registry image internals is out of scope, matches the project's existing "don't
walk into a dependency's rabbit hole" pattern for package manifests). `confidence: "EXTRACTED"`.

**http_calls edge** — call-site node -> handler node. `confidence: "INFERRED"`.

**Verified against the real target repo (My-Investment-Port) before finalizing — the original
method-based design was wrong and was corrected:** every real fetch call
(`src/data/services/api.js`, `yahoo.js`, `yahooFinanceService.js`, `scripts/backup.js`,
`scripts/ai-sync-entry.js`) hits the *same* `GAS_URL`, routed by a `?action=<name>` query-string
literal, not by HTTP method — `doGet` (`syncLocalStorageToGoogleSheets.gs:39-91`) is a single
~20-branch `if (action === '...')` dispatcher, including writes-via-GET as a documented CORS
workaround (comment at line 39). Matching call-site -> `doGet`-as-a-whole would be almost
uninformative (everything lands on the same node). User confirmed (2026-07-24): go deep, match the
literal `action=` value to its specific branch, not the enclosing function.

Resolution shape:
1. Call-site: a `fetch(...)` invocation whose first argument is a template literal / string
   concatenation containing a literal `action=<value>` segment (interpolated variables in the same
   literal, e.g. `` `${GAS_URL}?action=${action}...` ``, can't be resolved statically — skip those,
   they're not a design gap, just an inherent limit of static analysis, same as any other
   non-literal argument elsewhere in the codebase).
2. Handler branch: inside a `doGet`/`doPost` function body, each `if/else if (action === '<value>')`
   arm — target node is whatever that arm calls (e.g. `action === 'holdings'` -> `getHoldings()`).
3. Edge: call-site -> the specific target function called in the matching arm (not `doGet` itself).
   `confidence: "INFERRED"` (literal-string correlation, not a compiler-verified reference — same
   tier as any other cross-file string-matched edge in the codebase).
4. This is intentionally bespoke to the query-param-action-dispatch idiom (Apps Script's common
   CORS-workaround pattern), not a generalized Express/Flask route matcher — no confirmed target
   needs that pattern this round (YAGNI per interview finding). Structure the arm-parser as its own
   small function so a second idiom (real path-based routing) can be added later without touching
   the call-site/edge-emission logic.

**New parsing required, not reuse — verified, not assumed:** grepped `extract.py` for existing
`fetch` handling and found none (one incidental docstring mention only). The `fetch()` call-site
scan is net-new extraction work, not a reuse of existing `calls`-edge machinery.

## Logical Design

### `detect.py::classify_file()` — add before the `ext = path.suffix.lower()` fallback (~line 403),
same slot as the existing `is_package_manifest_path` check:
```python
from graphify.extract import is_dockerfile_path  # or wherever it ends up living
if is_dockerfile_path(path):
    return FileType.CODE
```

### `extract.py::_get_extractor()` — add two filename checks before the final
`_DISPATCH.get(path.suffix)` (~line 15449), matching the `is_mcp_config_path`/`is_package_manifest_path`
pattern already there:
```python
if is_dockerfile_path(path):
    return extract_dockerfile
if path.name in ("kustomization.yaml", "kustomization.yml"):
    return extract_kustomization
```
`is_dockerfile_path(path)`: `path.name == "Dockerfile" or path.name.startswith("Dockerfile.")`
(covers `Dockerfile`, `Dockerfile.dev`, `Dockerfile.prod` — the common multi-variant convention).

### `extractors/yaml_.py` changes
1. Multi-document fix: wrap the existing single-document body of `extract_yaml()` in a loop over
   `[c for c in root.children if c.type == "document"]` (falling back to treating `root` itself as
   one document if no `document`-typed children exist, for tree-sitter-yaml versions/single-doc
   files where the grammar doesn't wrap in an explicit `document` node — verify actual grammar shape
   against a real multi-doc fixture before assuming the child-type name).
2. Per document: after building the existing generic nodes, check if `apiVersion` and `kind` are
   both present as root-mapping keys (reuse `_mapping_pairs(root_mapping)`, already parsed). If so,
   emit the Resource node additionally, with the document's line offset as `source_location` (needed
   so N Resources in one multi-doc file don't collide on the same file-level location).

### `extractors/kustomization.py` (new, small)
`extract_kustomization(path) -> dict`: parse via the same `tree_sitter_yaml` pattern as `yaml_.py`,
find the `resources:` key's list value, for each string entry resolve it as a path relative to
`path.parent`, emit Module node (this file) + `imports` edge to `_make_id(resolved_path)` (matching
existing cross-file edge conventions — target ID computed the same way a real Resource node for that
file would be, so the edge resolves once that file's own extraction runs, same as any other
forward-reference in the corpus).

### New `LanguageResolver` for `http_calls` — registered at `extract.py:~11745` alongside the others:
```python
register_language_resolver(
    LanguageResolver("http_calls_linking", frozenset({".js", ".jsx", ".ts", ".tsx", ".gs"}), _resolve_http_calls)
)
```
`_resolve_http_calls(per_file, all_nodes, all_edges)`:
1. Scan `.gs`-file function nodes for `doGet`/`doPost`; parse each one's body for
   `if/else if (action === '<literal>')` arms, building `{"<action_value>": <target_call_node_id>}`
   per handler (the target is whatever function that arm calls, e.g. `getHoldings()` — resolve via
   the same `raw_calls` local-call resolution the rest of the file's extraction already does, don't
   reinvent name->node lookup).
2. Scan `fetch(...)` call-sites in `.js`/`.jsx`/`.ts`/`.tsx` files (new — confirmed no existing
   extraction covers this) for a literal `action=<value>` segment in the URL argument.
3. Emit `http_calls` edge from the call-site node to the matched action's target node, confidence
   `"INFERRED"`. Non-literal (interpolated) action values are skipped, not guessed.
4. If zero `.gs` handler nodes exist in the corpus, the resolver is a no-op (matches
   `resolver_registry`'s existing suffix-gate skip behavior — no wasted scan on repos without Apps
   Script).

## Test plan (per feature, assert-based, matching existing `tests/test_*.py` pattern)

- Dockerfile: multi-stage fixture (`FROM node AS build` ... `FROM nginx` + `COPY --from=build`) ->
  assert 2 stage nodes, 1 `depends_on` edge between them, 1 external node for `nginx`/`node` base
  images.
- Kustomize: fixture `kustomization.yaml` listing 2 `resources:` entries + the 2 target manifest
  files -> assert Module node + 2 `imports` edges resolving to the right Resource node IDs.
- Multi-doc YAML fix: fixture with 2 `---`-separated K8s documents (`Deployment` + `Service`) ->
  assert 2 Resource nodes, not 1 (this is the regression test proving the prerequisite bug is fixed).
- http_calls: fixture `.gs` `doGet` with 2 action branches (`action === 'holdings'` ->
  `getHoldings()`, `action === 'dividends'` -> `getDividends()`), fixture `.js` with
  `fetch(url + '?action=holdings')` and a second fetch using an interpolated (non-literal) action
  -> assert the literal call links to `getHoldings()` (not to `doGet` itself), and the
  non-literal call produces no edge (skipped, not guessed).
- Full suite: `uv run pytest -q` stays green, 0 regressions, after each feature lands (matches this
  repo's existing per-feature commit granularity, see `p17-post-competitor-audit-roadmap.md`).
