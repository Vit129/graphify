# Cross-language bridge resolution (Swift <-> ObjC, React Native / Expo Native Modules)
from __future__ import annotations

import bisect
import re
from pathlib import Path
import networkx as nx


def _read_source(cache: dict[str, str | None], root: str | None, source_file: str) -> str | None:
    if source_file in cache:
        return cache[source_file]
    candidates = []
    if root:
        candidates.append(Path(root) / source_file)
    candidates.append(Path(source_file))
    text: str | None = None
    for candidate in candidates:
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
            break
        except OSError:
            continue
    cache[source_file] = text
    return text


def resolve_cross_language_bridges(G: nx.Graph, root: str | None = None) -> int:
    """Detect and link cross-language bridges (React Native, Expo, Swift <-> ObjC).

    Node labels are bare symbol names (e.g. "trackEvent()"), never source text --
    they never contain "@objc"/"RCT_EXPORT_MODULE(...)"/"NativeModules.X". Bridge
    patterns only ever appear in the real file content, so this reads each
    relevant file's source text (relative to ``root`` when given) and anchors
    each match back to the nearest graph node at or before that line (same
    nearest-preceding-line approach graphify.affected.changed_seeds uses).

    ponytail: symbol matching on the ObjC/RN sides is name-based, not a real
    cross-language type resolver -- a generic name reused unrelated to the
    actual bridge (e.g. two different classes both called "Bridge") can still
    false-link. Word-boundary anchored against real source keeps this far
    tighter than the old unanchored label-substring check, but it is not a
    ceiling this module tries to remove; a real fix needs semantic symbol
    resolution, out of scope here.

    Returns the number of bridge edges added.
    """
    added_edges = 0
    source_cache: dict[str, str | None] = {}

    # source_file -> [(line, node_id), ...] sorted, and source_file -> its L1
    # file-level node id, for anchoring a source-text match to a real node.
    nodes_by_file: dict[str, list[tuple[int, str]]] = {}
    file_node: dict[str, str] = {}
    files_by_ext: dict[str, set[str]] = {}
    for nid, d in G.nodes(data=True):
        source_file = d.get("source_file")
        if not source_file:
            continue
        source_file = str(source_file)
        ext = Path(source_file.lower()).suffix
        files_by_ext.setdefault(ext, set()).add(source_file)
        loc = d.get("source_location")
        if str(loc) == "L1":
            file_node.setdefault(source_file, nid)
        m = re.match(r"^L(\d+)", str(loc or ""))
        if m:
            nodes_by_file.setdefault(source_file, []).append((int(m.group(1)), nid))
    for entries in nodes_by_file.values():
        entries.sort(key=lambda t: t[0])

    def nearest_node(source_file: str, line: int) -> str | None:
        entries = nodes_by_file.get(source_file)
        if entries:
            lines = [entry[0] for entry in entries]
            idx = bisect.bisect_right(lines, line) - 1
            if idx >= 0:
                return entries[idx][1]
        return file_node.get(source_file)

    def line_of(text: str, pos: int) -> int:
        return text.count("\n", 0, pos) + 1

    swift_files = files_by_ext.get(".swift", set())
    objc_files = files_by_ext.get(".m", set()) | files_by_ext.get(".mm", set()) | files_by_ext.get(".h", set())
    kt_java_files = files_by_ext.get(".kt", set()) | files_by_ext.get(".java", set())
    js_ts_files = (
        files_by_ext.get(".js", set()) | files_by_ext.get(".jsx", set())
        | files_by_ext.get(".ts", set()) | files_by_ext.get(".tsx", set())
    )

    # 1. Collect declarations from real source text.
    objc_symbols: dict[str, str] = {}   # Swift @objc symbol name -> node id
    native_modules: dict[str, str] = {}  # module name -> node id (file-level)
    native_methods: dict[tuple[str, str], str] = {}  # (module stem, method) -> node id

    objc_decl_re = re.compile(
        r"@objc\b[^\n]*\n?\s*(?:public|private|internal|fileprivate|final|override|static|class)?\s*"
        r"(?:class|struct|enum|protocol|func|var|let)\s+([A-Za-z_][A-Za-z0-9_]*)"
    )
    for source_file in swift_files:
        text = _read_source(source_cache, root, source_file)
        if not text:
            continue
        for match in objc_decl_re.finditer(text):
            nid = nearest_node(source_file, line_of(text, match.start()))
            if nid:
                objc_symbols[match.group(1)] = nid

    rct_module_re = re.compile(r"RCT_EXPORT_MODULE\s*\(\s*([A-Za-z0-9_]*)\s*\)")
    rct_method_re = re.compile(r"RCT_EXPORT_METHOD\s*\(\s*([A-Za-z0-9_]+)")
    for source_file in objc_files:
        text = _read_source(source_cache, root, source_file)
        if not text:
            continue
        stem = Path(source_file).stem
        for match in rct_module_re.finditer(text):
            mod_name = match.group(1) or stem
            nid = file_node.get(source_file) or nearest_node(source_file, line_of(text, match.start()))
            if nid:
                native_modules[mod_name] = nid
        for match in rct_method_re.finditer(text):
            nid = nearest_node(source_file, line_of(text, match.start()))
            if nid:
                native_methods[(stem, match.group(1))] = nid

    react_module_re = re.compile(r"\bReactContextBaseJavaModule\b|:\s*NativeModule\b")
    react_method_re = re.compile(
        r"@ReactMethod\b[^\n]*\n?\s*(?:public|private|internal|fun|void|override)?\s*"
        r"(?:fun\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\("
    )
    for source_file in kt_java_files:
        text = _read_source(source_cache, root, source_file)
        if not text:
            continue
        stem = Path(source_file).stem
        module_match = react_module_re.search(text)
        if module_match:
            nid = file_node.get(source_file)
            if nid:
                native_modules[stem] = nid
        for match in react_method_re.finditer(text):
            nid = nearest_node(source_file, line_of(text, match.start()))
            if nid:
                native_methods[(stem, match.group(1))] = nid

    # 2. Match callers against those declarations, from real source text.
    rn_call_re = re.compile(
        r"""(?:NativeModules\.|requireNativeModule\(\s*['"`]|requireNativeComponent\(\s*['"`])([A-Za-z0-9_]+)"""
    )
    for source_file in js_ts_files:
        text = _read_source(source_cache, root, source_file)
        if not text:
            continue
        for match in rn_call_re.finditer(text):
            target_nid = native_modules.get(match.group(1))
            if not target_nid:
                continue
            caller_nid = nearest_node(source_file, line_of(text, match.start()))
            if caller_nid and caller_nid != target_nid and not G.has_edge(caller_nid, target_nid):
                G.add_edge(
                    caller_nid, target_nid,
                    relation="bridges_to", confidence="EXTRACTED", context="react_native_bridge",
                    _src=caller_nid, _tgt=target_nid,
                )
                added_edges += 1

    if objc_symbols:
        symbol_re = re.compile(
            r"\b(" + "|".join(re.escape(name) for name in objc_symbols) + r")\b"
        )
        for source_file in objc_files:
            text = _read_source(source_cache, root, source_file)
            if not text:
                continue
            for match in symbol_re.finditer(text):
                target_nid = objc_symbols[match.group(1)]
                caller_nid = nearest_node(source_file, line_of(text, match.start()))
                if caller_nid and caller_nid != target_nid and not G.has_edge(caller_nid, target_nid):
                    G.add_edge(
                        caller_nid, target_nid,
                        relation="bridges_to", confidence="EXTRACTED", context="objc_bridge",
                        _src=caller_nid, _tgt=target_nid,
                    )
                    added_edges += 1

    return added_edges
