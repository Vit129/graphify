# Feature Provenance — graphify search/matching pipeline

Grep target: `grep -n "<keyword>" knowledge/architecture/feature-provenance.md`

Where each search/matching feature actually came from — tool researched, real gap hit, or
concept adopted vs rejected. Not a changelog (see CHANGELOG.md for that) — this is "why does
this exist and what did we look at before building it."

## Origin Story

- Starting point: graphify's `_score_nodes` was already a working lexical scorer — exact/prefix/
  substring tiers weighted by IDF (`_compute_idf`), fed by a trigram index (`_get_trigram_index`)
  used only as a candidate prefilter, never for ranking.
- Question that kicked off the whole investigation: "if I tell an agent to fix something in plain
  language, and maybe typo a little, will it actually find the right file?" — not a feature
  request, a trust question about the tool's core promise.
- Surveyed how the wider field solves "find the edit spot": Google/Sourcegraph Zoekt (trigram +
  ctags symbol boost), GitHub Blackbird (custom Rust engine, not applicable at graphify's scale),
  Cursor (RAG/embeddings via Turbopuffer), and two direct competitors in the same MCP-server niche
  — DeusData/codebase-memory-mcp and SocratiCode — plus classic DS&A (fzf, zoxide, ripgrep, fd)
  and, once the "we already ship a fuzzy matcher" realization hit, harness-terminal's own
  `FuzzyPathResolver.swift`.
- Every plan below (P3/P4/P5, referenced in `agent-memory/plans/`) came out of this sweep, not out
  of a pre-existing roadmap item.

## CamelCase/snake_case Tokenization (P3)

- Root gap: `_search_tokens` used a plain `\w+` split — `getUserData`/`get_user_data` never broke
  into sub-words, so a natural-language query term could hit at best the weak substring tier
  against a camelCase/snake_case label, never exact/prefix, regardless of how precisely it named
  the target.
- **Zoekt**: integrates `universal-ctags` so symbol *definitions* outrank plain-text matches —
  didn't solve the tokenization gap directly (trigram search is already boundary-agnostic) but
  confirmed symbol-boundary awareness is standard industry practice, not a nice-to-have.
- **DeusData/codebase-memory-mcp**: direct precedent adopted. Its SQLite FTS5 layer uses a custom
  `cbm_camel_split` tokenizer specifically to split camelCase/snake_case before BM25 scoring — this
  is the exact shape graphify's fix copies (conceptually, not code — graphify has no FTS5/SQLite
  dependency to plug into).
- **SocratiCode**: confirmed the *pattern* (every hybrid tool still runs a lexical/BM25 layer with
  code-aware tokenization even when full semantic search is available) but wasn't the source of the
  fix — its BM25 side is Qdrant sparse-vector, not directly portable.
- Regression caught while implementing, not predicted by any of the above: a sub-word match (e.g.
  `"payload"` inside `PayloadFactory`) was first wired into the *exact* scoring tier, which tied it
  with a genuine whole-label exact match (`Payload`). Fixed by routing sub-word matches into the
  *prefix* tier instead — exact stays reserved for whole-label equality. Caught via a real-graph
  regression test, not a code-review guess.

## Typo/Abbreviation Cascade Fallback (P5)

- Root gap: zero fuzzy layer at all — `_score_nodes(G, ["sesion"])` against a label containing
  `session` returns `[]`, not a low score.
- Compared four candidate algorithms against the same typo/abbreviation cases before picking one:

  | Algorithm | Source | Verdict |
  |---|---|---|
  | Ordered subsequence (greedy) | harness-terminal's own `FuzzyPathResolver.swift` (`FileFuzzyMatcher.score`) | **Adopted** — for abbreviations only |
  | Ordered subsequence (Smith-Waterman DP) | fzf `FuzzyMatchV2` | Considered, not adopted — see below |
  | Trigram Jaccard similarity | reuses graphify's existing `_get_trigram_index` | Tested, rejected as primary (too weak on transposition/substitution, fails on abbreviations entirely) |
  | Damerau-Levenshtein edit distance | classic DP, session-implemented | **Adopted** — for typos |
  | Frecency (frequency+recency) | zoxide | Rejected — solves a different problem (usage-based ranking), not text matching; would need new persisted state |

