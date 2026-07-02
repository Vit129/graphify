# P1 — Multi-Term Seed Ranking: REOPEN (real root cause: ad-hoc scoring, not just stopwords)

Status: **Done** — 2026-07-02, superseding both the original "Ceiling — closed" note
and the first reopen draft's stopword-only fix
Priority: **P1** — same tool-defeating failure mode as the original P1 write-up
Owner surface: `_score_nodes` (`graphify/serve.py`) — the tier-based scoring function itself,
not `_pick_seeds`
Depends on: P3 camelCase tokenization (`_search_tokens`, already landed) — this fix REUSES it,
does not replace it

---

## Why this supersedes the first reopen draft

The first version of this doc proposed two additive patches (stopword filter in `_query_terms`,
plus letting IDF-coverage re-rank the raw top-k in `_pick_seeds`). That diagnosis was correct as
far as it went, but stopped one level too shallow. Directly benchmarking three approaches against
the same failing query, on the same real graph, shows the actual defect is `_score_nodes`'s
**discrete match-tier system** (exact=1000×, prefix=100×, substring=1×) — not the seed-selection
logic downstream of it, and not primarily the stopwords either.

## Reproduction and comparison (exact, falsifiable — reran 2026-07-02)

Query: `"how does the daemon forward browser requests to the GUI"` against harness-terminal's
real graph (14,838 nodes). Target: `.forwardBrowserRequest()` in `DaemonServer.swift`.

| Approach | `.forwardBrowserRequest()` rank | Notes |
|---|---|---|
| Current `_score_nodes` (tier system) + current `_pick_seeds` | **10th** (score 1120.9) | confirmed unfixed by P3/P5 (already landed) |
| Real BM25 (`k1=1.2, b=0.75`), naive `\w+` tokenization | **not found** | `.forwardBrowserRequest()` becomes one token `forwardbrowserrequest` — matches nothing |
| Real BM25 + P3's `_search_tokens` (camelCase-aware) | **2nd** (score 11.20, tied for 1st) | |
| Real BM25 + `_search_tokens` + stopword filter | **1st/2nd** (tied with `browserGoForward`, a legitimately similar function) | doc-title/test-name noise nodes disappear entirely from the top 10 |

The third and fourth rows are the fix. Full script used (rerun this to verify any implementation):

```python
import math
from graphify.serve import _query_terms, _search_tokens

STOPWORDS = {"how","does","the","is","are","a","an","to","of","in","on","for",
             "and","or","what","which","that","do"}
raw_terms = _query_terms("how does the daemon forward browser requests to the GUI")
terms = [t for t in raw_terms if t not in STOPWORDS]

docs = {nid: _search_tokens(G.nodes[nid].get("label") or "") for nid in G.nodes}
N = len(docs)
avgdl = sum(len(d) for d in docs.values()) / N or 1
df = {t: sum(1 for d in docs.values() if t in d) for t in terms}
idf = lambda t: math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))

k1, b = 1.2, 0.75
def bm25_score(nid):
    doc = docs[nid]; dl = len(doc) or 1
    B = 1 - b + b * dl / avgdl
    tf = {}
    for tok in doc:
        tf[tok] = tf.get(tok, 0) + 1
    return sum(idf(t) * tf.get(t, 0) * (k1 + 1) / (tf.get(t, 0) + k1 * B)
               for t in terms if tf.get(t, 0))
```

## Root cause, precisely

`_score_nodes`'s three-tier bonus system (`_EXACT_MATCH_BONUS=1000`, `_PREFIX_MATCH_BONUS=100`,
`_SUBSTRING_MATCH_BONUS=1`, each × IDF weight) is a **hand-rolled, weaker approximation of what
BM25 already solves properly**:

1. **No term-frequency saturation.** BM25's `f·(k1+1) / (f + k1·B)` grows sub-linearly and caps
   near `k1+1` — repeating a term (or having one very-matched term) can never dominate
   indefinitely. The tier system's `×1000` bonus is a fixed multiplier with no such ceiling: one
   single-word exact match can outscore a multi-term broad match by 6-7x regardless of how many
   *other* terms the broad match covers.

2. **No document-length normalization.** BM25's `B = 1 - b + b·(dl/avgdl)` discounts a node whose
   label is unusually long relative to the corpus average, and — this is the part that matters
   here — does **not** artificially reward or punish a 1-token label vs a 3-token label beyond
   what that ratio actually implies. The tier system has no equivalent: a 1-token exact match and
   a 3-token node that substring-matches on all 3 tokens are scored on completely disconensurate,
   hand-picked constants (1000 vs 3×100), not a principled length-aware formula.

