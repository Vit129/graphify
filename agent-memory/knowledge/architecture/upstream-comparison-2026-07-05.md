# graphify fork vs. upstream (safishamsi/graphify) — verified comparison, 2026-07-05

Grep target: `grep -n "<keyword>" knowledge/architecture/upstream-comparison-2026-07-05.md`

Method: shallow-cloned `https://github.com/safishamsi/graphify` (HEAD `3140b2e`,
2026-07-05, `pyproject.toml` version `0.9.6`) into a scratch dir and diffed it
directly against this repo's `graphify/` package (local version `0.16.0`,
1042 local commits) — not a repeat of README's or CHANGELOG's existing claims,
a fresh read of both trees' actual current source.

## Headline finding

**README.md's "What's different from upstream" section (lines 42-52) is
significantly stale.** It was accurate at some point in this fork's history,
but on 2026-07-02 this fork did a large **merge FROM upstream**
(CHANGELOG.md:86, `## 0.9.5 (2026-07-02, merged from upstream)` — ~15 items,
all crediting real external contributors: @joanfgarcia, @jerryliurui,
@Synvoya, @sheik-hiiobd, etc.), which pulled a large fraction of upstream's
own codebase in wholesale. `safishamsi/graphify` is not a stale/abandoned
project the fork left behind — it's an actively maintained, real
community-driven OSS project (dozens of numbered issues, distinct named
contributors, commits as recent as today, 2026-07-05) that has kept moving
in the 3 days since this fork's merge point. The two trees have partially
**re-converged**, and in a few areas **upstream is now ahead of this fork**,
not behind it.

## Provenance correction — this is adoption, not convergent invention

The first pass of this audit (diffing current-HEAD source only) left it
ambiguous whether the byte-identical files were "both sides independently
built the same thing" or "one side copied the other." Checked with
`git log --diff-filter=A --follow` on this fork's own history — it's not
ambiguous:

- `graphify/affected.py` was added **2026-05-20** by a commit literally
  titled `feat: add v8 affected and import-resolution support`.
- This fork's own branch history contains repeated wholesale adoptions of
  upstream's **`v8`** branch as this fork's main content, going back months
  before the 2026-07-02 event this audit originally focused on:
  `merge: replace v1/v2 history with v8 codebase as new main`,
  `merge: adopt v8 tree as main content`,
  `Merge remote-tracking branch 'upstream/v8' into v8`,
  `Merge official v8 (v0.8.32) with CodeBuddy support`,
  `Merge pull request #1071 from TheFedaikin/v8`, going back to at least
  2026-05-15 (`Add v8 to CI branch list`).

**Plain reading: `safishamsi/graphify` did a major internal rewrite on a
branch called `v8`, and this fork has been repeatedly adopting that v8
branch wholesale as its own main content for months** — not independently
building equivalent code that happened to converge. `affected.py`,
`resolver_registry.py`, `symbol_resolution.py`, and almost certainly a large
fraction of the rest of the shared 45,419-LOC package, are upstream's own
work, absorbed via these merges — not this fork's original engineering.

The one place this audit can positively confirm original, fork-authored
work (not absorbed from a v8 merge) is `query.py`: added by commit
`2586f03` at **2026-07-02 16:26**, several hours *before* the final
`merge: upstream/v8 (through their 0.9.5) into main` commit (`ea2135e`,
2026-07-02 20:15). That merge commit's own message confirms it explicitly:
*"upstream still had the full pre-BM25 scoring implementation (their
serve.py never saw this session's P1 rewrite that moved everything to
query.py) — discarded upstream's copy, kept this fork's re-export shim."*
So the BM25/disambiguation/hub-avoidance query layer, `config.py`,
`update_check.py`, and the 7 fork-only extractors remain a fair claim to
"built here" — everything else claimed as a differentiator earlier in this
doc should be read as "this fork currently has it, upstream's `v8` line
is where it came from," not "this fork invented it."

## Quantified, as of right now

| Metric | This fork | Upstream (`3140b2e`) |
|---|---|---|
| Version | 0.16.0 | 0.9.6 |
| `graphify/*.py` total LOC | 47,126 | 45,419 |
| Top-level `.py` modules in `graphify/` | 45 | 42 |
| `tests/test_*.py` files | 126 | 125 |
| Tree-sitter/scanner grammars claimed in README | 54 | 36 |
| Platform install subcommands (`graphify <x> install`) | 23 | 23 (identical list) |
| Local commit count (this fork) | 1,042 | — (shallow clone, not comparable) |

**Real changed-line count on files that exist in both** (via direct `diff`,
not an estimate): ~4,840 diff lines across 13 shared files — nowhere near
README's claimed "~67k lines changed in `graphify/` alone." That 67k figure
is very likely a cumulative historical stat (total added+removed across all
~1000 commits since the original fork point), most of which the 2026-07-02
upstream merge has since reconciled away. The real, current, standing diff
is roughly **7,000-8,000 lines total** — ~4,840 of diff churn in shared files
plus ~2,459 lines of genuinely fork-exclusive modules (below).

