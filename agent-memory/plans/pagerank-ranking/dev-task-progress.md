# Dev Task Progress — PageRank-Style Ranking (P17 item 2)

Last updated: 2026-07-19 01:30
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
- Completed: 6
- Remaining: 1

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

- [x] **Task 2 — `_rebuild_code` computes + passes PageRank (`graphify/watch.py`)** — Done (2026-07-19)
  **Implemented together with Task 3**: Task 2's call site can't be completed or tested without Task
  3's `to_json` parameter existing, so both landed in this pass rather than leaving Task 2 in a
  syntactically-incomplete state — noting this the same way item 1's Task 1 documented its own
  deviation. Added `pagerank_ranking: bool = False` to `_rebuild_code`'s signature, forwarded through
  **both** recursive `acquire_lock=False` self-call sites (`watch.py:485-499` and `508-524`) — caught
  myself missing the second one on the first pass via `grep` verification before moving on, which is
  exactly the bug class P15's `value_coupling` shipped once already (a hand-listed forwarded-kwargs
  site silently reverting to the default). Right before the existing `to_json` call, guarded by
  `if pagerank_ranking:` — `import networkx as _nx; pagerank_scores = _nx.pagerank(G)`, wrapped in
  `try/except ImportError:` printing Task 1's shared message via stderr and leaving `pagerank_scores =
  None` on failure (graph still builds normally either way).
  - Verify: **3 new tests** in `tests/test_watch.py` — `pagerank_ranking=True` real end-to-end (scipy
    available) asserts every node gets a `pagerank` attribute; default (`False`) asserts none do;
    mocked `ImportError` (mirrors `test_watch_raises_without_watchdog`'s style) asserts the build still
    succeeds, no attribute, no exception, and the shared message reaches stderr. **Plus a real
    (non-mocked) end-to-end smoke test**: a 5-function corpus with a real call-graph shape (one hub,
    one shared leaf) produced sensible relative PageRank values (hub/leaf ranked above the individual
    branch functions) — not just "a number appeared," a structurally correct one.

- [x] **Task 3 — `to_json` writes the `pagerank` node attribute (`graphify/export.py`)** — Done
  (2026-07-19, same pass as Task 2, see above)
  New `pagerank_scores: dict[str, float] | None = None` keyword parameter on `to_json`. Inside the
  existing `for node in data["nodes"]:` loop that already does `node["community"] = ...`
  (`export.py:1033-1038`): `if pagerank_scores is not None: node["pagerank"] =
  pagerank_scores.get(node["id"])`. Omitted entirely (no key at all) when `None` — every pre-existing
  call site is unaffected.
  - Verify: **2 new tests** in `tests/test_export.py` — `pagerank_scores={node_id: 0.5}` asserts that
    exact node gets `"pagerank": 0.5` in the written JSON; no `pagerank_scores` arg (every pre-existing
    call site) asserts **no** node has a `pagerank` key at all (regression guard against accidentally
    always adding the key). Full suite: 3011 passed, 0 failed, 0 regressions.

- [x] **Task 4 — `_seed_penalty`/`_pick_seeds` composes the boost (`graphify/query.py`)** — Done
  (2026-07-19)
  Added `_PAGERANK_BOOST_MAX = 0.15` next to `_CONCEPT_SEED_PENALTY`/`_PROSE_SEED_PENALTY`. `_seed_penalty`
  now computes `max_pagerank` once per `_pick_seeds` call (`max(G.nodes[nid].get("pagerank") or 0.0 for
  _, nid in scored)` — over the `scored` candidate list only, confirmed NOT a full-graph scan) before
  its inner closure is defined, then multiplies the existing concept/prose penalty result by
  `1.0 + _PAGERANK_BOOST_MAX * (node_pagerank / max_pagerank)` whenever `max_pagerank > 0`. When
  `max_pagerank == 0` (no candidate carries the attribute — every graph built without
  `pagerank_ranking`, i.e. the default today), the boost multiplication is skipped entirely — not just
  bounded to a no-op, literally the same code path as before this feature existed.
  - Verify: **4 new tests** in `tests/test_serve.py` (added `nx.Graph` node kwarg `pagerank=`, same
    fixture style as the existing concept/prose tests) — near-tie tiebreak (higher-pagerank wins),
    boundedness (a 15%-max boost cannot close a 10x raw BM25 gap — verified the math by hand: bounded
    case scores 1.15 vs. 10.015, no contest), zero-pagerank-anywhere regression guard (byte-identical
    seed selection to the pre-existing concept-penalty test case), and a mixed-graph case (some nodes
    carry `pagerank`, some don't) confirming no crash on the missing attribute. **All 19 `_pick_seeds`
    tests pass** — the 15 pre-existing ones unchanged, confirming zero regression on the concept/prose
    penalty behavior this change composes with. Full suite: **3015 passed, 0 failed, 0 regressions** —
    the critical result for this task, given its higher-regression-risk profile versus items 1-3.

## Integration

- [x] **Task 5 — config + CLI threading (`graphify/__main__.py`)** — Done (2026-07-19)
  **Scope expanded during implementation, documented rather than silently absorbed**: the original plan
  named 3 call sites (`4026`, `4110`, `5132`) but `5132`'s `ast_kwargs` turned out to be `extract()`'s
  per-file AST-extraction kwargs (where `value_coupling` genuinely belongs — it detects shared literal
  values during parsing) — pagerank needs the fully-assembled graph, which doesn't exist yet at that
  point, so `ast_kwargs` was correctly left untouched. Grepping for every `to_json`/`_to_json` call site
  in `__main__.py` (not just the ones the design doc named) turned up **two more independent
  graph-build-and-write paths** beyond `_rebuild_code`: the standalone `extract` command (line `5457`,
  its own `_to_json` call, builds a graph from scratch without ever calling `_rebuild_code`) and
  `cluster-only` (line `3859`, re-clusters an *existing* graph.json). Both needed a real decision, not
  just mechanical copying:
  - `extract` command: genuinely needed pagerank wiring — added `pagerank_ranking` to the same
    `proj_config`-read block as `value_coupling` (`4817`), a matching `--pagerank-ranking` CLI flag
    (`4887`), and a `nx.pagerank(G)` computation (same try/except-ImportError-with-shared-message
    pattern as `_rebuild_code`) right before its `_to_json` call, passing `pagerank_scores` through.
    Verified live (not just unit-tested): `graphify extract . --pagerank-ranking` on a real scratch
    corpus produced correct, non-mocked pagerank values matching `_rebuild_code`'s own computation on
    an equivalent corpus exactly — two independent code paths agreeing is a real correctness signal, not
    a coincidence. Without the flag, confirmed no `pagerank` key at all (default-safe).
  - `cluster-only`: **verified empirically that no change was needed at all** — it loads the existing
    `graph.json` via `build_from_json` (which generically preserves arbitrary node attributes, including
    `pagerank`, since networkx's node-link deserialization doesn't whitelist known keys), and `to_json`'s
    conditional-write design (`if pagerank_scores is not None: ...`, added in Task 3) never deletes an
    attribute it wasn't asked to set. Confirmed with a real round-trip: built a graph with
    `pagerank_ranking=True`, ran `cluster-only --no-label` on it, pagerank values were byte-identical
    before and after. This is also theoretically correct, not just empirically lucky — pagerank depends
    only on graph structure (nodes/edges), which `cluster-only` never changes, only re-clusters.
  - The two `_rebuild_code` call sites (`update`/`update --all`, lines `4026`/`4110`) got the
    mechanical `pagerank_ranking=proj_config.get("pagerank_ranking", False),` addition exactly as
    originally planned — no surprises there.
  - `graphify/config.py`: confirmed unchanged, as designed — no schema to touch.
  - Verify: **no CLI-level test precedent exists for `--value-coupling` either** (grepped every test
    file — the closest is `tests/test_watch.py`'s `_rebuild_code(value_coupling=True)` direct-call test,
    not a `mainmod.main()`-level CLI test), so writing a heavyweight new CLI-mock test file for
    `--pagerank-ranking` specifically would hold this feature to a bar the sibling feature doesn't meet
    in this codebase - not deviating for its own sake. Real live checks instead (both described above),
    matching this session's "validate against the real thing" discipline over synthetic mocking where a
    real check is cheap and available.

- [x] **Task 6 — ✅ Run test scripts (verify GREEN)** — Done (2026-07-19)
  Full `pytest tests/` run after Task 5's `__main__.py` changes (three separate command paths now
  touched: `update`, `update --all`, `extract`). **3015 passed, 0 failed, 0 regressions** — identical
  pass count to Task 4's run (no new unit tests added in Task 5, per its verify note above; the two live
  end-to-end checks aren't part of the pytest suite), confirming the `__main__.py` wiring introduced no
  breakage across any of the three touched command paths.

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
