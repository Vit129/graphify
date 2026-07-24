"""YAML extractor (tree-sitter). New — YAML previously had no extractor at
all, so files with this extension were invisible to the graph (P2).

Structural extraction only, matching the plan's scoped-down goal: every
top-level key becomes a node; each item under it (list entries or nested
mapping keys) becomes a child node, labeled by an `alias`/`name`/`id`/
`description` field when present (the common convention in config-as-code
YAML — Home Assistant automations/scripts, GitHub Actions jobs, Kubernetes
resources) so a natural-language query can find a specific entry by what it
does, not just by its position in the file. No deep recursion beyond two
levels and no Jinja2/templating resolution — those are explicitly out of
scope until a real query gap demands them.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from graphify.extractors.base import _file_stem, _make_id, _read_text
from graphify.security import sanitize_metadata

_LABEL_KEYS = ("alias", "name", "id", "description", "summary", "title")

# P15: identifier-shaped leaf values, for opt-in cross-file value-coupling.
# Dotted (`climate.living_room_ac`, `binary_sensor.front_door`) or a long
# snake_case token. Booleans/numbers/short words/prose are excluded by shape.
_DOTTED_ID = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
_LONG_SNAKE = re.compile(r"^[a-z0-9_]{8,}$")


def _is_identifier_leaf(v: str) -> bool:
    if _DOTTED_ID.match(v):
        return True
    return bool(_LONG_SNAKE.match(v) and "." not in v)


def extract_yaml(path: Path) -> dict:
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

    stem = _file_stem(path)
    str_path = str(path)
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_ids: set[str] = set()

    def add_node(nid: str, label: str, line: int, *, node_type: str | None = None,
                 metadata: dict | None = None) -> None:
        if nid not in seen_ids:
            seen_ids.add(nid)
            node = {"id": nid, "label": label, "file_type": "code",
                    "source_file": str_path, "source_location": f"L{line}"}
            if node_type:
                node["type"] = node_type
            if metadata:
                node["metadata"] = sanitize_metadata(metadata)
            nodes.append(node)

    def add_edge(src: str, tgt: str, relation: str, line: int) -> None:
        edges.append({"source": src, "target": tgt, "relation": relation,
                       "confidence": "EXTRACTED", "source_file": str_path,
                       "source_location": f"L{line}", "weight": 1.0})

    file_nid = _make_id(str(path))
    add_node(file_nid, path.name, 1)

    # P15: collect identifier-shaped scalar leaves across the whole tree,
    # attached to the file node (the granularity the value-coupling gate was
    # validated at). Deduped per (value) - first line kept.
    values: list[dict] = []
    seen_values: set[str] = set()

    def _collect_leaves(node) -> None:
        if node is None:
            return
        if node.is_named and not node.children:
            text = _read_text(node, source).strip("'\"").strip()
            if text and text not in seen_values and _is_identifier_leaf(text):
                seen_values.add(text)
                values.append({"value": text, "node_id": file_nid,
                               "source_file": str_path,
                               "line": node.start_point[0] + 1})
            return
        for child in node.children:
            _collect_leaves(child)

    _collect_leaves(root)

    def _unwrap(node):
        """block_mapping_pair's key/value may be wrapped in block_node/
        flow_node layers before reaching the real block_mapping/
        block_sequence/scalar — descend through single-named-child wrappers
        only (never into a mapping/sequence's own children)."""
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
        return _read_text(n, source).strip("'\"")

    def _mapping_pairs(mapping_node):
        """Yield (key_text, value_node_or_None) for each pair in a
        block_mapping, tolerating the ':' punctuation child tree-sitter-yaml
        includes alongside the key/value named children."""
        if mapping_node is None:
            return
        for pair in mapping_node.children:
            if pair.type != "block_mapping_pair":
                continue
            named = [c for c in pair.children if c.is_named]
            if not named:
                continue
            key_text = _scalar_text(named[0])
            value_node = named[1] if len(named) > 1 else None
            yield key_text, value_node, pair.start_point[0] + 1

    def _find_label(mapping_node) -> str | None:
        for key_text, value_node, _line in _mapping_pairs(mapping_node):
            if key_text in _LABEL_KEYS and value_node is not None:
                text = _scalar_text(value_node)
                if text:
                    return text
        return None

    def _find_root_mapping(node):
        cur = node
        while cur is not None and cur.type != "block_mapping":
            named = [c for c in cur.children if c.is_named]
            if not named:
                return None
            cur = named[0]
        return cur

    # A `---`-separated multi-document file (the shape Kubernetes manifests
    # commonly use to bundle several resources in one file) has multiple
    # `document` children under the `stream` root — descending from `root`
    # directly (the old behavior) only ever reached the first one, silently
    # dropping the rest. Iterate documents explicitly; fall back to treating
    # `root` itself as the one document for grammar shapes with no explicit
    # `document` wrapper.
    documents = [c for c in root.children if c.type == "document"]
    if not documents:
        documents = [root]

    for doc_idx, doc in enumerate(documents):
        root_mapping = _find_root_mapping(doc)
        # Disambiguate node IDs across documents only when there's more than
        # one - keeps the single-document ID scheme byte-identical to before
        # (K8s manifests routinely repeat keys like `apiVersion`/`kind`/`spec`
        # across documents in the same file; without this, the second
        # document's nodes would collide into the first's).
        key_stem = stem if len(documents) == 1 else _make_id(stem, str(doc_idx))
        pairs = list(_mapping_pairs(root_mapping))

        # K8s Resource-node typing: additive, layered on top of the generic
        # per-key nodes below (not replacing them) - a document counts as a
        # Kubernetes manifest when both `apiVersion` and `kind` are top-level
        # keys, the same shape check kubectl itself relies on.
        top_level = {k: v for k, v, _line in pairs if k}
        if "apiVersion" in top_level and "kind" in top_level:
            kind_text = _scalar_text(top_level["kind"])
            api_version_text = _scalar_text(top_level["apiVersion"])
            resource_name = None
            metadata_mapping = _unwrap(top_level.get("metadata"))
            if metadata_mapping is not None and metadata_mapping.type == "block_mapping":
                for meta_key, meta_value, _meta_line in _mapping_pairs(metadata_mapping):
                    if meta_key == "name" and meta_value is not None:
                        resource_name = _scalar_text(meta_value)
                        break
            resource_label = f"{kind_text} {resource_name}" if resource_name else kind_text
            resource_line = root_mapping.start_point[0] + 1
            resource_nid = _make_id(key_stem, "resource")
            add_node(resource_nid, resource_label, resource_line, node_type="resource",
                     metadata={"kind": kind_text, "api_version": api_version_text,
                               "name": resource_name})
            add_edge(file_nid, resource_nid, "contains", resource_line)

        for key_text, value_node, line in pairs:
            if not key_text:
                continue
            key_nid = _make_id(key_stem, key_text)
            add_node(key_nid, key_text, line)
            add_edge(file_nid, key_nid, "contains", line)

            child = _unwrap(value_node)
            if child is None:
                continue
            if child.type == "block_sequence":
                for i, item in enumerate(child.children):
                    if item.type != "block_sequence_item":
                        continue
                    item_named = [c for c in item.children if c.is_named]
                    item_value = _unwrap(item_named[0]) if item_named else None
                    label = _find_label(item_value) if item_value and item_value.type == "block_mapping" else None
                    label = label or f"{key_text}[{i}]"
                    item_line = item.start_point[0] + 1
                    item_nid = _make_id(key_nid, str(i))
                    add_node(item_nid, label, item_line)
                    add_edge(key_nid, item_nid, "contains", item_line)
            elif child.type == "block_mapping":
                for sub_key, sub_value, sub_line in _mapping_pairs(child):
                    if not sub_key:
                        continue
                    sub_child = _unwrap(sub_value)
                    label = sub_key
                    if sub_child is not None and sub_child.type == "block_mapping":
                        found = _find_label(sub_child)
                        if found:
                            label = found
                    sub_nid = _make_id(key_nid, sub_key)
                    add_node(sub_nid, label, sub_line)
                    add_edge(key_nid, sub_nid, "contains", sub_line)

    return {"nodes": nodes, "edges": edges, "values": values}
