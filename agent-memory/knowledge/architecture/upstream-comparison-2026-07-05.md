# graphify fork vs. upstream (safishamsi/graphify) — verified comparison, 2026-07-05

Grep target: `grep -n "<keyword>" knowledge/architecture/upstream-comparison-2026-07-05.md`

Method: shallow-cloned `https://github.com/safishamsi/graphify` (HEAD `3140b2e`,
2026-07-05, `pyproject.toml` version `0.9.6`) into a scratch dir and diffed it
directly against this repo's `graphify/` package (local version `0.16.0`,
1042 local commits) — not a repeat of README's or CHANGELOG's existing claims,
a fresh read of both trees' actual current source, file by file, function by
function on every file with a nonzero diff.

## Status update (same PR, after this audit)

Three items below were fixed directly in this PR rather than left as findings
— see CHANGELOG.md's Unreleased section for the user-facing writeup:

- ✅ **Fixed** — symlink-containment security gap (`_resolves_under_root`
  ported into `collect_files()`/`detect()`).
- ✅ **Fixed** — #1638 (`ref:`-prefixed unresolved JS/TS imports, prevents
  phantom cross-language `imports_from` collisions).
- ✅ **Fixed** — #1659 (JS/TS direct calls no longer bind cross-file without
  import evidence) + the companion `sf_to_file_nid` lookup hardening it
  depends on.
- ✅ **Fixed** — C# receiver-typed member-call resolution (#1609):
  `_csharp_member_type_table` + `_resolve_csharp_member_calls`, closing the
  `_server.Save()` / `Cache.Save()` mis-binding bug described below.

Everything else in this document (Obsidian/Canvas export, Ruby/Kotlin/Apex
extraction gaps, Windows path handling, deterministic merge ordering, etc.)
is unchanged — still open, not addressed by this PR.

## Headline finding

**README.md's "What's different from upstream" section (before this audit's
rewrite) was significantly stale.** It was accurate at some point in this
fork's history, but on 2026-07-02 this fork did a large **merge FROM
upstream** (CHANGELOG.md:86, `## 0.9.5 (2026-07-02, merged from upstream)` —
~15 items, all crediting real external contributors: @joanfgarcia,
@jerryliurui, @Synvoya, @sheik-hiiobd, etc.), which pulled a large fraction
of upstream's own codebase in wholesale. `safishamsi/graphify` is not a
stale/abandoned project the fork left behind — it's an actively maintained,
real community-driven OSS project (dozens of numbered issues, distinct
named contributors, commits as recent as today, 2026-07-05) that has kept
moving in the 3 days since this fork's merge point. The two trees have
partially **re-converged**, and in several areas — including one
security-relevant one — **upstream is now ahead of this fork**, not behind
it.

## Provenance correction — this is adoption, not convergent invention

`git log --diff-filter=A --follow` on this fork's own history removes any
ambiguity about who wrote the shared foundation:

- `graphify/affected.py` was added **2026-05-20** by a commit literally
  titled `feat: add v8 affected and import-resolution support`.
- This fork's own branch history contains repeated wholesale adoptions of
  upstream's **`v8`** branch as this fork's main content, going back months:
  `merge: replace v1/v2 history with v8 codebase as new main`,
  `merge: adopt v8 tree as main content`,
  `Merge remote-tracking branch 'upstream/v8' into v8`,
  `Merge official v8 (v0.8.32) with CodeBuddy support`,
  `Merge pull request #1071 from TheFedaikin/v8`, going back to at least
  2026-05-15 (`Add v8 to CI branch list`).

**Plain reading: `safishamsi/graphify` did a major internal rewrite on a
branch called `v8`, and this fork has repeatedly adopted that v8 branch
wholesale as its own main content for months** — not independently built
equivalent code that happened to converge. `affected.py`,
`resolver_registry.py`, `symbol_resolution.py`, and most of the rest of the
shared package are upstream's own work, absorbed via these merges.

