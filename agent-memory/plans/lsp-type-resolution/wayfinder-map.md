# Wayfinder Map — LSP-Style Semantic Type Resolution

Status: Ticket 1 resolved (real gap confirmed, Swift-only) AND the confirmed overload-drop bug is now
fixed (commit `4db71f7`, 2026-07-25) — Ticket 2 (build-vs-adopt language scope, the bigger LSP
question) still open, unaffected by this fix, still needs user's HITL call
Tracker: local (`agent-memory/plans/`, matching every other plan in this repo)
Origin: descoped from `agent-memory/plans/iac-http-linking/` round — flagged as reimplementing a
language-server-grade inference engine, not an additive patch.

## Destination

graphify's call/reference resolution correctly handles the cases its current tree-sitter-AST +
heuristic matching gets wrong today — for the language(s) the user actually hits real gaps in, not
a from-scratch reimplementation of tsserver/pyright/gopls/rust-analyzer across every supported
language.

## Notes

- Competitor precedent: `codebase-memory-mcp` implements "Hybrid LSP" in C for 10 languages
  (parameter binding, return-type inference, generic substitution, JSX component dispatch, overload
  resolution, etc.), structurally inspired by real language servers.
- **Re-scoped mid-charting, not assumed**: the original framing ("graphify has zero type awareness,
  pure syntactic AST") is not entirely accurate — checked the actual code before charting further.
  graphify already has a per-file `type_table: dict[str, str]` (local name -> declared type text)
  threaded out as `swift_type_table`/`ts_type_table`/`csharp_type_table` for exactly 3 languages
  (Swift #1356, TypeScript, C#), consumed by `_resolve_swift_member_calls`/
  `_resolve_typescript_member_calls`/`_resolve_csharp_member_calls` to resolve receiver-typed member
  calls (`vm.update()` -> the real `VM.update` definition). This is real but narrow: a
  declared-type lookup table, not generics substitution, not overload resolution, not flow-sensitive
  narrowing, not JSX component dispatch. The actual gap is narrower than "zero type resolution
  exists" - it's "the existing type-table mechanism doesn't cover generics/overloads/JSX," which is
  a smaller, more answerable question.
- Real existing investment already in this exact area, don't duplicate: per-language member-call
  resolvers exist for Swift, Python, Ruby, TypeScript, C++, ObjC, C# (`extract.py:~11753-11785`
  registration block) - any new work here extends that lineage, doesn't replace it.

## Decisions so far

- **Re-framed the destination during charting**: not "add type resolution" (already partially
  exists) but "close specific, confirmed gaps in the existing type-table mechanism, for languages
  that actually matter to the user's real projects." Recorded here so a future session doesn't
  re-discover the `type_table` mechanism from scratch and re-scope wrongly a second time.

## Tickets

### Ticket 1 — RESOLVED (2026-07-25): real gap confirmed, Swift-only
Before any design work: audit real queries against the user's actual repos (kouen-terminal/Swift,
My-Investment-Port/TS+JS, graphify itself/Python) for cases where the CURRENT resolver (tree-sitter
+ existing type_table) gives a wrong or missing `calls`/`references` edge specifically because of
missing generics/overload/polymorphism handling - not a hypothetical gap. Mirrors how
`agent-memory/knowledge/architecture/feature-provenance.md`'s BM25/P3/P5 work was scoped (real
benchmark failures, not assumed gaps). If zero real failures are found, this whole track should be
re-classified Out of scope, not sit open.

**Verdict: yes, one real confirmed failure, Swift only.** `kouen-terminal`'s `GlyphRasterizer`
(`Packages/KouenTerminalRenderer/Sources/KouenTerminalRenderer/GlyphRasterizer.swift`) declares 3
real overloads of `rasterize` (L234/266/277). `GlyphAtlas.swift` calls all 3 on the same
`rasterizer: GlyphRasterizer` typed field (L156/173/187). Checked the actual graph
(`graphify-out/2026-07-23/graph.json`): only the L156 call resolves to a `calls` edge — L173 and
L187 produce **zero edges anywhere**, not misdirected edges, silently dropped. Root cause: all 3
overloads merge into one graph node keyed by name only, not full signature; `_resolve_swift_member_calls`
only manages to link 1 of 3 real call sites. Reproducible, not hypothetical.
- **My-Investment-Port (TS/JS): no candidate exists.** Actual source (143 `.js` + 132 `.jsx` + 30
  `.ts`, first-party only) has zero generic functions/methods and zero overloaded signatures
  anywhere — it's effectively untyped JS. The claimed gap has no surface to trigger here.
- **graphify itself (Python): mechanism not applicable.** No `@overload`, no `Generic[...]`
  anywhere in `graphify/`. Python has no compile-time name+arity overload dispatch — nothing
  analogous to resolve.
Blocks: everything below (now unblocked, narrowed to Swift).

