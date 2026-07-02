"""HTML extractor (tree-sitter). New — .html files previously had no
extractor at all. Structural extraction is deliberately narrow: only
elements with an `id` attribute become nodes (label = `#the-id`, matching
the CSS extractor's `#id` convention) — an HTML document commonly has
hundreds of elements, but only the ones with an `id` are the ones a
developer actually references (from CSS, from JS `getElementById`, from a
test's element selector) and searches for by name. Extracting every
`<div>`/`<span>` would be pure noise with no searchability benefit.
"""
from __future__ import annotations

from pathlib import Path

from graphify.extractors.base import _file_stem, _make_id, _read_text


def extract_html(path: Path) -> dict:
    try:
        import tree_sitter_html as tshtml
        from tree_sitter import Language, Parser
    except ImportError:
        return {"nodes": [], "edges": [], "error": "tree_sitter_html not installed"}

    try:
        language = Language(tshtml.language())
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

    def add_node(nid: str, label: str, line: int) -> None:
        if nid not in seen_ids:
            seen_ids.add(nid)
            nodes.append({"id": nid, "label": label, "file_type": "code",
                          "source_file": str_path, "source_location": f"L{line}"})

    def add_edge(src: str, tgt: str, relation: str, line: int) -> None:
        edges.append({"source": src, "target": tgt, "relation": relation,
                       "confidence": "EXTRACTED", "source_file": str_path,
                       "source_location": f"L{line}", "weight": 1.0})

    file_nid = _make_id(str(path))
    add_node(file_nid, path.name, 1)

    def _tag_id(start_tag_node) -> str | None:
        for attr in start_tag_node.children:
            if attr.type != "attribute":
                continue
            name_node = next((c for c in attr.children if c.type == "attribute_name"), None)
            if name_node is None or _read_text(name_node, source) != "id":
                continue
            value_node = next(
                (c for c in attr.children if c.type == "quoted_attribute_value"), None
            )
            if value_node is None:
                continue
            inner = next((c for c in value_node.children if c.type == "attribute_value"), None)
            if inner is not None:
                return _read_text(inner, source)
        return None

    def walk(node) -> None:
        if node.type == "element":
            start_tag = next((c for c in node.children if c.type == "start_tag"), None)
            if start_tag is not None:
                elem_id = _tag_id(start_tag)
                if elem_id:
                    line = node.start_point[0] + 1
                    nid = _make_id(stem, elem_id)
                    add_node(nid, f"#{elem_id}", line)
                    add_edge(file_nid, nid, "contains", line)
        for child in node.children:
            walk(child)

    walk(root)

    return {"nodes": nodes, "edges": edges}