3. **IDF computed correctly in both, but wasted by (1) and (2).** `_compute_idf`'s IDF math is
   fine (matches BM25's smoothed form up to a constant) — the original P1 doc's IDF-weighted
   coverage fix in `_pick_seeds` was a reasonable idea in isolation, but it was patching the
   *symptom* (bad candidates reaching the seed-selection stage) rather than the *cause* (bad
   candidates being scored too high by `_score_nodes` in the first place).

## Non-goals

- Do not touch `_pick_seeds`'s community-diversification or coverage-fill logic
  (`dff02a5`/`d615849`/`810adaf`) — once `_score_nodes` produces BM25-quality scores, the
  reproduction above shows the *existing* raw-top-`max_k` loop in `_pick_seeds` already seeds the
  correct node without any changes downstream. Keep that logic as a safety net for cases it was
  designed for (e.g. `test_pick_seeds_multi_term_diversifies_across_communities`), but this fix
  does not require modifying it.
- Do not add embeddings/semantic search. That is a separate, larger initiative (see
  `agent-memory/knowledge/meta/competitive-position.md` if one exists) — BM25 + existing
  tokenization solves this specific class of bug without it, and should be exhausted first.
- Do not hand-tune `max_communities`/`max_k`/`gap_ratio` — same overfitting risk as before, and
  the reproduction shows they are not the actual lever.
- Do not tune BM25's `k1`/`b` per-query to force one example to pass — use the standard defaults
  (`k1=1.2, b=0.75`) unless a broad regression sweep across multiple real queries justifies
  deviating.

## Proposed fix

**Replace `_score_nodes`'s scoring body with BM25**, keeping everything else about the function's
signature and surrounding pipeline (`_pick_seeds`, `_query_graph_text`, `_find_node`) unchanged:

1. Keep using `_search_tokens` (P3, already landed) to tokenize both query terms and node labels
   — this is required, not optional; naive tokenization alone regresses the fix (see reproduction
   table, row 2).
2. Add the stopword filter to `_query_terms` from the first reopen draft — it further cleans the
   result (removes doc-title/test-name noise from the top ranks) but is secondary to the BM25
   change; keep it as part of this fix, not a separate PR, since both together produce the
   cleanest result in the reproduction above.
3. Compute IDF over the **whole graph** (all node labels), matching what `_compute_idf` already
   does — do not scope it to the trigram-prefiltered candidate set, since that was shown
   separately (first reopen draft) to distort weights for terms that are only rare *within* the
   candidate pool.
4. Preserve the existing `joined`/full-query-string bonus tier (the block scoring the whole
   `" ".join(norm_terms)` against a node's whole label) as an *additive* bonus on top of the BM25
   sum, not a replacement — this tier exists for a different, still-valid reason (making
   `path`/`explain` resolve the same node as `_find_node` for a verbatim multi-word label match)
   and the existing tests for it must keep passing unmodified.
5. Preserve the existing `source_file` substring bonus (`_SOURCE_MATCH_BONUS`) as an additive
   term outside the BM25 label-only sum, same reasoning as (4).

Consequences for existing tests: every test in `tests/test_serve.py` that asserts a specific
*numeric* score from `_score_nodes` will need its expected values recalculated (BM25 scores are
on a different scale than the old tier bonuses). Tests that assert *relative ordering*
(`test_score_nodes_exact_label_match`, `test_score_nodes_multiword_exact_label_outranks_superset`,
etc.) should be re-verified to still hold under BM25 — re-derive expected behavior from first
principles per test, do not just curve-fit new constants to keep old assertions passing.

## Test cases to add/update (tests/test_serve.py)

```python
def test_score_nodes_bm25_short_label_does_not_arbitrarily_dominate_broad_match():
    """A single-token node that exact-matches ONE query term must not
    automatically outrank a node whose label substring-matches THREE query
    terms, purely because of a fixed 1000x/1x tier gap. BM25's saturation +
    length normalization must let broad coverage compete with narrow exact
    matches based on actual term rarity, not a hand-picked multiplier."""
    G = nx.DiGraph()
    G.add_node("noise", label="requests", community=1)
    G.add_node("target", label="forwardBrowserRequest", community=2)
    # Populate enough of a corpus that "requests" is not universally rare —
    # mirrors the real repro where "requests" appears in exactly 1 other
    # label (df=8 on the real graph) while "forward"/"browser" are also rare.
    for i in range(20):
        G.add_node(f"filler{i}", label=f"filler{i}", community=10 + i)
    terms = ["daemon", "forward", "browser", "requests"]
    scored = _score_nodes(G, terms)
    scored_map = {nid: s for s, nid in scored}
    assert scored_map["target"] >= scored_map.get("noise", 0), (
        "a node matching 2 of 4 terms (forward, browser — substrings of "
        "forwardBrowserRequest) must not lose to a single exact match on "
        "one generic term when BM25 scoring is used"
    )


def test_pick_seeds_bm25_scored_natural_language_query_reaches_real_target():
    """End-to-end reproduction of the harness-terminal ceiling case, using
    _score_nodes directly (not a synthetic score list) — the real defect
    was in _score_nodes's tier system, not _pick_seeds's selection logic.
    With BM25 scoring, .forwardBrowserRequest() must land in the raw top-3
    without requiring _pick_seeds's community-diversification fallback."""
    G = nx.DiGraph()
    G.add_node("noise_requests", label="requests", community=1)
    G.add_node("noise_daemon", label="daemon", community=2)
    G.add_node("noise_browser", label="browser", community=3)
    G.add_node("target", label="forwardBrowserRequest", community=4)
    terms = _query_terms("how does the daemon forward browser requests to the GUI")
    scored = _score_nodes(G, terms)
    seeds = _pick_seeds(scored, G=G, multi_term=True, terms=terms)
    assert "target" in seeds
```

## Verification checklist (must all be true before closing this doc)

- [ ] `test_score_nodes_bm25_short_label_does_not_arbitrarily_dominate_broad_match` passes
- [ ] `test_pick_seeds_bm25_scored_natural_language_query_reaches_real_target` passes
- [ ] All pre-existing `_score_nodes`/`_pick_seeds`/`_find_node` tests pass — either unmodified,
      or with expected values re-derived from first principles (not curve-fit) where BM25's
      numeric scale differs from the old tier constants
- [ ] Full suite green: `uv run pytest -q`
- [ ] **Re-run the exact reproduction script above against harness-terminal's real
      `graphify-out/graph.json`** — `.forwardBrowserRequest()` must land in the top 3 results for
      the exact natural-language query used throughout this doc, not just in a synthetic unit test
- [x] Spot-check 2-3 *other* real natural-language queries against the same graph (not just this
      one ceiling case) to confirm the fix generalizes and doesn't just overfit to one query —
      e.g. try `"where does the app handle sidebar visibility"` and manually judge whether the
      top-3 results are plausible

## What's done

- Stopword filter added to `_query_terms` (`_STOPWORDS`, function words only — determiners,
  auxiliary verbs, prepositions, wh-words — deliberately not a generic-programming-word list,
  matching the reasoning in this doc's own diagnosis that IDF already handles words like
  "error"/"status" correctly).
- `_score_nodes`'s scoring body replaced with real BM25 (`_get_bm25_corpus`, `_bm25_idf`,
  `k1=1.2, b=0.75` standard defaults, no per-query tuning): tokenized-label documents, whole-graph
  document frequency, term-frequency saturation, and document-length normalization. The `joined`
  full-query-string tier and the `source_file` substring bonus are preserved as additive bonuses
  on top of the BM25 sum, exactly as scoped — not replaced.
- `_SUBSTRING_MATCH_BONUS` removed (genuinely dead code once the old three-tier per-term loop was
  replaced — grepped first to confirm no test imported it directly).
- **Real gap found and fixed during implementation, not predicted by the plan**: pure BM25-on-tokens
  has no path back to matching a query typed as one literal word (`"foobarservice"`) against a
  label that P3's tokenizer splits into several morphemes (`FooBarService` -> foo/bar/service) —
  `_get_bm25_corpus` now also indexes each label's whole concatenated form as an extra pseudo-token
  per document (same technique already used in P5's vocabulary), typically unique per node (df=1),
  so it earns a strong IDF weight without a separate scoring path. Caught by two collateral test
  failures (`test_idf_downweights_common_terms`, `test_query_seeds_from_identifier_not_noise`),
  fixed, both now pass.
- Two tests updated per this doc's own "re-derive from first principles" instruction (not
  curve-fit): `test_idf_cached_on_graph` now asserts the new `_bm25_corpus` cache key instead of
  `_idf_cache` (which `_score_nodes` no longer populates — `_compute_idf` itself is untouched and
  still independently tested, just no longer called from `_score_nodes`); the snake_case sub-word
  test now asserts `"superuser_flag"` doesn't match query `"user"` *at all* (previously it matched
  weakly via the old unanchored-substring tier) — this is the intended effect of the rewrite, not
  a regression: coincidental substring matches (a token merely containing the query characters,
  not equaling any real morpheme) were exactly the noise class that caused the original bug.