- **fzf's Smith-Waterman DP (V2)** finds the *optimal* alignment instead of greedy's first-found
  match — genuinely better when a query character has a better match later in the same string
  (demonstrated concretely: `greedy_score("ab", "xa_xb_ab")` scores low because it locks onto the
  early split match instead of the trailing contiguous `ab`). Decided **not** to port the DP
  version: that failure mode is common in *long paths with repeated components* (harness-terminal's
  actual domain — searching file trees) but rare in graphify's domain (*short* identifiers, which
  don't typically self-repeat). Greedy — i.e. harness-terminal's own already-proven code — was
  judged sufficient for the domain actually being matched (`label` sub-words), with DP as a
  documented, scoped-out upgrade path if `source_file` path-matching is ever added.
- **Damerau-Levenshtein was the deciding evidence**, not an assumption: side-by-side test showed it
  is the *only* one of the four that correctly handles adjacent-transposition typos
  (`recieve`/`receive`, distance 1) while every subsequence-based and trigram-based approach either
  failed or scored weakly on that exact case. It also *correctly rejects* the abbreviation case
  (`gud`/`getUserData`, distance 8) rather than false-positiving on it — abbreviation and typo need
  different tools, and edit distance's own length-sensitivity naturally tells them apart.
- Design decision made independent of any single source: rejected building a second scoring
  algorithm that runs *alongside* `_score_nodes` (scores wouldn't be on a comparable scale to the
  existing IDF-weighted tiers). Instead corrected terms are re-run through the *unmodified*
  `_score_nodes`/`_pick_seeds` pipeline — a corrected term is just a term, inheriting P3's
  camelCase sub-word matching and IDF weighting automatically.
- Real gap found post-implementation, not predicted: cross-word abbreviations (`"hus"` for
  `handleUserSession`, spanning three sub-words) failed initially because the vocabulary only held
  individual sub-words (`handle`/`user`/`session`) — fixed by also indexing each label's whole
  concatenated form.
- **Compound-span typo gap, found and closed same session**: typos of a *specific 2-3-word
  compound span* inside a longer label (e.g. `wholesals` for `WholeSales` inside a much longer
  Playwright test description) failed — individual sub-words and the full label bracketed this
  case without covering it. User explicitly pushed to research the DS&A literature rather than
  accept the gap. Found the actual textbook answer: **Bitap/agrep's approximate-substring-search
  problem** — searching for a pattern as a fuzzy match *anywhere* in a longer text, no word
  boundaries assumed. Landed as two additive fixes (user's explicit choice when presented with a
  simpler-vs-more-complete tradeoff, "do both"):
  - Bounded 2-/3-token n-gram spans added to the *typo* vocabulary pool only (`_get_vocabulary`'s
    `_NGRAM_SPAN_SIZES`) — covers realistic 2-3-morpheme compounds as an ordinary typo-path
    candidate, no new algorithm needed.
  - A genuine Bitap-style fuzzy-substring DP (`_fuzzy_substring_distance`/`_fuzzy_substring_seeds`)
    as a last-resort third cascade tier, for spans longer than the n-gram window — architecturally
    forced to break from P5's original "correct the term, retry the pipeline" design, because a
    substring match is a *position*, not a vocabulary word to hand back to `_score_nodes`. Returns
    node IDs directly, with an explicit lower-confidence note.
  - **Second regression caught mid-implementation**: the n-gram spans were initially added to
    *both* the typo and abbreviation candidate pools — this broke abbreviation matching
    (`"hus"` started resolving to a synthetic 2-token span `"handleuser"` instead of the correct
    `"handleusersession"`, because the shorter synthetic candidate scores higher in the
    subsequence-match formula purely for being shorter, an artifact of the scoring function, not a
    real target). Fixed by splitting `_get_vocabulary` into two genuinely separate pools. Caught by
    the existing test suite immediately, not by manual review — the value of having written
    `test_correct_term_fixes_cross_word_abbreviation` in the first pass paid off in the second.

## test()/describe() Block Extraction (P4)

- Not a search-algorithm concept — an extraction-layer gap, found by directly inspecting real
  extraction output on a client `.spec.ts` file (`cpi-qa-automation`, kept out of test fixtures —
  see the genericized examples in `tests/test_real_world_naming_conventions.py`): the extractor
  produced a node for the file and one top-level helper function, and *zero* nodes for any
  `test(...)` block — the thing a query like "fix the WholeSales Territory Level 2 test" is
  actually asking about didn't exist in the graph at all, so no ranking algorithm (P3 or P5) could
  ever have found it.
- No external tool comparison here — this was root-caused directly against graphify's own
  `_extract_generic`/`_js_extra_walk` architecture (confirmed no other language extracts a
  `call_expression` as a node anywhere in the codebase; this is a genuinely new pattern, not an
  extension of one).

