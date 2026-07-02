"""TOML extractor (tree-sitter). New — .toml files previously had no
extractor at all. Structural extraction, same granularity choice YAML made:
each `[section]`/`[[array.of.tables]]` header becomes a node labeled by its
dotted key path, plus each root-level `key = value` pair (before any
section) becomes its own node. Individual keys *inside* a section are left
unextracted — same reasoning HTML scoped down to id-attributed elements
only: a section is the unit a developer actually searches for ("database
config"), not each leaf value inside it.

Named with a trailing underscore (`toml_.py`) to avoid shadowing the
`tomli`/`tomllib` ecosystem's own `toml` module name, same convention as
`yaml_.py`.
"""
from __future__ import annotations

from pathlib import Path

from graphify.extractors.base import _file_stem, _make_id, _read_text

_TABLE_TYPES = ("table", "table_array_element")


def extract_toml(path: Path) -> dict:
    try:
        import tree_sitter_toml as tstoml
        from tree_sitter import Language, Parser
    except ImportError:
        return {"nodes": [], "edges": [], "error": "tree_sitter_toml not installed"}

    try:
        language = Language(tstoml.language())
        parser = Parser(language)
        source = path.read_bytes()
        tree = parser.parse(source)
        root = tree.root_node
    except Exception as e:
        return {"nodes": [], "edges": [], "error": str(e)}

    stem = _file_stem(path)
    str_path = str(path)
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_ids: set[str] = set()
    table_counter: dict[str, int] = {}

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

    def _header_text(table_node) -> str:
        for child in table_node.children:
            if child.type in ("bare_key", "dotted_key", "quoted_key"):
                return _read_text(child, source).strip()
        return ""

    for node in root.children:
        line = node.start_point[0] + 1
        if node.type == "pair":
            key_child = next(
                (c for c in node.children if c.type in ("bare_key", "dotted_key", "quoted_key")),
                None,
            )
            if key_child is None:
                continue
            label = _read_text(key_child, source).strip()
            if not label:
                continue
            nid = _make_id(stem, label)
            add_node(nid, label, line)
            add_edge(file_nid, nid, line)
        elif node.type in _TABLE_TYPES:
            label = _header_text(node)
            if not label:
                continue
            # `[[array.of.tables]]` repeats the same dotted key per entry —
            # dedup with a counter so each entry is still a distinct node
            # (same collision fix CSS's nested-rule counter applies).
            table_counter[label] = table_counter.get(label, 0) + 1
            occurrence = table_counter[label]
            nid = _make_id(stem, label) if occurrence == 1 else _make_id(stem, label, str(occurrence))
            add_node(nid, label, line)
            add_edge(file_nid, nid, line)

    return {"nodes": nodes, "edges": edges}
