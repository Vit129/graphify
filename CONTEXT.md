# Graphify — Domain Language

Codebase knowledge graph generator turning source code and architecture into queryable graphs.

## Language

**Resource node**:
A graph node representing a single Kubernetes or infrastructure object (keyed by `kind` + `metadata.name`), distinct from generic structural YAML nodes.
_Avoid_: K8s config, Manifest item, YAML node

**Module node**:
A graph node representing a Kustomize overlay (`kustomization.yaml`), connecting to referenced Resource nodes via `imports` edges.
_Avoid_: Kustomize package, Component folder

**http_calls edge**:
An inferred graph relation linking an HTTP/webhook call-site (e.g. `fetch()`, `axios`, `doGet`/`doPost`) to its serving handler endpoint. Confidence is always `INFERRED`.
_Avoid_: API link, Network edge, RPC edge

**imports edge**:
A deterministic relation linking a Module node to the Resource nodes listed in its `resources:` field. Confidence is `EXTRACTED`.
_Avoid_: Includes, Dependencies

**EXTRACTED**:
A deterministic AST-derived relationship or node extracted directly by parser grammar with 100% syntactic certainty.
_Avoid_: Static edge, Hardcoded relation

**INFERRED**:
A heuristic, string-correlated, or pattern-matched relationship that cannot be guaranteed by static compiler analysis alone.
_Avoid_: Guessed edge, Dynamic relation

**God Node**:
A central module or symbol with an unusually high degree of inbound/outbound graph dependencies, identified for refactoring or impact analysis.
_Avoid_: Core class, Central file