Per-file diff size (shared files only, line-diff count):

```
1167  export.py
1161  extract.py
 826  serve.py
 563  __main__.py
 468  watch.py
 170  analyze.py
 137  detect.py
 125  report.py
 122  llm.py
  56  cache.py
  34  ruby_resolution.py
   9  build.py
   2  wiki.py
   1  __init__.py
   0  everything else (30 files, byte-identical)
```

30 of the 43 shared top-level modules are **byte-for-byte identical**,
including `symbol_resolution.py`, `resolver_registry.py`, `affected.py`,
`reflect.py`, `security.py`, `prs.py`, `manifest.py`, `paths.py`,
`multigraph_compat.py`, `mcp_ingest.py`, `scip_ingest.py`, `transcribe.py`,
`tree_html.py`, `validate.py`. README's claim that upstream "has no
`affected.py`... those don't exist in its package at all" (README.md:48) is
**false as of today** — `affected.py`, `resolver_registry.py`, and
`symbol_resolution.py` all exist upstream, verbatim identical to this fork's
copies.

## What's still genuinely true and fork-exclusive (verified against real upstream source)

1. **Language extraction breadth.** Upstream's own README table lists 36
   tree-sitter grammars; this fork's lists 54. Confirmed by grepping for the
   actual extractor functions in upstream's `extract.py` — `extract_css`,
   `extract_html`, `extract_yaml`, `extract_toml`, `extract_robot`,
   `extract_gherkin`, `extract_fish` **do not exist anywhere in upstream**,
   not inline, not as modules. This fork's `.css/.scss/.html/.htm/.yaml/.yml
   /.toml/.robot/.resource/.feature/.fish` support (the P2/P6/P7/P8/P9/P10
   work logged in `feature-provenance.md`) is a real, still-standing,
   verified gap upstream hasn't closed.
2. **`query.py` — the BM25/disambiguation query layer — genuinely doesn't
   exist upstream.** Upstream's `serve.py` still carries the old hand-rolled
   tiered scorer (`_EXACT_MATCH_BONUS = 1000.0`, confirmed present at
   `serve.py:149` upstream) rather than this fork's real BM25 scorer (which
   now lives in `graphify/query.py`, not `serve.py`). `config.py` (per-project
   `graphify.toml`/`pyproject.toml` config + `update --all`) and
   `update_check.py` (self-update checker) are likewise absent upstream.
   Combined: ~2,459 lines of fork-exclusive code across these 3 files +
   7 extractor modules that upstream has no equivalent of at all.
3. **Hub-avoidance in `shortest_path` — still real, but the framing needs
   correcting.** Read both implementations side by side
   (`serve.py:_tool_shortest_path`, both sides): upstream's version is *not*
   the bare, naive call README implies — it already does BM25-adjacent
   scoring via `_score_nodes` for source/target resolution, a same-node
   guard, and a top-vs-runner-up ambiguity warning (`< 10%` gap). But it
   still calls **raw** `nx.shortest_path(G.to_undirected(as_view=True), ...)`
   with **no hub-degree penalty and no retry** — it will happily route
   through a high-degree utility node and only ever tries the single
   top-scored candidate pair. This fork's `find_path_with_disambiguation`
   (in `query.py`, called from `serve.py`) genuinely does more: it retries
   every near-tied candidate pair (`tried_pairs`), explicitly tracks
   `used_hub_fallback`, and only settles for a hub-routed path as a last
   resort with a warning. **Net: the underlying behavior difference is
   real and confirmed, but "ambiguity-safe resolution" is not unique to this
   fork anymore — only the combinatorial retry + hub-avoidance is.**
4. **Opt-in value-coupling (`shares_value:<value>` edges, config-gated).**
   Confirmed absent from upstream entirely (`value_coupling`/`shares_value`
   grep returns zero hits in upstream's tree). Still a real, fork-only
   feature.
5. **CLI surface — mostly converged, not "much larger."** All 23 platform
   install subcommands (`claude`, `codex`, `kilo`, `cursor`, `aider`, `claw`,
   `droid`, `trae`, `trae-cn`, `hermes`, `amp`, `agents`/`skills`, `kiro`,
   `pi`, `devin`, `antigravity`, `codebuddy`, `opencode`, `copilot`,
   `vscode`, `gemini`, `hook`, ...) exist **identically** upstream, and so do
   `prs`, `prs --triage`, `prs --conflicts`, `reflect`, `global add/remove/
   list/path`, `merge-graphs`, `save-result`, `clone`. README's "much larger
   CLI surface" bullet is **not currently accurate** — the only real CLI
   delta left is the query-layer subcommands this fork's `query.py` adds
   (typo/synonym-corrected retry flags) and whatever `config.py`'s
   `update --all`/`update-all` batch command adds.

## What upstream now has that this fork is missing (the reverse gap — new finding, not in any existing doc)

All from upstream commits **after** this fork's 2026-07-02 merge point
(i.e., 3 days of upstream work not yet pulled back in):

- **C# receiver-typed member-call resolution** (upstream `extract.py:11923`,
  `_resolve_csharp_member_calls`, upstream issue #1609, 2026-07-02).
  Completely absent from this fork's `extract.py` — confirmed by grep,
  zero matches. Without it, `recv.Method()` on a typed C# field/property/
  param/local can mis-bind to any same-named method corpus-wide, the exact
  failure mode `#1591`'s fix (already shared/merged) was adjacent to but
  didn't cover.
