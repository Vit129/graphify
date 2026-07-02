"""Robot Framework extractor (tree-sitter). New — .robot files previously
had no extractor at all, so entire test suites were invisible to the graph
(P6). Grammar quirk: tree-sitter-robot's nodes don't expose usable
`child_by_field_name` results for the fields this extractor needs (verified
empirically), so children are matched by `.type` throughout, same as the
non-field-based branches in zig.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from graphify.extractors.base import _file_stem, _make_id, _read_text


def extract_robot(path: Path) -> dict:
    try:
        import tree_sitter_robot as tsrobot
        from tree_sitter import Language, Parser
    except ImportError:
        return {"nodes": [], "edges": [], "error": "tree_sitter_robot not installed"}

    try:
        language = Language(tsrobot.language())
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

    def _name_text(def_node) -> str:
        """A test_case_definition / keyword_definition's `name` child holds
        the human-readable name across one or more `name_chunk` pieces —
        concatenate rather than assume a single chunk (long names can wrap)."""
        for child in def_node.children:
            if child.type == "name":
                return _read_text(child, source).strip()
        return ""

    def _find_invoked_keywords(body_node) -> list[tuple[str, int]]:
        """Every `keyword_invocation`'s callee name inside a definition's
        body, so a test case/keyword calling a locally-defined keyword gets
        a `calls` edge — same value as tracking function calls in any other
        language extractor."""
        found: list[tuple[str, int]] = []

        def _walk(node) -> None:
            if node.type == "keyword_invocation":
                for child in node.children:
                    if child.type == "keyword":
                        found.append((_read_text(child, source).strip(),
                                       node.start_point[0] + 1))
                        break
            for child in node.children:
                _walk(child)

        _walk(body_node)
        return found

    # Pass 1: definitions (test cases + user-defined keywords) become nodes.
    # keyword_nid_by_name lets pass 2 resolve calls to locally-defined
    # keywords without a second full tree walk.
    keyword_nid_by_name: dict[str, str] = {}
    pending_calls: list[tuple[str, list[tuple[str, int]]]] = []

    def walk(node) -> None:
        t = node.type
        if t == "test_case_definition":
            name = _name_text(node)
            if name:
                line = node.start_point[0] + 1
                nid = _make_id(stem, name)
                add_node(nid, name, line)
                add_edge(file_nid, nid, "contains", line)
                body = next((c for c in node.children if c.type == "body"), None)
                if body is not None:
                    pending_calls.append((nid, _find_invoked_keywords(body)))
            return
        if t == "keyword_definition":
            name = _name_text(node)
            if name:
                line = node.start_point[0] + 1
                nid = _make_id(stem, name)
                add_node(nid, name, line)
                add_edge(file_nid, nid, "contains", line)
                keyword_nid_by_name[name.lower()] = nid
                body = next((c for c in node.children if c.type == "body"), None)
                if body is not None:
                    pending_calls.append((nid, _find_invoked_keywords(body)))
            return
        for child in node.children:
            walk(child)

    walk(root)

    # Pass 2: resolve calls now that every locally-defined keyword has a nid.
    # Calls to built-in/library keywords (no matching local definition) are
    # dropped rather than fabricating a phantom node — same convention as
    # every other extractor's cross-file call resolution.
    for caller_nid, invocations in pending_calls:
        seen_pairs: set[str] = set()
        for callee_name, line in invocations:
            tgt_nid = keyword_nid_by_name.get(callee_name.lower())
            if tgt_nid and tgt_nid != caller_nid and tgt_nid not in seen_pairs:
                seen_pairs.add(tgt_nid)
                add_edge(caller_nid, tgt_nid, "calls", line)

    return {"nodes": nodes, "edges": edges}
