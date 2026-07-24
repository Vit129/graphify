# Wayfinder Map — Cross-Repo Edges

Status: Charting only — no ticket resolved yet
Tracker: local (`agent-memory/plans/`, matching every other plan in this repo — p1 through p18/
iac-http-linking are all local docs, no GitHub Issues used for planning in this repo)
Origin: descoped from `agent-memory/plans/iac-http-linking/` round (see that design.md's Tactical
Design + `agent-memory/knowledge/architecture/feature-provenance.md`) — flagged too big to spec in
one interview, real core-assumption rework, not an additive patch.

## Destination

graphify can express a real dependency/reference between a node in Repo A and a node in Repo B —
when the user genuinely has repos that reference each other — without abandoning graphify's core
value proposition (a portable, git-diffable `graph.json` per repo, explicitly re-affirmed in
`p17-post-competitor-audit-roadmap.md`'s "What's explicitly NOT on this list": *"Switching to a
real embedded graph database... a real DB file is a regression on that axis unless a concrete need
surfaces"*).

## Notes

- Competitor precedent: `codebase-memory-mcp` does this via a shared store, node IDs namespaced by
  repo, `CROSS_*` edges, multi-galaxy 3D UI layout for cross-repo visualization.
- graphify today: confirmed zero infra for this (`grep -rniE "cross_repo|CROSS_|multi_project"` =
  0 hits) — single `nx.Graph` per process/instance, node ids are file-stem-based and only
  disambiguated within one corpus (see `_file_stem`'s docstring and the id-remap post-pass found
  during `iac-http-linking`'s Task 5/8 debugging — ids are NOT stable/global identifiers today,
  they're recomputed per-corpus).
- Real prior art already in this repo for a DIFFERENT but related problem: `p15-config-value-coupling.md`'s `shares_value` edges connect files by a shared identifier
  string, INFERRED confidence, hub-capped — a lighter-weight "correlation, not reference" pattern
  that might be a cheaper first step than true cross-repo linking (see Ticket 1).

## Decisions so far

(none yet — charting only)

## Tickets

### Ticket 1 — grilling (HITL): does a concrete cross-repo need actually exist?
Advisor flagged this during `iac-http-linking`: the user's actual projects (kouen-terminal,
My-Investment-Port, Home-Assistant, Fitness-Tracker, graphify itself) are mostly single-repo. Before
designing anything, confirm: is there a REAL pair of repos the user references together often
enough to want a graph edge between them (e.g. a shared library repo + an app consuming it)? If no
concrete case exists, this whole track should be re-classified as Out of scope, not sit as an open
ticket indefinitely.
Blocks: everything below.

### Ticket 2 — research (AFK): what does "cross-repo edge" actually need to answer?
Once Ticket 1 confirms a real case, research what query the user actually wants answered
("what in Repo B breaks if I change this in Repo A?" vs. "show me every place Repo B calls into
Repo A" vs. something else) — the answer shapes everything downstream (storage model, id scheme).
Blocked by: Ticket 1.

### Ticket 3 — grilling (HITL): storage model
Three real options, each with a real tradeoff against the portable-`graph.json` value prop:
(a) keep one `graph.json` per repo + a lightweight external cross-reference index (most portable,
most additive) (b) merge into one combined `graph.json` spanning both repos (loses per-repo
portability/git-diffability) (c) a real graph DB shared across repos (already rejected once for
single-repo reasons, would need explicit re-litigation). Needs the user's actual usage pattern from
Ticket 2 to pick correctly.
Blocked by: Ticket 2.

### Ticket 4 — grilling (HITL): node ID namespacing
Cross-repo edges need node ids that don't collide across repos. Current ids are file-stem-based
and only unique within one corpus/extraction run (confirmed fragile even within a single corpus —
see the id-remap post-pass `iac-http-linking` had to work around 3 times). Decide: prefix every id
with a repo identifier (breaking change to existing `graph.json` consumers/tests?), or a separate
mapping layer that doesn't touch existing single-repo ids at all.
Blocked by: Ticket 3.

### Ticket 5 — task: CLI/MCP surface
Once the model is picked: does `graphify query`/`explain`/`path`/`blast_radius` need a
multi-repo-aware mode (e.g. `--repo` flag, or auto-detect a linked-repo manifest), or is this
purely a data-layer addition with no new user-facing surface yet?
Blocked by: Ticket 3, Ticket 4.

## Not yet specified (fog)

- Whether "cross-repo" should include the company-workspace repos (`~/Git/Company/**`) at all, or
  is scoped to personal-workspace-only repos — a policy question that touches
  `rules/core.md`'s VCS-Remote-by-Path split, not just a graphify code question. Surface this to
  the user once Ticket 1 confirms a real case exists.

## Out of scope

(none yet — nothing has been ruled out beyond what iac-http-linking's design.md already recorded)
