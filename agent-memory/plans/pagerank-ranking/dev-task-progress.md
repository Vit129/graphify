# Dev Task Progress — PageRank-Style Ranking (P17 item 2)

Last updated: 2026-07-19 00:20
Status: In Progress

## Context
- System: graphify
- Feature: pagerank-ranking
- Workflow: Dev
- Complexity: Standard (touches production scoring code used by every `query`/`explain`/`path` call —
  higher regression risk than item 1's purely-additive infra, per the design doc's own risk framing)
- Test Root: `tests/` (flat pytest, matches this repo's existing convention)

## Category Mapping (no DB/no client app, same as item 1)
- Infrastructure → N/A (reuses `graph.json`, no new storage/schema/broker)
- Data Storage → N/A (the `pagerank` node attribute rides inside the existing `graph.json` node-link
  format, no new persistence mechanism)
- Server Logic → the actual units: `_rebuild_code`'s pagerank computation (`watch.py`), `to_json`'s
  attribute-attachment (`export.py`), `_seed_penalty`'s boost composition (`query.py`), config/CLI
  threading (`__main__.py`)
- Client Application → N/A
- Integration → config → build → query end-to-end wiring + live validation against the named
  motivating case (kouen-terminal's "zoom/fullscreen" query)

## Artifacts
- Design: `agent-memory/plans/pagerank-ranking/design.md`
- Published: PR #15 (draft), https://github.com/Vit129/graphify/pull/15

## Summary
- Total tasks: 7
- Completed: 1
- Remaining: 6

## Server Logic

- [x] **Task 1 — shared scipy-missing message constant** — Done (2026-07-19)
  Added `_PAGERANK_SCIPY_MISSING_MSG` in `graphify/analyze.py` (right above `god_nodes`), holding just
  the reusable install-instructions half of the message ("requires scipy - install with `pip install
  graphifyy[pagerank]` or `uv tool install --with scipy graphifyy`"). `god_nodes`'s `raise ImportError`
  now does `f"god_nodes(by='pagerank') {_PAGERANK_SCIPY_MISSING_MSG}"` — kept the context-specific
  prefix ("god_nodes(by='pagerank')") local to `god_nodes` itself, only the actual install instructions
  are shared, so Task 2's `_rebuild_code` call site can prepend its own natural context instead of
  reusing an oddly-`god_nodes`-flavored sentence.
  - Verify: byte-identical message text confirmed via direct string comparison (old concatenation vs.
    new f-string). Existing `tests/test_analyze.py`/`tests/test_watch.py` pagerank tests (3 total) pass
    unchanged — neither asserted on the exact error string, so this was a safe refactor, not just a
    lucky one. Full suite: 3006 passed, 0 failed, 0 regressions.

- [ ] **Task 2 — `_rebuild_code` computes + passes PageRank (`graphify/watch.py`)**
  New `pagerank_ranking: bool = False` parameter on `_rebuild_code` (`watch.py:417-432`), mirroring
  `value_coupling`'s exact shape. When `True`: `try: import scipy` (probe only) `except ImportError:`
  print Task 1's shared message to stderr, continue without pagerank (graph still builds normally) —
  else `pr_scores = nx.pagerank(G)`. Pass `pr_scores` (or `None`) to `to_json` as the new
  `pagerank_scores` parameter (Task 3) at the call site (`watch.py:861`).
  - Blocked by Task 1.
  - Verify: extend `tests/test_watch.py` — `_rebuild_code(pagerank_ranking=True)` on a real tmp_path
    corpus with scipy available asserts nodes end up with a `pagerank` attribute in the written
    `graph.json`; `pagerank_ranking=False` (default) asserts the attribute is absent (backward-compat);
    a mocked `ImportError` on the scipy probe asserts the build still succeeds with no `pagerank`
    attribute and no exception raised (mirrors `test_watch_raises_without_watchdog`'s style for the
    equivalent guarantee on a different optional dependency).

- [ ] **Task 3 — `to_json` writes the `pagerank` node attribute (`graphify/export.py`)**
  New `pagerank_scores: dict[str, float] | None = None` keyword parameter on `to_json`
  (`export.py:1001`). Inside the existing `for node in data["nodes"]:` loop that already does
  `node["community"] = ...` (`export.py:1033-1038`), add: `if pagerank_scores is not None:
  node["pagerank"] = pagerank_scores.get(node["id"])`. Omitted entirely (no key at all, not even
  `null`) when `pagerank_scores` is `None` — keeps old-shape `graph.json` byte-identical for every
  caller that doesn't pass it, zero risk of an unexpected key breaking a downstream JSON consumer.
  - Blocked by Task 2 (needs the parameter to exist to pass through it correctly), but implementable
    in parallel and merged before Task 2's call-site wiring lands.
  - Verify: extend `tests/test_export.py` — `to_json(G, communities, path, pagerank_scores={"a": 0.5})`
    asserts node `"a"` in the written JSON has `"pagerank": 0.5`; `to_json(...)` with no
    `pagerank_scores` arg (existing call sites, unchanged) asserts no node has a `pagerank` key at all
    (regression guard against accidentally always adding the key).

- [ ] **Task 4 — `_seed_penalty`/`_pick_seeds` composes the boost (`graphify/query.py`)**
  New module constant `_PAGERANK_BOOST_MAX = 0.15` near `_CONCEPT_SEED_PENALTY`/`_PROSE_SEED_PENALTY`
  (`query.py:661-662`). Extend `_seed_penalty` (`query.py:726-731`, currently returns a flat
  0.85/0.9/1.0 multiplier) to multiply its existing result by a pagerank boost factor:
  `1.0 + _PAGERANK_BOOST_MAX * (node_pagerank / max_pagerank_in_candidates)`, where
  `max_pagerank_in_candidates` is computed **once per `_pick_seeds` call, over only the `scored`
  candidate list already passed in** (NOT a full graph scan — `scored` is already the BM25-narrowed
  candidate set every other part of `_pick_seeds` operates on; scanning the whole graph on every seed
  pick would undo Task 2's build-time-precompute performance win). A node with no `pagerank` attribute
  (old graph, or feature was off at build time) contributes `0` to that max computation and gets boost
  factor exactly `1.0` (no-op) — must not crash on `None`/absent.
  - Blocked by Task 3 (needs real `pagerank`-attributed test graphs to verify against).
  - Verify: **confirmed location** — `tests/test_serve.py:938+` ("`--- _pick_seeds tests (#897) ---`"),
    already has the exact precedent pattern to mirror:
    `test_pick_seeds_prefers_ast_node_over_near_tied_concept_node`/
    `test_pick_seeds_concept_node_still_wins_when_genuinely_dominant` (same shape of test — a modifier
    that should tie-break but not override a clear winner — just for the concept-penalty factor instead
    of pagerank). Add analogous cases: (a)
    synthetic graph, one node high-pagerank + near-equal BM25 score to a lower-pagerank node → higher-
    pagerank node wins the tie; (b) a much-lower-BM25 high-pagerank node must NOT out-rank a clearly-
    better BM25 match → asserts the boost is bounded, not dominant; (c) a graph with zero `pagerank`
    attributes anywhere → `_pick_seeds` behavior is byte-for-byte identical to before this change
    (critical regression guard, since this is the default state for every existing graph/user).

## Integration

- [ ] **Task 5 — config + CLI threading (`graphify/__main__.py`)**
  `pagerank_ranking = proj_config.get("pagerank_ranking", False)` alongside the existing
  `value_coupling` read (`__main__.py:4817`). New `--pagerank-ranking` CLI flag mirroring
  `--value-coupling`'s exact parsing (`__main__.py:4887`). Thread through to every `_rebuild_code`/
  `ast_kwargs` call site `value_coupling` already flows through (`__main__.py:4026`, `4110`, `5132`).
  No `graphify/config.py` change needed (verified during design — it's an unschemad generic TOML
  loader, any key just works via `.get()`).
  - Blocked by Task 2.
  - Verify: **note on file naming** — `tests/test_value_coupling.py` turned out to be about the YAML
    extractor's `shares_value` edge logic itself, not CLI flag threading; the right precedent for
    `--value-coupling`'s CLI/config threading is more likely in `tests/test_watch.py` (also matched the
    grep) — confirm exact test name there before writing the new one, then add an analogous case:
    `graphify update --pagerank-ranking` and a `graphify.toml` with `pagerank_ranking = true` both reach
    `_rebuild_code` with the flag set.

- [ ] **Task 6 — ✅ Run test scripts (verify GREEN)**
  Full `pytest tests/` run. Zero regressions expected on the default (`pagerank_ranking=False`) path —
  every default-path assertion in Tasks 2-4 exists specifically to guarantee this. This is the one task
  in this feature where "zero regressions" is the actual hard requirement, not just a nice-to-have,
  given the design doc's own framing of this as higher-regression-risk than item 1.
  - Blocked by Tasks 1-5.

- [ ] **Task 7 — live validation against the named motivating case**
  Per the design doc's own acceptance bar: enable `pagerank_ranking` on kouen-terminal (already
  graphified from this session's earlier work), rebuild, re-run the exact query from this session's
  original benchmark ("where would I add a new keyboard shortcut to temporarily zoom/maximize the
  focused pane" — scored 2/5 originally, landing on `MainWindowController.toggleVisibleFrameZoom()`
  instead of the correct `SessionEditor`/`KouenCommands` pane-zoom path) and check whether the correct
  result now ranks above the wrong-but-plausible one. This is a real user repo — confirm before
  touching it whether to rebuild in place (reversible: `graphify.toml`/`graph.json` changes, easy to
  revert) or in a scratch copy, and revert the `graphify.toml` opt-in afterward unless the user wants
  to keep it enabled there.
  - Blocked by Task 6.
  - **Honest acceptance criterion**: if the boost genuinely doesn't move this specific case (e.g. the
    correct node's pagerank isn't actually higher than the wrong one's — a real possibility this design
    doc doesn't get to assume away), report that finding directly rather than declaring victory on
    weaker evidence. The feature can still be correct/shippable (bounded, backward-compatible, opt-in)
    even if this one motivating case turns out not to move — that would just mean the roadmap's
    hypothesis about this specific failure needs revisiting, not that the implementation is wrong.

## Next Step

All tasks done + verified GREEN + live-validated → report back before merging, given this feature's
higher regression-risk profile (touches every query's ranking) versus item 1's purely-additive shape.
