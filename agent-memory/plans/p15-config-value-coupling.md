# P15 — Opt-In Config Value-Coupling Edges (`shares_value`)

Status: **DONE** (2026-07-04) — Phase 0 gate passed with the tightened filter set (~96%),
Phase 1 implemented, Phase 2 verified on the real Home-Assistant corpus. Opt-in via
`graphify.toml` `value_coupling = true` or `extract --value-coupling`. See Phase 0/2 results below.
Priority: **P2** — real gap confirmed on a real repo (Home-Assistant), validated before shipping
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

#### Phase 0 RESULT (2026-07-04, Home-Assistant real corpus, 73 YAML files, worktrees excluded)

Script: throwaway, implemented the 3 plan filters exactly (identifier-shape, hub-cap >5, ≥2 files).

- distinct identifier-shaped values: 326 → 78 coupling (2–5 files) → 215 candidate pairs.
- **As-specified (plan's 3 filters only): ~27% meaningful (8 of a 30-pair even-stride sample) → GATE FAILS.**
  Two noise classes dominate, both admitted by the plan's own filters:
  1. **Service-verb values** — `fan.turn_on`, `switch.turn_on`, `climate.set_temperature`,
     `scene.turn_on`, `input_boolean.turn_off` (11 of 78 values). These are `domain.<service>`
     CALLS, not entity references — they pass the dotted-identifier regex but couple every file
     that performs the same ACTION, which is meaningless.
  2. **Lovelace/UI co-occurrence** — 83 of 215 pairs (39%) touch a `lovelace/` dashboard file.
     A dashboard references every entity it displays, so it couples to every automation touching
     that entity without any operational dependency.
  Plus HA schema keywords (`conditional`, `vertical`, `time_pattern`, `homeassistant`) via the
  long-snake rule (26 of 78 values are keyword/non-dotted).
- **Tightened (+2 filters: exclude `domain.<service_verb>` values; exclude any pair where either
  side is a `lovelace/`/dashboard file): ~96% meaningful (24 of a 25-pair sample) → GATE PASSES.**
  57 candidate pairs survive; the sample is almost entirely real couplings — shared scripts
  (`script.yuki_mode_cleanup` across bedroom/living-room AC + notification), shared presence
  (`device_tracker.*_iphone`, `binary_sensor.*_home_wifi_connected`), shared control switches
  (`switch.navi_power`, `remote.rm4_mini`), and the plan's canonical `input_boolean.home_mode`
  coupling bedroom-AC ↔ home-mode ↔ working-mode.

**Verdict:** the value-coupling IDEA is validated (a corrected filter set hits 96% on real data),
but the plan's SPECIFIED filter set is rejected — it must gain the two extra filters above before
Phase 1. Status advanced to Phase 1 with the tightened filter set as the spec.

Reproduce: `~/.claude/jobs/*/tmp/p15_phase0_validate.py` (throwaway; not committed).

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

#### Phase 2 RESULT (2026-07-04, Home-Assistant real corpus)

- **Default-off guard**: flag off → 0 `shares_value` edges. ✅
- **Canonical case**: `bedroom_ac_management.yaml` and `home_mode.yaml` were UNCONNECTED with the
  flag off (the exact "No path found" bug from the Problem section); with the flag on they connect
  via a 1-hop `shares_value:input_boolean.home_mode` edge. ✅
- **Precision**: 31 distinct coupled values, ALL clean dotted entity/script/scene references,
  0 non-dotted junk survivors — matches the 96% Phase 0 sample. ✅
- **Graph-size delta**: 86 coupling edges added = **+1.6% of the full 5327-edge HA graph** (well
  under the <10% budget). ✅  (Measured naively on the 73-file YAML subgraph in isolation it looked
  like +36%, but the budget is a whole-graph figure and YAML is a small fraction of the real graph.)

**Implementation correction found during Phase 2** (recorded honestly): the first pass emitted the
non-dotted long-snake branch too, which exploded edges +106% and let HA schema keywords through
(`automation`, `binary_sensor`, `brightness`). Root cause: the Phase 0 sample that scored 96% was
measured on **dotted refs only** — the long-snake branch was never validated. Fix: `_resolve_value_coupling`
requires a dot (`domain.entity` shape); `_is_identifier_leaf` still collects long-snake leaves into
the `values` field for possible future use, but they are not coupled. This is the filter the gate
actually passed.

## Risks

- **Noise / false confidence** — mitigated by opt-in + INFERRED + hub cap + identifier filter,
  but Phase 0 is the real mitigation: measure before building.
- **Graph size growth** on config-heavy repos — measure in Phase 2, cap if needed.
- Scope creep toward "real" resolution (Jinja templates, `!include`) — explicitly out of scope;
  those need schema knowledge this tool refuses by design.
