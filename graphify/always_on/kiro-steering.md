---
inclusion: always
---

graphify: A knowledge graph of this project lives in `graphify-out/`. For codebase, architecture, or dependency questions, when `graphify-out/graph.json` exists, first run `graphify query "<question>"` (or `graphify path "<A>" "<B>"` / `graphify explain "<ClassName/FileName>"` for a known symbol/file - name match, not free-form concept search). These return a scoped subgraph, usually much smaller than `GRAPH_REPORT.md` or raw grep output. Read `GRAPH_REPORT.md` only for broad architecture review or when those commands do not surface enough context. After judging a result useful, a dead end, or wrong, run `graphify save-result --question "Q" --answer "A" --outcome useful|dead_end|corrected --nodes N1 N2` so future sessions don't re-derive the same dead end; check `graphify-out/reflections/LESSONS.md` (via `graphify reflect`) at session start for accumulated lessons.
