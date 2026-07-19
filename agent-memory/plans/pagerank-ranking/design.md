# PageRank-Style Symbol/File Importance Ranking — Design

Source: P17 item 2 (`agent-memory/plans/p17-post-competitor-audit-roadmap.md`).

## Orientation (required before design, per this session's own established discipline)

Confirmed by reading the real code and benchmarking on real graphs, not assumed:

- `_score_nodes` (`graphify/query.py:607-658`) and `_pick_seeds` (`query.py:685-770`) unchanged in
  shape/line-position since this session's earlier reading (item 1's investigation). `_score_nodes`
  returns `list[(score, nid)]` from BM25 term-frequency + an exact/prefix full-query bonus + a
  source-match bonus. `_pick_seeds` then applies a **multiplicative** `_seed_penalty` — `0.85` for
  concept nodes, `0.9` for prose/doc nodes, `1.0` otherwise (`_CONCEPT_SEED_PENALTY`/
  `_PROSE_SEED_PENALTY`, `query.py:661-662`) — "for THIS selection only" (doesn't mutate the caller's
  `scored` list), re-sorts, then keeps everything within `gap_ratio=0.8` of the top score as seeds
  (plus an optional multi-community diversity fill for multi-term queries). **This multiplicative
  penalty step is the existing composition point a new ranking factor should join, not compete with.**
- `god_nodes(by="pagerank")` already exists (`graphify/analyze.py:113-160`) and calls `nx.pagerank(G)`
  directly — real precedent, not something to reimplement. But it's computed **on demand**, inside
  `god_nodes()`, which is only called from the report-generation path (`GRAPH_REPORT.md`), not from
  `query`/`explain`/`path`.
- **`scipy` (required by `nx.pagerank`) is optional and is NOT even in the `all` extras bundle**
  (`pyproject.toml:64`, `pagerank = ["scipy"]`, vs. the separate `all = [...]` list which omits it) —
  confirmed by reading `pyproject.toml` directly. This is the single most important constraint: this
  feature **cannot** become a hard dependency of `query`/`explain`/`path` working at all. It must degrade
  to today's pure-BM25 behavior whenever scipy wasn't available at build time.
- **Benchmarked, not assumed**: `nx.pagerank(G)` on this session's largest known real graph
  (kouen-terminal, 15,251 nodes / 34,273 edges) took **0.297s**. Cheap enough to run once per
  `extract`/`update` (a build already takes seconds-to-minutes), far too slow to redo on every single
  `query`/`explain`/`path` call within one agent session (which can fire dozens of times) — settles the
  "compute at build time vs. query time" question decisively in favor of **build time, precomputed and
  stored**, not query-time computation.
- **Found the exact existing hook point** to store it: `to_json` (`graphify/export.py:1001-1050`)
  already does exactly this pattern for `community` — `for node in data["nodes"]: node["community"] =
  node_community.get(node["id"])`, right before the graph is serialized to `graph.json`. Adding a
  `node["pagerank"] = pr_scores.get(node["id"])` line in the same loop is the natural, minimal-diff
  place — mirrors an established convention instead of inventing a new one.

**Conclusion: this is not "add PageRank to graphify" (it already has PageRank, in `god_nodes`) — it's
"precompute it once at build time like `community` already is, store it on the node, and let `_pick_seeds`
use it as one more multiplicative factor alongside the concept/prose penalties it already applies."**

## Strategic Design

Same as item 1: this is an algorithm/CLI feature, not a business-domain model — bounded-context/
aggregate/domain-event vocabulary doesn't map onto it. The real strategic decision is **opt-in vs.
automatic-when-available**:

| | **A. Automatic whenever scipy is installed** | **B. Opt-in flag, mirroring `value_coupling`** |
|---|---|---|
| Precedent | None in this codebase for a *scoring* behavior change | `graphify.toml`'s `value_coupling = true` (P15) — exact same shape: an optional-dependency-gated feature that changes graph output, off by default |
| `god_nodes(by="pagerank")` itself | Requires explicit `by="pagerank"` even when scipy IS installed — default stays `"degree"` | Consistent with this — the codebase's own convention already leans toward explicit opt-in for pagerank specifically, not "on because the import succeeded" |
| Risk if wrong | Every existing user who happens to have scipy installed (e.g. for an unrelated reason) gets silently different query/explain/path result ordering on their next `update` — no signal, no changelog line seen, a real "why did results change" support burden | None — nothing changes until a user deliberately opts in, same rollout shape P15 already validated |
| Regression surface | Same code path (`_pick_seeds`) serves every `query`/`explain`/`path` call for every user, not a new isolated feature | Same, but scoped to opted-in projects only during initial rollout |

