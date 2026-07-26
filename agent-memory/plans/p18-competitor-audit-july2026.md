# P18 — Competitor Audit, July 2026 (consolidated)

Status: **Audit only — no implementation started.** This doc consolidates every competitor-landscape
finding scattered across P17 and its descoped tracks into one current snapshot. It does **not**
supersede or delete those source docs — each is still the fuller record for its own decision and stays
where it is; see "Source docs" below. Written 2026-07-26 at explicit user request ("บันทึกไว้เป็นตัวใหม่
ทั้งหมด update July 2026") after a live re-check of `DeusData/codebase-memory-mcp` showed the finding
was already on record from 2026-07-25, one day earlier — this doc exists so the next session doesn't
have to re-derive that consolidation from 8 separate files again.

## Source docs (still authoritative for their own decision — not deleted, not replaced)

- `p17-post-competitor-audit-roadmap.md` — original 2026-07-18 audit (PKM tools, CodeGraph, GitNexus,
  CodeGraphContext, Serena, claude-context, grepai, Aider repo-map) + roadmap, 4/6 items shipped
- `agent-memory/knowledge/architecture/feature-provenance.md` — `## Rejected: Full Semantic/Embedding
  Search` section, reopened and reconfirmed 2026-07-25 against `DeusData/codebase-memory-mcp` and
  SocratiCode
- `cross-repo-edges/wayfinder-map.md` — cross-repo edge track, Ticket 1 resolved 2026-07-25 (no
  concrete need across any of the user's 12 personal repos), closed against the same DeusData
  precedent
- `lsp-type-resolution/wayfinder-map.md` — LSP-style semantic type resolution, Ticket 1 resolved
  2026-07-25 (real gap confirmed, Swift-only)
- `pagerank-ranking/`, `file-watcher-auto-sync/` — shipped items P17 roadmap items 1-2 above

## Full competitor list evaluated to date (all sessions, cumulative)

| Tool | Scale (as last checked) | Category | Status |
|------|------|------|------|
| CodeGraph | 47k stars (5mo) | code-graph MCP | audited 2026-07-18, no fresh check since |
| GitNexus | — | code-graph MCP | audited 2026-07-18 + 2026-07-25 (trace/context/rename/PDG) |
| CodeGraphContext | — | code-graph MCP | audited 2026-07-18 |
| Serena | — | code-graph MCP | audited 2026-07-18 |
| claude-context (Zilliz) | — | embedding search | audited 2026-07-18 |
| grepai | — | local-Ollama embedding search | audited 2026-07-18, reconfirmed 2026-07-25 |
| Aider repo-map | — | PageRank repo summarization | audited 2026-07-18, informed PR #15 |
| Obsidian/Logseq/Roam/Foam/Dendron | — | PKM, not code-graph | audited 2026-07-18, no action (different domain) |
| **DeusData/codebase-memory-mcp** | **35,464 stars**, pushed 2026-07-26, arXiv:2603.27277, SLSA3 | code-graph MCP, pure C, single binary | **audited 2026-07-25 (semantic search, cross-repo) + re-verified live 2026-07-26** |
| SocratiCode | — | Qdrant+Ollama semantic search | audited 2026-07-25 |

## DeusData/codebase-memory-mcp — full feature diff (verified live 2026-07-26 via GitHub API + README)

Largest single data point in the whole audit history — bigger than CodeGraph's 47k, live-maintained
(pushed same day as this check), backed by a published paper and supply-chain attestation (SLSA3,
VirusTotal-scanned releases).

### Already evaluated and decided (no new work needed — restated here, not re-litigated)

- **Semantic/embedding search** (bundled `nomic-embed-code`, no external API/Docker/Ollama) —
  reopened+reconfirmed rejected 2026-07-25 in `feature-provenance.md`. Real reason: not "infra cost"
  (they have none) but **distribution shape** — a bundled compiled model means graphify's
  single-Python-package model would need to become a binary-distribution project, a much bigger
  build/release change than the feature itself. No query gap found that provably needs it (P3/P4/P5
  vocabulary/tokenization fixes already close the closable gaps). Revisit only if a real unclosable
  query gap surfaces.
  - **Correction (2026-07-26, same day): this claim was checked against the wrong assumption.**
    graphify already ships a local embedding-based semantic fallback (`_embedding_seed_fallback`,
    `graphify/query.py`, opt-in via the pre-existing `embeddings` extra, `sentence-transformers/
    all-MiniLM-L6-v2`) — it was just a last-resort-only tier (tried only when BM25/typo/fuzzy all
    return zero seeds), not a primary/every-query signal. What actually stayed rejected was only:
    (a) fusing embeddings into *every* query's scoring, and (b) bundling a model into a binary
    distribution. **(a) was reopened and shipped same day** — see next entry.
  - **Shipped (2026-07-26): embedding fusion on every query**, not just as a last resort. Two opt-in
    modes, both no-ops without the `embeddings` extra, both user-selected after a live tradeoff
    discussion (not silently picked): `--semantic-fusion boost` (default) — bounded multiplicative
    nudge, same shape/ceiling as the existing `_PAGERANK_BOOST_MAX` (P17 item 2); can reorder
    near-ties, can never let a weak semantic match outrank a confident BM25 winner. `--semantic-fusion
    rrf` — equal-weight Reciprocal Rank Fusion, matching DeusData's actual mechanism; accepted
    tradeoff is that a purely-semantic top match can tie a confident lexical top match (both "rank 0
    of their own list"), which "boost" mode is specifically built to avoid. New: `_embedding_similarity_map`,
    `_fuse_embedding_rrf` in `graphify/query.py`; `embedding_sims` param on `_pick_seeds`;
    `--semantic-fusion` CLI flag and `semantic_fusion` MCP param on `query`/`query_graph`. 8 new tests
    in `tests/test_serve.py`, full suite green (3067 passed).
  - **Live-tested (2026-07-26) against 3 real repos** (graphify itself, kouen-terminal, My-Investment-Port)
    across easy/medium/hard/very-hard queries. Honest results, not just the wins: no regressions on
    easy/exact-match queries; `rrf` mode found genuinely better answers on 2 of 4 hard/very-hard cases
    (a doc node on a graphify meta-query, "Portfolio Context" on a My-Investment-Port paraphrase);
    `boost` mode (the safe default) changed almost nothing in this test set — consistent with its
    design (bounded, can't override a real BM25 gap) but also means it rarely closes a genuine
    zero-overlap gap on its own. **The originally-documented kouen-terminal "zoom/fullscreen" gap
    (P17 item 2, PageRank boost couldn't fix it) was re-tested with a full paraphrase query
    ("make one terminal pane take up the entire window temporarily") and still did NOT surface
    `zoomPane`, even with `rrf`** — it moved to a topically-closer doc node, but the original gap
    is not fully closed. Testing a single word ("zoom") instead of a real paraphrase is not a valid
    reproduction of that gap (trivial substring match dominates) - a methodology note for next time.
  - **Shipped (2026-07-26): on-disk embedding index cache**, closing a real perf gap found during live
    testing — every `graphify query` CLI call is a fresh process, so without disk persistence the
    embedding index (encoding every node's label+source_file) was rebuilt from scratch on every single
    query. New: `_embedding_corpus_hash()` (SHA-256 of model name + node ids + texts, detects a stale
    cache) and disk persistence in `_get_embedding_index()` (`graphify-out/cache/embeddings/index.npz`,
    atomic tmp-then-replace write), wired through `_embedding_seed_fallback`/`_embedding_similarity_map`/
    `_fuse_embedding_rrf`/`_query_graph_text` via a new `cache_file`/`embedding_cache_file` param
    (defaults `None` = old in-memory-only behavior, zero risk to any existing caller). CLI and MCP
    both wire it automatically from the already-known graph path. Caught a real bug while writing the
    first test: `np.savez` silently appends `.npz` to a path string that doesn't already end with it,
    so the original tmp-then-replace write silently failed every time (swallowed by the same
    never-crash-a-query `except Exception: pass` the cache read also uses) — fixed by writing through
    an open file handle instead, which numpy does not auto-suffix. Verified live on graphify's own
    10,564-node graph: 24.2s → 13.1s (~46% faster) on the second call against the same graph; the
    remaining time is the model-load step itself (torch/sentence-transformers import), which a
    per-query disk cache can't remove — only a standing process (the MCP server already behaves this
    way via its own in-memory cache) avoids paying that repeatedly. 5 new tests in `tests/test_serve.py`
    (hash determinism, write+read across a fresh graph object, stale-corpus rebuild, corrupt-cache
    fallback, cache_file=None unchanged-behavior guard), full suite green (3072 passed).
- **Cross-repo `CROSS_*` edges + multi-galaxy UI** — closed 2026-07-25, `cross-repo-edges/wayfinder-map.md`
  Ticket 1: zero cross-repo dependency evidence across all 12 of the user's personal repos
  (`package.json` local/file:/link: deps, `.gitmodules` — all checked, zero hits). Would also regress
  graphify's core value prop (portable per-repo `graph.json`) per P17's explicit non-goal list.

### Real gaps, evaluated for the first time this session (2026-07-26) — not yet decided, no implementation

These are genuinely new relative to the 2026-07-18/07-25 audits — flagging them here, decision deferred:

1. **Cypher-like ad-hoc query language** (`MATCH (f:Function)-[:CALLS]->(g) WHERE f.name = 'main'
   RETURN g.name`) — graphify has fixed-shape commands (`query`/`affected`/`shortest_path`/
   `blast_radius`), no general graph query DSL. Would need a parser + execution engine against the
   existing `nx.Graph` — real build cost, not a small addition.
2. **ADR management tool** (`manage_adr`, persists architecture decisions across sessions via MCP) —
   orthogonal to graph querying; closer to this repo's own `agent-memory/plans/` convention but as an
   MCP-exposed tool rather than markdown files. Unclear if it should be a graphify feature or stays a
   workflow convention (this repo already does ADR-equivalent record-keeping via markdown, informally).
3. **Dedicated dead-code-detection command** — **shipped same day (2026-07-26)**. Orientation found the
   core logic already existed and was already tested: `unreachable_functions()` in `graphify/analyze.py`
   (heuristic calls-graph reachability from name-pattern entry points), with 3 passing tests in
   `tests/test_analyze.py` — it was implemented but never wired to a CLI command or an MCP tool. Added:
   `graphify dead-code [--top-n N] [--graph path]` CLI command (`graphify/__main__.py`) and a `dead_code`
   MCP tool (`graphify/serve.py`), both thin wrappers around the existing function — no new algorithm,
   no new dependency. 3 new tests in `tests/test_dead_code_cli.py`, full suite green (3059 passed).
4. **Cross-service protocol breadth** — DeusData covers HTTP, gRPC, GraphQL, tRPC, and pub-sub
   (Socket.IO/EventEmitter) across 8 languages. graphify's cross-service linking is narrower: HTTP
   `fetch()` → Google Apps Script handler only (shipped in #18). Real scope gap if the user's actual
   projects use gRPC/GraphQL/tRPC anywhere (not yet checked against the user's 12 repos the way
   cross-repo-edges was).
5. **158 language / Hybrid-LSP-on-10-languages coverage** vs. graphify's current
   Python/JS/TS/Swift+config scope, and raw throughput (Linux kernel 28M LOC in 3 min, sub-ms query) —
   noted for completeness, not treated as an actionable gap: no evidence any of the user's repos
   exceed graphify's current performance envelope.

None of items 1-5 have a design doc, a Ticket, or a go/no-go decision yet — this is intentionally just
the audit record. Per this session's explicit instruction, implementation does not start from this doc
without a separate go-ahead on which item (if any) to pursue.

## What graphify still defends on architecture, not feature count (unchanged from P17)

- `graph.json` — portable, git-diffable, human-reviewable in a PR diff. DeusData's in-memory SQLite +
  binary store is not diff-able the same way.
- No standing cross-session daemon. DeusData runs a shared "Session Coordination Daemon" across every
  configured agent client on the machine; graphify's `file-watcher-auto-sync` (P17 item 1) is a
  detached one-shot background rebuild, not a standing service.
- Pure Python — source is directly readable/patchable without a C build toolchain.
