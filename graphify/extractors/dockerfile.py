"""Dockerfile extractor. New — multi-stage build graphs (stage -> base image /
stage dependencies) were previously invisible to the graph; "Dockerfile" has
no suffix, so `detect.py` never even classified it as CODE. No
tree-sitter-dockerfile grammar published on PyPI (checked), and Dockerfile's
instruction syntax is simple/line-oriented (not whitespace-sensitive, no
nesting) - a hand-rolled scanner is enough, same reasoning as fish.py. Scope:
FROM/AS stage graph + COPY --from= cross-stage dependencies only, not every
instruction - that's the only part with real cross-reference structure worth
graphing.
"""
from __future__ import annotations

import re
from pathlib import Path

from graphify.extractors.base import _file_stem, _make_id

_FROM_RE = re.compile(r"^\s*FROM\s+(\S+)(?:\s+AS\s+(\S+))?\s*$", re.IGNORECASE)
_COPY_FROM_RE = re.compile(r"^\s*COPY\s+(?:--\S+\s+)*--from=(\S+)", re.IGNORECASE)


def is_dockerfile_path(path: Path) -> bool:
    """Dockerfile has no suffix, so `detect.py`/`extract.py`'s suffix-based
    dispatch never sees it - route by filename instead, same convention as
    `is_mcp_config_path`/`is_package_manifest_path`. Covers the common
    multi-variant naming too (`Dockerfile.dev`, `Dockerfile.prod`)."""
    return path.name == "Dockerfile" or path.name.startswith("Dockerfile.")


def extract_dockerfile(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"nodes": [], "edges": [], "error": str(e)}

    stem = _file_stem(path)
    str_path = str(path)
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_ids: set[str] = set()

    def add_node(nid: str, label: str, line: int, *, node_type: str | None = None) -> None:
        if nid not in seen_ids:
            seen_ids.add(nid)
            node = {"id": nid, "label": label, "file_type": "code",
                    "source_file": str_path, "source_location": f"L{line}"}
            if node_type:
                node["type"] = node_type
            nodes.append(node)

    def add_edge(src: str, tgt: str, line: int) -> None:
        edges.append({"source": src, "target": tgt, "relation": "depends_on",
                       "confidence": "EXTRACTED", "source_file": str_path,
                       "source_location": f"L{line}", "weight": 1.0})

    file_nid = _make_id(str(path))
    add_node(file_nid, path.name, 1)

    stage_nid_by_name: dict[str, str] = {}
    stage_nid_by_index: list[str] = []
    current_stage_nid: str | None = None

    def _resolve_base(ref: str, line: int) -> str:
        """A FROM/--from= reference is either a previously-named stage, a
        positional stage index (`--from=0`), or an external registry image -
        only the first two are already graph nodes; an external image gets a
        new, unwalked node (registry contents are out of scope, same "don't
        chase a dependency's internals" pattern used for package manifests)."""
        if ref in stage_nid_by_name:
            return stage_nid_by_name[ref]
        if ref.isdigit():
            idx = int(ref)
            if 0 <= idx < len(stage_nid_by_index):
                return stage_nid_by_index[idx]
        image_nid = _make_id(stem, "image", ref)
        add_node(image_nid, ref, line)
        return image_nid

    for i, raw_line in enumerate(text.splitlines(), start=1):
        m = _FROM_RE.match(raw_line)
        if m:
            base_ref, stage_name = m.group(1), m.group(2)
            idx = len(stage_nid_by_index)
            label = stage_name or f"stage[{idx}]"
            stage_nid = _make_id(stem, "stage", stage_name or str(idx))
            add_node(stage_nid, label, i, node_type="stage")
            stage_nid_by_index.append(stage_nid)
            if stage_name:
                stage_nid_by_name[stage_name] = stage_nid
            base_nid = _resolve_base(base_ref, i)
            if base_nid != stage_nid:
                add_edge(stage_nid, base_nid, i)
            current_stage_nid = stage_nid
            continue

        m = _COPY_FROM_RE.match(raw_line)
        if m and current_stage_nid:
            src_nid = _resolve_base(m.group(1), i)
            if src_nid != current_stage_nid:
                add_edge(current_stage_nid, src_nid, i)

    return {"nodes": nodes, "edges": edges}