**Decision: B (opt-in), matching `value_coupling`'s established rollout shape exactly.** A new
`graphify.toml` key, `pagerank_ranking = true` (default `false`), gates whether `extract`/`update`
attempts to compute and store PageRank at all. Reasoning: (1) this changes ranking behavior for every
query in every session on an opted-in project, and unlike item 1 (purely additive infra) there's no way
to "notice and revert" a ranking regression as cleanly as reverting a config line and rebuilding — P15
already proved this exact opt-in-config shape works cleanly for a similarly build-time-computed,
scipy-adjacent optional graph enrichment; (2) `god_nodes` itself already sets the precedent that having
scipy installed is not sufficient signal to change default behavior.

## Tactical Design

No entities/aggregates in the DDD sense (infrastructure/algorithm feature, as item 1's design also
noted). The actual "domain object" here is a per-node float attribute, computed once and composed into
an existing scoring pipeline. Described as data flow + composition rule, not a domain event stream:

```
extract/update (graphify/watch.py's _rebuild_code, and the equivalent extract-CLI path)
  -> if graphify.toml's pagerank_ranking = true:
       try: import scipy  (probe only, before attempting nx.pagerank)
       except ImportError: print a one-line stderr notice (mirrors god_nodes' existing
         ImportError message text/install instructions) and skip - graph still builds
         normally, just without the pagerank attribute this run (same graceful-degradation
         shape as `watch` being unavailable when watchdog is missing)
       else: pr_scores = nx.pagerank(G)  (same call god_nodes already makes - no new
         algorithm code, just relocated to build time and made persistent)
  -> to_json (export.py:1001), same loop that already does node["community"] = ...:
       node["pagerank"] = pr_scores.get(node["id"])  (omitted/None when pagerank_ranking
       is off or scipy is missing - graph.json stays valid old-shape JSON either way,
       no schema-breaking required field added)

query/explain/path (graphify/query.py's _pick_seeds, query.py:725-734)
  -> _seed_penalty(nid) extended, not replaced:
       existing: 0.85 (concept) / 0.9 (prose) / 1.0 (default) multiplicative penalty
       new: multiply that existing factor by a pagerank BOOST factor, bounded to
       [1.0, 1.0 + PAGERANK_BOOST_MAX] (default PAGERANK_BOOST_MAX = 0.15 - small
       relative to BM25's dominant signal, intentionally: this is described in the
       roadmap as "layer on top of, not replace" BM25, and the concept/prose penalties
       already prove out that a modest multiplicative nudge, not a large one, is
       graphify's established idiom here) computed as:
         1.0 + PAGERANK_BOOST_MAX * (node_pagerank / max_pagerank_in_this_graph)
       - relative-to-graph-max, not the raw nx.pagerank value directly, because raw
       PageRank values are tiny probabilities (sum to 1.0 across the whole graph) with
       a long-tail distribution - using them unnormalized would make the boost either
       negligible on small graphs or need per-graph-size tuning; max-normalizing keeps
       the boost's effective range identical regardless of graph size
       - a node with no "pagerank" attribute (attribute absent = old graph, or
       pagerank_ranking was off at build time) gets factor 1.0 (no-op) - the ONLY new
       failure mode is "attribute missing," and it degrades to exactly today's behavior,
       not an error
```

**Why compose inside `_seed_penalty`, not as a separate step**: `_seed_penalty` already runs "for THIS
selection only" (doesn't mutate the caller's `scored` list) and already re-sorts afterward — the exact
lifecycle a new multiplicative factor needs. Adding a second, separate re-scoring pass elsewhere would
either (a) run before `_seed_penalty` and get silently overwritten by its own re-sort, or (b) require
duplicating the "non-destructive, re-sort after" pattern a second time. Extending the one existing
function is the smaller, more correct diff.

**Why bounded/multiplicative, not additive-to-raw-BM25-score**: BM25 scores in this codebase already
carry large multiplicative bonuses (`_EXACT_MATCH_BONUS * 10`, etc. — see `_score_nodes`) that can differ
by orders of magnitude between an exact match and a weak partial match. A raw additive PageRank term
risks being either invisible against a strong BM25 signal or (if scaled up to be visible) capable of
promoting an irrelevant-but-central node over a genuinely on-topic peripheral one — exactly the failure
this feature is meant to prevent, inverted. A small, bounded multiplicative nudge can only ever act as a
tie-breaker among already-close candidates, never override a clear BM25 winner - matching "layer on top
of, don't replace" literally, not just in spirit.

## Logical Design

**New CLI/config surface**:
- `graphify.toml`: `pagerank_ranking = true` (default `false`), same declaration shape as
  `value_coupling` (P15).
- No new CLI flags on `query`/`explain`/`path` — ranking behavior is a build-time property of the graph
  (whether nodes carry a `pagerank` attribute), not a per-query choice, consistent with how `community`
  membership isn't a per-query flag either.