The one place this audit can positively confirm original, fork-authored
work (not absorbed from a v8 merge) is `query.py`: added by commit
`2586f03` at **2026-07-02 16:26**, several hours *before* the final
`merge: upstream/v8 (through their 0.9.5) into main` commit (`ea2135e`,
2026-07-02 20:15). That merge commit's own message confirms it: *"upstream
still had the full pre-BM25 scoring implementation ... discarded upstream's
copy, kept this fork's re-export shim."*

## Quantified, as of right now

| Metric | This fork | Upstream (`3140b2e`) |
|---|---|---|
| Version | 0.16.0 | 0.9.6 |
| `graphify/*.py` total LOC | 47,126 | 45,419 |
| Top-level `.py` modules in `graphify/` | 45 | 42 |
| `tests/test_*.py` files | 126 | 125 |
| Tree-sitter/scanner grammars claimed in README | 54 | 36 |
| Platform install subcommands (`graphify <x> install`) | 23 | 23 (identical list) |
| Local commit count (this fork) | 1,042 | — (shallow clone, not comparable) |

**Real changed-line count on files that exist in both** (via direct `diff`,
not an estimate): ~4,840 diff lines across 13 shared files — nowhere near
README's old claim of "~67k lines changed in `graphify/` alone." That 67k
figure is very likely a cumulative historical stat (total added+removed
across ~1000 commits since the original fork point), most of which the
2026-07-02 upstream merge has since reconciled away. The real, current,
standing diff is roughly **7,000-8,000 lines total** — ~4,840 of diff churn
in 13 shared files plus ~2,459 lines of genuinely fork-exclusive modules.

Per-file diff size (shared files only, line-diff count):

```
1167  export.py
1161  extract.py
 826  serve.py
 563  __main__.py
 468  watch.py
 170  analyze.py
 137  detect.py
 125  report.py
 122  llm.py
  56  cache.py
  34  ruby_resolution.py
   9  build.py
   2  wiki.py
   1  __init__.py
   0  everything else (30 files, byte-identical, incl.
      symbol_resolution.py, resolver_registry.py, affected.py, reflect.py,
      security.py, prs.py, manifest.py, paths.py, multigraph_compat.py,
      mcp_ingest.py, scip_ingest.py, transcribe.py, tree_html.py, validate.py)
```

## File-by-file: what actually differs (not just line counts)

Read every nonzero-diff file end to end and categorized each hunk. `+` =
upstream-only, `-` = fork-only, unless noted.

**`export.py`** (1167 diff lines)
- Fork-only: the full 3D/2D interactive `graph.html` viewer
  (`switchMode`/`init3DGraph`/`update3DGraphData`, 3D-force-graph via CDN),
  a Community/File/Dependencies "lens" toggle, and a physics/display
  settings panel. Upstream's `to_html` ships a plain 2D vis-network view
  only.
- Fork-only: backup retention (`_prune_old_backups()` +
  `GRAPHIFY_BACKUP_KEEP_DAYS`, default 14 days) — upstream's dated backup
  dirs accumulate forever with no pruning.
- **Upstream-only, and fork has zero equivalent: the entire Obsidian export
  pipeline** — `to_obsidian()` (one `.md` note per node, `_COMMUNITY_*.md`
  overview notes, Dataview queries, `.obsidian/graph.json` color groups),
  `to_canvas()` (Obsidian Canvas grid layout), `_cap_filename` (255-byte
  filename cap + hash suffix, upstream #1094), `_dedup_node_filenames`
  (case-insensitive collision guard), and an ownership manifest
  (`.graphify_obsidian_manifest.json`) so re-runs don't clobber a user's
  vault. This is not a small gap — it's a whole export target this fork
  doesn't have at all (confirmed: `__main__.py`'s `export` subcommand
  whitelist has no `obsidian`/`canvas` entry, `export.py` defines neither
  function).

