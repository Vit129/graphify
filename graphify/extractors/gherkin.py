"""Gherkin (.feature) extractor. New — .feature files previously had no
extractor at all. No tree-sitter grammar exists for Gherkin on PyPI (checked:
neither tree-sitter-gherkin nor tree-sitter-cucumber are published) — but
Gherkin is a simple line-oriented, keyword-prefixed format (unlike CSS/YAML's
real nesting), so a small hand-rolled line scanner covers it without a new
dependency. Each `Feature:` becomes a node; each `Scenario:`/`Scenario
Outline:`/`Background:` under it becomes a child node labeled by its name.
Given/When/Then/And/But steps are left as node content, not separate nodes —
same granularity choice P2 (YAML) and P6 (Robot) made: the searchable unit is
"the scenario", not each individual step line.
"""
from __future__ import annotations

from pathlib import Path

from graphify.extractors.base import _file_stem, _make_id

_SCENARIO_KEYWORDS = ("scenario outline:", "scenario:", "background:")


def extract_gherkin(path: Path) -> dict:
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

    feature_nid: str | None = None
    scenario_counter = 0
    for i, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("@"):
            continue
        lower = line.lower()
        if lower.startswith("feature:"):
            name = line.split(":", 1)[1].strip() or path.name
            feature_nid = _make_id(stem, name)
            add_node(feature_nid, name, i)
            add_edge(file_nid, feature_nid, i)
            continue
        matched_keyword = next((k for k in _SCENARIO_KEYWORDS if lower.startswith(k)), None)
        if matched_keyword is not None:
            parent_nid = feature_nid or file_nid
            name = line.split(":", 1)[1].strip()
            if not name:
                scenario_counter += 1
                name = f"{matched_keyword.rstrip(':')} {scenario_counter}"
            scenario_nid = _make_id(stem, name)
            add_node(scenario_nid, name, i)
            add_edge(parent_nid, scenario_nid, i)

    return {"nodes": nodes, "edges": edges}
