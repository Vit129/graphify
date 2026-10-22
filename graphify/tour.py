"""Guided reading tour: an ordered "read this first, then that" path through a graph.

Pure graph analysis, no LLM calls. Communities become tour stops; stops are
ordered top-down (callers/importers before the code they depend on) so a new
reader meets entry points first and foundations last.
"""
from __future__ import annotations

from collections import Counter, defaultdict

import networkx as nx

from graphify.analyze import (
    _is_builtin_noise_label,
    _is_concept_node,
    _is_file_node,
    _is_json_key_node,
)


def _is_real_entity(G: nx.Graph, node_id: str) -> bool:
    if _is_file_node(G, node_id) or _is_concept_node(G, node_id) or _is_json_key_node(G, node_id):
        return False
    if _is_builtin_noise_label(G, node_id):
        return False
    return G.nodes[node_id].get("type") not in ("module", "namespace")


def _is_test_path(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return any(p in ("tests", "test", "__tests__") for p in parts[:-1]) or parts[-1].startswith("test_")


def _community_of(G: nx.Graph, node_id: str) -> int | None:
    cid = G.nodes[node_id].get("community")
    return cid if isinstance(cid, int) and cid >= 0 else None


def build_tour(G: nx.Graph, max_steps: int = 8, per_stop: int = 3) -> list[dict]:
    """Return up to max_steps tour stops, ordered from entry points toward foundations.

    Each stop: {step, community, title, size, files, key_nodes, leads_to}.
    Only the max_steps largest communities are kept; they are then ordered by
    the direction of cross-community edges (condensation topological order).
    """
    members: dict[int, list[str]] = defaultdict(list)
    for n in G.nodes():
        cid = _community_of(G, n)
        if cid is not None:
            members[cid].append(n)
    if not members:
        return []

    chosen = sorted(members, key=lambda c: (-len(members[c]), c))[:max_steps]
    chosen_set = set(chosen)

    flow = nx.DiGraph()
    flow.add_nodes_from(chosen)
    weight: Counter = Counter()
    for u, v, data in G.edges(data=True):
        src, tgt = data.get("_src", u), data.get("_tgt", v)
        if src not in G or tgt not in G:
            continue
        cu, cv = _community_of(G, src), _community_of(G, tgt)
        if cu is None or cv is None or cu == cv:
            continue
        if cu in chosen_set and cv in chosen_set:
            weight[(cu, cv)] += 1
    for (cu, cv), w in weight.items():
        flow.add_edge(cu, cv, weight=w)

    size = {c: len(members[c]) for c in chosen}
    cond = nx.condensation(flow)
    order: list[int] = []
    for scc in nx.lexicographical_topological_sort(
        cond, key=lambda s: -sum(size[c] for c in cond.nodes[s]["members"])
    ):
        order.extend(sorted(cond.nodes[scc]["members"], key=lambda c: (-size[c], c)))

    stops = []
    for step, cid in enumerate(order, start=1):
        nodes = members[cid]
        files = Counter(
            f for f in (G.nodes[n].get("source_file") for n in nodes)
            if f and not _is_test_path(f)
        ) or Counter(G.nodes[n].get("source_file") for n in nodes if G.nodes[n].get("source_file"))
        entities = sorted(
            (n for n in nodes if _is_real_entity(G, n)),
            key=lambda n: (-G.degree(n), G.nodes[n].get("label", n)),
        )
        name = next(
            (G.nodes[n].get("community_name") for n in nodes if G.nodes[n].get("community_name")),
            None,
        )
        leads = sorted(flow.successors(cid), key=lambda c: -flow[cid][c]["weight"])
        stops.append({
            "step": step,
            "community": cid,
            "title": name or (
                f"Community {cid} (around {G.nodes[entities[0]].get('label', entities[0])})"
                if entities else f"Community {cid}"
            ),
            "size": len(nodes),
            "files": [f for f, _ in files.most_common(per_stop)],
            "key_nodes": [
                {"label": G.nodes[n].get("label", n), "source_file": G.nodes[n].get("source_file", "")}
                for n in entities[:per_stop]
            ],
            "leads_to": [name_of for name_of in leads],
        })

    titles = {s["community"]: s["title"] for s in stops}
    for s in stops:
        s["leads_to"] = [titles[c] for c in s["leads_to"] if c in titles]
    return stops


def format_tour(stops: list[dict]) -> str:
    if not stops:
        return "No communities found in graph - run `graphify extract` first."
    lines = ["Guided tour - read in this order:", ""]
    for s in stops:
        lines.append(f"{s['step']}. {s['title']} ({s['size']} nodes)")
        if s["files"]:
            lines.append("   start with: " + ", ".join(s["files"]))
        if s["key_nodes"]:
            lines.append("   key concepts: " + ", ".join(k["label"] for k in s["key_nodes"]))
        if s["leads_to"]:
            lines.append("   depends on: " + ", ".join(s["leads_to"][:3]))
        lines.append("")
    return "\n".join(lines).rstrip()
