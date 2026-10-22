"""Onboarding guide: one markdown page for someone new to the codebase.

Assembled from existing graph analysis (layers, entry points, tour, god nodes,
cross-community couplers). No LLM.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

from graphify.analyze import cross_cutting_nodes, god_nodes
from graphify.layers import detect_layers
from graphify.tour import build_tour, find_entry_points


def _communities(G: nx.Graph) -> dict[int, list[str]]:
    out: dict[int, list[str]] = defaultdict(list)
    for n, data in G.nodes(data=True):
        cid = data.get("community")
        if isinstance(cid, int) and cid >= 0:
            out[cid].append(n)
    return dict(out)


def build_onboarding(
    G: nx.Graph,
    project_name: str = "this project",
    max_steps: int = 8,
    descriptions: dict[str, str] | None = None,
) -> str:
    """`descriptions` is the optional output of `graphify describe` (load_descriptions); None = unchanged output."""
    descriptions = descriptions or {}
    files = {d["source_file"] for _, d in G.nodes(data=True) if d.get("source_file")}
    exts = Counter(Path(f).suffix.lower() for f in files if Path(f).suffix)
    lines = [f"# Onboarding: {project_name}", ""]
    lines += [
        "## Overview",
        f"- {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(files)} files",
        "- File types: " + (", ".join(f"{e} ({n})" for e, n in exts.most_common(6)) or "n/a"),
        "",
    ]

    entries = find_entry_points(G)
    if entries:
        lines += ["## Start here", *[f"- `{e['source_file']}`" for e in entries], ""]

    layers = detect_layers(G)
    if layers:
        lines += ["## Architecture layers", "Grouped by directory names (heuristic).", ""]
        for layer in layers:
            lines.append(f"- **{layer['name']}**: {layer['description']} ({layer['node_count']} nodes)")
            if layer["files"]:
                lines.append("  - e.g. " + ", ".join(f"`{f}`" for f in layer["files"][:3]))
        lines.append("")

    stops = build_tour(G, max_steps=max_steps)
    if stops:
        lines += ["## Guided tour", "Read in this order; entry points first, foundations last.", ""]
        for s in stops:
            lines.append(f"{s['step']}. **{s['title']}** ({s['size']} nodes)")
            desc = descriptions.get(f"community:{s['community']}")
            if desc:
                lines.append(f"   - {desc}")
            if s["files"]:
                lines.append("   - start with: " + ", ".join(f"`{f}`" for f in s["files"]))
            if s["key_nodes"]:
                lines.append("   - key concepts: " + ", ".join(f"`{k['label']}`" for k in s["key_nodes"]))
            if s["leads_to"]:
                lines.append("   - depends on: " + ", ".join(s["leads_to"][:3]))
        lines.append("")

    try:
        core = god_nodes(G, top_n=8, by="pagerank")
    except ImportError:
        core = god_nodes(G, top_n=8)
    if core:
        lines += ["## Core abstractions", "Most central nodes in the graph.", ""]
        for c in core:
            lines.append(f"- `{c['label']}` (degree {c['degree']})")
            desc = descriptions.get(f"node:{c['id']}")
            if desc:
                lines.append(f"  - {desc}")
        lines.append("")

    couplers = cross_cutting_nodes(G, _communities(G), top_n=5)
    if couplers:
        lines += ["## Careful here", "These couple many parts of the code; changes ripple widely.", ""]
        lines += [f"- `{c['label']}` bridges {c['communities_bridged']} communities" for c in couplers]
        lines.append("")

    lines += [
        "## Next steps",
        "- `graphify query \"<question>\"` to ask about any area",
        "- `graphify explain \"<Name>\"` for one symbol and its neighbours",
        "- `graphify affected \"<Name>\"` before changing something",
        "",
    ]
    return "\n".join(lines)
