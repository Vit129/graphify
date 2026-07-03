## graphify

For any question about this repo's architecture, structure, components, or how to add/modify/find
code, your first action should be `graphify query "<question>"` when `graphify-out/graph.json`
exists. Use `graphify path "<A>" "<B>"` for relationship questions and `graphify explain "<ClassName/FileName>"`
for a known symbol/file - name match, not free-form concept search (use `query` for that). These
return a scoped subgraph, usually much smaller than the full report or raw grep output.

Triggers: "how do I…", "where is…", "what does … do", "add/modify a <component>",
"explain the architecture", or anything that depends on how files or classes relate.

If `graphify-out/wiki/index.md` exists, use it for broad navigation. Read `graphify-out/GRAPH_REPORT.md`
only for broad architecture review or when query/path/explain do not surface enough context. Only read
source files when (a) modifying/debugging specific code, (b) the graph lacks the needed detail, or
(c) the graph is missing or stale.

After judging a result useful, a dead end, or wrong, run `graphify save-result --question "Q" --answer "A"
--outcome useful|dead_end|corrected --nodes N1 N2` so future sessions don't re-derive the same dead end;
check `graphify-out/reflections/LESSONS.md` (via `graphify reflect`) at session start for accumulated lessons.

Type `/graphify` in Copilot Chat to build or update the graph.
