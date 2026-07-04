# Plans Index — graphify

## Active Plans

| File | Title | Status |
|------|-------|--------|
| [p1-multiterm-seed-ranking.md](p1-multiterm-seed-ranking.md) | P1 — Multi-Term Seed Ranking (Coverage-Based) | Superseded — see p1-multiterm-seed-ranking-reopen.md |
| [p1-multiterm-seed-ranking-reopen.md](p1-multiterm-seed-ranking-reopen.md) | P1 (reopen) — BM25 rewrite of `_score_nodes` | Done |
| [p2-yaml-extraction.md](p2-yaml-extraction.md) | P2 — YAML Extraction Support | Done |
| [p6-robot-framework-extraction.md](p6-robot-framework-extraction.md) | P6 — Robot Framework Extraction Support | Done |
| [p3-camelcase-tokenization.md](p3-camelcase-tokenization.md) | P3 — CamelCase / snake_case Tokenization in Search | Done |
| [p4-spec-test-block-extraction.md](p4-spec-test-block-extraction.md) | P4 — test()/describe() Block Extraction (spec.ts) | Done |
| [p5-fuzzy-fallback-cascade.md](p5-fuzzy-fallback-cascade.md) | P5 — Typo/Abbreviation Cascade Fallback | Done |
| [p7-additional-language-coverage.md](p7-additional-language-coverage.md) | P7 — Additional Language Coverage (CSS, HTML, .resource, .gs) | Done |
| [p8-scss-cross-file-and-gherkin.md](p8-scss-cross-file-and-gherkin.md) | P8 — SCSS + Gherkin Extraction, Robot Cross-File Resolution | Done |
| [p9-query-synonym-expansion.md](p9-query-synonym-expansion.md) | P9 — Lightweight Query Synonym Expansion (semantic-search alternative) | Done |
| [p10-toml-and-fish-extraction.md](p10-toml-and-fish-extraction.md) | P10 — TOML + Fish Extraction, Real-Project Validation | Done |
| [p11-personal-project-coverage-sweep.md](p11-personal-project-coverage-sweep.md) | P11 — Personal-Project Coverage Sweep (.hook free win + full validation) | Done |
| [p12-code-extensions-classifier-gap.md](p12-code-extensions-classifier-gap.md) | P12 — CODE_EXTENSIONS Classifier Gap (critical: real CLI never saw the new languages) | Done |
| [p13-3d-force-graph-lazy-view.md](p13-3d-force-graph-lazy-view.md) | P13 — Lazy-Loaded 3D Force Graph Option (Additive, Opt-In) | Done |
| [p14-obsidian-like-graph-control.md](p14-obsidian-like-graph-control.md) | P14 — Obsidian-like Graph Control & Automation | In Progress |
| [p15-config-value-coupling.md](p15-config-value-coupling.md) | P15 — Opt-In Config Value-Coupling Edges (`shares_value`) | Done (2026-07-04) — gate passed ~96%, verified on HA (+1.6% edges) |
| [p16-qualified-node-resolution.md](p16-qualified-node-resolution.md) | P16 — Qualified Node Resolution for `path`/`explain` (duplicate-name root cause) | Phase 1 Done (2026-07-04); Phase 2 rejected — no evidence needed |

## Rejected Ideas (evaluated, decided against — not just deferred)

| Idea | Decision date | Reasoning |
|------|------|-----------|
| `affected --include-contains` (or make `contains` a default relation) | 2026-07-04 | `contains` is universal within a file/doc — every function is `contains`-linked to its file, every automation entry to its YAML file. Including it would return most/all co-located nodes for ANY query, turning `affected` from a precise dependency-impact tool into noise. Confirmed on a real case (`AiOverview.jsx`, a page component with real `imports`/`calls` edges but zero code-level dependents — `affected` correctly reports "No affected nodes found" even though removing the page would drop its route, which is a `contains`-only relation). The tradeoff (precise dependency impact vs. blind to routing/containment impact for entry-point nodes) is intentional; not revisiting without a new real case that needs it. |
| P16 Phase 2 (`file:Label` syntax in `_find_node_core`) | 2026-07-04 | See p16-qualified-node-resolution.md — Phase 1's flags already resolve every real duplicate-name case found; Phase 2 would touch the resolver shared by `path`/`explain`/`save-result` for unproven benefit. |
| Switching `god_nodes()` default ranking from `by="degree"` to `by="pagerank"` or a HITS hub-score (both already/newly measured) | 2026-07-04 | Measured directly on 9 real corpora (75–14,593 nodes), using `cross_cutting_nodes()`'s `communities_bridged` as an independent proxy for "real architectural hub." Undirected PageRank: promotions beat demotions on bridge-score in only 2/8 corpora. Directed PageRank (reconstructed from the committed graph.json's real `source`→`target`, no re-extraction): 0/9 — it systematically *demoted* the actual highest-bridge nodes (`SessionCoordinator` bridge=54, `main()` bridge=57, `BaseEntity` bridge=19) in favor of narrower ones. HITS hub-score: 1/9, same failure. Root cause common to all three: PageRank/HITS are eigenvector-family algorithms that reward membership in a tightly self-reinforcing core clique; an architectural god-node's defining property is the *opposite* — it bridges many otherwise-unrelated communities. Plain (non-recursive) degree has no such bias toward concentration, so it tracks `communities_bridged` better than any recursive centrality tried. Not revisiting this family (PageRank/HITS/eigenvector/Katz) for `god_nodes()` ranking without a fundamentally different validation signal than bridge-score. `god_nodes(by="pagerank")` stays as an existing opt-in escape hatch (`--rank-by pagerank`), not promoted to default. |
