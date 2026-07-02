"""Fish shell extractor. New — .fish files previously had no extractor at
all. No tree-sitter grammar for fish is published on PyPI (checked
tree-sitter-fish, tree-sitter-fish-shell, py-tree-sitter-fish — none
resolve), so this is a hand-rolled scanner, same reasoning as Gherkin:
`function <name>` definitions are a simple, unambiguous line pattern (fish
is not whitespace-sensitive, so a plain regex anchored at the keyword is
reliable without full block/`end` nesting tracking). Comments/`end`/other
block keywords (if/for/while/switch/begin) don't need to be understood for
this — the only extraction target is "what functions does this script
define," matching Gherkin's flat Feature/Scenario granularity rather than a
full parse.
"""
from __future__ import annotations

import re
from pathlib import Path

from graphify.extractors.base import _file_stem, _make_id

_FUNCTION_RE = re.compile(r"^\s*function\s+([A-Za-z0-9_.:-]+)")


def extract_fish(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"nodes": [], "edges": [], "error": str(e)}

    stem = _file_stem(path)
    str_path = str(path)
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_ids: set[str] = set()

    def add_node(nid: str, label: str, line: int) -> None:
        if nid not in seen_ids:
            seen_ids.add(nid)
            nodes.append({"id": nid, "label": label, "file_type": "code",
                          "source_file": str_path, "source_location": f"L{line}"})

    def add_edge(src: str, tgt: str, line: int) -> None:
        edges.append({"source": src, "target": tgt, "relation": "contains",
                       "confidence": "EXTRACTED", "source_file": str_path,
                       "source_location": f"L{line}", "weight": 1.0})

    file_nid = _make_id(str(path))
    add_node(file_nid, path.name, 1)

    for i, raw_line in enumerate(text.splitlines(), start=1):
        m = _FUNCTION_RE.match(raw_line)
        if not m:
            continue
        name = m.group(1)
        nid = _make_id(stem, name)
        add_node(nid, name, i)
        add_edge(file_nid, nid, i)

    return {"nodes": nodes, "edges": edges}
