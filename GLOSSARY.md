# LANGUAGE.md — graphify domain glossary

Terms resolved during interview for: porting IaC indexing and cross-service HTTP linking from competitor tool `codebase-memory-mcp` into graphify. (A third feature, semantic-search fallback, was scoped then dropped as moot — see Decisions recorded below.)

## Terms

**Resource node** — a graph node representing one Kubernetes object (one YAML document within a manifest, keyed by its `kind` + `metadata.name`), distinct from the existing generic YAML structural nodes (`extractors/yaml_.py`) which are key-shaped, not kind-aware. A Resource node is additive: it sits alongside the existing generic nodes for the same file, it does not replace them.

**Module node** — a graph node representing one Kustomize overlay (one `kustomization.yaml`). Connects to the Resource nodes it references via `imports` edges (see below), matching the existing lower-case edge-name convention (`calls`, `contains`, `navigates`).

**http_calls edge** — new edge relation linking an HTTP/webhook call-site (a `fetch()`/`axios`/`google.script.run` invocation, etc.) to the handler that serves it (a route-registration function, or for Google Apps Script specifically a `doGet`/`doPost` function). Confidence is always `INFERRED` (string/URL correlation, not a compiler-verified reference) — never `EXTRACTED`, per the existing two-tier confidence convention (`EXTRACTED` = deterministic AST-derived, `INFERRED` = heuristic/pattern-matched).

**imports edge (Kustomize sense)** — edge from a Module node to the Resource node(s) listed in its `resources:` field. Confidence `EXTRACTED` (deterministic — the path is a literal string in the YAML, no ambiguity to infer).

## Existing terms reused (not redefined)

- **Resource/Module node vs. generic YAML node** — generic nodes from `extractors/yaml_.py` already index every YAML file structurally (top-level key → node, matching alias/name/id fields). Resource/Module nodes are a semantic layer on top, specific to files that are actually Kubernetes/Kustomize manifests (detected by `apiVersion`+`kind` keys, or filename `kustomization.yaml`).
- **EXTRACTED / INFERRED** — existing two-tier confidence values (see `extractors/yaml_.py`'s edge shape), reused as-is for all new edges.

## Conflicts surfaced during interview

- Initial framing assumed IaC indexing was a from-scratch gap. Codebase check found Terraform already fully handled (`extract_terraform`, tree-sitter-hcl) and generic YAML nodes already give baseline K8s visibility. Resolved: real gap narrowed to Dockerfile (zero support, filename-based file with no current detection path) + Kustomize cross-file edges + K8s-kind-aware typing layered on top of existing generic nodes — not a new extraction subsystem.
- HTTP route-linking value confirmed against a real target: My-Investment-Port's React frontend (`fetch`) calling a Google Apps Script backend (`doGet`/`doPost` in `syncLocalStorageToGoogleSheets.gs`) — confirmed zero existing `doGet`/`doPost` handling in `extract.py`, real gap, not a hypothetical framework nobody uses.

## Decisions recorded

- Two items explicitly out of scope for this round, deferred to a separate `wayfinder`-charted multi-session initiative: cross-repo `CROSS_*` edges, LSP-style semantic type resolution. Both require reworking graphify's single-graph-per-instance core assumption or reimplementing a language-server-grade type inference engine — not additive patches.
- **Feature 3 (TF-IDF semantic-search fallback) dropped, not implemented.** The `~/.claude/plans/quizzical-soaring-stream.md` Feature B spec it was based on describes a stale state of `_score_nodes` — the function has since been rewritten to real BM25 (`graphify/query.py:607`, see `agent-memory/knowledge/architecture/feature-provenance.md`'s "Rejected: TF-IDF Fallback Search Tier" for the full reasoning). BM25 strictly supersedes TF-IDF's weighting; neither closes the zero-word-overlap gap only real embeddings would, and that gap was already declined for infra-cost reasons ("Rejected: Full Semantic/Embedding Search", same file). This round proceeds with Features 1 (IaC indexing) and 2 (HTTP linking) only.
