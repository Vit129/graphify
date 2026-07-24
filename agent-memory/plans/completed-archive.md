# Completed Plans Archive

All plans below are **done** — no remaining tasks, no open decisions blocking them. Full detail
stays in each plan's own file; this is the compact index. Matches the convention established in
`kouen-terminal/agent-memory/plans/completed-archive.md`.

---

## P1 (reopen) — BM25 rewrite of `_score_nodes`
- Replaced the old exact/prefix/substring/trigram+IDF tier system with real Okapi BM25 (saturating
  term-frequency + document-length normalization)
- Superseded the original P1 doc's "ceiling closed" claim and a first reopen draft (stopword
  filter) — both re-validated and found not actually fixed
- See `p1-multiterm-seed-ranking.md` for the superseded original

## P2 — YAML Extraction Support
- New `extractors/yaml_.py` — YAML previously had zero extractor, files were invisible to the graph
- Structural extraction: top-level key → node, list/mapping children → child nodes, labeled by
  `alias`/`name`/`id`/`description` when present

## P3 — CamelCase / snake_case Tokenization in Search
- `_search_tokens` now splits `getUserData`/`get_user_data` into sub-words before scoring
- Adopted the shape of `DeusData/codebase-memory-mcp`'s `cbm_camel_split` tokenizer (concept, not
  code — no FTS5/SQLite dependency)
- Regression caught: sub-word matches were first wired into the exact tier (false-tied with whole-
  label exact matches) — fixed by routing them into the prefix tier instead

## P4 — test()/describe() Block Extraction (spec.ts)
- `test(...)`/`describe(...)` blocks now become graph nodes (previously invisible)

## P5 — Typo/Abbreviation Cascade Fallback
- Damerau-Levenshtein edit distance for typos, ordered-subsequence matching (ported from
  harness-terminal's `FuzzyPathResolver.swift`) for abbreviations
- Corrected terms re-run through the unmodified `_score_nodes`/`_pick_seeds` pipeline — no second
  scoring algorithm needed
- Later closed a compound-span gap (Bitap/agrep-style fuzzy-substring search) for typos inside a
  longer multi-word label

## P6 — Robot Framework Extraction Support
- `.robot`/`.resource` files extracted (Robot Framework test suites)

## P7 — Additional Language Coverage (CSS, HTML, .resource, .gs)
- CSS, HTML, `.resource`, `.gs` (Google Apps Script) added to extraction coverage

## P8 — SCSS + Gherkin Extraction, Robot Cross-File Resolution
- SCSS extraction + cross-file resolution, Gherkin (`.feature`) extraction, Robot Framework
  cross-file call resolution

## P9 — Lightweight Query Synonym Expansion
- Synonym/vocabulary expansion as the semantic-search alternative — explicitly chosen over full
  embedding search (infra-cost tradeoff declined, see `feature-provenance.md`)

## P10 — TOML + Fish Extraction, Real-Project Validation
- TOML extraction, Fish shell function extraction (hand-rolled scanner — no tree-sitter-fish
  grammar published), validated against real personal projects

## P11 — Personal-Project Coverage Sweep
- `.hook` file coverage (free win) + full validation sweep across personal projects

## P12 — CODE_EXTENSIONS Classifier Gap
- Critical fix: the real CLI never saw newly-added languages because `CODE_EXTENSIONS` (the
  classifier gate) wasn't updated alongside new extractors — silent invisibility bug for an entire
  session before caught

## P13 — Lazy-Loaded 3D Force Graph Option
- Additive, opt-in 3D force-graph visualization mode

## P14 — Obsidian-like Graph Control & Automation
- Auto-open, live-reload, settings panel for the graph viewer (shipped in `e4e4f9c`/`d79b6fb`) —
  plan doc had gone stale claiming otherwise, corrected 2026-07-18

## P15 — Opt-In Config Value-Coupling Edges (`shares_value`)
- `shares_value:<value>` INFERRED edges between files sharing an identifier-shaped leaf value
  (e.g. two Home Assistant automations both referencing `input_boolean.home_mode`)
- Gate passed ~96% precision on real Home-Assistant validation (+1.6% edges); dotted-reference-only
  filter + service-verb exclusion + hub cap — the filter set that actually hit precision, not the
  plan's original 3-filter set (~27%)

## P16 — Qualified Node Resolution for `path`/`explain`
- Phase 1 done: `--path`/`--source-path`/`--target-path` flags resolve duplicate-name node
  collisions deterministically
- Phase 2 (`file:Label` syntax in `_find_node_core`) explicitly rejected, not deferred — Phase 1
  already resolves every real case found; the plan's own gate ("only if Phase 1 proves clumsy in
  real use") never triggered

## IaC Indexing + HTTP Call-Site Linking (`iac-http-linking`)
- Dockerfile extractor (multi-stage build graph, `depends_on` edges), multi-document YAML fix
  (silently-dropped `---`-separated documents — a P2-era bug, only found while designing this),
  K8s Resource-node typing (additive `type="resource"` nodes), Kustomize `imports` edges
- `http_calls` edge: parses `doGet`/`doPost` action-dispatch arms + `fetch()` literal-action
  call-sites, links them cross-file by action-string match — verified live against
  My-Investment-Port (`fetch(action=all) -> syncLocalStorageToGoogleSheets()`, confidence INFERRED)
- Feature 3 (TF-IDF search fallback) dropped mid-round — confirmed moot, BM25 (P1 reopen) already
  supersedes it; recorded in `feature-provenance.md`'s "Rejected: TF-IDF Fallback Search Tier"
- 9/9 tasks, 3025 tests passing, 2 real bugs found and fixed via TDD before shipping (id-collision,
  stale-id dangling edge) plus 3 more found via a live multi-file smoke test (wrong cache directory,
  missed second if-chain, wrong-call heuristic) — see `iac-http-linking/dev-task-progress.md` for
  full detail
