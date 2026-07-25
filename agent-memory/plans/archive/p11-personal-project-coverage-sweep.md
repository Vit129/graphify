# P11 — Personal-Project Coverage Sweep (.hook free win + full validation)

Status: **Done** (2026-07-02)
Priority: user-directed ("แล้วกับ personal project" — the same completeness check, now against
every personal project rather than just the one work project checked in P10)
Owner surface: `graphify/extract.py` (`_is_config_json`, `_DISPATCH`)
Created: 2026-07-02
Depends on: P10 (established the wider-search methodology this reuses)

---

## Why

P10 validated one real project (`cpi-qa-automation`, the user's work repo). Asked directly whether
the same held for personal projects — all 9 (`9arm-skills`, `agy-plugin-cc`, `agy-plugin-codex`,
`Fitness-Tracker`, `harness-terminal`, `Home-Assistant`, `Language-Learning`, `My-Investment-Port`,
`QA-Automation-Coding-Course`) were extension-audited and, where real gaps turned up, fixed —
not just re-asserted from memory.

## Non-goals (checked and explicitly rejected, with reasoning)

- **`.golden`** (harness-terminal, 49 real git-tracked files) — terminal-reflow snapshot test
  fixtures. Inspected real content: pure raw buffer dump (`cols=13 rows=5 ... |the quick bro|`),
  no internal identifiers or structure — the searchable unit (the test name) already lives entirely
  in the *filename*, not content worth AST-walking. Same class as `junit.xml`/generated test output
  excluded in P7.
- **`.strings`** (harness-terminal, 72 raw hits) — checked git-tracked count: **0**. Every hit was
  inside a compiled `.app` bundle (`Harness.app/.../Sparkle.framework/`), and the content itself
  turned out to be a *binary* compiled plist (`bplist00` magic header), not the plain-text source
  `.strings` format — a build artifact two ways over, not real source.
  the fish/TOML reversal earlier, this is the opposite finding: some "raw hit" extensions really
  are just noise, and the fix is checking (`git ls-files`), not assuming either direction.
- **`.plist`** — only 1 real git-tracked file across *all 9* personal projects
  (`harness-terminal`'s `Info.plist`). Checked wider (all personal projects, not just one) before
  concluding — still below the bar TOML/fish cleared (those had real files in 3+ independent
  locations). Left unsupported; revisit if a second real project surfaces one.
- **Home-Assistant's `.storage/*.iids`/`.aids`/`.state`** (123 git-tracked files) — despite being
  git-tracked (this repo version-controls its whole HA config dir including runtime state, an
  unusual but real setup choice), inspected content: HomeKit accessory-ID persistence, pure
  generated runtime state with UUID-shaped filenames, nothing a natural-language query would ever
  target. Git-tracked status alone isn't suffient evidence of "real source" — content still has to
  be checked, same lesson as `.golden` above.
- **`custom_components/hacs/hacs_frontend/`** inside Home-Assistant — a HACS-installed (Home
  Assistant Community Store) vendored frontend JS bundle, same category as `node_modules`/
  `Sparkle.framework` from earlier sessions. Caught mid-validation: an early un-scoped query run
  surfaced a minified vendor bundle file as a top result before this directory was added to the
  exclusion set — a live instance of the "raw extension count needs active triage" lesson, not a
  hypothetical one.

## What's done

- **`.hook` → `extract_json`** (real free win, found via the same-format-different-extension
  pattern as `.gs`→`extract_js`/`.resource`→`extract_robot`). Kiro Autopilot's `*.kiro.hook` files
  (16 real git-tracked files across `Home-Assistant` + `My-Investment-Port` — directly the user's
  own agent-orchestration tooling, not a hypothetical format) are plain JSON, but `extract_json`'s
  existing `_is_config_json` recognizer didn't know the shape (no filename match, no
  `_CONFIG_JSON_KEYS` top-level key — `name`/`when`/`then` are too generic to add to that set
  without risking false-positiving on real data JSON) and silently produced 0 nodes for every one.
  Fixed with a narrow, precise filename-suffix check (`name.endswith(".kiro.hook")`) rather than
  loosening the generic key probe — verified real content extracts correctly (`name`, `when`,
  `then`, `prompt` keys all become nodes).
- Full-suite extraction + 0-error validation run across **all 9 personal projects** (not just the
  one checked previously), from `9arm-skills` (12 files) to `My-Investment-Port` (1839 files,
  ~20k nodes): every project extracts with **0 errors** using the current dispatch table.
- Real end-to-end search validation on a second personal project beyond what was already checked
  this session (`Home-Assistant`, after properly excluding the HACS vendor bundle found above):
  `"pre-cool the house before arrival"` correctly surfaces the real
  `agent-memory/knowledge/home-mode-arrival-system.md` doc — directly matching the automation the
  user's own profile memory names ("AC scheduling, pre-cooling, arrival triggers").
- 2 new tests (`test_extract_json_kiro_hook_still_extracted`,
  `test_extract_hook_dispatches_to_json_extractor`) in `tests/test_extract.py`.
- Full suite: 2855 passed, 0 failures (2853 -> 2855, +2 new). Dispatch table 102 -> 103.
