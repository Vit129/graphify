# P17 — Post-Competitor-Audit Roadmap (priority order for what's next)

Status: **Planning** (2026-07-18) — this doc is the prioritized punch-list; `dev-architect` is being
invoked next to turn item 1 into an actual design.
Priority: see per-item priority below; this doc exists to sequence them, not just list them
Owner surface: spans `graphify/query.py`, `graphify/detect.py`, `graphify/__main__.py`, watch/update
pipeline; each item's real surface is refined by `dev-architect` when its turn comes
Depends on: this session's 6-project search-quality benchmark (kouen-terminal, My-Investment-Port,
Home-Assistant, Fitness-Tracker, QA-Automation-Coding-Course, cpi-qa-automation), the live upstream
diff (`upstream/v8` @ `fb992ce`/v0.9.19), and a 3-agent competitor-landscape research pass (PKM tools:
Obsidian/Logseq/Roam/Foam/Dendron; code-graph MCP tools: CodeGraph/GitNexus/CodeGraphContext/Serena/
claude-context/grepai; AI-agent context approaches: Aider repo-map/Cursor/Copilot/Claude Code's
no-index bet) — none of the source transcripts are saved, this doc is the durable record

---

## Why this doc exists

Session did two things back to back: (1) shipped 3 real search-resolution fixes + a `graph.html`
viewer overhaul (PR #12, #13, both merged; v0.17.0 tagged/released), (2) ran a broad competitor audit
asking "is graphify still worth maintaining" — verdict: yes, but not on pure technical superiority.
Real gaps surfaced that pure feature-parity work never would have (nobody was going to file a "we lack
a file watcher" bug against a personal fork). This doc captures those before the context evaporates.

## Priority order

### 1. File-watcher auto-sync — biggest concrete gap found, do first

**Design + tasks done**: see `file-watcher-auto-sync/design.md` and `dev-task-progress.md` (same
directory). Orientation found not one but two existing partial mechanisms (`graphify watch`'s
foreground/opt-in filesystem daemon, and `graphify/hooks.py`'s already-installed git post-commit hook —
missed on the first orientation pass, caught and corrected mid-task-design). Real remaining gap: neither
fires between an agent's edit and their next commit. Decided: a new `PostToolUse` hook (Edit/Write/
MultiEdit) triggering a debounced background `graphify update`, not a new daemon (no new dependency, no
process-lifecycle surface) — 6 tasks broken down, none started yet.
Next: implement (task 1 first, `trigger_background_update()` in `watch.py`) — not yet started, awaiting
the go-ahead.

The single most-repeated architectural gap vs. actively-growing competitors (**CodeGraph**, 47k GitHub
stars in 5 months — largest data point in the whole audit; **GitNexus**, similar auto-sync claim):
they watch the filesystem and incrementally re-extract on save. graphify requires an explicit
`graphify update .` — this session hit that gap directly twice (Home-Assistant and Fitness-Tracker
both needed a manual rebuild before a fix could be validated against real data, and Fitness-Tracker's
cache had to be manually cleared because content-hash caching doesn't know the *extractor code*
changed, only that file content didn't).
- Why first: every other roadmap item is a quality/precision improvement; this is a workflow-friction
  item that affects literally every session using graphify, and it's the one competitors visibly
  differentiate on.
- Known prior art in this repo: `graphify watch` already exists (referenced throughout
  `graphify-out/`'s own log lines, e.g. "[graphify watch] Rebuilt: N nodes..." — the rebuild pipeline
  itself is not new) — the gap is likely "opt-in manual invocation" vs. "always-on background
  daemon/file-watcher," not missing rebuild logic entirely. **First real task for `dev-architect`:
  confirm this distinction precisely** (read `graphify watch`'s actual current trigger model) before
  designing anything net-new.
- Non-goal (probably): don't need a Merkle-tree-over-network sync like Cursor's — that's solving a
  cloud-embedding-consistency problem graphify doesn't have (everything's local already).

### 2. PageRank-style symbol/file importance ranking — cheap, complements existing clustering

Aider's repo-map (closest philosophical cousin to graphify: tree-sitter, no database, local) ranks
files by **personalized PageRank** over the call graph, not just community membership. graphify's
Leiden clustering answers "what group does this belong to," not "how important is this specific node
within a query's results" — a different axis. Layering a PageRank-style score on top of (not instead
of) the existing BM25 tiers could sharpen result ordering, especially for the fuzzy-natural-language
queries that scored worst in this session's benchmark (kouen-terminal's "zoom/fullscreen" query pulling
in a wrong-but-plausible-sounding subsystem — see P9/BM25 fallback work already landed).
- Cost: no new infra (pure graph-algorithm addition on data already in `graph.json`), unlike the
  embedding-search path (rejected once already, see `feature-provenance.md`'s "Rejected: Full
  Semantic/Embedding Search").
- Do after item 1 - item 1 is a workflow blocker affecting daily use; this is a quality polish.

**Shipped (PR #15, all 7 tasks done) — but the named motivating case wasn't actually fixed by it, stated
plainly**: see `pagerank-ranking/dev-task-progress.md` Task 7 for the full root-cause. The
implementation itself is correct and verified (bounded, backward-compatible, opt-in, zero regressions,
composes correctly with the existing concept/prose penalties) — Task 4's test suite proves this in
isolation. What this session's *hypothesis* got wrong: the kouen-terminal "zoom/fullscreen" query's
failure isn't a near-tie a small ranking nudge can fix. Root-caused live on the real repo: the correct
answer (`SessionEditor.zoomPane()`) scores #7 of 1765 real BM25 candidates, ~27% behind the top
(false-positive) match (`.addNewTab()`, a genuine "add"/"new"/"tab" keyword collision) — a real
relevance gap, not a tie, and one whose size exceeds `_PAGERANK_BOOST_MAX`'s 15% ceiling by design (a
larger cap would risk the opposite failure this feature exists to prevent). **If this specific class of
fuzzy-query failure is still worth chasing, the right next hypothesis is a synonym/vocabulary fix (P9's
own territory - `_SYNONYM_GROUPS`/`_PHRASE_SYNONYMS`) or accepting it as this session's benchmark
already labeled it: a documented ceiling of the lightweight query-expansion approach, not something
every subsequent feature is expected to close.**

### 3. Cut a 0.18.0 release for PR #12's content

Small housekeeping, not a design task. CHANGELOG's `## Unreleased` section already holds PR #12's
entries (Calls lens, lens-aware search) — they merged to main *after* v0.17.0 was tagged. Bump
`pyproject.toml`/`version.json`/`CURRENT_VERSION`, rename the heading, tag, GitHub Release — same
mechanics as the v0.17.0 cut this session already did, whenever there's enough new work to justify it
(or just do it now if the user wants the Calls-lens work notified to git-clone users via the
self-update check sooner rather than later).

### 4. `affected --relation` prefix-matching for parameterized relations

Small, safe, found but not fixed this session (see session record / PR #13 body): `--relation
shares_value` can't match `shares_value:input_boolean.home_mode`-style parameterized relation labels
without knowing the exact value in advance, because the filter in `affected.py`'s `affected_nodes` does
exact string membership (`relation not in relation_set`). `graphify query`'s own traversal doesn't have
this restriction. Fix shape: prefix/startswith match when the passed `--relation` doesn't contain `:`
but a candidate edge's relation does (`shares_value` should match `shares_value:*`) - bounded, low-risk,
no design-decision reversal involved (unlike item 6 below).

### 5. Home-Assistant `graphify.toml`'s `value_coupling = true` — not a graphify code task

Left uncommitted in `/Users/supavit.cho/Git/Personal/Home-Assistant/graphify.toml` this session,
deliberately (verify-only, per advisor guidance: "let the user decide whether to persist it" - a
different repo's config, not graphify's own code). Purely a reminder entry so it doesn't get lost -
no design work needed here, just a user decision: commit it there, or leave it reverted.

### 6. Content-as-data indexing — still on hold, needs explicit heuristic sign-off

QA-Automation-Coding-Course gap (lesson content stored as JS object-literal string properties,
completely invisible to the graph - 3/3 benchmark scenarios scored 1/5). A feasibility investigation
this session found a bounded ~40-60 line heuristic (gate on key ∈ {title,name,label,id,description} AND
enclosing array has 3+ sibling objects with 3+ properties each, mirroring `extract_json`'s
`_is_config_json` shape-probe pattern) - but this is the exact class of heuristic that already burned
the project once (#1224, JSON case, walked back to an explicit allowlist after producing "hundreds of
orphan key-nodes"). **Do not implement without the user explicitly approving the trigger heuristic
first** - this is a repeat instruction from earlier in the session, restated here so it survives
context compaction.

---

## What's explicitly NOT on this list (evaluated, not just forgotten)

- Full semantic/embedding search - re-evaluated implicitly by this session's competitor audit
  (`claude-context`/Zilliz-cloud and Cursor/Copilot both confirmed the infra-cost tradeoff graphify
  already declined; `grepai`'s fully-local-Ollama path is the one new data point that could reopen this
  someday, but no request to revisit came from the user this session)
- Switching to a real embedded graph database (KuzuDB/FalkorDB, like GitNexus/CodeGraphContext) -
  graphify's whole value proposition to this user is a portable, git-diffable `graph.json`; a real DB
  file is a regression on that axis unless a concrete need surfaces
