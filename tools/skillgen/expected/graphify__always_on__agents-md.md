## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<ClassName/FileName>"` for a known symbol/file (name match, not free-form concept search - use `query` for that). These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output. Find through graphify first: `graphify grep "<text>"` for exact text/regex (each hit shows its enclosing symbol), `--snippet` on `query`/`explain` to get the source without a separate file read, `graphify affected "<X>"` / `affected --git-diff` before changing a symbol, and `graphify flow "<fn>" --param p --to "<sink regex>"` to see where a Python parameter flows. Use raw grep/find only to confirm that a caller list is exhaustive before changing a signature (the graph can miss dynamic or attribute calls) or for files graphify does not index, and say so.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- After judging a query/path/explain result useful, a dead end, or wrong, run `graphify save-result --question "Q" --answer "A" --outcome useful|dead_end|corrected --nodes N1 N2` - this accumulates across sessions so the same dead end or vocabulary mismatch isn't re-derived every time. At the start of a session, check `graphify-out/reflections/LESSONS.md` if it exists (built via `graphify reflect`) for preferred sources, known dead ends, and past corrections.
