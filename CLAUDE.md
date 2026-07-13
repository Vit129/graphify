## graphify

Project got graphify knowledge graph at graphify-out/.

Bug-fix workflow (always run this order, before open raw source):
1. `graphify query "<symptom>"` — find entry point / known-issue already recorded
2. `graphify explain "<ClassName/FileName>"` or `graphify affected "<X>"` — see everything touch it before open file
3. Read only files graphify pointed at

General rules:
- graphify-out/wiki/index.md exist → navigate it instead raw files
- Read graphify-out/GRAPH_REPORT.md only when query/explain/affected not enough (broad architecture review)
- After modify code files this session, run `graphify update .` keep graph current (AST-only, no API cost)