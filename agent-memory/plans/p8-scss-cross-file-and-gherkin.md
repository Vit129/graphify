# P8 — SCSS + Gherkin Extraction, Robot Cross-File Resolution

Status: **Done** (2026-07-02)
Priority: user-directed override of P7's real-file-count non-goals
Owner surface: `graphify/extractors/css.py` (extract_scss), `graphify/extractors/gherkin.py` (new),
`graphify/extractors/robot.py` (cross-file resolution)
Created: 2026-07-02
Depends on: P6 (Robot Framework), P7 (CSS)

---

## Why

Three items explicitly requested despite the audit-driven non-goals this session had already
recorded for two of them:

1. **Robot Framework `.resource` cross-file keyword resolution** — P6 documented this as a
   same-file-only non-goal. Reopened: see `p6-robot-framework-extraction.md`'s updated Non-goals
   section for the fix and real-file validation (53 previously-invisible cross-file `calls` edges
   on harness-terminal's real suite).
2. **SCSS/Sass** — P7's audit found 1 real local file and deprioritized it on the same real-file
   threshold that rejected fish/TOML. Re-checking that "1 file" while building this: it was
   `.venv/.../coverage/htmlfiles/style.scss`, a **vendored dependency file**, not real project
   source — actual real local count is 0, same as `.feature`. Noted here explicitly rather than
   silently building it: this is a deliberate user override of the real-file-count methodology,
   not a case where new evidence changed the verdict.
3. **Gherkin (`.feature`)** — P7 found 0 real local files. Same override.

## Non-goals

- `.sass` (indented, non-brace syntax) — `tree-sitter-scss` parses brace-based SCSS only; the
  indented dialect is a genuinely different grammar with no evidence (0 real files, either syntax)
  that it's worth sourcing a third parser for. Only `.scss` is wired into `_DISPATCH`.
- Gherkin step (`Given`/`When`/`Then`/`And`/`But`) lines as separate nodes — same granularity
  choice P2/P6 made: the searchable unit is the scenario, not each step. `Examples:` tables are
  left unparsed (their content is step-adjacent, low value as an independent search target).
- SCSS `@include`/`@extend`/`@use`/`@import` reference edges — structural extraction only, matching
  the same scoped-down goal P7 set for CSS's `@import`/`url()`.

## What's done

- **`extract_scss`** (`graphify/extractors/css.py`) — verified empirically that `tree-sitter-css`
  produces `ERROR` nodes on SCSS variables/nesting/`&`-selectors (would have silently mis-extracted
  real SCSS files), so this uses the separate `tree-sitter-scss` grammar instead. The two grammars
  share the same `rule_set`/`selectors`/`block`/`media_statement` node shape, so `extract_css` was
  refactored into a shared `_extract_stylesheet(path, language, at_rule_types)` walker rather than
  duplicating the file — `extract_scss` just passes the SCSS language + an extended at-rule-types
  tuple that adds `mixin_statement` (`@mixin`, which plain CSS has no equivalent of). Added
  `tree-sitter-scss` as an **optional extra** (`scss = [...]`), not a hard dependency — unlike
  CSS/HTML's high real-file counts, real local SCSS evidence is 0, matching the `robot`/`sql`/`dm`
  extras convention for audience-specific/low-volume formats.
- **`extract_gherkin`** (new `graphify/extractors/gherkin.py`) — no tree-sitter grammar exists for
  Gherkin on PyPI (checked `tree-sitter-gherkin` and `tree-sitter-cucumber`, neither published).
  Gherkin is a simple line-oriented, keyword-prefixed format unlike CSS/YAML's real nesting, so
  this is a hand-rolled line scanner (no new dependency) instead of the tree-sitter template every
  other extractor this session used. `Feature:` becomes a node; `Scenario:`/`Scenario
  Outline:`/`Background:` become child nodes via `contains` edges. Tags (`@smoke`) and comments
  (`#`) are skipped.
- **Robot Framework `.resource` cross-file resolution** — see updated
  `p6-robot-framework-extraction.md`.
- 5 tests in `tests/test_scss_extraction.py`, 6 in `tests/test_gherkin_extraction.py`, 3 new in
  `tests/test_robot_extraction.py` (resource import edge, deferred raw_call, end-to-end
  cross-file `calls` resolution).
- Full suite: 2838 passed, 0 failures (2827 -> 2838, +11 new). Dispatch table 98 -> 100 extensions.
- Real validation: no real local `.scss`/`.feature` files exist (see Why above), so validated
  against constructed fixtures modeled on real Gherkin/SCSS shape (nested selectors, `Scenario
  Outline`/`Examples`) rather than a real corpus — the honest caveat for these two, unlike every
  other extractor added this session which had real-file validation.