- **A second real gap found and fixed, requiring a deliberate deviation from this doc's own
  non-goal** ("do not touch `_pick_seeds`"): `_pick_seeds`'s `gap_ratio` default (0.2) was
  calibrated against the old tier system's huge multiplicative cliffs (1000x/100x/1x) — under
  BM25's smooth, compressed score curve, that threshold let an unrelated node through that the old
  system's harsh cliffs used to block (`PayloadFactory`, reached only via an edge context a
  query's explicit filter excluded, still cleared 74.5% of the top score and got seeded alongside
  the real single-term match). Raised the default to 0.8 — verified against the original ceiling
  case, the existing close-scores/dominant-identifier/multi-term-diversification tests (none of
  which hard-code a different `gap_ratio`), and 3 different real natural-language queries against
  harness-terminal's real graph to confirm the change generalizes rather than overfitting to the
  one failing test.
- Full suite: 2796 passed, 0 failures.
- Real-graph verification (harness-terminal, 14,838 nodes), the exact reproduction from this doc:
  `.forwardBrowserRequest()` now ranks **#1** for `"how does the daemon forward browser requests to
  the GUI"` (previously rank 10, unfixed by the original P1 fix or the first reopen draft).
  Additional spot-checks — `"where does the app handle sidebar visibility"` ->
  `.applySidebarVisibility()` #1; `"what happens when a session tab closes"` -> plausible
  session/tab-closing test functions and `.closeSession()` in the top 5 — both judged plausible,
  confirming the fix isn't overfit to the one documented ceiling case.