- **Ruby `module`/`Struct.new`/`Class.new`/`Data.define` container nodes**
  (upstream #1640, 2026-07-04). `resolve_ruby_member_calls` (the
  call-resolution half, in `ruby_resolution.py`) is byte-identical between
  fork and upstream — but the *container-node creation* half (in
  `extract.py`, confirmed present upstream via a `Struct.new` docstring
  match, confirmed absent in this fork's `extract.py` via the same grep)
  isn't. Plain Ruby `module Foo` blocks and `Foo = Struct.new(...)`/
  `Class.new(...)`/`Data.define(...)` constant-assignment idioms currently
  produce no queryable node in this fork's graphs.
- **Kotlin interface delegation edges** (`class Foo : Bar by baz`, upstream
  #1644, 2026-07-04) — `explicit_delegation` unwrapping is present upstream,
  absent from this fork's `extract.py` (confirmed via grep, zero matches).
- **Apex `interface X extends A, B` multi-inheritance edges** (upstream
  #1645, 2026-07-04) — confirmed absent from this fork's
  `extractors/apex.py` (no `extends`-per-parent loop found there).
- A cluster of smaller upstream fixes from the same 3-day window not
  independently verified line-by-line here but worth flagging as likely
  also missing (same "post-merge lag" reasoning): symlinked-input
  containment (#1613), 4 TS/JS extractor gaps — generator functions,
  namespace/module containers, import-equals edges (#1615), `.mts`/`.cts`
  extension recognition (#1607), malformed-semantic-chunk crash hardening
  (#1631), bare-npm-import false-aliasing fix (#1638), non-deterministic
  `graph.json` node/edge ordering fix (#1632), `obsidian export to_canvas`
  crash on dangling community members (#1236 follow-up), stale-source
  reconciliation on `update`/`watch` (#1623/#1622), Windows long-path
  hashing (#1655), Office-file `--update` re-entry bug (#1649), cached word
  counts for incremental detection (#1656).

## Curiosity, not verified further

`update_check.py` (fork-only) checks PyPI for package name `graphifyy`
(`PACKAGE_NAME = "graphifyy"`) — but this fork explicitly does **not**
publish to PyPI (README.md:85, "the PyPI name `graphifyy` is already taken
by upstream's package"). So this fork's self-update-check mechanism, if it
still runs, would be checking upstream's PyPI releases, not this fork's own
git commits. Not confirmed whether this code path is actually wired up to
run anywhere (`grep`-only check, not traced), just flagged as a loose end
worth a look if `graphify --version` nags about updates unexpectedly.

## Bottom line

The honest answer to "how different are they really, and whose work is
this": **far less different than README claims, and most of what's shared
is upstream's own code, adopted — not two teams independently converging.**
This fork's own, verifiably-original contribution on top of that adopted
base is narrower than README implies but real: *breadth* (7 extra
language/config-format extractors upstream has none of) and a *genuinely
better query/pathfinding layer built in a single documented session*
(real BM25 + combinatorial disambiguation + hub-avoidance vs. upstream's
still-tiered heuristic scorer + single-shot resolution, confirmed by commit
timestamps and the merge commit's own message), plus value-coupling.
Upstream's standing, real advantage right now is 3 days of
*extraction-correctness* fixes (C#, Ruby, Kotlin, Apex, TS/JS, Windows path
handling) shipped by its real contributor community since this fork's last
sync, that this fork hasn't pulled back in. Everything else the README
calls out as a differentiator (`affected.py`, `resolver_registry.py`,
`symbol_resolution.py`, the CLI command surface, "ambiguity-safe
resolution" as a headline) is either identical because it **is** upstream's
`v8` code, or has a materially different, narrower shape than README
describes. **README.md:42-52 should be rewritten** to stop implying this
fork built the shared foundation, and it would be worth pulling upstream's
last 3 days of commits (C#/Ruby/Kotlin/Apex/TS-JS fixes) into this fork the
same way the repeated `v8` adoptions did.
