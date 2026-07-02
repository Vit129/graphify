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

    def _resource_imports(settings_node) -> list[tuple[str, int]]:
        """`Resource    path/to/common.resource` settings — the RF mechanism
        for importing keywords defined in another file. `Library` settings
        are skipped: most name an installed package (SeleniumLibrary), not a
        project-relative file, and any that IS a local Python keyword library
        is a .py file already covered by extract_python's own file node."""
        found: list[tuple[str, int]] = []
        for stmt in settings_node.children:
            if stmt.type != "setting_statement":
                continue
            name_child = next((c for c in stmt.children if c.type == "setting_name"), None)
            if name_child is None or _read_text(name_child, source).strip().lower() != "resource":
                continue
            args_child = next((c for c in stmt.children if c.type == "arguments"), None)
            if args_child is None:
                continue
            raw = _read_text(args_child, source).strip()
            if raw:
                found.append((raw, stmt.start_point[0] + 1))
        return found

    def _walk_settings(node) -> None:
        if node.type == "settings_section":
            resource_imports.extend(_resource_imports(node))
            return
        for child in node.children:
            _walk_settings(child)

    resource_imports: list[tuple[str, int]] = []
    _walk_settings(root)
    for raw, line in resource_imports:
        tgt_nid = _make_id(str((path.parent / raw)))
        edges.append({
            "source": file_nid, "target": tgt_nid, "relation": "imports_from",
            "context": "import", "confidence": "EXTRACTED", "source_file": str_path,
            "source_location": f"L{line}", "weight": 1.0,
        })

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
    # Calls to a keyword not defined in this file (imported via `Resource`/
    # `Library`, e.g. from a .resource file) are deferred to the shared
    # cross-file `raw_calls` resolver in extract() rather than dropped — the
    # same mechanism every other language extractor uses. That resolver
    # matches by exact label first, falling back to a case-fold match only
    # for extensions in `_CASE_INSENSITIVE_EXTS` (.robot/.resource included,
    # since Robot Framework keyword names are case-insensitive by spec).
    raw_calls: list[dict] = []
    for caller_nid, invocations in pending_calls:
        seen_pairs: set[str] = set()
        for callee_name, line in invocations:
            tgt_nid = keyword_nid_by_name.get(callee_name.lower())
            if tgt_nid:
                if tgt_nid != caller_nid and tgt_nid not in seen_pairs:
                    seen_pairs.add(tgt_nid)
                    add_edge(caller_nid, tgt_nid, "calls", line)
                continue
            raw_calls.append({
                "caller_nid": caller_nid,
                "callee": callee_name,
                "is_member_call": False,
                "indirect": False,
                "context": "call",
                "source_file": str_path,
                "source_location": f"L{line}",
            })

    return {"nodes": nodes, "edges": edges, "raw_calls": raw_calls}