**Fix landed 2026-07-25 (commit `4db71f7`), scope: overload disambiguation only, not the bigger
Ticket 3 build-vs-adopt question.** Re-verified the root cause empirically before fixing (don't trust
the pre-fix hypothesis on read-alone): it was earlier and worse than "the `method_index` dict
collision picks the wrong overload" — `_make_id(parent_class_nid, func_name)` keys a Swift method's
node id on the bare name alone, and `add_node` is first-write-wins, so all 3 `rasterize` overloads
collapsed onto **one node** at extraction time. Confirmed by re-extracting the real kouen-terminal
files (AST-only, `graphify.extract.extract()`, no LLM cost): before the fix, only 1 `rasterize`
definition node existed and only 1 of the 3 cross-file call sites produced an edge (the other 2
candidate edges didn't fail to resolve — they resolved to the SAME merged node as the first, and got
deduped away by the resolver's own `(caller, target)` pair-guard, since duplicate identical pairs
collapse to one).

Fix: pre-scan each Swift type body for names declared 2+ times and, only for those, qualify the
node id/label with the full Swift selector (parameter external labels, e.g.
`rasterize(codepoint:bold:)`), tagged with `swift_bare_name`/`swift_param_labels` metadata.
`_resolve_swift_member_calls` groups same-bare-name candidates and, when ambiguous (2+ candidates),
matches the call site's captured argument labels against each candidate's declared labels — binds
only on an exact single match, otherwise falls back to today's type-level `references` edge (no
guessing). Non-overloaded methods (the vast majority) keep their existing plain node id/label
unchanged — this was scoped as additive, not a general Swift node-id format change.

Re-verified after the fix, same real kouen-terminal files: all 3 `rasterize` overloads now produce
distinct definition nodes, and all 3 `GlyphAtlas.swift` call sites (L156/173/187) resolve to their
own correct overload. Full suite: 3013 passed, 28 skipped, 0 failures (no regression).

**Honest remaining ceiling (not fixed, documented not overclaimed):** (1) an overload split across
a class in one file and an `extension` in a *different* file — the pre-scan is per-file, so it can't
see the sibling file's declarations and that split silently falls back to pre-fix (first-write-wins)
behavior; (2) a call site with no parenthesized argument list to read (e.g. a trailing-closure-only
call `f.bar { ... }`) can't be label-matched and falls back to the type-level `references` edge
rather than a `calls` edge to a specific overload; (3) default-argument calls where the passed labels
don't exactly enumerate every declared parameter aren't specifically handled — same fallback. None of
these are crash risks; all degrade to the pre-fix behavior (bail to `references`, or the general
single-node collapse for the same-name-across-files case), not a wrong guess.

### Ticket 2 — grilling (HITL): which language(s), if any real gap is confirmed
graphify already invests per-language (Swift/Python/Ruby/TS/C++/ObjC/C#) - a full LSP-grade engine
across all of them is out of realistic scope. If Ticket 1 finds real gaps, narrow to the 1-2
languages the user's actual projects hit most (likely TS/JS given My-Investment-Port, or Python
given graphify's own codebase) rather than chasing parity with the competitor's 10-language claim.

**Ticket 1's evidence already narrows this far more than expected: Swift is the only language with
a confirmed real failure** (kouen-terminal's overload-drop case above) — TS/JS and Python both came
back with zero candidates, not just zero confirmed failures. This makes Ticket 2's own question
close to self-answering (Swift, scoped to overload resolution specifically — not generics, not
polymorphism, since only the overload case was found), but the actual go/no-go on spending build
effort here is still the user's call, not mine to presume. Surfacing for that decision rather than
proceeding into Ticket 3.
Blocked by: Ticket 1 (now clear).

### Ticket 3 — research (AFK): build vs. adopt
A genuinely different architecture option, not yet evaluated: shell out to a REAL existing language
server (`tsserver`, `pyright --outputjson`, or LSP client protocol) for the narrowed language(s),
rather than reimplementing inference heuristics from scratch in Python. Tradeoffs to weigh: real
language servers are authoritative (no reinvention risk) but add a runtime dependency + process
lifecycle (a real cost graphify has avoided so far, per its own "zero dependency/portable" ethos
noted throughout `feature-provenance.md`) vs. extending the existing lightweight `type_table`
heuristic (cheaper, no new dependency, but caps out below true inference by design). This decision
was never on the table during the original competitor audit (which only looked at reimplementing
inference in C) - a real alternative worth researching before committing to either extreme.
Blocked by: Ticket 2.

### Ticket 4 — grilling (HITL): scope the actual mechanism
Once build-vs-adopt is decided: what specifically gets built (e.g. "extend `type_table` to track
generic parameter substitution for TS" vs. "wire a `pyright` subprocess call behind a new resolver")
- this is where a real `design.md` (dev-architect) starts, not before.
Blocked by: Ticket 3.

## Not yet specified (fog)

- Whether a "build vs adopt" decision for one language should set precedent for all future
  language-specific resolution work, or stay a one-off scoped to whatever Ticket 2 narrows to -
  don't presume a general policy from one language's answer.

## Out of scope

(none yet)