- `extract`/`update --pagerank-ranking` CLI override flag, mirroring the existing `--value-coupling`
  flag pattern (`graphify/__main__.py`'s `extract`/`update` arg parsing already threads a boolean flag
  like this through to `_rebuild_code`) — lets a user try it once without committing to
  `graphify.toml` first.

**Changed files**:
- `graphify/watch.py`'s `_rebuild_code` — new `pagerank_ranking: bool = False` parameter (mirrors the
  existing `value_coupling: bool = False` parameter exactly), gates a `nx.pagerank(G)` call before
  `to_json` is invoked; catches `ImportError` and prints the same install-instructions message
  `god_nodes` already uses (single source of truth for that message text — factor it into a shared
  constant both call sites import, don't duplicate the string).
- `graphify/export.py`'s `to_json` — **resolved, verified**: `communities` (the equivalent precomputed
  per-node value) is passed as an explicit positional parameter from `_rebuild_code`
  (`watch.py:861`, `to_json(G, communities, str(graph_tmp), force=True, built_at_commit=commit)`), not
  attached to `G`'s node data beforehand. `pagerank_scores: dict[str, float] | None = None` joins as a
  new keyword parameter on `to_json`, same convention — `_rebuild_code` computes it (or leaves it
  `None`) and passes it through explicitly, not via a side-channel on `G`.
- `graphify/query.py`'s `_seed_penalty`/`_pick_seeds` — the boost-factor composition described above.
  New module constant `_PAGERANK_BOOST_MAX = 0.15`.
- `graphify/config.py` — **no change needed, verified**: `load_project_config` is a generic, unschemad
  TOML-to-dict loader (`config.py:6-55`) — any `graphify.toml` key becomes available via
  `proj_config.get(key, default)` with zero validation, confirmed by reading how `value_coupling` itself
  is read (`__main__.py:4817`, `proj_config.get("value_coupling", False)` — a plain dict read, no schema
  registration anywhere). `pagerank_ranking` needs the exact same one-line read at the equivalent call
  sites, nothing more.
- `graphify/__main__.py` — `extract`/`update` arg parsing: add `pagerank_ranking =
  proj_config.get("pagerank_ranking", False)` alongside the existing `value_coupling` read
  (`__main__.py:4817`), plus a `--pagerank-ranking` CLI flag mirroring `--value-coupling`'s existing
  parsing (`__main__.py:4887`) exactly, threaded into the same `ast_kwargs`/`_rebuild_code` call sites
  `value_coupling` already flows through (`__main__.py:4026`, `4110`, `5132`).

**Test plan** (mirrors this session's own discipline: real-repo validation, not just synthetic):
1. Unit: `_rebuild_code(pagerank_ranking=True)` on a tmp_path corpus with scipy available → asserts
   `graph.json`'s nodes carry a `pagerank` float attribute; `pagerank_ranking=False` (default) → asserts
   the attribute is absent (schema stays backward-compatible).
2. Unit: `_rebuild_code(pagerank_ranking=True)` with scipy import mocked to raise `ImportError` → graph
   still builds successfully (nodes get built, no `pagerank` attribute), a stderr notice is printed, no
   exception propagates — mirrors `test_watch_raises_without_watchdog`'s style for the equivalent
   guarantee on the `watch` feature.
3. Unit: `_seed_penalty`/`_pick_seeds` with a synthetic graph where one node has a high `pagerank`
   attribute and near-equal BM25 score to a lower-pagerank node → asserts the higher-pagerank node wins
   the tie. A separate case: a much-lower-BM25-score high-pagerank node must NOT out-rank a
   clearly-better BM25 match — asserts the boost is bounded, not dominant.
4. Live validation: enable `pagerank_ranking` on a real graphified repo (this session's known real repos
   are already graphified — kouen-terminal is the best candidate given it's also this session's known
   fuzzy-query failure case), rebuild, re-run the exact "zoom/fullscreen" query from this session's
   original 6-project benchmark, and check whether the correct `SessionEditor`/pane-zoom result now
   ranks above the wrong-but-plausible window-manager result it lost to originally — this is the
   concrete, named motivating case from the roadmap doc; validating against it directly (not just a
   synthetic improvement) is the actual bar for calling this feature done.

## Non-goals

- No change to `god_nodes(by="pagerank")` itself — it stays query-time/report-only, unrelated call site,
  no reason to touch it.
- No PageRank-based re-ranking of `_score_nodes`'s raw BM25 output directly — composition happens only
  in `_pick_seeds`'s existing penalty step, per the Tactical Design reasoning above.
- No attempt to make PageRank the *default* even for opted-in projects on old (pre-feature) graphs —
  the attribute being absent is a normal, expected, permanently-supported state (a user who opts in must
  still rebuild once), not a migration to force.