## Rejected: Full Semantic/Embedding Search

- Both DeusData/codebase-memory-mcp (bundled `nomic-embed-code`, no external API) and SocratiCode
  (Qdrant + Ollama, Docker-managed) run real dense-vector semantic search alongside BM25/lexical,
  fused with Reciprocal Rank Fusion.
- Deliberately not adopted for graphify. Cost/benefit: both require either a bundled embedding
  model compiled into a binary (DeusData's approach — a much larger distribution/build change than
  graphify's current single-Python-package shape) or a Docker-managed vector DB + local LLM runtime
  (SocratiCode's approach — a hard dependency graphify doesn't currently have and a real ongoing
  infra cost, not a one-time build). The *closable* gaps found this session (camelCase
  tokenization, typo/abbreviation, missing extraction nodes) didn't require it — they were
  vocabulary-representation and extraction-completeness problems, not "the query means something
  semantically different from any word in the code" problems. Revisit only if a real query gap
  surfaces that P3/P4/P5-style fixes provably can't close.

## Real BM25 Scoring (P1 reopen, superseding two earlier fix attempts)

- The original P1 doc's "ceiling closed" claim (IDF-coverage weighting fixes multi-term seed
  selection) and a first reopen draft (add a stopword filter) were both re-validated against the
  same harness-terminal query and found **not actually fixed** — `.forwardBrowserRequest()` stuck
  at rank 10 through both. A second, deeper re-diagnosis benchmarked three approaches side by side
  on the same real graph (naive tokenization + real BM25, P3's tokenizer + real BM25, + stopword
  filter) and found the actual defect one level below where both earlier attempts were patching:
  `_score_nodes`'s hand-rolled three-tier bonus system (exact=1000x/prefix=100x/substring=1x) is a
  weaker, unprincipled approximation of what real BM25 already solves — no term-frequency
  saturation (one exact match could outscore broad multi-term coverage regardless of how many
  *other* terms it covered) and no document-length normalization.
- This is the point in the session where BM25 — mentioned earlier only as a comparison point for
  DeusData/codebase-memory-mcp and SocratiCode's hybrid search — became something graphify's own
  core scorer actually adopts, not just a competitor concept noted in passing.
- **Real gap found during implementation**: pure BM25-on-tokens has no path back to matching a
  query typed as one literal word (`"foobarservice"`) against a label P3's tokenizer splits into
  several morphemes (`FooBarService` -> foo/bar/service) — fixed the same way P5's vocabulary
  handles the identical problem (index each label's whole concatenated form as an extra token).
  Second time this exact technique has independently solved two different problems in the same
  session — worth remembering as a general pattern, not just a one-off fix.
- **Second real gap, requiring a deliberate deviation from this doc's own stated non-goal**
  ("do not touch `_pick_seeds`"): `_pick_seeds`'s `gap_ratio` cutoff (0.2) was calibrated against
  the old tier system's huge multiplicative cliffs — BM25's smooth, compressed score curve let an
  unrelated node clear that same threshold that the old cliffs used to block. Raised to 0.8, and
  — per this doc's own review process, echoing what the user pushed for on the P5 compound-span
  fix earlier in the session — verified against 3 different real natural-language queries on the
  real graph, not just the one failing test, before accepting the change as generalizing rather
  than overfitting to one case.
- **P5's compound-span typo gap** — closed same session (see above, n-gram vocabulary + Bitap
  fallback).

## Language Extraction Coverage (P2 YAML, P6 Robot Framework) — why breadth matters

- Prompted directly by re-checking DeusData/codebase-memory-mcp and SocratiCode's own README
  claims about broad language support: DeusData benchmarks itself across **31 real-world repos**
  and vendors **158 tree-sitter grammars** into one binary; SocratiCode falls back to naive
  line-based chunking for anything without a dedicated AST parser rather than going dark. Neither
  uses LSP as its primary coverage mechanism — DeusData's "Hybrid LSP" badge covers only 9 of its
  158 languages, layered *on top of* tree-sitter coverage as an enhancement, not a replacement.
  **Lesson explicitly rejected for graphify**: LSP was considered and correctly ruled out for bulk
  graph extraction — it's built for interactive single-file sessions (hover/autocomplete), not
  parsing 10,000 files fast, and would mean shipping N external server binaries instead of
  graphify's current pure-`pip install` tree-sitter-grammar model. `tree-sitter-yaml` and
  `tree-sitter-robot` both installed as ordinary PyPI packages with prebuilt wheels — same shape
  as every other of graphify's 90+ languages, no architecture change needed.
