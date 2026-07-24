# Plans Index — graphify

## Active Plans

| File | Title | Status |
|------|-------|--------|
| [p1-multiterm-seed-ranking.md](p1-multiterm-seed-ranking.md) | P1 — Multi-Term Seed Ranking (Coverage-Based) | Superseded — see p1-multiterm-seed-ranking-reopen.md (completed-archive.md) |
| [p17-post-competitor-audit-roadmap.md](p17-post-competitor-audit-roadmap.md) | P17 — Post-Competitor-Audit Roadmap (file-watcher auto-sync, PageRank ranking, 0.18.0 cut, `affected --relation` prefix match, content-as-data hold) | 4/6 items done (auto-sync, PageRank, 0.18.0 cut, `affected --relation` fix — all shipped), item 5 N/A (not a graphify code task), item 6 (content-as-data indexing) still on hold — needs user sign-off on the trigger heuristic before it can proceed |
| [cross-repo-edges/wayfinder-map.md](cross-repo-edges/wayfinder-map.md) | Cross-Repo Edges — wayfinder map, descoped from iac-http-linking round | Charting (2026-07-24) — 5 tickets, Ticket 1 (does a real need exist?) blocks everything |
| [lsp-type-resolution/wayfinder-map.md](lsp-type-resolution/wayfinder-map.md) | LSP-Style Semantic Type Resolution — wayfinder map, descoped from iac-http-linking round | Charting (2026-07-24) — re-scoped mid-chart (existing `type_table` mechanism found for Swift/TS/C#, gap narrower than assumed); 4 tickets, Ticket 1 blocks everything |

## Completed

→ [completed-archive.md](completed-archive.md) — P1 (reopen), P2–P16, `iac-http-linking`

## Rejected Ideas (evaluated, decided against — not just deferred)

| Idea | Decision date | Reasoning |
|------|------|-----------|
| `affected --include-contains` (or make `contains` a default relation) | 2026-07-04 | `contains` is universal within a file/doc — every function is `contains`-linked to its file, every automation entry to its YAML file. Including it would return most/all co-located nodes for ANY query, turning `affected` from a precise dependency-impact tool into noise. Confirmed on a real case (`AiOverview.jsx`, a page component with real `imports`/`calls` edges but zero code-level dependents — `affected` correctly reports "No affected nodes found" even though removing the page would drop its route, which is a `contains`-only relation). The tradeoff (precise dependency impact vs. blind to routing/containment impact for entry-point nodes) is intentional; not revisiting without a new real case that needs it. |
| P16 Phase 2 (`file:Label` syntax in `_find_node_core`) | 2026-07-04 | See p16-qualified-node-resolution.md — Phase 1's flags already resolve every real duplicate-name case found; Phase 2 would touch the resolver shared by `path`/`explain`/`save-result` for unproven benefit. |
| Switching `god_nodes()` default ranking from `by="degree"` to `by="pagerank"` or a HITS hub-score (both already/newly measured) | 2026-07-04 | Measured directly on 9 real corpora (75–14,593 nodes), using `cross_cutting_nodes()`'s `communities_bridged` as an independent proxy for "real architectural hub." Undirected PageRank: promotions beat demotions on bridge-score in only 2/8 corpora. Directed PageRank (reconstructed from the committed graph.json's real `source`→`target`, no re-extraction): 0/9 — it systematically *demoted* the actual highest-bridge nodes (`SessionCoordinator` bridge=54, `main()` bridge=57, `BaseEntity` bridge=19) in favor of narrower ones. HITS hub-score: 1/9, same failure. Root cause common to all three: PageRank/HITS are eigenvector-family algorithms that reward membership in a tightly self-reinforcing core clique; an architectural god-node's defining property is the *opposite* — it bridges many otherwise-unrelated communities. Plain (non-recursive) degree has no such bias toward concentration, so it tracks `communities_bridged` better than any recursive centrality tried. Not revisiting this family (PageRank/HITS/eigenvector/Katz) for `god_nodes()` ranking without a fundamentally different validation signal than bridge-score. `god_nodes(by="pagerank")` stays as an existing opt-in escape hatch (`--rank-by pagerank`), not promoted to default. |
