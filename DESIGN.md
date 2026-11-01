# Design

graphify has no graphical UI of its own. The interface is the CLI and the MCP tools, plus the static `graph.html` report it writes.

- **CLI first:** commands print plain text or JSON. Keep output stable so assistants can parse it.
- **Output files are the contract:** `graph.json` and `GRAPH_REPORT.md` are what downstream tools read; changing their shape is a breaking change and needs a version bump.
- **Generated report stays small:** `graph.html` is generated output and is not hand-edited;
