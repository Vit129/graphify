"""Opt-in LSP confirmation of INFERRED call edges (``graphify lsp-resolve``).

Tree-sitter extraction cannot do type resolution, so some ``calls`` edges stay
INFERRED. This module asks a Language Server for the definition at each call
site and either confirms the edge, retargets it, or leaves it alone. The server
command comes only from the CLI flag; server output is treated as untrusted
(only a uri + line is read, and every uri is confined to the project root).
"""

from __future__ import annotations

import json
import os
import queue
import re
import shlex
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from graphify.paths import write_json_atomic
from graphify.security import check_graph_file_size_cap

DEFAULT_SERVERS = {".py": "pyright-langserver --stdio"}
_LANGUAGE_IDS = {".py": "python", ".ts": "typescript", ".tsx": "typescriptreact", ".js": "javascript", ".go": "go", ".rs": "rust"}
_TARGET_RELATIONS = {"calls", "indirect_call"}
_MAX_SOURCE_BYTES = 2_000_000


class LspError(RuntimeError):
    """The language server is missing, died, timed out, or sent garbage."""


class LspClient:
    """Minimal stdio JSON-RPC client (Content-Length framing)."""

    def __init__(self, argv: list[str], root: Path, timeout: float = 15.0):
        self.timeout = timeout
        self.root = root
        self._next_id = 0
        self._inbox: queue.Queue = queue.Queue()
        self._opened: set[str] = set()
        try:
            self._proc = subprocess.Popen(
                argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=str(root),
            )
        except OSError as exc:
            raise LspError(f"could not start language server {argv[0]!r}: {exc}") from exc
        threading.Thread(target=self._read_loop, daemon=True).start()

    # -- framing ----------------------------------------------------------
    def _read_loop(self) -> None:
        out = self._proc.stdout
        try:
            while True:
                length = None
                while True:
                    line = out.readline()
                    if not line:
                        return
                    line = line.strip()
                    if not line:
                        break
                    if line.lower().startswith(b"content-length:"):
                        length = int(line.split(b":", 1)[1])
                if length is None or length < 0 or length > 64 * 1024 * 1024:
                    return
                body = out.read(length)
                if len(body) < length:
                    return
                self._inbox.put(json.loads(body))
        except (ValueError, OSError):
            return
        finally:
            self._inbox.put(None)  # EOF / bad frame sentinel

    def _send(self, msg: dict) -> None:
        body = json.dumps(msg).encode("utf-8")
        try:
            self._proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
            self._proc.stdin.flush()
        except (OSError, ValueError) as exc:
            raise LspError(f"language server connection lost: {exc}") from exc

    def notify(self, method: str, params: dict) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def request(self, method: str, params: dict, timeout: float | None = None) -> Any:
        self._next_id += 1
        rid = self._next_id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.monotonic() + (timeout or self.timeout)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise LspError(f"language server timed out on {method}")
            try:
                msg = self._inbox.get(timeout=remaining)
            except queue.Empty:
                raise LspError(f"language server timed out on {method}") from None
            if msg is None:
                raise LspError("language server exited unexpectedly")
            if not isinstance(msg, dict):
                continue
            if "method" in msg and "id" in msg:
                self._answer_server_request(msg)
            elif msg.get("id") == rid and "method" not in msg:
                if "error" in msg:
                    raise LspError(f"{method} failed: {str(msg['error'])[:200]}")
                return msg.get("result")

    def _answer_server_request(self, msg: dict) -> None:
        # Servers (pyright) ask for config / capability registration; answer
        # neutrally so they never block waiting on us.
        result: Any = None
        if msg.get("method") == "workspace/configuration":
            items = (msg.get("params") or {}).get("items") or []
            result = [None] * len(items)
        self._send({"jsonrpc": "2.0", "id": msg["id"], "result": result})

    # -- lifecycle --------------------------------------------------------
    def initialize(self) -> None:
        self.request(
            "initialize",
            {
                "processId": os.getpid(),
                "rootUri": self.root.as_uri(),
                "workspaceFolders": [{"uri": self.root.as_uri(), "name": self.root.name}],
                "capabilities": {"textDocument": {"definition": {"linkSupport": False}}},
            },
            timeout=max(self.timeout, 30.0),
        )
        self.notify("initialized", {})

    def open_file(self, path: Path, text: str, language_id: str) -> None:
        uri = path.as_uri()
        if uri in self._opened:
            return
        self._opened.add(uri)
        self.notify("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": language_id, "version": 1, "text": text}})

    def definition(self, path: Path, line: int, column: int) -> Any:
        return self.request(
            "textDocument/definition",
            {"textDocument": {"uri": path.as_uri()}, "position": {"line": line, "character": column}},
        )

    def close(self) -> None:
        try:
            if self._proc.poll() is None:
                try:
                    self.request("shutdown", {}, timeout=2.0)
                    self.notify("exit", {})
                except LspError:
                    pass
                try:
                    self._proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    pass
        finally:
            if self._proc.poll() is None:
                self._proc.kill()
                self._proc.wait()
            for stream in (self._proc.stdin, self._proc.stdout):
                try:
                    stream.close()
                except OSError:
                    pass


