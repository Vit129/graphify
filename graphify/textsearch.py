"""Exact-text / regex search over the files the graph knows about.

Graph queries match symbol labels and meaning; they cannot find a literal such as an error
message, a config key or a TODO. ``search_text`` fills that gap *inside* graphify: it scans
only the files that have nodes in the graph (so ignore rules and scope match every other
graphify command) and maps each hit to the innermost enclosing symbol, so an agent gets
``file:line  [in function()]`` and can continue with ``explain`` / ``affected``.

ponytail: pure-Python scan of the graph's own file set - fast enough for the corpora graphify
targets; swap in ripgrep per chunk if a single corpus ever needs minutes.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import networkx as nx

MAX_FILE_BYTES = 2_000_000
MAX_LINE_CHARS = 240
_LOC = re.compile(r"L?(\d+)")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def _start_line(data: dict) -> int | None:
    m = _LOC.match(str(data.get("source_location") or ""))
    return int(m.group(1)) if m else None


def _rel(source_file: str) -> str:
    return str(source_file).replace("\\", "/").lstrip("./")


def _graph_files(G: nx.Graph, root: Path, paths: list[str], exclude_paths: list[str]) -> dict[str, Path]:
    """rel path -> absolute path, for graph source files that exist inside ``root``."""
    root = root.resolve()
    found: dict[str, Path] = {}
    for _, data in G.nodes(data=True):
        sf = data.get("source_file")
        if not sf:
            continue
        rel = _rel(sf)
        if rel in found:
            continue
        if paths and not any(rel.startswith(_rel(p)) for p in paths):
            continue
        if exclude_paths and any(rel.startswith(_rel(p)) for p in exclude_paths):
            continue
        p = Path(sf)
        p = p if p.is_absolute() else root / p
        try:
            p = p.resolve()
            p.relative_to(root)
        except (OSError, ValueError):
            continue  # missing, or outside the project root: never read it
        if p.is_file():
            found[rel] = p
    return found


def _ranges_by_file(G: nx.Graph) -> dict[str, list[tuple[int, int, str, str]]]:
    ranges: dict[str, list[tuple[int, int, str, str]]] = {}
    for nid, data in G.nodes(data=True):
        start, end = _start_line(data), data.get("end_line")
        if not data.get("source_file") or start is None or not isinstance(end, int) or end < start:
            continue
        ranges.setdefault(_rel(data["source_file"]), []).append(
            (start, end, str(data.get("label", nid)), str(nid))
        )
    return ranges


def _enclosing(ranges: list[tuple[int, int, str, str]], line: int) -> tuple[str, str] | tuple[None, None]:
    best = None
    for start, end, label, nid in ranges:
        if start <= line <= end and (best is None or end - start < best[1] - best[0]):
            best = (start, end, label, nid)
    return (best[2], best[3]) if best else (None, None)


def _clean(text: str) -> str:
    text = _CONTROL.sub(" ", text.rstrip("\n"))
    return text if len(text) <= MAX_LINE_CHARS else text[: MAX_LINE_CHARS - 1] + "…"


def search_text(
    G: nx.Graph,
    pattern: str,
    *,
    root: Path | str,
    regex: bool = False,
    ignore_case: bool = False,
    paths: list[str] | None = None,
    exclude_paths: list[str] | None = None,
    context: int = 0,
    limit: int = 100,
) -> dict[str, Any]:
    if not pattern:
        raise ValueError("pattern must not be empty")
    if regex:
        try:
            matcher = re.compile(pattern, re.IGNORECASE if ignore_case else 0).search
        except re.error as exc:
            raise ValueError(f"invalid regex: {exc}") from exc
    elif ignore_case:
        needle = pattern.lower()
        matcher = lambda line: needle in line.lower()  # noqa: E731
    else:
        matcher = lambda line: pattern in line  # noqa: E731

    root = Path(root)
    files = _graph_files(G, root, paths or [], exclude_paths or [])
    ranges = _ranges_by_file(G)
    context = max(0, min(int(context), 10))
    limit = max(1, int(limit))
    hits: list[dict[str, Any]] = []
    truncated = False
    searched = 0
    for rel in sorted(files):
        p = files[rel]
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
            raw = p.read_bytes()
        except OSError:
            continue
        if b"\x00" in raw[:4096]:
            continue  # binary
        searched += 1
        lines = raw.decode("utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines):
            if not matcher(line):
                continue
            if len(hits) >= limit:
                truncated = True
                break
            label, nid = _enclosing(ranges.get(rel, []), i + 1)
            hits.append({
                "file": rel,
                "line": i + 1,
                "text": _clean(line),
                "node": label,
                "node_id": nid,
                "before": [_clean(x) for x in lines[max(0, i - context): i]] if context else [],
                "after": [_clean(x) for x in lines[i + 1: i + 1 + context]] if context else [],
            })
        if truncated:
            break
    return {"pattern": pattern, "hits": hits, "files_searched": searched, "truncated": truncated}


def format_text_hits(result: dict[str, Any]) -> str:
    hits = result["hits"]
    if not hits:
        return f"No matches for {result['pattern']!r} in {result['files_searched']} graph file(s)."
    out: list[str] = []
    printed: set[tuple[str, int]] = set()
    last: tuple[str, int] | None = None
    for h in hits:
        block = (
            [(h["line"] - len(h["before"]) + k, f"{h['file']}-{h['line'] - len(h['before']) + k}- {t}")
             for k, t in enumerate(h["before"])]
            + [(h["line"], f"{h['file']}:{h['line']}: {h['text']}" + (f"  [in {h['node']}]" if h["node"] else ""))]
            + [(h["line"] + k, f"{h['file']}-{h['line'] + k}- {t}") for k, t in enumerate(h["after"], start=1)]
        )
        fresh = [(n, line) for n, line in block if (h["file"], n) not in printed]
        if not fresh:
            continue
        has_context = bool(h["before"] or h["after"])
        if last and has_context and (last[0] != h["file"] or fresh[0][0] > last[1] + 1):
            out.append("--")
        for n, line in fresh:
            printed.add((h["file"], n))
            out.append(line)
        last = (h["file"], fresh[-1][0])
    files = len({h["file"] for h in hits})
    out.append(
        f"\n{len(hits)} match(es) in {files} file(s); searched {result['files_searched']} graph file(s)."
        + (" Output capped; raise --limit or narrow --path." if result["truncated"] else "")
    )
    return "\n".join(out)
