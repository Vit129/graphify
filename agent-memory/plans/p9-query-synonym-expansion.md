# P9 — Lightweight Query Synonym Expansion (semantic-search alternative)

Status: **Done** (2026-07-02)
Priority: user-directed, chosen over full embedding search via explicit AskUserQuestion
Owner surface: `graphify/query.py` (`_query_terms`, new `_expand_synonyms`/`_SYNONYM_GROUPS`/`_PHRASE_SYNONYMS`)
Created: 2026-07-02
Depends on: P1 (BM25 rewrite) — expansion rides the same term pipeline unmodified

---

## Why

The one gap explicitly *not* claimed as fixed after P1-P8: a query and the code it's about can use
completely different words for the same concept ("log the user in" vs. a function named
`authenticate`), with zero literal terms in common — BM25 (or any lexical scorer) cannot bridge
that no matter how good the ranking/typo-correction is. `feature-provenance.md` already recorded
that full embedding search was evaluated and rejected once before on infra cost; re-opening that
question required a real decision (backend, cost, dependency weight) that only the user could make
— not something to silently re-decide mid-session. Presented via `AskUserQuestion`: lightweight
query expansion / local embeddings / API embeddings / skip. **User picked lightweight query
expansion.**

## Non-goals

- Open-ended concept similarity (embeddings' actual strength) — this only helps word pairs that are
  literally enumerated in `_SYNONYM_GROUPS`/`_PHRASE_SYNONYMS` below. A query using a domain word
  not in the map gets zero help; this is the documented ceiling of the "lightweight" option, not a
  bug.
- WordNet or any external synonym dataset — a hand-curated list scoped to common
  software/QA-domain concept pairs (the user's own domain), matching "lightweight" over
  "comprehensive."
- Per-project/configurable synonym maps — a fixed built-in list; revisit only if a real query gap
  shows the built-in set insufficient for a specific project's vocabulary.

## What's done

- `_SYNONYM_GROUPS` (`graphify/query.py`): 16 frozensets of interchangeable single-token concepts
  (login/signin/logon/authenticate/auth, delete/remove/erase, fetch/retrieve/get,
  create/add/new, update/edit/modify, start/begin/launch/init/initialize,
  stop/halt/terminate/kill, config/configuration/settings/options, error/exception/fail/failure,
  test/spec/check/verify/validate, click/tap/press, send/submit/dispatch, show/display/render,
  hide/dismiss, register/signup, logout/signout). A query term matching any group gets every other
  member of that group appended.
- `_PHRASE_SYNONYMS`: 6 bounded-gap regexes (`\blog\b(?:\s+\w+){0,3}\s+\bin\b`, etc.) for separable
  phrasal verbs whose particle ("in"/"up"/"out") is a filtered stopword and whose verb ("log"/
  "sign") is too ambiguous with logging/signage to put in a synonym group by itself. Matched
  against the *raw* (unfiltered) question so "log in", "log on", and "log **the user** in" (the
  motivating example — genuinely split by an object) all match, while a 4+-word-distant unrelated
  "log" and "in" in the same sentence mostly don't (small bounded gap, not unrestricted proximity —
  documented as a precision/recall tradeoff, not exact).
- Both wired into `_query_terms` via `_expand_synonyms(terms, question)` — the single choke-point
  every consumer (`_score_nodes`, `_pick_seeds`, `_query_graph_text`) already reads from, so
  expansion applies unconditionally (same as camelCase splitting), not gated behind a
  zero-results fallback tier. Expanded terms are ordinary BM25 terms afterward — no second scoring
  algorithm, inherits IDF weighting automatically (a generic expanded term like "get" contributes
  little; a specific one contributes more).
- 4 tests in `tests/test_query_synonym_expansion.py`: single-token group expansion, the exact
  motivating phrase ("log the user in" -> "authenticate"/"login"), a query with no synonym-map hits
  is left untouched (regression guard against over-expansion), and an end-to-end zero-literal-
  overlap case (`_score_nodes` on a synthetic 2-node graph correctly ranks the `authenticateUser`
  node #1 for a query containing neither "auth" nor "authenticate").
- Full suite: 2842 passed, 0 failures (2838 -> 2842, +4 new).
- Real-corpus validation attempted, not obtained: ran the exact motivating query against
  harness-terminal's real 14,838-node graph — it's a terminal emulator with no login/auth feature
  at all, so there's no `authenticateUser`-shaped node in that corpus to demonstrate the gap
  closing against (the query instead surfaced `.installForLoginShell()`, a legitimate but
  different "login" match via the literal word already in its name). Grepped
  QA-Automation-Coding-Course for an auth function too — no hits. Validated via the constructed
  end-to-end test above instead; documented here rather than silently substituted for real-corpus
  validation.
