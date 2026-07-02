# P5 — Typo/Abbreviation Cascade Fallback

Status: **Done** (2026-07-02)
Priority: **P1** — same "find the edit spot" impact class as P3; closes a gap P3 explicitly left open
Owner surface: `graphify/serve.py` (`_query_graph_text`, `_find_node`, new helpers)
Created: 2026-07-02
Depends on: P3 (done) — reuses `_search_tokens` for vocabulary extraction

---

## Why

P3 fixed camelCase/snake_case tokenization so a correctly-spelled multi-word
query reaches the exact/prefix scoring tier. It explicitly did **not** cover
typos — confirmed empirically that session's own real-graph validation:
`_score_nodes(G, ["sesion"])` against a label containing `session` returns
`[]`. Zero results, not a low score — the primary lexical pipeline has no
fuzzy layer at all.

Surveyed three real algorithmic approaches (session research, 2026-07-02),
tested against the same 4 cases (`sesion`/`session` omission,
`recieve`/`receive` transposition, `resieve`/`receive` substitution,
`gud`/`getUserData` abbreviation):

| Case | Subsequence (fzf/harness-terminal style) | Trigram Jaccard | Damerau-Levenshtein |
|---|---|---|---|
| omission | match | 0.5 | distance=1 |
| transposition | **fail** | 0.11 (weak) | distance=1 |
| substitution | **fail** | 0.0 (fail) | distance=2 |
| abbreviation | match | 0.0 (fail) | distance=8 (correctly rejects — not a typo) |

