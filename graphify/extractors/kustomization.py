"""Kustomize overlay extractor (`kustomization.yaml`/`.yml`). New — the
generic YAML extractor (`extractors/yaml_.py`) already gives structural nodes
for a kustomization file's own keys, but never links it to the manifest files
its `resources:` list actually references — that cross-file relationship is
the whole point of a Kustomize overlay.

Deterministic (`resources:` entries are literal path strings, no ambiguity to
infer), so `imports` edges use confidence EXTRACTED. Resolution is deferred to
a corpus-wide pass (`_resolve_kustomize_imports` in `graphify.extract`,
mirroring the existing `_resolve_value_coupling` pattern) because a single
file's extraction only knows its own constructed path string, not the final
node id the referenced file will get in the assembled graph (ids get remapped
post-extraction - see `_resolve_value_coupling`'s docstring for why this
can't be resolved eagerly).
"""
from __future__ import annotations

from pathlib import Path

from graphify.extractors.base import _make_id


def extract_kustomization(path: Path) -> dict:
    try:
        import tree_sitter_yaml as tsyaml
        from tree_sitter import Language, Parser
    except ImportError:
        return {"nodes": [], "edges": [], "error": "tree_sitter_yaml not installed"}

    try:
        language = Language(tsyaml.language())
        parser = Parser(language)
        source = path.read_bytes()
        tree = parser.parse(source)
        root = tree.root_node
    except Exception as e:
        return {"nodes": [], "edges": [], "error": str(e)}

    str_path = str(path)
    file_nid = _make_id(str_path)
    nodes = [{"id": file_nid, "label": path.name, "file_type": "code",
              "source_file": str_path, "source_location": "L1",
              "type": "module", "metadata": {"kind": "kustomize_overlay"}}]

    def _unwrap(node):
        n = node
        while n is not None and n.type in ("block_node", "flow_node") and n.children:
            named = [c for c in n.children if c.is_named]
            if not named:
                return n
            n = named[0]
        return n

    def _scalar_text(node) -> str:
        n = _unwrap(node)
        if n is None:
            return ""
        return source[n.start_byte:n.end_byte].decode("utf-8", errors="replace").strip("'\"")

    def _find_root_mapping(node):
        cur = node
        while cur is not None and cur.type != "block_mapping":
            named = [c for c in cur.children if c.is_named]
            if not named:
                return None
            cur = named[0]
        return cur

    documents = [c for c in root.children if c.type == "document"]
    if not documents:
        documents = [root]

    kustomize_targets: list[dict] = []
    for doc in documents:
        root_mapping = _find_root_mapping(doc)
        if root_mapping is None:
            continue
        for pair in root_mapping.children:
            if pair.type != "block_mapping_pair":
                continue
            named = [c for c in pair.children if c.is_named]
            if len(named) < 2:
                continue
            key_text = _scalar_text(named[0])
            if key_text != "resources":
                continue
            value = _unwrap(named[1])
            if value is None or value.type != "block_sequence":
                continue
            for item in value.children:
                if item.type != "block_sequence_item":
                    continue
                item_named = [c for c in item.children if c.is_named]
                if not item_named:
                    continue
                entry = _scalar_text(item_named[0])
                if not entry:
                    continue
                target_path = path.parent / entry
                kustomize_targets.append({
                    "target_path": str(target_path),
                    "source_file": str_path,
                    "line": item.start_point[0] + 1,
                })

    return {"nodes": nodes, "edges": [], "kustomize_targets": kustomize_targets}
