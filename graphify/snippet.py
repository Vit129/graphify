"""Source snippets for graph nodes.

AST nodes carry ``source_location`` (start line) and ``end_line``, so the exact body of a
function/method/class is known. Returning it next to the match saves the extra file Read an
agent otherwise needs after every ``query`` / ``explain``.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import networkx as nx

from graphify.textsearch import _rel, _start_line

DEFAULT_MAX_LINES = 60
_NODE_LINE = re.compile(r"^NODE (?P<label>.+) \[src=(?P<src>.*?) loc=(?P<loc>\S+)")


def _resolve(source_file: str, root: Path) -> Path | None:
    root = root.resolve()
    p = Path(source_file)
    p = p if p.is_absolute() else root / p
    try:
        p = p.resolve()
        p.relative_to(root)
    except (OSError, ValueError):
        return None  # missing, or outside the project root: never read it
    return p if p.is_file() else None


def node_snippet(G: nx.Graph, nid: str, root: Path | str, max_lines: int = DEFAULT_MAX_LINES) -> dict[str, Any] | None:
    """Return ``{file, start, end, node_end, truncated, lines}`` for ``nid`` or None when the node
    has no known line range / its file is unreadable or outside ``root``."""
    d = G.nodes[nid]
    sf, start, end = d.get("source_file"), _start_line(d), d.get("end_line")
    if not sf or start is None or not isinstance(end, int) or end < start:
        return None
    path = _resolve(str(sf), Path(root))
    if path is None:
        return None
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    end = min(end, len(lines))
    if start > end:
        return None
    shown = max(1, int(max_lines))
    last = min(end, start + shown - 1)
    return {
        "file": _rel(str(sf)),
        "start": start,
        "end": last,
        "node_end": end,
        "truncated": last < end,
        "lines": lines[start - 1:last],
    }


def format_snippet(label: str, snip: dict[str, Any]) -> str:
    out = [f"── {label}  {snip['file']}:{snip['start']}-{snip['node_end']}"]
    for n, line in enumerate(snip["lines"], start=snip["start"]):
        out.append(f"{n:>5}| {line}")
    if snip["truncated"]:
        out.append(f"      … {snip['node_end'] - snip['end']} more line(s)")
    return "\n".join(out)


def snippets_for_query_result(
    G: nx.Graph, result_text: str, root: Path | str, limit: int = 3, max_lines: int = DEFAULT_MAX_LINES
) -> str:
    """Snippets for the first ``limit`` code nodes listed in a ``query`` result. File-level nodes are
    skipped (a whole file is never a useful snippet)."""
    from graphify.security import sanitize_label

    index: dict[tuple[str, str, int], str] = {}
    for nid, d in G.nodes(data=True):
        start = _start_line(d)
        if d.get("source_file") and start is not None:
            index.setdefault((sanitize_label(str(d.get("label", nid))), str(d["source_file"]), start), nid)

    blocks: list[str] = []
    seen: set[str] = set()
    for line in result_text.splitlines():
        m = _NODE_LINE.match(line)
        if not m:
            continue
        loc = re.match(r"L?(\d+)", m["loc"])
        if not loc:
            continue
        nid = index.get((m["label"], m["src"], int(loc.group(1))))
        if nid is None or nid in seen:
            continue
        label = str(G.nodes[nid].get("label", nid))
        if label == Path(str(G.nodes[nid].get("source_file", ""))).name:
            continue  # file-level node
        snip = node_snippet(G, nid, root, max_lines)
        if snip is None:
            continue
        seen.add(nid)
        blocks.append(format_snippet(sanitize_label(label), snip))
        if len(blocks) >= limit:
            break
    return "\n\n".join(blocks)
