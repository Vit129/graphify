# P2 — YAML Extraction Support

Status: **Done** (2026-07-02)
Priority: **P2** — blocks search entirely for any project whose real logic lives in YAML (Home Assistant automations/scripts), not a ranking tweak
Owner surface: extraction pipeline (`graphify/build.py` extractor registration + language dispatch, exact entrypoint TBD — not yet investigated)
Created: 2026-07-01
Depends on: none directly, but should land after P1's ranking fix is confirmed stable

---

## Why

Real-query validation on Home-Assistant (`~/git/personal/Home-Assistant`) for "แก้เปิดแอร์ living room จาก 2 เหลือ 1.5 ชม. โชว์ prompt ถามต่อกี่นาที" found **zero YAML nodes anywhere in the graph** — confirmed via direct inspection of `graphify-out/graph.json`:

```
[('py', 2482), ('md', 466), ('json', 328), ('mjs', 39), ('none', 29), ('sh', 12)]
yaml nodes total: 0
```

`.graphifyignore` does not exclude `packages/` or any YAML paths — this is a genuine extraction-language gap, not a config mistake. The real target file for that query, `packages/living_room_ac/living_room_ac_timers.yaml`, is completely invisible to `graphify query` no matter how the query is phrased. This is unlike P1 (a ranking problem where the target scores low but exists) — here the target doesn't exist in the graph at all.

For a Home Assistant repo, YAML *is* the application logic (automations, scripts, scenes) — Python in this repo is mostly tooling/skills/scaffolding, not the actual home-automation behavior. So this gap likely affects most real developer queries against this project, not just the one tested.

## Non-goals (this plan, until scoped)

- Full YAML semantic understanding (e.g. resolving Jinja2 templates inside HA automations) — start with structural extraction only (keys, anchors, referenced entities) unless a real query gap demands more.
- Extending to other YAML-heavy ecosystems (Kubernetes manifests, GitHub Actions) speculatively — scope to what Home-Assistant's real usage needs first; revisit generalization only if another project surfaces the same gap.

## Scope (not yet investigated — first step before implementation)

1. Confirm whether graphify's extractor pipeline is tree-sitter-based per-language (likely, given `tree-sitter-swift`/`tree-sitter-typescript` etc. show up in `uv tool install` output) and whether a YAML grammar (`tree-sitter-yaml`) is a viable same-pattern addition.
2. Identify the extractor registration/dispatch point in `graphify/build.py` (or wherever language → extractor mapping lives) — mirror however Python/Markdown extraction is wired rather than inventing a new pipeline shape.
3. Decide minimum useful node granularity for HA YAML specifically: top-level automation/script IDs + their `alias`/`description` fields is likely enough to make them findable by label — full key-tree extraction may be unnecessary for search purposes.

## Verification (once implemented)

- Rebuild Home-Assistant's graph, confirm YAML node count > 0.
- Re-run the original failing query and confirm `packages/living_room_ac/living_room_ac_timers.yaml` (or its automation-level node) now surfaces.
- Confirm `uv run pytest -q` stays green and existing non-YAML projects (harness-terminal, My-Investment-Port) are unaffected.

## What's done

- `tree-sitter-yaml==0.7.2` confirmed to have prebuilt wheels (fast install, no
  compile-from-source like `tree-sitter-dm`) — added as a **hard** dependency
  in `pyproject.toml`'s main `dependencies` list, not an optional extra, since
  YAML shows up in nearly every real repo (confirmed: 121 files combined
  across the session's Company/Personal project audit, the single largest
  unsupported-format gap found).
- New `graphify/extractors/yaml_.py` (module named `yaml_` to avoid shadowing
  the stdlib `yaml` package) — self-contained bespoke extractor, following
  `zig.py`'s established template (not `_extract_generic`, since YAML has no
  function/class/call concept to route through the shared config-driven
  walker). Registered in `extractors/__init__.py`'s `LANGUAGE_EXTRACTORS`,
  re-exported from `extract.py`, wired into `_DISPATCH` for both `.yaml` and
  `.yml`.
- Scope matches what this doc's own "Scope" section (item 3) called for:
  each top-level key becomes a node; each item under it (list entries or
  nested mapping keys) becomes a child node, labeled by an
  `alias`/`name`/`id`/`description`/`summary`/`title` field when present,
  falling back to the raw key name or a positional label
  (`automation[0]`) otherwise. No Jinja2 resolution, no unbounded recursion —
  matches the stated non-goals exactly.
- 8 tests in `tests/test_yaml_extraction.py`: top-level key node, list-item
  alias labeling, position-fallback when no label field exists, nested
  mapping labeling (the `timer:` shape), key-fallback when no `name` field
  exists, file->key->item edge chain, empty file produces only the file
  node (no crash), and — the one that actually proves this isn't dead code
  — dispatch through the real `graphify.extract.extract()` entrypoint, not
  just the standalone function in isolation.
- Full suite: 2804 passed, 0 failures (2796 -> 2804, +8 new, zero regressions
  in the other 90 language extractors already registered).
- Real-file validation against the exact file from this doc's original
  investigation (`packages/living_room_ac/living_room_ac_timers.yaml`):
  produces `timer` -> `Living Room AC Cleanup` (using the file's `name:`
  field) — previously 0 nodes for this entire file. Extracted the whole
  Home-Assistant `packages/` directory (9 real YAML files): 21 nodes, 0
  errors, 0.01s. Ran the full search pipeline end-to-end (no changes to
  `serve.py` needed, confirming the "search layer is language-agnostic"
  finding from earlier in the session): query `"living room ac timer"`
  correctly surfaces `Living Room AC Cleanup` as a seed.