**`extract.py`** (1161 diff lines)
- Fork-only extractors (7, in `graphify/extractors/`): CSS/SCSS, Fish,
  Gherkin, TOML, YAML, HTML, Robot Framework — genuinely absent from
  upstream, not just unimported.
- Fork-only: Playwright/Jest `test()`/`it()`/`describe()` call synthesis —
  each test case becomes its own queryable node. Upstream lacks this
  entirely.
- Fork-only: "P15 value coupling" (`_resolve_value_coupling`,
  `shares_value:<v>` edges, opt-in `value_coupling=` flag).
- Fork-only: `.gs` (Google Apps Script) and `.kiro.hook` recognition. Apex
  (`.cls`/`.trigger`) exists on both sides with identical regex logic —
  fork just moved it to `extractors/apex.py`; cosmetic only.
- Upstream-only: `.mts`/`.cts` TypeScript extension support (dispatch
  table, resolvers, language-family grouping).
- Upstream-only JS/TS: generator functions registered as callable nodes;
  `namespace`/`module`/`declare module` TS containers (`_ts_extra_walk`);
  decorator edges (`_ts_emit_decorator_edges`, `@Component`/`@Injectable`).
- Upstream-only Ruby: `module` as a container type (fixes dot-less method
  labels); `Struct.new`/`Class.new`/`Data.define` factory-assignment
  container synthesis (#1640).
- Upstream-only Kotlin: `class Foo : Bar by baz` delegation resolves an
  `implements` edge.
- **Upstream-only C# receiver-typed call resolution** (`extract.py:11923`,
  `_resolve_csharp_member_calls`, #1609) — **a real correctness bug in this
  fork's favor for upstream**: without it, this fork's C# resolver does a
  bare-name match corpus-wide, so `_server.Save()` can mis-bind to an
  unrelated `Cache.Save()` — a *wrong* edge, not just a missing one.
- **Upstream-only TS/JS receiver typing** (#1630, tracks calls inside
  inline/returned closures like `return () => svc.doThing()` that this
  fork's walker currently drops).
- **Upstream-only fix #1638**: unresolved JS import targets are namespaced
  (`ref:<raw>`) instead of a bare last-segment id — prevents phantom
  cross-language `imports_from` collisions (this fork's own README
  documents fixing an almost-identical class of bug for JS bare imports,
  #1224/#1581 style — this is a related bug upstream closed and the fork
  hasn't).
- **Upstream-only fix #1659**: a JS/TS direct call with no import evidence
  is no longer resolved cross-file by bare name — this fork keeps the more
  permissive (and more bug-prone) behavior for JS/TS.
- **Security-relevant, upstream-only: symlink containment.** Upstream's
  `collect_files()` gained `_resolves_under_root()` checks (for both
  single-file targets and directory walks) so a symlink inside the scan
  root pointing *outside* it is skipped rather than followed. **This fork's
  `collect_files()` has no such guard** — confirmed absent via grep across
  `extract.py`, `detect.py`, `llm.py` (only symlink *cycle* detection
  exists, not containment). Practical impact: pointing `graphify extract`
  at a repo containing an attacker- or accident-planted symlink to
  `/etc/passwd` or a sibling private repo would silently ingest and extract
  that target's content into `graph.json` today.

**`__main__.py`** (563 diff lines — CLI subcommand *names* are identical on
both sides; this is internal-implementation diff)
- Fork-only: `--path`/`--source-path`/`--target-path` on `path`/`explain`,
  `--path`/`--exclude-path` on `query`, `update-all`/`--all` batch mode
  (config-driven, scans a global manifest or search roots),
  `--rank-by degree|pagerank`, browser automation
  (`_auto_open_browser`/`_trigger_live_reload` via `osascript`), and a PyPI
  update-check that runs on most commands.
- Fork-only: `extract` auto-generates `GRAPH_REPORT.md`/`GRAPH_SUMMARY.md`/
  wiki/`graph.html` at the end; upstream's `extract` stops at `graph.json`
  and tells the user to run `cluster-only` next.
- Upstream-only: the new `export obsidian` subcommand; PowerShell-safe `;`
  command chaining in reminder text (fork still uses `&&`, which upstream's
  own #1646 fix says PowerShell 5.1 rejects).

**`watch.py`** (468 diff lines)
- Upstream refactored the ad hoc "preserve/evict nodes+edges" logic into
  `_StoredSourcePaths` + `_reconcile_existing_graph`, handling
  lexical-vs-resolved paths and legacy-relative-root detection —
  **this is upstream's fix for stale-source reconciliation on
  update/delete/rename (#1623/#1622), and this fork still has the older,
  more bug-prone inline logic** (confirmed: fork's `watch.py` has neither
  helper; `_relativize_source_files` still has the pre-fix signature).
- Fork-only: exposes `rank_by`/`resolution`/`exclude_hubs`/`no_viz`/`wiki`/
  `value_coupling` from project config; regenerates wiki + GRAPH_SUMMARY.md
  inside `watch`.
- Small but real: fork writes `.graphify_root` *before* the shrink-guard
  check; upstream defers that write until after the candidate graph is
  accepted, avoiding a marker/graph mismatch if the guard rejects the
  rebuild.

**`analyze.py`** (170 diff lines — beyond the already-confirmed-identical
god-node module/namespace exclusion)
- Fork-only: `god_nodes(by="pagerank")` option, extra noise-label
  exclusions (primitive types, `package.json` keys), `cross_cutting_nodes()`
  (ranks nodes bridging the most distinct communities), and
  `unreachable_functions()` (dead-code heuristic via call-graph
  reachability). All absent upstream.
- Fork-only: `surprising_connections()` bonus for a `documents_bug_in`
  relation upstream doesn't have.

**`detect.py`** (137 diff lines)
- Upstream-only, all real fixes this fork lacks: `.mts`/`.cts` recognized
  as code; Office `.docx`/`.xlsx` sidecar re-conversion when the source is
  newer (#1649 — this fork's sidecar logic still unconditionally skips
  re-conversion once a sidecar exists, so an edited Office file after first
  conversion never updates); word-count caching keyed by file stat
  signature (#1656 — fork recomputes every run); Windows long-path-safe
  I/O wrapper (#1655 — fork uses plain `Path` calls, so paths past 260
  chars fail to hash on Windows); symlink-containment guard (same
  `_resolves_under_root()` gap noted under `extract.py`).
- Fork-only: `.html`/`.yaml`/`.yml` are AST-extracted as code (own
  extractors); upstream classifies these as plain documents since it has
  no dedicated extractors for them.

**`report.py`** (125 diff lines)
- Fork-only: `summarize()` (`GRAPH_SUMMARY.md`), a "Cross-Cutting Nodes"
  section, and an `unreachable_functions()`-backed Knowledge Gaps entry —
  none exist upstream.
- Upstream-only: a "Community Hubs (Navigation)" section with Obsidian
  wikilinks (tied to the obsidian export this fork lacks), and gating the
  "Import Cycles" section on the graph actually containing code (#1657 —
  this fork still emits a "None detected" Import Cycles section
  unconditionally, including on doc-only corpora).

**`llm.py`** (122 diff lines)
- Upstream-only, real hardening this fork lacks: `_sanitize_fragment()`
  coercing malformed LLM JSON entries so one bad edge/node doesn't crash
  the whole chunk merge (#1631 — confirmed: fork's `_parse_llm_json`
  returns `parsed` with no sanitization step); deterministic
  submission-order merging for parallel LLM chunks (#1632 — fork still
  merges via `as_completed()` completion order, so `graph.json` node/edge
  ordering can churn between identical runs); symlink-escape checks for
  text/image extraction units (same containment gap as above); and a fix
  to stop passing `--system-prompt` to the Claude Code CLI backend (newer
  CLIs ≥2.1 don't treat it as sole authority, so extraction can stall
  mid-bisection — fork still uses the old `--system-prompt` approach).
- Fork-only: `documents_bug_in` relation support, `GRAPHIFY_NO_LLM`
  skip/log short-circuit.

**`cache.py`** (56 diff lines) — upstream adds `cached_word_count()` and
hardens `file_hash()` to coexist with word-count-only cache entries; fork
has neither (ties into the `detect.py` word-count-caching gap above).

**`ruby_resolution.py`** (34 diff lines) — upstream registers
method-less class/module container nodes (bare-constant nodes for
empty/error classes) and generalizes `Class.new`-only resolution to other
capitalized-receiver calls (e.g. `Service.call`, the dominant Rails idiom);
this fork only handles the `.new` case.

**`build.py`** (9 diff lines) — upstream guards against a crash when a
node's `source_file` relativizes to `Path('.')` (#1618) and adds
`.mts`/`.cts` to the JS language family; fork has neither.

**`wiki.py`** (2 diff lines) — cosmetic only: footer link points at
`Vit129/graphify` (fork) vs `safishamsi/graphify` (upstream).

**`__init__.py`** (1 diff line) — upstream registers a lazy `"to_canvas"`
export entry (ties to the obsidian export); fork doesn't, consistent with
lacking that feature entirely.

## Verification checklist — all 13 "assumed missing" items from the first pass, now confirmed

The first pass of this audit flagged 12-13 upstream fixes as "likely also
missing, not independently verified." Re-checked every one directly against
this fork's source (file:line evidence, not assumption):

| # | Item (upstream issue) | Verdict | Evidence |
|---|---|---|---|
| 1 | Symlinked-input containment (#1613) | **CONFIRMED ABSENT** | No `_resolves_under_root`/`_resolve_under_root` in `detect.py`/`extract.py`/`llm.py`; only symlink *cycle* detection exists (`detect.py:1072-1074`, `extract.py:15927-15928`) |
| 2 | TS/JS generator functions as nodes (#1615) | **CONFIRMED ABSENT** | `generator_function_declaration` only in scope-boundary set (`extract.py:1594-1595`), missing from `function_types`/`function_boundary_types` (`extract.py:2728-2759`) |
| 3 | TS namespace/module containers (#1615) | **CONFIRMED ABSENT** | No `_ts_extra_walk`/`internal_module` anywhere; never added, not reverted (checked fork's own commit history) |
| 4 | TS import-equals edges (#1615) | **CONFIRMED ABSENT** | No `import_require_clause` in `extract.py`; import resolvers only scan direct `string` children |
| 5 | `.mts`/`.cts` recognition (#1607) | **CONFIRMED ABSENT** | Zero matches anywhere in `extract.py`/`detect.py` |
| 6 | Malformed LLM chunk sanitization (#1631) | **CONFIRMED ABSENT** | `llm.py:781`, `_parse_llm_json` has no `_sanitize_fragment` step |
| 7 | `ref:` prefix on unresolved imports (#1638) | **CONFIRMED ABSENT** | `extract.py:1782`, `_resolve_js_import_target` still returns a bare id |
| 8 | Deterministic parallel-merge ordering (#1632) | **CONFIRMED ABSENT** | `llm.py:1853-1863`, merges via `as_completed()` directly |
| 9 | `to_canvas` dangling-member guard (#1236 follow-up) | **CONFIRMED ABSENT (bigger gap)** | The entire obsidian/canvas export target doesn't exist in the fork — nothing to guard |
| 10 | Stale-source reconciliation (#1623/#1622) | **CONFIRMED ABSENT** | `watch.py` has no `_reconcile_existing_graph`/`_StoredSourcePaths` |
| 11 | Windows long-path hashing (#1655) | **CONFIRMED ABSENT** | `cache.py:144-151` only strips `\\?\` for cache keys, doesn't add it for real I/O |
| 12 | Office `--update` re-entry fix (#1649) | **CONFIRMED ABSENT** | `detect.py:637-639`, `convert_office_file` unconditionally skips existing sidecars |
| 13 | Cached word counts (#1656) | **CONFIRMED ABSENT** | No `cached_word_count` anywhere in `cache.py`/`detect.py` |

**All 13 are genuinely absent** — none partially present, none independently
reimplemented differently. Item 9 turned out to be a much bigger gap than
originally scoped (a missing guard on a feature that doesn't exist at all,
not a missing guard on an existing feature).

## Consolidated: fork-only wins vs. upstream-only wins

**This fork has, and upstream has nothing equivalent to:**
`query.py`'s BM25 + typo/synonym retry + combinatorial-disambiguation +
hub-avoidance query/pathfinding layer; 7 extra language/config extractors
(CSS/SCSS, HTML, YAML, TOML, Robot Framework, Gherkin, Fish); value-coupling
(`shares_value` edges); per-project config (`config.py`,
`graphify.toml`/`[tool.graphify]`) + `update --all`; the 3D/lens
`graph.html` viewer; backup pruning; Playwright/Jest test-node synthesis;
`cross_cutting_nodes()`/`unreachable_functions()` analysis + `GRAPH_SUMMARY.md`;
`--path`/`--source-path`/`--target-path`/`--context` CLI flags; browser
auto-open/live-reload; `documents_bug_in` relation + `GRAPHIFY_NO_LLM`.

**Upstream has, and this fork has nothing equivalent to:**
the entire Obsidian/Canvas export pipeline; C# receiver-typed call
resolution (+ a real bugfix over this fork's bare-name matching); TS/JS
receiver typing for inline/returned closures; two real JS/TS cross-file
false-edge fixes (#1638, #1659) this fork's resolver still exhibits; Ruby
`module`/factory-class container nodes; TS namespace/module containers,
generator-function nodes, decorator edges, import-equals edges; Kotlin
delegation edges; Apex multi-interface `extends`; `.mts`/`.cts` support;
**symlink-containment security guard** (missing across `extract.py`,
`detect.py`, `llm.py` — the one item here worth prioritizing above the
others); malformed-LLM-JSON hardening; deterministic parallel-merge
ordering; Windows long-path I/O; Office incremental re-conversion; cached
word counts; stale-source reconciliation on `update`/`watch`.

## Curiosity, not verified further

`update_check.py` (fork-only) checks PyPI for package name `graphifyy`
(`PACKAGE_NAME = "graphifyy"`) — but this fork explicitly does **not**
publish to PyPI (README.md, "the PyPI name `graphifyy` is already taken by
upstream's package"). So this fork's self-update-check mechanism, if it
still runs, would be checking upstream's PyPI releases, not this fork's own
git commits. Not confirmed whether this code path is actually wired up to
run anywhere (`grep`-only check, not traced), just flagged as a loose end
worth a look if `graphify --version` nags about updates unexpectedly.

## Bottom line

**Far less different than README used to claim, the difference runs in
both directions, and most of the shared foundation is upstream's own code
adopted via repeated `v8` merges — not this fork's original engineering.**
This fork's genuinely original contribution is: the query/pathfinding layer
(`query.py`, built in one documented session, confirmed by commit
timestamps and the merge commit's own message), 7 extra language/config
extractors, value-coupling, per-project config, and a handful of UX/tooling
additions (3D viewer, backup pruning, browser automation, extra analysis
metrics). Upstream's genuinely original, currently-unmerged contribution is
larger than first estimated: real extraction-correctness fixes across 6+
languages, deterministic/robustness hardening in the LLM and caching
layers, Windows compatibility fixes, and — the one item worth acting on
first — **a symlink-containment guard this fork's extraction pipeline
currently lacks entirely.** Pulling upstream's post-2026-07-02 commits back
in (the same way the repeated `v8` adoptions worked) would close all of the
above in one pass; the symlink-containment gap is the one item here with a
plausible security angle and worth prioritizing independently of a full
re-sync.