No single algorithm covers everything. Edit distance (Damerau-Levenshtein)
is the only one that reliably catches real typos (insertion/deletion/
substitution/adjacent-transposition) — and it correctly *rejects* the
abbreviation case (`gud`/`getUserData`, distance 8) rather than
false-positiving on it, because abbreviation and typo are different
problems needing different tools. Subsequence matching (already scoped
in harness-terminal's `FuzzyPathResolver.swift`, same family as fzf) is
the right tool specifically for abbreviations.

## Design: query-term correction + retry, not a parallel scorer

Earlier framing considered a second scoring algorithm that runs *alongside*
`_score_nodes` and produces its own `list[tuple[float, str]]`. Rejected —
scores from a fuzzy algorithm and scores from IDF-weighted exact/prefix/
substring tiers are not on a comparable scale, and blending them requires
ad-hoc calibration.

Instead: when the primary pass finds nothing, **spell-correct the failing
query terms against the graph's own vocabulary, then re-run the existing,
unmodified `_score_nodes` pipeline with the corrected terms.** A corrected
term is just a term — it goes through the same IDF weighting and
exact/prefix/substring tiers (including P3's camelCase sub-word matching)
as any hand-typed term. No new scoring path, no score-scale mismatch, and
every improvement already made to `_score_nodes` automatically benefits
corrected queries too.

Cascade order per failing term:
1. **Vocabulary check** — if the term already matches a token in the
   graph's vocabulary verbatim, no correction needed (this is what makes
   the whole thing safe to run unconditionally on retry: correcting an
   already-correct term is a no-op, so there's no infinite-recursion risk
   from a single bounded retry).
2. **Typo correction** — Damerau-Levenshtein against length-similar
   vocabulary words (`|len(term) - len(candidate)| <= threshold`, threshold
   scaled by term length: 1 for len<=4, else 2). Bounded, not O(vocab) full
   scan: candidates are pre-bucketed by length.
3. **Abbreviation correction** — only if step 2 found nothing and the term
   is short (<=5 chars): ordered-subsequence match (harness-terminal's
   greedy `FuzzyPathResolver` algorithm, ported) against vocabulary words
   at least 2x the term's length. Best score wins.
4. No match at either step -> leave the term uncorrected (it contributes
   nothing to the retry, same as it contributed nothing to the first pass).

Trigger point: `_query_graph_text` only attempts correction when
`_pick_seeds` returns an empty `start_nodes` list from the *uncorrected*
terms — zero cost added to any query that already finds something.
`_find_node` gets the same treatment for the exact-symbol-lookup path
(`get_node`/`get_neighbors`/`shortest_path` tools all route through it).

Transparency requirement: when a correction fires and produces results,
the output must say so (e.g. `Note: no exact match for "sesion" — showing
results for "session" instead (possible typo)`). Silent substitution would
let an agent believe it found what it asked for when it actually got a
best-effort guess.

## Non-goals

- Solving abbreviation matching against `source_file` paths (long, can
  have repeated components — greedy subsequence can pick a suboptimal
  alignment there, per session's `xa_xb_ab` demonstration). Scope this
  fallback to `label`/vocabulary tokens only; revisit paths separately if
  a real query gap demands it.
- Making the fallback fire on *every* query as a confidence-boosting
  re-rank — only on total emptiness, to keep the happy path untouched and
  avoid the score-blending problem described above.
- Fuzzy-correcting the multi-word `joined` full-query tier — correction
  operates per-term; a corrected term still has to individually clear
  `_score_nodes`'s existing tiers same as any other term.
- Trigram-index-based prefiltering of vocabulary candidates before
  edit-distance — length-bucketing already keeps candidate counts small in
  practice; add trigram prefiltering later only if a real large-vocabulary
  graph shows this step is slow.

## Scope

1. `_get_vocabulary(G)` — every distinct `_search_tokens` output across all
   node labels, cached on `G.graph` (same pattern as `_idf_cache` /
   `_trigram_index`), plus a length-bucketed index for candidate lookup.
2. `_damerau_levenshtein(a, b, max_dist)` — standard DP, ported/adapted
   from the session's validated implementation.
3. `_subsequence_score(query, target)` — greedy ordered-subsequence scorer,
   ported from harness-terminal's `FuzzyPathResolver.swift` (word-boundary
   bonus, consecutive-match bonus, gap penalty, prefix bonus).
4. `_correct_term(term, G)` — the 4-step cascade above, returns `str | None`.
5. `_apply_vocabulary_corrections(G, terms)` — maps `_correct_term` over a
   term list, returns `(corrected_terms, corrections)` where `corrections`
   is the list of `(original, corrected)` pairs that actually changed.
6. Wire into `_query_graph_text` (retry `_score_nodes`/`_pick_seeds` once
   with corrected terms when the first pass is empty; add the transparency
   note to the header when corrections were used).
7. Split `_find_node`'s current body into `_find_node_core` (unchanged) +
   thin `_find_node` wrapper that retries once via `_search_tokens`/
   `_apply_vocabulary_corrections` when `_find_node_core` returns empty.

## Verification

- Unit tests: typo (omission, transposition, substitution) resolves via
  correction; abbreviation resolves via subsequence; an unrelated/unfixable
  query still returns "No matching nodes found." (no over-eager
  correction); an already-correct query is untouched (no wasted correction
  work, verified by call-count or by asserting output has no correction
  note).
- Real-graph validation: reuse a project already validated for P1/P3
  (harness-terminal or My-Investment-Port), deliberately typo a real
  identifier from those graphs, confirm the corrected query surfaces the
  same node the correctly-spelled query does.
- Full suite green: `uv run pytest -q`.

## What's done

- `_get_vocabulary(G)` — distinct sub-word tokens *and* each label's whole
  concatenated form (see below), length-bucketed, cached on `G.graph`.
- `_damerau_levenshtein(a, b)`, `_subsequence_score(query, target)` —
  standard DP / greedy-subsequence, matching the session's validated
  reference implementations.
- `_correct_term(term, G)` — the cascade (vocabulary check -> typo ->
  abbreviation -> give up).
- `_apply_vocabulary_corrections(G, terms)` and wiring into
  `_query_graph_text` (retries `_score_nodes`/`_pick_seeds` once, adds a
  `Note: ...` line to the header when a correction fired) and `_find_node`
  (split into `_find_node_core` + a thin retry wrapper, non-recursive).
- **Design correction found during implementation, not left for later**:
  the plan's abbreviation step assumed per-sub-word vocabulary
  (`"handle"`/`"user"`/`"session"`) would be enough, but a cross-word
  abbreviation like `"hus"` for `handleUserSession` can't subsequence-match
  any *single* sub-word — it needs the whole label's concatenated form
  (`"handleusersession"`) as a candidate too. Fixed by adding that form to
  `_get_vocabulary`'s output; the length-window filters in `_correct_term`
  naturally keep it out of the typo path (a short mistyped term's window
  never reaches a full label's length) so this is safe to add without a
  separate code path. Caught by writing
  `test_correct_term_fixes_cross_word_abbreviation` against the exact case,
  not assumed to work from the plan's prose.
- 22 new tests in `tests/test_fuzzy_fallback.py`: pure algorithm checks
  (Damerau-Levenshtein transposition/omission, subsequence success/failure),
  `_correct_term`'s full cascade including the no-op and give-up cases, and
  the retry wiring in both `_query_graph_text` and `_find_node`. Full suite:
  2776 passed, 0 failures.
- Real-graph validation (harness-terminal, 14,838 nodes / 11,238-word
  vocabulary): query `"reconsile sesion persistance"` (3 simultaneous typos
  in one query) correctly resolves all three (`reconcile`, `session`,
  `persistence`) and surfaces `.reconcileSessionPersistenceWithMode()` as
  the top seed — the same node P3's validation targeted, now reachable
  even when every word in the query is misspelled.
- Performance measured on that same graph: vocabulary build ~70ms (cached
  after first call), full fallback query ~660ms, happy-path (correctly
  spelled) query ~465ms with zero fallback overhead — confirms the
  plan's deferred trigram-prefiltering optimization isn't needed yet.

## Extension: compound-span typos (2026-07-02, same-session follow-on)

Found immediately after the above closed: P4's new test-description labels
(long, many sub-words) surfaced a case the original design didn't cover —
a typo of a *compound span* like `"wholesals"` for `"WholeSales"` (two
adjacent camelCase sub-words concatenated by whoever typed the query).
`_correct_term` returned `None` for it: the vocabulary had `"whole"` and
`"sales"` as separate sub-words (too short to be candidates for a 9-char
typo) and the whole label concatenated (too long). Nothing in between.

Researched the actual DS&A answer rather than patching around it — see
`agent-memory/knowledge/architecture/feature-provenance.md` for the full
comparison. Two additive fixes, deliberately kept separate (user's explicit
choice when presented with the tradeoff — see below):

1. **N-gram vocabulary spans** (`_get_vocabulary`, `_NGRAM_SPAN_SIZES =
   (2, 3)`): concatenated 2- and 3-adjacent-token spans added to the typo
   candidate pool. Covers realistic compound identifiers (2-3 morphemes)
   as a normal typo-path candidate — no new algorithm, reuses
   `_damerau_levenshtein` unchanged. **Regression caught while
   implementing**: initially added the same n-gram spans to the
   *abbreviation* candidate pool too — this broke
   `test_correct_term_fixes_cross_word_abbreviation` (`"hus"` started
   resolving to the synthetic span `"handleuser"` instead of the correct
   whole-label `"handleusersession"`, because the shorter synthetic
   candidate scores higher in `_subsequence_score`'s formula purely for
   being shorter). Fixed by splitting `_get_vocabulary` into two genuinely
   separate pools (`typo_words`/`typo_buckets` include n-gram spans;
   `abbr_words`/`abbr_buckets` deliberately do not) — caught by the
   existing test suite, not by manual review.
2. **Bitap-style fuzzy-substring fallback** (`_fuzzy_substring_distance`,
   `_fuzzy_substring_seeds`): a plain-DP variant of the Bitap/agrep
   "approximate substring search" algorithm (first row all-zero so a match
   can start anywhere in the text; answer is the min of the last row so it
   can end anywhere) — for compound spans *longer* than the n-gram
   vocabulary's 3-token window. Architecturally distinct from
   `_correct_term`'s design on purpose: a Bitap match is a *position*
   inside a label, not a vocabulary word, so there's no clean "corrected
   term" to hand back to `_score_nodes`. Returns node IDs directly as a
   third cascade tier in `_query_graph_text`, after both the primary pass
   and vocabulary correction fail — with an explicit "low confidence"
   note distinct from the ordinary typo-correction note, since this tier
   is a genuinely weaker signal than the first two.
3. Verified the tier ordering actually works as designed, not just that
   each tier works in isolation: real query against the actual
   `territory-so-type.spec.ts` extraction (`"wholesals territary level
   2"`) resolves silently through the (cheaper, n-gram-corrected) typo
   tier — no "low confidence" note — confirming Bitap is reserved for
   cases the earlier tiers genuinely can't reach, not competing with them.
- 8 additional tests in `tests/test_fuzzy_fallback.py` (compound-span typo
  fix, n-gram/abbreviation pool separation, `_fuzzy_substring_distance`/
  `_fuzzy_substring_seeds` unit tests, full 3-tier cascade end-to-end).
  Full suite: 2793 passed, 0 new failures (3 pre-existing failures from
  the separately-tracked, not-yet-implemented P1 reopen work, confirmed
  via `git stash` to predate this change).