@dataclass
class Stats:
    examined: int = 0
    confirmed: int = 0
    retargeted: int = 0
    unresolved: int = 0
    external: int = 0
    skipped: int = 0
    aborted: str = ""
    seconds: float = 0.0
    changed: bool = field(default=False, repr=False)


def confine(root: Path, rel: str) -> Path | None:
    """Resolve *rel* under *root*; None if it escapes (or is not a file)."""
    try:
        p = (root / rel).resolve()
        p.relative_to(root)
    except (ValueError, OSError):
        return None
    return p if p.is_file() else None


def _start_line(loc: Any) -> int | None:
    m = re.match(r"L(\d+)", str(loc or ""))
    return int(m.group(1)) if m else None


def callee_name(label: str) -> str:
    """Bare identifier from a node label: ``Foo.bar()`` / ``.bar()`` -> ``bar``."""
    name = str(label).strip()
    if name.endswith("()"):
        name = name[:-2]
    return name.rsplit(".", 1)[-1].strip()


def find_column(line_text: str, name: str, relation: str = "calls") -> int | None:
    """0-based column of *name* on the line, or None unless unambiguous."""
    if not name or not name.isidentifier():
        return None
    hits = [m for m in re.finditer(rf"(?<![\w]){re.escape(name)}(?!\w)", line_text)]
    if relation == "calls" and len(hits) > 1:
        hits = [m for m in hits if re.match(r"\s*\(", line_text[m.end():])]
    return hits[0].start() if len(hits) == 1 else None


def _uri_to_path(uri: str) -> Path | None:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return None
    try:
        return Path(url2pathname(unquote(parsed.path))).resolve()
    except (OSError, ValueError):
        return None


def _definition_site(result: Any) -> tuple[str, int] | None:
    """Reduce a definition result to one (uri, 0-based line), or None if absent/ambiguous."""
    items = result if isinstance(result, list) else [result]
    sites = set()
    for it in items:
        if not isinstance(it, dict):
            continue
        uri = it.get("targetUri") or it.get("uri")
        rng = it.get("targetSelectionRange") or it.get("range")
        try:
            line = int(rng["start"]["line"])
        except (TypeError, KeyError, ValueError):
            continue
        if isinstance(uri, str):
            sites.add((uri, line))
    return next(iter(sites)) if len(sites) == 1 else None


def _caller_callee_keys(edge: dict) -> tuple[str, str]:
    """Edge-dict keys holding the (caller, callee) ids; honours ``_src``/``_tgt``."""
    if "_src" in edge and "_tgt" in edge:
        return "_src", "_tgt"
    return "source", "target"