- Real audit (same method as every other gap in this session — check the user's own real
  projects, don't guess) across Company/Personal found YAML (121 files) and Robot Framework (125
  raw / 12 real, rest were duplicate worktree copies) as the two largest unsupported-format gaps.
  Confirmed harness-terminal's own LSP investment (`LSPServerRegistry.swift`) covers exactly 5
  languages — Swift, TypeScript/JavaScript, Python, Rust, Go — all 5 already fully supported by
  graphify's extraction; the *actual* gaps (YAML, Robot Framework, HTML, CSS) are a structurally
  different category (declarative/config or DSL formats with no function/class concept), not
  "core languages nobody built yet."
- Both new extractors are bespoke, self-contained modules (`extractors/yaml_.py`,
  `extractors/robot.py`) following `zig.py`'s established template, not routed through the shared
  `_extract_generic` engine — same reasoning P4's research already established: `_extract_generic`
  is for languages sharing its imperative function/class/import type-dispatch shape, and neither
  YAML nor Robot Framework's `*** Section ***` structure fits that shape.
- **Confirmed empirically, not assumed**: the entire session's search-layer work (P1 BM25, P3
  camelCase tokenization, P5 typo/fuzzy fallback) required *zero* changes to support either new
  language — `serve.py` has no language-specific branching anywhere (grepped to confirm), so any
  extractor that populates a normal `label` field gets full search capability for free. Adding
  language coverage and improving search quality are genuinely orthogonal axes of this codebase.

## P7 — CSS, HTML, .resource, .gs (same-session follow-on)

- Asked to re-run the audit and "just do it" for whatever else turned up. Diffing the *entire*
  real-project file census against the (now 93-extension) dispatch table, rather than checking a
  few guessed formats, surfaced two zero-cost wins the earlier narrower audits missed entirely:
  `.resource` (Robot Framework's shared-keyword-library format — literally the same grammar as
  `.robot`, just needed a second `_DISPATCH` entry pointing at the same `extract_robot`) and `.gs`
  (Google Apps Script — plain JS syntax, dispatched straight to `extract_js`). Neither needed a
  single line of new extraction logic.
- Also had to actively discard false positives from the wider audit: `.dia` (1174 raw hits) turned
  out to be Swift compiler diagnostic files inside `.build/` — an exclusion-filter gap (the noise
  filter excluded `/build/` as a substring, which doesn't match `.build/` — a leading-dot directory
  name is a different string), not a real source format. `.podspec` and most of the `.xml` hits
  were vendored third-party dependency files (Sparkle, pulled in via SPM) or generated test-result
  output (`junit.xml`), not the user's own code. Worth remembering: a raw extension count from a
  real-project scan needs active triage before trusting it as a work-item list, not just a better
  exclusion regex.
- CSS and HTML got real new extractors (`extractors/css.py`, `extractors/html.py`), same bespoke
  self-contained template as YAML/Robot. HTML's scope was deliberately narrowed to `id`-attributed
  elements only, which turned out to validate something from earlier in the session: real-file
  extraction against `QA-Automation-Coding-Course/Playwright/index.html` produced exactly the same
  22 element ids (`run-tests-btn`, `hint-btn`, `next-lesson-btn`, `progress-bar-fill`, ...) that
  P3's synthetic test fixtures had been modeling from manual inspection — the earlier tests weren't
  guessing at a plausible shape, they were describing a real one that just didn't have an extractor
  behind it yet.
- fish shell and TOML were investigated and explicitly deprioritized, not silently skipped: after
  removing vendored/generated noise, fish had 2 real files and TOML had essentially 1
  (`cliff.toml`, a changelog-generator config) — too low a real-file count to justify new extractor
  code right now, documented as a non-goal with the reasoning rather than left unexplained.

## P8 — SCSS + Gherkin, Robot cross-file resolution (explicit override of P7's non-goals)

- Cross-checked dispatch coverage against harness-terminal's own `LSPServerRegistry.swift` (its
  independent "what counts as a supported language" list) — every LSP-backed language it lists was
  already covered except Gherkin, SCSS/Sass, and treating `.zsh`/`.jsonc`/`.markdown`/`.hxx` as
  aliases of an existing extractor. All six were checked against real local files and rejected on
  the same real-file-count grounds as fish/TOML — `.zsh` in particular looked like a free
  `extract_bash` alias until actually parsing a real file with `tree-sitter-bash` turned up genuine
  `ERROR` nodes on zsh-only syntax (`${+functions[...]}`, `(( ))`), proving bash's grammar can't
  parse zsh even setting the file-count question aside; `.jsonc` similarly turned up `ERROR` nodes
  parsing a comment with `tree-sitter-json`.
