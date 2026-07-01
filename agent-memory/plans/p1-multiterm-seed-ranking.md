# P1 — Multi-Term Seed Ranking (Coverage-Based)

Status: **Active**
Priority: **P1** — search that misses the file a developer actually needs to edit defeats the point of the tool
Owner surface: `_pick_seeds`, `_score_nodes` (`graphify/serve.py`)
Created: 2026-07-01
Depends on: community-diversification pass already landed (commit `dff02a5`, fixes single-dominant-community noise)

---

## Why

Real-query validation against 3 production graphs (Home-Assistant, My-Investment-Port, harness-terminal) surfaced two distinct multi-term ranking failures, discovered by simulating actual bug-fix queries a developer would type (not synthetic test cases):

1. **Single dominant match** (fixed, `dff02a5`): one term's coincidental exact-label match (e.g. a test-fixture variable literally named `"holdings"`) scores 1000x higher than substring matches, so `gap_ratio` drops every other candidate. Fixed by diversifying seeds across up to 5 additional graph communities.
2. **Scattered noise across many communities** (this plan): verbose natural-language queries (10+ terms) hit generic single-word nodes (`running`, `attention`, `board`, `status`) each in a *different* community — these fill all 5 diversity slots before a node that substring-matches MANY terms (but never wins the 1000x exact-match tier) is ever reached. Confirmed on harness-terminal: the real target `.agentDotColor()` in `SidebarSessionListView.swift` scored only 12.3 (out of 3240 candidates, top score 7661) and its community ranked 11th by term-coverage — outside the `max_communities=5` cap.

## Non-goals (this plan)

- Rewriting `_score_nodes`'s scoring tiers (exact/prefix/substring/source bonuses) — out of scope, would ripple through every existing caller and test.
- Semantic/embedding-based fallback search — already evaluated and rejected as Feature B (architecturally dead code: never fires because rationale/docstring nodes are already regular scored nodes, so `_score_nodes` is essentially never empty).
- Tuning `max_communities` arbitrarily upward to force one example query to pass — see Ceiling below.

## What's done

- Added optional `terms: list[str] | None` param to `_pick_seeds`. When present, the community-fill loop (used only when `multi_term=True`) ranks remaining candidates by `(-coverage, -score)` instead of pure score — `coverage` = count of distinct query terms found in a node's label/source path. This lets a node matching 4-5 terms broadly outrank a node matching 1 term with a huge exact-match bonus, when picking which additional communities to seed.
- Backward compatible: omitting `terms` preserves the exact `dff02a5` behavior (pure score-order fill).
- Verified against harness-terminal's real graph: seeds moved from generic README/BoardModel noise (`attention`, `running`, `done`, `copyPath`) to genuinely relevant candidates — `AgentStatusDot` (a dot-status UI component), `tab-bar.md`'s exact `[agentIcon?] [statusDot]` layout doc, and a plan doc literally titled "Git status dots in NodeRow."
- Full suite green: `uv run pytest -q` — 2689 passed, 0 failures.

## Ceiling (known, not fixed by this pass)

`SidebarSessionListView.swift`'s `.agentDotColor()` — the literal target function — still doesn't make the cut. Its community ranks 11th by coverage; `max_communities=5` stops before reaching it. Bumping the cap to "whatever number surfaces this one example" is overfitting to a single validation query, not a general fix — noted here instead of silently forcing it.

`ponytail:` if this recurs across other real queries (not just this one validation case), the next lever is either (a) raising `max_communities` with an empirically-chosen number backed by multiple real queries, or (b) scoping coverage to *meaningful* terms only (drop generic single-syllable words like "board"/"status"/"icon" from the coverage count so they stop occupying top-coverage slots) — not attempted here because it requires a stopword list, which is new surface area beyond what today's validation justifies.

## Verification

- `tests/test_serve.py::test_pick_seeds_multi_term_diversifies_across_communities` / `test_pick_seeds_multi_term_stays_single_community_unaffected` — unchanged, still pass (backward-compat guard).
- Manual validation: `graphify query "panel session status icon agent logo instead of yellow dot needs attention running board"` against harness-terminal's real graph, before/after comparing seed lists (see session log, 2026-07-01).
