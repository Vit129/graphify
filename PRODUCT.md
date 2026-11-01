# Product

graphify turns a project (code, docs, PDFs, images, videos) into a knowledge graph that an AI coding assistant can query instead of grepping through files.

- **Users:** developers who run graphify inside their AI coding assistant (Claude Code, Codex and others listed in README.md) or from the CLI.
- **Outputs:** `graphify-out/` with `GRAPH_REPORT.md` (highlights), `graph.json` (the full graph) and `graph.html` (browser view). Query commands read `graph.json`.
- **Scope of this fork:** a personal fork of safishamsi/graphify, maintained independently. README.md section "What's different from upstream" lists the differences. It is not published to PyPI; install from source.
