# P16 — Qualified Node Resolution for `path`/`explain` (duplicate-name root cause)

Status: **Phase 1 DONE** (2026-07-04) — `--path`/`--source-path`/`--target-path` on `path`,
`--path` on `explain`, threaded into the shared `find_path_with_disambiguation` (query.py) and
`explain`'s `_find_node`/`_find_node_tied_group` filtering. Verified live on all three evidence
cases below. Phase 2 (`file:Label` syntax) remains deferred — Phase 1 covered the real cases
without touching the shared resolver, so Phase 2 stays gated on "only if the flag proves clumsy."
Priority: **P2** — the symptom is already mitigated (path retries all near-tied candidates,
2026-07-03); this plan addresses the root cause, so it is important but not urgent
Owner surface: Phase 1 touches only `__main__.py`'s `path`/`explain` arg parsing (additive
flag). Phase 2 (optional, higher risk) touches `_find_node_core` (`graphify/query.py`) —
shared by `path`, `explain`, and `save-result` node citation.
Depends on: query's `--path`/`--exclude-path` filter (landed 2026-07-03, commit 91d1de6) —
Phase 1 reuses the same scoping approach

---

## Problem (evidence, 2026-07-03 dogfooding)

graphify resolves a plain-text name to a node by label match. Duplicate labels across files
are common and legitimate:
- `Stats` ×3 across parallel EN/JP progress files (Language-Learning) → `path` ambiguous tie
- `handleNotification` ×2 (harness-terminal) — the bug being investigated WAS the difference
  between the two
- `calcPaperPortfolioValue()` ×2 with divergent logic (My-Investment-Port) — QA audit missed
  the second one entirely

The retry-all-tied-candidates fix makes "no path found" honest, but the user still cannot SAY
which `Stats` they mean.

## Research grounding (2026-07-03, sourced)

SCIP/LSIF (Sourcegraph, GitHub precise nav) eliminate this with a structural symbol key
(`scheme package version descriptor-chain`), derived from a compiler at a source position.
Two facts matter for scoping:
1. graphify cannot mint true SCIP symbols (no compiler/binder) — full parity is out of reach
   and NOT the goal.
2. Sourcegraph's own text/name search has graphify's exact ambiguity — this is inherent to
   name-based entry, so the fix is *letting the caller qualify*, not guessing better.

Key existing asset: since #1504, node IDs are already path-qualified
(`apps_harness_..._sessioncoordinator_handlenotification`), and `_find_node_core` already
matches on exact node ID. The ambiguity warning (landed 2026-07-03) already prints those IDs.
So the "escape hatch" exists today — this plan makes it ergonomic.

## Design

### Phase 1 — `--path P` scoping on `path` and `explain` (additive, low risk)
Mirror query's landed `--path`/`--exclude-path` flags:

```
graphify path "Overview" "Stats" --target-path japanese/
graphify explain "handleNotification" --path Apps/Harness/.../NotificationCoordinator.swift
```

- `path` needs per-endpoint scoping: `--source-path P` / `--target-path P` (a single shared
  `--path` cannot disambiguate when BOTH endpoints are duplicated in different dirs).
  Plain `--path P` = applies to both, for the common case.
- Filter candidate lists (`src_candidates`/`tgt_candidates`, `_find_node` results) by
  `source_file.startswith(P)` BEFORE the tie-retry loop.
- Zero changes to `_find_node_core` — pure arg-parsing + list filtering in `__main__.py`.
- Update the ambiguity warning to suggest the flag:
  `"...trying each before giving up (narrow with --source-path/--target-path)"`.

### Phase 2 (optional, separate gate) — `file:Label` qualified syntax in `_find_node_core`
Accept `"japanese/progress.md:Stats"` / `"NotificationCoordinator.swift:handleNotification"`
as a first-class lookup form: split on the last `:`, treat the left side as a source_file
suffix filter, the right as the label. Touches the shared resolver, so:
- Gate: full regression suite + re-run all landed `path`/`explain` regression tests + verify
  `save-result --nodes` citation matching is unaffected.
- Must not change behavior for any input without a `:` (labels containing `:` — e.g. C++
  `ns::sym` — need an explicit test proving they still resolve via the current path).
Do Phase 2 only if Phase 1's flag proves clumsy in real use; flags may be enough.

## Verification

- Unit: duplicate-label fixture (reuse `_write_duplicate_name_graph` in `tests/test_path_cli.py`)
  + `--target-path japanese/` → resolves the japanese `Stats` deterministically, no ambiguity
  warning.
- Real repos: the three evidence cases above — Language-Learning `Stats`, harness-terminal
  `handleNotification` (should let a user path to the NotificationCoordinator one specifically),
  My-Investment-Port `calcPaperPortfolioValue` (explain each of the two independently).

## Risks

- Phase 1: near-zero (additive flag, no shared-code change). Main risk is flag sprawl —
  keep naming consistent with query's existing `--path`.
- Phase 2: touches the resolver every command depends on; the `:`-in-label collision is the
  concrete known hazard. Stays optional until Phase 1 proves insufficient.
