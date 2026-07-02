# P10 — TOML + Fish Extraction, Real-Project Validation

Status: **Done** (2026-07-02)
Priority: user-directed ("ไปค้นหา แล้วแก้มาให้ครบ" — go search wider, then close remaining gaps)
Owner surface: new `graphify/extractors/toml_.py`, `graphify/extractors/fish.py`
Created: 2026-07-02
Depends on: P7 (originally deprioritized TOML/fish on a narrow search scope)

---

## Why

After summarizing this session's known limitations (SCSS/Gherkin never validated against real
files, TOML/fish rejected on real-file-count, no validation against the user's actual work
project), user asked to search further and close what could be closed rather than leave it as a
documented ceiling.

P7's original TOML/fish rejection searched only `~/Git` and `~/Documents` — a narrower scope than
this pass. Widening the search to the whole home directory (`~/.config`, `~/.codex`,
`~/.claude/plugins`, and real project dirs beyond just `~/Git/Personal`) reversed the verdict:

| Format | P7 scope (Git/Personal, Documents) | This pass (whole home dir) |
|---|---|---|
| TOML | ~1 real file (`cliff.toml`) | `~/.config/starship.toml`, `~/.codex/config.toml`, 2x real `cliff.toml` (harness-terminal, My-Investment-Port), several `ponytail` plugin command configs — a real, actively-maintained config format across the user's own tooling |
| Fish | 2 real files (mostly duplicate `activate.fish` venv boilerplate) | `~/.config/fish/config.fish`, `~/.config/fish/completions/harness-cli.fish`, harness-terminal's real `harness.fish` (3 genuine function definitions: OSC 133 prompt/preexec/postexec hooks) |

SCSS and Gherkin were searched again too, with the same negative result as P8 (0 real files
anywhere reasonable on this machine) — not reversed, since no new evidence turned up.

Also validated end-to-end against `~/Git/Company/cpi-qa-automation` — the user's actual work
project, never checked earlier this session (all prior validation was on personal-repo side
projects). Extension census: 198 real files, entirely `.ts`/`.md`/`.yml`/`.yaml`/`.json`/`.sql`/
`.html` — every format already supported before this plan. 0 extraction errors, 1542 nodes/1951
edges in 0.69s. Real queries against it: `"submit order flow"` correctly seeds
`submitOrderFlow()`/`submitEditFlow()`/`submitSmartFlow()` (the exact functions referenced
earlier in this project's own memory notes), `"login test"` surfaces the real
`smoke-login.spec.ts` suite.

## Non-goals

- SCSS/Gherkin real-file validation — searched again, still 0 real files found anywhere on this
  machine. Left as the documented ceiling from P8 (validated via constructed fixtures only).
- Fish `end`/block-nesting-aware extraction (functions calling other functions, scoped variables)
  — same granularity choice as Gherkin: only `function <name>` definitions become nodes, matching
  the actual searchable unit. No call-graph edges between fish functions.
- TOML array-of-primitives / inline-table (`{ a = 1, b = 2 }`) value-level extraction — only
  `[table]`/`[[array_of_tables]]` headers and root-level key names become nodes, matching the same
  "section is the unit, not each leaf value" scoping every other config-format extractor in this
  session used (YAML, HTML's id-only scope).

## What's done

- **`extract_toml`** (new `graphify/extractors/toml_.py`) — `tree-sitter-toml` (published on PyPI,
  checked first), 0 errors parsing real `cliff.toml`/`starship.toml`. Each `[table]`/
  `[[array_of_tables]]` header becomes a node labeled by its dotted key path
  (`project.optional-dependencies`); repeated array-of-tables entries get a counter suffix to stay
  distinct (same collision fix as CSS's nested-rule counter). Root-level `key = value` pairs
  (before any table) also become nodes, matching YAML's top-level-key granularity. Added as a
  **hard** dependency (real, common format — same tier as YAML/CSS/HTML, not the `robot`/`scss`
  optional-extra tier).
- **`extract_fish`** (new `graphify/extractors/fish.py`) — no tree-sitter grammar published for
  fish (checked `tree-sitter-fish`/`tree-sitter-fish-shell`/`py-tree-sitter-fish`, none resolve).
  Hand-rolled `function <name>` line scanner, same reasoning as Gherkin (fish's function-definition
  syntax is a simple anchored keyword pattern; fish is not whitespace-sensitive so no indentation
  tracking is needed to find it regardless of nesting depth inside `if`/`begin` guards). No new
  dependency.
- Registered both in `_DISPATCH`, `extractors/__init__.py`, `extract.py` facade re-exports.
- 6 tests in `tests/test_toml_extraction.py`, 5 in `tests/test_fish_extraction.py`.
- Full suite: 2853 passed, 0 failures (2842 -> 2853, +11 new). Dispatch table 100 -> 102.
- Real-file validation: `starship.toml` + `cliff.toml` -> 12 nodes, 0 errors; `harness.fish` +
  `config.fish` -> 5 nodes (3 real function definitions correctly extracted from inside a nested
  `if`/`end` guard, matching what the extractor's test fixture predicted before checking the real
  file).