- User then explicitly asked for two of the just-rejected items anyway (SCSS/Sass, Gherkin) plus
  reopening P6's documented Robot `.resource` cross-file non-goal. Built all three, but the
  real-file-count methodology itself wasn't silently abandoned — re-checking SCSS's earlier "1 real
  file" while building this found it was `.venv/.../coverage/htmlfiles/style.scss`, a vendored
  Python package template, not real project source (actual count: 0, same as Gherkin). Recorded
  explicitly as a deliberate user override, not new evidence changing the verdict — see
  `p8-scss-cross-file-and-gherkin.md`.
- Robot `.resource` cross-file resolution turned out not to need a bespoke resolver: `extract.py`
  already has a generic `raw_calls` deferral mechanism (any per-file extractor can emit an
  unresolved call and the shared cross-file pass in `extract()` matches it against every other
  file's node labels). `extract_robot` previously *dropped* keyword calls it couldn't resolve
  locally instead of deferring them — the fix was routing them into that existing mechanism, not
  building a new one. Also had to add `.robot`/`.resource` to `_CASE_INSENSITIVE_EXTS` (the set
  #1581 introduced for PHP/SQL/Nim), since Robot Framework keyword names are case-insensitive by
  spec (`log message` must resolve to a keyword defined as `Log Message`). Validated on
  harness-terminal's real suite: 53 previously-invisible cross-file `calls` edges into a shared
  `.resource` file's keywords.
- Gherkin has no maintained tree-sitter grammar published on PyPI (checked `tree-sitter-gherkin`
  and `tree-sitter-cucumber` directly — neither resolves). Rather than force a tree-sitter fit,
  `extract_gherkin` is a hand-rolled line scanner — reasonable because Gherkin's format is
  genuinely line-oriented/keyword-prefixed (`Feature:`, `Scenario:`), unlike CSS/YAML's real
  nesting that justified a full parser for those.

## P9 — Lightweight query synonym expansion (the semantic-search re-decision)

- After P1-P8, the one gap explicitly *not* claimed fixed: query and code using different words
  for the same concept ("log the user in" vs `authenticate`), zero literal terms in common — no
  amount of BM25/typo/fuzzy tuning bridges that, only recall of a *different* word helps. This is
  exactly what embeddings solve well and lexical search structurally can't.
- The origin-story section of this doc already records full embedding search as evaluated and
  rejected once (infra cost). Re-deciding that mid-session without asking would have been the same
  mistake as the P1/P5 confusion earlier this session (silently building something adjacent to,
  not identical with, what was actually being asked) — except worse, because it would have
  silently *reversed* a decision instead of just missing one. Surfaced as an explicit
  `AskUserQuestion` with the real tradeoff spelled out: local embedding model (real dependency +
  slower indexing, private/free), API embeddings (best quality, needs a key + network + per-query
  cost — a real constraint for a local dev-tool MCP server), lightweight query expansion (small
  synonym map, ~5% of the effort, ceiling is it only helps mapped word pairs), or skip. **User
  picked lightweight query expansion.**
- Implementation rides the existing pipeline instead of adding a new one: `_query_terms` (the one
  choke-point every consumer already reads from) expands matched terms via a curated
  `_SYNONYM_GROUPS` table, then hands the enriched term list to the *unmodified* BM25 scorer — same
  "corrected/expanded terms re-enter the normal pipeline, don't get a second scoring path" pattern
  P5's typo/abbreviation cascade already established.
- The motivating example itself ("log the user **in**") turned out to need more than single-token
  synonym lookup: "in" is a filtered stopword, and "log" alone is too overloaded with logging to
  put in a synonym group unconditionally. Solved with a second mechanism — bounded-word-gap regexes
  matched against the *raw* question — specifically because the object ("the user") splits the
  phrasal verb; a plain substring check for `"log in"` verified failed on this exact input during
  test-writing (caught by the test, not assumed correct) before being fixed to a proximity regex.

## P10 — TOML + fish, and the first real-work-project validation

- Asked directly "does it find everything" after P9, honestly answered with the known ceilings
  (SCSS/Gherkin never validated against real files, TOML/fish rejected on real-file-count, never
  validated against the user's actual work repo). User's response: go search wider and close what
  can be closed — not "silently claim it's done," an explicit instruction to re-verify before
  accepting the earlier verdict.
- The TOML/fish rejection in P7 searched only `~/Git` and `~/Documents`. Widening to the whole home
  directory reversed it: `~/.config/starship.toml`, `~/.codex/config.toml`, a second real
  `cliff.toml` (My-Investment-Port, not just harness-terminal), several `ponytail` plugin command
  configs for TOML; `~/.config/fish/config.fish` and harness-terminal's real `harness.fish` (3
  genuine OSC-133 prompt-hook function definitions) for fish. Same lesson P7 already learned about
  `.dia`/`.podspec` false positives, mirrored in the opposite direction this time: a narrow search
  scope produces false *negatives* just as easily as a loose noise filter produces false positives
  — the fix both times was widening what got checked, not trusting the first pass's scope.
  SCSS/Gherkin were re-searched with the same wider scope and still came back at 0 real files —
  not reversed, because no new evidence turned up this time.
- `tree-sitter-toml` exists on PyPI and parses real `cliff.toml`/`starship.toml` with 0 errors, so
  `extract_toml` is a normal tree-sitter extractor, added as a hard dependency (config-file volume
  found put it in the same tier as YAML/CSS/HTML, not the low-volume `robot`/`scss` extras tier).
  Fish has no published tree-sitter binding (checked 3 plausible package names) — `extract_fish`
  is a hand-rolled `function <name>` scanner, the same choice made for Gherkin and for the same
  reason (a simple anchored-keyword format doesn't need a full grammar).
- First real end-to-end validation this session against the user's actual work project
  (`~/Git/Company/cpi-qa-automation`, not a personal side project): 198 files, all formats already
  supported before this plan (`.ts`/`.md`/`.yml`/`.json`/`.sql`/`.html`), 0 extraction errors.
  Real queries confirm the whole pipeline works on real day-job code, not just personal-repo
  fixtures: `"submit order flow"` seeds `submitOrderFlow()`/`submitEditFlow()`/`submitSmartFlow()`
  — the exact functions this project's own earlier memory notes named as real examples.

## P11 — "แล้วกับ personal project" (the same check, now for all 9 personal projects)

- P10 validated exactly one project (the user's work repo). Asked directly whether personal
  projects got the same treatment — they hadn't, not really: earlier validation this session
  touched harness-terminal heavily but not the other 8. Extension-census-audited all 9
  (`9arm-skills` through `My-Investment-Port`) the same way P7's original audit worked, then
  extraction-ran every one against the current dispatch table.
- Two outcomes from the raw extension hits this surfaced, in opposite directions — worth recording
  both since only checking for false negatives (missing formats) would repeat the mistake P7's
  narrow-scope search made, but only checking for false positives would miss real gaps:
  - **False negative (a real gap):** `.kiro.hook` files (Kiro Autopilot hooks, part of the user's
    own agent-orchestration stack per their profile) are plain JSON but didn't match
    `extract_json`'s existing config/manifest recognizer, so they silently produced 0 nodes. 16
    real files across 2 projects. Fixed with a precise filename-suffix check rather than loosening
    the generic top-level-key probe (which risks false-positiving on real data JSON — the exact
    failure mode #1224 already exists to prevent).
  - **False positives correctly rejected:** `.golden` (content is a raw buffer dump with the
    test name only in the filename, not the content — same class as `junit.xml`), `.strings` (0
    real git-tracked files — every raw hit was a compiled binary plist inside a `.app` bundle, not
    plain-text source), Home-Assistant's `.storage/*.iids`/`.aids`/`.state` (git-tracked, which
    made this the closest call, but content is pure generated HomeKit runtime state — git-tracked
    status alone isn't evidence of "real source worth extracting," content still has to be
    checked).
  - A live instance of the "raw counts need active triage" lesson happened *during* validation,
    not just during the audit: an early un-scoped real-query test against Home-Assistant surfaced a
    `custom_components/hacs/hacs_frontend/` minified vendor JS bundle as a top BFS-seed result —
    HACS (Home Assistant Community Store) installs third-party integration frontends into the repo
    tree, the same category of noise as `node_modules`/`Sparkle.framework` from earlier sessions.
    Caught by inspecting the actual query output before reporting it, not assumed clean because the
    extraction step itself succeeded with 0 errors.
