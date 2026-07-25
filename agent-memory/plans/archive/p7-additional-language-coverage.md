# P7 — Additional Language Coverage (CSS, HTML, .resource, .gs)

Status: **Done** (2026-07-02)
Priority: **P2** — same class of gap as P2/P6, lower real-file volume per format than YAML/Robot
Owner surface: `graphify/extractors/css.py`, `graphify/extractors/html.py`, `_DISPATCH` entries
Created: 2026-07-02
Depends on: P2 (YAML), P6 (Robot Framework) — same audit method, same day

---

## Why

Re-ran the extension audit after P2/P6 closed (dispatch table now 93 extensions), this time
diffing the *entire* real-project file census against the supported set instead of guessing at
specific formats, then hand-triaging each hit: build artifacts (`.dia` — Swift compiler
diagnostics inside `.build/`, not source), vendored third-party code (`.podspec` — all instances
were `Sparkle.podspec` inside a dependency checkout), and generated output (`junit.xml`/
`output.xml` test results) were excluded as noise, not real gaps.

What survived triage, ranked by real (non-vendored, non-duplicate) file count:

| Format | Real files | Verdict |
|---|---|---|
| CSS | 117 | New extractor (this plan) |
| HTML | 85 | New extractor (this plan) |
| `.resource` (Robot Framework) | 2 | **Free** — same grammar/extractor as `.robot`, just a dispatch entry |
| `.gs` (Google Apps Script) | 2 | **Free** — JS syntax, dispatch to `extract_js` |
| fish shell | 2 (after excluding vendored `venv/bin/activate.fish`) | Deprioritized — too low real value to justify a new extractor right now |
| TOML | ~1 real (`cliff.toml`, changelog-generator config) | Deprioritized — same reasoning |

## Non-goals

- fish/TOML extractors — real file counts too low (2 and ~1 respectively, after removing vendored/
  generated noise) to justify new extractor code right now. Revisit if a real project surfaces
  more of either.
- **Cross-check against harness-terminal's `LSPServerRegistry.swift` (2026-07-02 follow-up)** — used
  it as an independent "what counts as a language" checklist (17 LSP-backed language groups) instead
  of guessing. Every extension it lists is already covered by the dispatch table **except**:
  Gherkin (`.feature`), SCSS/Sass, and treating `.zsh`/`.jsonc`/`.markdown`/`.hxx` as aliases of an
  existing extractor. Checked each against real local files and rejected all of them:
  - `.feature` (Gherkin) — 0 real files found on this machine. No extractor built.
  - `.scss`/`.sass` — 1 real file. Below the fish/TOML bar already set above.
  - `.zsh` — only 1 real *unique* file after dedup (16 raw hits were 15 duplicates of the same file
    across harness-terminal's `.claude/worktrees/*`, the exact noise pattern documented earlier in
    this session). Even setting the count aside, parsing it with `tree-sitter-bash` (the obvious
    "just alias it" move) produces genuine `ERROR` nodes on zsh-only syntax
    (`${+functions[...]}` flag expansion, `(( ))` arithmetic conditionals) — confirms this isn't a
    free win, bash's grammar doesn't actually parse zsh.
  - `.jsonc` — 0 real files. Also checked whether aliasing to `extract_json` would even work: fed a
    JSONC sample (`//` and `/* */` comments) to `tree-sitter-json` and it produces `ERROR` nodes —
    the JSON grammar doesn't tolerate comments, so this wouldn't be a free win even if real files
    existed.
  - `.markdown` — 32 raw hits, but every single one was a duplicate of one vendored file
    (`Sparkle/README.markdown`) repeated across harness-terminal's worktrees. 0 real unique files.
  - `.hxx` — 0 real files.

  Conclusion: dispatch-table coverage is complete relative to every language harness-terminal's own
  LSP registry considers "supported," once vendored/worktree-duplicate noise is filtered out. No
  further extractor work identified from this angle.
- HTML: extracting every element, not just `id`-attributed ones — a real document has hundreds of
  `<div>`/`<span>` elements; only elements with an `id` are the ones a developer actually
  references (from CSS, from JS `getElementById`, from a test's selector) and searches for by
  name. See `graphify/extractors/html.py`'s module docstring.
- CSS: resolving `@import`/`url()` references as edges, CSS-in-JS (styled-components etc.),
  SCSS/LESS preprocessor syntax — plain CSS structural extraction only, matching this plan's
  scoped-down goal.
- `.resource` cross-file `Resource` import resolution (a `.robot` file importing keywords defined
  in a separate `.resource` file) — same same-file-only scope P6 already documented as a
  non-goal; not revisited here since it's the identical gap, not a new one.

## What's done

- **Free wins** (zero new extraction code, just `_DISPATCH` entries):
  - `.gs` -> `extract_js` (verified on a real file: `syncLocalStorageToGoogleSheets.gs`,
    51 nodes including real function names `doGet()`/`doPost()`).
  - `.resource` -> `extract_robot` (verified on harness-terminal's real
    `Tests/HarnessRobotTests/resources/harness.resource`: 15 keyword nodes, 0 errors — same
    grammar, same `*** Keywords ***` section shape as `.robot`, the extractor needed no changes).
- **New `graphify/extractors/css.py`** — self-contained (`zig.py` template, same reasoning as
  YAML/Robot: CSS's `rule_set`/`media_statement` shape has no equivalent in `_extract_generic`).
  Each `rule_set` becomes a node labeled by its selector text (`.btn-primary`, `#header
  .nav-item`); `@media`/`@supports`/`@keyframes` blocks become container nodes so a rule with the
  same selector nested inside a media query is a *distinct* node from the top-level rule with that
  selector, not a collision (verified with a dedicated regression test). `tree-sitter-css` added
  as a **hard** dependency (high real-file volume, same reasoning as YAML).
- **New `graphify/extractors/html.py`** — same template. Deliberately narrow scope: only elements
  with an `id` attribute become nodes (label = `#the-id`, matching the CSS extractor's `#id`
  convention for consistency). Real-file validation against
  `QA-Automation-Coding-Course/Playwright/index.html` extracted exactly the 22 ids already
  identified during this session's earlier competitor-tool research pass (`run-tests-btn`,
  `hint-btn`, `next-lesson-btn`, `progress-bar-fill`, etc.) — confirms the synthetic test fixtures
  used earlier in the session for P3's naming-convention tests were modeling a real, now-extracted
  shape, not a hypothetical one. `tree-sitter-html` added as a hard dependency.
- 6 tests in `tests/test_css_extraction.py`, 5 in `tests/test_html_extraction.py`, plus 1 each in
  `tests/test_robot_extraction.py` (`.resource` dispatch) and `tests/test_extract.py`
  (`.gs` dispatch) — all following the established pattern (synthetic unit cases + a dispatch
  test proving the extractor is actually wired into `graphify.extract.extract()`, not just
  callable in isolation).
- Full suite: 2824 passed, 0 failures (2811 -> 2824, +13 new).
- Real-project end-to-end validation (`QA-Automation-Coding-Course`, CSS + HTML combined): 265
  total nodes. Query `"run tests button"` correctly surfaces `#run-tests-btn`; query `"sidebar
  title"` correctly surfaces `.sidebar-title`. No changes to `serve.py` needed — same
  language-agnostic search-layer confirmation as every prior extractor added this session.