def resolve_graph(
    data: dict,
    root: Path,
    client: LspClient,
    ext: str = ".py",
    max_edges: int | None = None,
) -> Stats:
    """Confirm/retarget INFERRED call edges in the node-link dict *data*, in place."""
    stats = Stats()
    root = root.resolve()
    nodes = {n["id"]: n for n in data.get("nodes", []) if isinstance(n, dict) and "id" in n}
    by_site: dict[tuple[str, int], list[str]] = {}
    for nid, n in nodes.items():
        ln = _start_line(n.get("source_location"))
        if ln is not None and n.get("source_file"):
            by_site.setdefault((str(n["source_file"]), ln), []).append(nid)
    edges = data.get("links") if "links" in data else data.get("edges", [])
    targets = [
        e for e in edges
        if isinstance(e, dict) and e.get("relation") in _TARGET_RELATIONS and e.get("confidence") == "INFERRED"
        and str(e.get("source_file", "")).endswith(ext) and _start_line(e.get("source_location")) is not None
    ]
    targets.sort(key=lambda e: (str(e["source_file"]), _start_line(e["source_location"])))
    if max_edges is not None and len(targets) > max_edges:
        stats.skipped += len(targets) - max_edges
        targets = targets[:max_edges]
    lang = _LANGUAGE_IDS.get(ext, ext.lstrip("."))
    texts: dict[str, list[str] | None] = {}
    existing = {(e.get(_caller_callee_keys(e)[0]), e.get(_caller_callee_keys(e)[1]), e.get("relation")) for e in edges if isinstance(e, dict)}
    drop: list[dict] = []

    for i, e in enumerate(targets):
        ckey, tkey = _caller_callee_keys(e)
        old_target = e.get(tkey)
        tnode = nodes.get(old_target)
        rel = str(e["source_file"])
        if rel not in texts:
            path = confine(root, rel)
            lines = None
            if path is not None and path.stat().st_size <= _MAX_SOURCE_BYTES:
                try:
                    lines = path.read_text(encoding="utf-8").splitlines()
                except (OSError, UnicodeDecodeError):
                    lines = None
            texts[rel] = lines
        lines = texts[rel]
        lineno = _start_line(e["source_location"])
        if tnode is None or lines is None or not 1 <= lineno <= len(lines):
            stats.skipped += 1
            continue
        col = find_column(lines[lineno - 1], callee_name(tnode.get("label", "")), e["relation"])
        if col is None:
            stats.skipped += 1
            continue
        path = confine(root, rel)
        try:
            client.open_file(path, "\n".join(lines) + "\n", lang)
            result = client.definition(path, lineno - 1, col)
        except LspError as exc:
            stats.aborted = str(exc)
            stats.skipped += len(targets) - i
            break
        stats.examined += 1
        site = _definition_site(result)
        if site is None:
            stats.unresolved += 1
            continue
        dpath = _uri_to_path(site[0])
        try:
            drel = dpath.relative_to(root).as_posix() if dpath else None
        except ValueError:
            drel = None
        if drel is None:
            stats.external += 1
            continue
        cands = by_site.get((drel, site[1] + 1), [])
        cands = [c for c in cands if not str(nodes[c].get("label", "")).endswith(ext)]  # drop file-level nodes
        if len(cands) > 1:
            name = callee_name(tnode.get("label", ""))
            cands = [c for c in cands if callee_name(nodes[c].get("label", "")) == name] or cands
        if len(cands) != 1:
            stats.unresolved += 1
            continue
        new_target = cands[0]
        if new_target == old_target:
            stats.confirmed += 1
        else:
            stats.retargeted += 1
            dup = (e.get(ckey), new_target, e.get("relation"))
            if dup in existing:
                drop.append(e)  # the corrected edge already exists; don't duplicate it
            else:
                existing.add(dup)
                for k in ("source", "target", "_src", "_tgt"):
                    if e.get(k) == old_target:
                        e[k] = new_target
        e["confidence"] = "EXTRACTED"
        e["confidence_score"] = 1.0
        e["resolved_by"] = "lsp"
        stats.changed = True

    if drop:
        ids = {id(e) for e in drop}
        kept = [e for e in edges if id(e) not in ids]
        edges[:] = kept
    return stats


def run(
    graph_path: Path,
    root: Path,
    server: str | None = None,
    ext: str = ".py",
    max_edges: int | None = None,
    timeout: float = 15.0,
    dry_run: bool = False,
) -> Stats:
    """Load the graph, resolve edges via the server, write back atomically."""
    t0 = time.monotonic()
    if not ext.startswith("."):
        ext = "." + ext
    cmd = server or DEFAULT_SERVERS.get(ext)
    if not cmd:
        raise LspError(f"no default language server for {ext!r}; pass --server \"CMD ARGS\"")
    try:
        argv = shlex.split(cmd)
    except ValueError as exc:
        raise LspError(f"cannot parse --server: {exc}") from exc
    if not argv:
        raise LspError("--server is empty")
    exe = shutil.which(argv[0])
    if exe is None:
        raise LspError(f"language server {argv[0]!r} not found on PATH; install it or pass --server \"CMD ARGS\"")
    argv[0] = exe
    root = root.resolve()
    if not root.is_dir():
        raise LspError(f"root is not a directory: {root}")
    if not graph_path.is_file():
        raise LspError(f"graph file not found: {graph_path}")
    check_graph_file_size_cap(graph_path)
    try:
        data = json.loads(graph_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LspError(f"could not read graph: {exc}") from exc

    client = LspClient(argv, root, timeout)
    try:
        try:
            client.initialize()
        except LspError as exc:
            raise LspError(f"language server failed to initialize: {exc}") from exc
        stats = resolve_graph(data, root, client, ext, max_edges)
    finally:
        client.close()
    if stats.changed and not dry_run:
        write_json_atomic(graph_path, data, indent=2)
    stats.seconds = time.monotonic() - t0
    return stats


def format_summary(stats: Stats, dry_run: bool = False) -> str:
    lines = [
        f"lsp-resolve{' (dry run, graph not written)' if dry_run else ''}:",
        f"  examined:   {stats.examined}",
        f"  confirmed:  {stats.confirmed}",
        f"  retargeted: {stats.retargeted}",
        f"  unresolved: {stats.unresolved}",
        f"  external:   {stats.external}",
        f"  skipped:    {stats.skipped}",
        f"  time:       {stats.seconds:.1f}s",
    ]
    if stats.aborted:
        lines.append(f"  stopped early: {stats.aborted} (results so far kept)")
    return "\n".join(lines)
