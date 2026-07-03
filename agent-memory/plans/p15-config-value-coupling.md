# P15 — Opt-In Config Value-Coupling Edges (`shares_value`)

Status: **Planned** — not started
Priority: **P2** — real gap confirmed on a real repo (Home-Assistant), but heuristic is unvalidated; validation gate must pass before any implementation
Owner surface: `graphify/extractors/yaml_.py` (leaf-value collection) + a new cross-file pass in `graphify/extract.py` (precedent: `_resolve_cross_file_csharp_imports`)
Depends on: nothing landed; independent of P16

---

## Problem (evidence, 2026-07-03 dogfooding)

Home Assistant automations couple through shared `entity_id`/`service` string values, not
through anything the AST sees as a call/import. The YAML extractor emits only parent-child
`contains` edges, so two operationally-connected automations have NO graph path:

- `graphify path "home_mode" "AC Arrival Notification"` → **"No path found"** (real repo, real query)
- The bug postmortem doc was reachable only via text match on a curated knowledge doc — the
  actual faulty YAML (`living_room_ac_management.yaml`) never surfaced through graph structure.

## Research grounding (2026-07-03, sourced)

- Terraform resolves `${aws_instance.foo.id}` by **hardcoding HCL's interpolation syntax**.
- kube-linter resolves Deployment→ConfigMap by **hardcoding known k8s field paths** per kind.
- **No production tool resolves identifier coupling across an arbitrary/unknown YAML schema.**
  Hypothesis verified, not assumed. So this plan does NOT attempt reference resolution — it
  ships a schema-agnostic co-occurrence heuristic, explicitly labeled as such.

## Design

A value that looks like an identifier and appears as a leaf in ≥2 documents gets a
low-confidence edge between the containing nodes:
`{relation: "shares_value:<key>", confidence: "INFERRED", weight: 0.3}`.

Filters (all required, to keep precision usable):
1. **Identifier-shaped only**: value matches `^[a-z0-9_]+(\.[a-z0-9_]+)+$` (dotted, e.g.
   `climate.living_room_ac`, `binary_sensor.front_door`) or `^[a-z0-9_]{8,}$` (long snake).
   Excludes booleans, numbers, short words, prose.
2. **Hub cap**: a value appearing in > 5 files gets NO edges (it's a constant, not a reference).
3. **Same-file pairs excluded** (contains edges already cover those).
4. **Off by default**: enabled only via `graphify.toml` → `value_coupling = true` or
   `extract --value-coupling`. Never on implicitly.

Mark the pass with a `ponytail:` ceiling comment: co-occurrence heuristic, not reference
resolution — a shared value proves co-occurrence, not causation.

## Phases (gated — do NOT skip Phase 0)

### Phase 0 — validation gate (throwaway script, no product code)
Write a standalone script that runs the filter rules over Home-Assistant's real YAML corpus
and prints candidate pairs. Manually judge a sample of ≥20 pairs.
**Gate: proceed to Phase 1 only if ≥70% of sampled pairs are meaningful couplings.**
If the gate fails, record the failure numbers here and close the plan as rejected —
that outcome is as valuable as shipping.

### Phase 1 — implementation (only after gate passes)
1. `yaml_.py`: collect `(node_id, key, leaf_value, line)` tuples for identifier-shaped leaves
   (new optional `values` field in the extraction dict; additive, ignored by current consumers).
2. `extract.py`: new `_resolve_value_coupling(extractions)` pass, called only when the config
   flag is on. Emits the edges described above.
3. Config plumbing: `value_coupling` in `load_project_config()` + `--value-coupling` on `extract`.

### Phase 2 — verification
- Unit fixtures: two YAML files sharing `climate.x` → edge; value in 6 files → no edge (hub cap);
  flag off → zero edges (default-behavior regression guard).
- Real repo: rebuild Home-Assistant with the flag on; the exact failing `path` query above must
  return a path through a `shares_value` edge. Also check graph size delta (< +10% edges expected;
  if it explodes, the hub cap is wrong).

## Risks

- **Noise / false confidence** — mitigated by opt-in + INFERRED + hub cap + identifier filter,
  but Phase 0 is the real mitigation: measure before building.
- **Graph size growth** on config-heavy repos — measure in Phase 2, cap if needed.
- Scope creep toward "real" resolution (Jinja templates, `!include`) — explicitly out of scope;
  those need schema knowledge this tool refuses by design.
