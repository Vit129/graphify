# P3 — CamelCase / snake_case Tokenization in Search

Status: **Done** (2026-07-02)
Priority: **P1** — same class of problem as P1's ceiling: a query that shares vocabulary with the target symbol still fails to hit the top-scoring tier, defeating "find the edit spot" for a whole class of common query shapes
Owner surface: `_search_tokens`, `_node_search_text`, `_score_nodes` (`graphify/serve.py`)
Created: 2026-07-02
Depends on: none — orthogonal to P1's coverage/IDF fix (P1 fixes *which seeds get picked among candidates*, this fixes *whether a camelCase/snake_case symbol becomes a candidate at all* for a multi-word natural-language query)

---

## Why

`_search_tokens` splits query and label text with `re.findall(r"\w+", text.lower())` — `\w` includes underscores and does not split on case changes. Confirmed directly:

```python
>>> re.findall(r'\w+', 'getUserData'.lower())
['getuserdata']
>>> re.findall(r'\w+', 'get_user_data'.lower())
['get_user_data']
```

Both collapse to a single opaque token. Consequence in `_score_nodes`:

- The **substring tier** (`_SUBSTRING_MATCH_BONUS`) still fires — `"user" in "getuserdata"` is `True` — so the node isn't invisible.
- But the **exact tier** (`_EXACT_MATCH_BONUS * 10`, joined-query) and **prefix tier** (`_PREFIX_MATCH_BONUS * 10`) — the two tiers carrying 100x–1000x the weight — can never fire for a multi-word query like `"get user data"` against a label `getUserData`/`get_user_data`, because the joined query (`"get user data"`, with spaces) can never equal or prefix an unsplit token (`"getuserdata"`/`"get_user_data"`, no spaces matching the query's word boundaries).

Net effect: any query phrased as separate words against a camelCase or snake_case symbol is permanently capped at the lowest-value scoring tier, regardless of how precisely the query names the target. This is a distinct failure mode from P1 (which is about *ranking among candidates that already scored*) — this is about a symbol *never reaching the score tier its match quality deserves* in the first place.

Cross-checked against how established tools handle this same problem (see conversation research, 2026-07-02):

- **Zoekt** (Google/Sourcegraph) integrates `universal-ctags` for symbol-aware indexing and trigram — doesn't solve this directly (trigram is case/boundary agnostic already) but confirms symbol-boundary awareness is treated as a first-class ranking signal industry-wide.
- **DeusData/codebase-memory-mcp** uses SQLite FTS5 with a **custom `cbm_camel_split` tokenizer** specifically to split camelCase/snake_case into sub-tokens before BM25 scoring — this is the direct precedent for the fix below.
- **SocratiCode** pairs BM25 sparse vectors with dense semantic vectors (RRF-fused) — even with full semantic search available, it still runs a lexical/BM25 layer, and code-aware BM25 tokenizers universally split identifier casing conventions as table stakes, not an advanced feature.

## Non-goals (this plan)

- Semantic/embedding search — already evaluated and rejected in P1 (Feature B, architecturally dead code). Out of scope again here; this plan is a zero-dependency tokenizer fix, not a retrieval-architecture change.
- Symbol-type boost (ranking function/class definitions over references, à la Zoekt+ctags) — a separate, real opportunity surfaced by the same research pass, but touches different code (`_score_nodes` tiering logic + node `type` field) and should be its own plan if pursued.
- Docstring/comment enrichment of search text — separate vocabulary-gap fix (business language vs. identifier language), independent of tokenization; not needed to close *this* gap.
- Rewriting `_score_nodes`'s tier structure (exact/prefix/substring/source bonuses) — out of scope, same boundary P1 drew. This plan only changes what a "token" is, not how tokens are scored.

## Scope

1. Add a camelCase/snake_case/kebab-case splitter to `_search_tokens` (or a new helper it calls) — split on:
   - underscore/hyphen boundaries (`get_user_data`, `get-user-data`)
   - lower→upper case transitions (`getUserData` → `get`, `User`, `Data`)
   - upper-run→upper+lower transitions for acronyms (`HTTPServer` → `HTTP`, `Server`, not `H`, `T`, `T`, `P`, `Server`)
   - Preserve the **original unsplit token too** (don't lose exact-match capability for queries that already type the identifier verbatim, e.g. someone pastes `getUserData` directly — that should still hit the exact tier via the whole-token form).
2. Confirm `_node_search_text` (which feeds the trigram index) and `_score_nodes` both consume the expanded token set consistently — the trigram index is built from `_node_search_text`, so if that function's `label_tokens` line also needs the same split, verify the two feeds don't disagree.
3. Check `_find_node` (mentioned in `_node_search_text`'s docstring as sharing the `label_tokens` field) — same splitter should apply there too, since it depends on the same tokenized form; a fix in one path but not the other would reintroduce the same bug for `_find_node`'s query resolution.

## Verification (once implemented)

- New unit test(s) in `tests/test_serve.py` mirroring P1's style: construct a small graph with a node labeled `getUserData` (or similar), assert a query `"get user data"` reaches the exact/prefix tier (not just substring) — i.e. assert score magnitude, not just presence in results.
- Same for snake_case (`get_user_data`) and an acronym case (`HTTPServer` / `parseHTTPResponse`) to confirm the acronym-boundary rule doesn't fragment into single letters.
- Regression: confirm a literal-paste query (`"getUserData"`, no spaces) still hits the exact tier via the preserved whole-token form — don't regress the case that already worked.
- Full suite green: `uv run pytest -q`.
- Manual validation: pick one real camelCase/snake_case-named function from a project already used for P1's validation (harness-terminal or My-Investment-Port) and confirm a natural-language multi-word query for it now surfaces the node at a meaningfully higher rank than before.

## What's done

- `_search_tokens` (`graphify/serve.py`) rewritten: camelCase/PascalCase/acronym-run splitting via a single regex (`[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+|[^\W\d_]+`), applied to the *original-case* text before lowering (the old code lowered first, destroying the case signal needed to find boundaries). Underscore/hyphen act as natural separators since neither alternative matches them. Non-Latin scripts (Thai, Chinese, Cyrillic, ...) fall through to the unicode-letter catch-all and still match as whole runs — no regression there, verified (`test_search_tokens_non_latin_scripts_unaffected`).
- `_score_nodes`'s per-term loop: added `label_token_set` (the same split already computed for the existing `label_tokens` full-query check, no new cost) as an additional way to reach the **prefix** tier — a term exactly equal to one sub-word, or a sub-word starting with the term, now scores at the prefix tier instead of falling through to substring. Deliberately **not** promoted to the exact tier — caught this via a real test regression (`PayloadFactory` tied with a genuine exact match on `Payload` when sub-word match was wired into the exact-tier condition instead of prefix).
- `_find_node` and `_node_search_text` needed **no separate code change** — both already call the shared `_search_tokens`, so the tokenizer fix propagates automatically. Verified with a dedicated test (`test_find_node_matches_spaced_query_against_camel_case_label`) rather than assumed.
- 8 new tests added to `tests/test_serve.py` (camelCase/snake_case/kebab-case splitting, acronym-run preservation, non-Latin passthrough, prefix-vs-substring tiering, prefix-vs-exact tiering, `_find_node` propagation). Full suite: 2744 passed, 0 failures, 28 skipped (unrelated/pre-existing).
- Real-graph validation (harness-terminal): query `["reconcile", "session", "persistence"]` against `.reconcileSessionPersistenceWithMode()` — before the fix, that node did not appear in the top 5 (beaten by a generic "Persistence" doc node and multiple bare "session" nodes); after, it ranks #1 at ~1.6x the next-highest score. Compared via `git stash` on `graphify/serve.py` against the identical query on the identical graph, not a synthetic fixture.
