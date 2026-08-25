# Staleness detection for graphify MCP and query responses
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def find_stale_files(
    graph_path: Path | str,
    source_files: Iterable[str],
    project_root: Path | str | None = None,
) -> list[str]:
    """Return relative paths of source files modified after graph_path was written."""
    gpath = Path(graph_path)
    if not gpath.exists():
        return []
    try:
        graph_mtime = gpath.stat().st_mtime
    except OSError:
        return []

    if project_root is None:
        # Standard layout: <project_root>/graphify-out/graph.json
        if gpath.parent.name == "graphify-out":
            root = gpath.parent.parent
        else:
            root = gpath.parent
    else:
        root = Path(project_root)

    stale: list[str] = []
    seen: set[str] = set()
    for rel_path in source_files:
        if not rel_path or rel_path in seen:
            continue
        seen.add(rel_path)
        file_path = root / rel_path if not os.path.isabs(rel_path) else Path(rel_path)
        try:
            if file_path.exists() and file_path.stat().st_mtime > graph_mtime:
                stale.append(rel_path)
        except OSError:
            continue

    return sorted(stale)


def format_staleness_banner(
    graph_path: Path | str,
    source_files: Iterable[str],
    project_root: Path | str | None = None,
    max_display: int = 3,
) -> str:
    """Return a warning banner string if any source files are stale, else empty string."""
    stale = find_stale_files(graph_path, source_files, project_root)
    if not stale:
        return ""
    displayed = ", ".join(stale[:max_display])
    if len(stale) > max_display:
        displayed += f", ... (+{len(stale) - max_display} more)"
    return (
        f"[graphify staleness notice: {len(stale)} file(s) modified since graph was built ({displayed}). "
        f"Read them directly if recent changes affect your query.]\n\n"
    )
