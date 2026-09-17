## Skills & Rules

- **Global skills** (`~/.claude/skills/`) — always available every session; pick whichever fits the task.
- **Project-local skills** (`.claude/skills/`, when this repo has any) — check first; these specialize/override the global ones for this repo's own conventions.
- **Global rules** (`~/.claude/rules/`) — behavior/workflow/coding conventions that apply everywhere.
- **Project-local rules** (`rules/`, when this repo has any) — check first; these specialize the global ones for this repo's own domain.

## graphify

This project has a graphify knowledge graph at graphify-out/.

Bug-fix workflow (always run in this order, before opening raw source):
1. `graphify query "<symptom>"` — find the entry point / known-issue already recorded for it
2. `graphify explain "<ClassName/FileName>"` or `graphify affected "<X>"` — see everything that touches it before opening the file
3. Read only the files graphify pointed at

General rules:
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- Read graphify-out/GRAPH_REPORT.md only when query/explain/affected don't surface enough (broad architecture review)
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
