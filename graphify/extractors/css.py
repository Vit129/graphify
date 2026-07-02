"""CSS extractor (tree-sitter). New — .css files previously had no
extractor at all. Structural extraction: each rule set becomes a node
labeled by its selector text (e.g. `.btn-primary`, `#header .nav-item`),
so a query for a class/id name finds the rule that defines it. Rules
nested inside `@media`/`@supports` blocks are connected through that
block's own node, so a media-query-scoped override is still distinguishable
from the base rule with the same selector.
"""
from __future__ import annotations

from pathlib import Path

from graphify.extractors.base import _file_stem, _make_id, _read_text

_AT_RULE_TYPES = ("media_statement", "supports_statement", "keyframes_statement")


def extract_css(path: Path) -> dict:
    try:
        import tree_sitter_css as tscss
        from tree_sitter import Language, Parser
    except ImportError:
        return {"nodes": [], "edges": [], "error": "tree_sitter_css not installed"}

    try:
        language = Language(tscss.language())
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
    rule_counter = [0]

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

    def _selector_text(rule_set_node) -> str:
        for child in rule_set_node.children:
            if child.type == "selectors":
                return _read_text(child, source).strip()
        return ""

    def _next_rule_nid(parent_nid: str) -> str:
        rule_counter[0] += 1
        return _make_id(parent_nid, f"rule{rule_counter[0]}")

    def walk(node, parent_nid: str) -> None:
        t = node.type
        if t == "rule_set":
            selector = _selector_text(node)
            line = node.start_point[0] + 1
            label = selector or f"rule{rule_counter[0] + 1}"
            nid = _next_rule_nid(parent_nid)
            add_node(nid, label, line)
            add_edge(parent_nid, nid, "contains", line)
            # Nested rule sets (only possible inside @media/@supports blocks
            # here, since plain CSS rule_sets don't nest) still need walking.
            block = next((c for c in node.children if c.type == "block"), None)
            if block is not None:
                for child in block.children:
                    walk(child, nid)
            return
        if t in _AT_RULE_TYPES:
            name_node = next((c for c in node.children if c.type.startswith("@")), None)
            at_name = _read_text(name_node, source) if name_node else "@rule"
            prelude = "".join(
                _read_text(c, source) for c in node.children
                if c.type not in ("block",) and not c.type.startswith("@")
            ).strip()
            label = f"{at_name} {prelude}".strip()
            line = node.start_point[0] + 1
            nid = _next_rule_nid(parent_nid)
            add_node(nid, label, line)
            add_edge(parent_nid, nid, "contains", line)
            block = next((c for c in node.children if c.type == "block"), None)
            if block is not None:
                for child in block.children:
                    walk(child, nid)
            return
        for child in node.children:
            walk(child, parent_nid)

    for child in root.children:
        walk(child, file_nid)

    return {"nodes": nodes, "edges": edges}
