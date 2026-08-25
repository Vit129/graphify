from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import bisect
import re
import subprocess
import unicodedata

import networkx as nx


DEFAULT_AFFECTED_RELATIONS = (
    "calls",
    "indirect_call",
    "references",
    "imports",
    "imports_from",
    "re_exports",
    "inherits",
    "extends",
    "implements",
    "uses",
    "mixes_in",
    "embeds",
)


@dataclass(frozen=True)
class AffectedHit:
    node_id: str
    depth: int
    via_relation: str


def _node_label(graph: nx.Graph, node_id: str) -> str:
    data = graph.nodes[node_id]
    return str(data.get("label") or node_id)


def _format_location(data: dict) -> str:
    source_file = data.get("source_file") or "-"
    source_location = data.get("source_location")
    if source_location:
        return f"{source_file}:{source_location}"
    return str(source_file)


def _bare_name(label: str) -> str:
    """Lowercased label with the callable decoration (trailing "()") removed."""
    label = _normalize_label(label)
    return label[:-2] if label.endswith("()") else label


def _normalize_label(label: str) -> str:
    return unicodedata.normalize("NFC", label).casefold()


def _prefer_file_node(
    graph: nx.Graph,
    node_ids: list[str],
    query: str,
) -> str | None:
    """Return the file-level node when a source_file query matches many nodes."""
    query_basename = _normalize_label(Path(query).name)
    exact_file_nodes = [
        node_id
        for node_id in node_ids
        if str(graph.nodes[node_id].get("source_location", "")) == "L1"
        and _normalize_label(str(graph.nodes[node_id].get("label", ""))) == query_basename
    ]
    if len(exact_file_nodes) == 1:
        return exact_file_nodes[0]

    l1_nodes = [
        node_id
        for node_id in node_ids
        if str(graph.nodes[node_id].get("source_location", "")) == "L1"
    ]
    if len(l1_nodes) == 1:
        return l1_nodes[0]

    basename_nodes = [
        node_id
        for node_id in node_ids
        if _normalize_label(str(graph.nodes[node_id].get("label", ""))) == query_basename
    ]
    if len(basename_nodes) == 1:
        return basename_nodes[0]

    return None


def resolve_seed(graph: nx.Graph, query: str) -> str | None:
    # A trailing path separator must not change a source-file match — serve's
    # _find_node tokenizes the path (which drops it), so strip it here for parity
    # (otherwise `affected "src/x.ts/"` returned None while `explain` resolved it).
    query = query.rstrip("/\\") or query
    if query in graph:
        return query
    query_lower = _normalize_label(query)
    exact_label_matches = [
        str(node_id)
        for node_id, data in graph.nodes(data=True)
        if _normalize_label(str(data.get("label", ""))) == query_lower
    ]
    if len(exact_label_matches) == 1:
        return exact_label_matches[0]
    # Callable labels are decorated ("name()"), so a bare "name" query falls
    # through exact matching and then ties with any "name*" sibling in the
    # contains pass. Match on the undecorated name before giving up.
    query_bare = _bare_name(query_lower)
    bare_name_matches = [
        str(node_id)
        for node_id, data in graph.nodes(data=True)
        if _bare_name(str(data.get("label", ""))) == query_bare
    ]
    if len(bare_name_matches) == 1:
        return bare_name_matches[0]
    exact_source_matches = [
        str(node_id)
        for node_id, data in graph.nodes(data=True)
        if _normalize_label(str(data.get("source_file", ""))) == query_lower
    ]
    if len(exact_source_matches) == 1:
        return exact_source_matches[0]
    if exact_source_matches:
        preferred_file_node = _prefer_file_node(graph, exact_source_matches, query)
        if preferred_file_node is not None:
            return preferred_file_node
    contains_matches = [
        str(node_id)
        for node_id, data in graph.nodes(data=True)
        if query_lower in _normalize_label(str(data.get("label", "")))
    ]
    if len(contains_matches) == 1:
        return contains_matches[0]
    return _bm25_confident_pick(graph, query)


def _bm25_confident_pick(graph: nx.Graph, query: str) -> str | None:
    """Last-resort tier: the same cross-field BM25 ranking query/explain/path
    already use (query.py's _score_nodes), for names none of the strict
    single-field tiers above could assemble a unique winner for - either a
    qualified cross-field name (class in source_file, method in label) no
    single field spans, or a raw substring count that looked ambiguous
    (several nodes happen to contain the term) even though relevance scoring
    clearly separates one from the rest.

    Only returns a pick when the top score clearly separates from the next
    (same 10% gap threshold find_path_with_disambiguation uses) - a genuine
    near-tie still returns None here, same as every tier above. This adds a
    case strict counting can't see, it does not turn a real ambiguity into a
    silent guess.
    """
    from graphify.query import _score_nodes  # local: avoid import-time cost when affected isn't used

    scored = _score_nodes(graph, [query])
    if not scored:
        return None
    top = scored[0][0]
    if top <= 0:
        return None
    near_tied = [nid for score, nid in scored if (top - score) / top < 0.10]
    return near_tied[0] if len(near_tied) == 1 else None


def affected_nodes(
    graph: nx.Graph,
    seed: str,
    *,
    relations: Iterable[str] = DEFAULT_AFFECTED_RELATIONS,
    depth: int = 2,
) -> list[AffectedHit]:
    relation_set = set(relations)
    # Parameterized relations (P15's shares_value:<value>-style labels) can't be passed
    # exact-value in advance, so a bare filter (no ':') also prefix-matches relation:*.
    relation_prefixes = tuple(f"{r}:" for r in relation_set if ":" not in r)
    seen = {seed}
    queue: deque[tuple[str, int]] = deque([(seed, 0)])
    hits: list[AffectedHit] = []

    while queue:
        current, current_depth = queue.popleft()
        if current_depth >= depth:
            continue
        incoming: list[tuple[str, str, dict]] = []
        if hasattr(graph, "in_edges"):
            for u, v, data in graph.in_edges(current, data=True):
                if data.get("_src", u) == u:
                    incoming.append((u, v, data))
            for u, v, data in graph.out_edges(current, data=True):
                if data.get("_src", u) != u:
                    incoming.append((v, u, data))
        else:
            for source, target, data in graph.edges(data=True):
                if data.get("_src", source) == source:
                    if target == current:
                        incoming.append((source, target, data))
                else:
                    if source == current:
                        incoming.append((target, source, data))
        for source, _target, data in incoming:
            relation = str(data.get("relation", ""))
            if relation not in relation_set and not relation.startswith(relation_prefixes):
                continue
            source = str(source)
            if source in seen:
                continue
            seen.add(source)
            hit = AffectedHit(source, current_depth + 1, relation)
            hits.append(hit)
            queue.append((source, current_depth + 1))

    return hits


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _parse_git_diff_hunks(diff_output: str) -> dict[str, list[tuple[int, int]]]:
    """Parse `git diff --unified=0` output into {file: [(start_line, end_line), ...]}
    on the new-file side (matching line numbers in the currently checked-out tree,
    which is what the graph was built from)."""
    changed: dict[str, list[tuple[int, int]]] = {}
    current_file: str | None = None
    for line in diff_output.splitlines():
        if line.startswith("+++ "):
            path = line[4:]
            current_file = None if path == "/dev/null" else path[2:]  # strip "b/" prefix
            continue
        m = _HUNK_RE.match(line)
        if m and current_file:
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) is not None else 1
            if count == 0:
                # Pure deletion on the new side has no new-file lines to map;
                # anchor on the line the deletion happened after so it still
                # attributes to the right symbol.
                count = 1
            changed.setdefault(current_file, []).append((start, start + count - 1))
    return changed


def git_diff_changed_ranges(
    repo_root: Path, base: str | None = None
) -> dict[str, list[tuple[int, int]]]:
    """Run `git diff` in repo_root and return changed line ranges per file.

    ``base`` is the ref to diff against (default: working tree vs HEAD, i.e.
    uncommitted changes — staged and unstaged).
    """
    cmd = ["git", "diff", "--unified=0"]
    if base:
        cmd.append(base)
    result = subprocess.run(
        cmd, cwd=str(repo_root), capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr.strip()}")
    return _parse_git_diff_hunks(result.stdout)


_RATIONALE_LIKE_FILE_TYPES = frozenset({"rationale", "document"})


def _nodes_by_file(graph: nx.Graph) -> dict[str, list[tuple[int, str]]]:
    """{source_file: [(line, node_id), ...]} sorted ascending, for nodes with a
    parseable single-line source_location (the "Lnn" format every extractor emits).

    Excludes rationale/document nodes (docstrings, headings — same file_type
    set dedup.py's _FILE_ANCHORED_NONCODE treats as identity-anchored, not the
    call-graph). These are frequently co-located on the same line as the real
    code/file node they describe (e.g. a module docstring and the file node
    both at L1); left in, the nearest-preceding-line bisect in changed_seeds
    can arbitrarily pick the leaf rationale node (in_degree 0, no dependents)
    over the real node with real dependents, silently losing the whole
    downstream traversal for that changed range.
    """
    by_file: dict[str, list[tuple[int, str]]] = {}
    for node_id, data in graph.nodes(data=True):
        source_file = data.get("source_file")
        loc = data.get("source_location")
        if not source_file or not loc:
            continue
        if data.get("file_type") in _RATIONALE_LIKE_FILE_TYPES:
            continue
        m = re.match(r"^L(\d+)", str(loc))
        if not m:
            continue
        by_file.setdefault(str(source_file), []).append((int(m.group(1)), str(node_id)))
    for entries in by_file.values():
        entries.sort(key=lambda t: t[0])
    return by_file


def changed_seeds(
    graph: nx.Graph, repo_root: Path, base: str | None = None
) -> dict[str, list[str]]:
    """Map git-diff changed line ranges to graph node ids.

    Returns {file: [node_id, ...]} — for each changed range, the nearest
    node whose definition starts at or before the range (the innermost
    enclosing definition, since source_location has no end line); if a
    range starts before any node in the file, the file-level node (L1) is
    used. New nodes whose own start line falls inside a changed range are
    also included (covers newly-added functions).
    """
    changed = git_diff_changed_ranges(repo_root, base)
    by_file = _nodes_by_file(graph)
    result: dict[str, list[str]] = {}
    for file_path, ranges in changed.items():
        entries = by_file.get(file_path)
        if not entries:
            continue
        hit_ids: list[str] = []
        seen: set[str] = set()
        lines = [line for line, _nid in entries]
        for start, end in ranges:
            # Nearest-preceding node (bisect from the right).
            idx = bisect.bisect_right(lines, start) - 1
            if idx >= 0:
                nid = entries[idx][1]
                if nid not in seen:
                    seen.add(nid)
                    hit_ids.append(nid)
            # Any node whose own definition starts inside the changed range
            # (new function/method added by this diff).
            for line, nid in entries:
                if start <= line <= end and nid not in seen:
                    seen.add(nid)
                    hit_ids.append(nid)
        if hit_ids:
            result[file_path] = hit_ids
    return result


def format_git_diff_affected(
    graph: nx.Graph,
    repo_root: Path,
    *,
    base: str | None = None,
    relations: Iterable[str] = DEFAULT_AFFECTED_RELATIONS,
    depth: int = 2,
) -> str:
    """Report blast radius for every symbol touched by the current git diff."""
    seeds_by_file = changed_seeds(graph, repo_root, base)
    if not seeds_by_file:
        return "No changed symbols found (clean working tree, or changes fall outside indexed files)."

    relation_list = tuple(relations)
    lines = [
        f"Git-diff impact ({'working tree vs ' + base if base else 'uncommitted changes'})",
        f"Relations: {', '.join(relation_list)}",
        f"Depth: {depth}",
        "",
    ]
    total_affected = 0
    for file_path, seed_ids in sorted(seeds_by_file.items()):
        lines.append(f"## {file_path}")
        for seed_id in seed_ids:
            hits = affected_nodes(graph, seed_id, relations=relation_list, depth=depth)
            total_affected += len(hits)
            if not hits:
                risk = "isolated (no dependents found)"
            elif len(hits) <= 5:
                risk = f"contained ({len(hits)} dependent{'s' if len(hits) != 1 else ''})"
            else:
                risk = f"HIGH blast radius ({len(hits)} dependents)"
            lines.append(f"- {_node_label(graph, seed_id)} [{risk}]")
            for hit in hits:
                data = graph.nodes[hit.node_id]
                lines.append(
                    f"    -> {_node_label(graph, hit.node_id)} [{hit.via_relation}] {_format_location(data)}"
                )
        lines.append("")

    lines.append(f"Total: {sum(len(v) for v in seeds_by_file.values())} changed symbol(s), {total_affected} dependent edge(s) found.")
    return "\n".join(lines)


def ci_affected_tests(
    graph: nx.Graph,
    repo_root: Path,
    *,
    base: str | None = None,
    relations: Iterable[str] = DEFAULT_AFFECTED_RELATIONS,
    depth: int = 2,
) -> list[str]:
    """Sorted, deduplicated test-file paths whose coverage is touched by the
    current git diff -- for a CI hook to select which tests to run, distinct
    from format_git_diff_affected's full human-readable blast-radius report.

    A changed test file is included directly; a changed non-test file is
    included via any test file reachable in its dependent set (same traversal
    as affected_nodes/format_git_diff_affected). Uses paths.is_ci_runnable_test_file
    rather than the directory-segment-aware _is_test_path, since a fixture or
    conftest.py living under tests/ is not something a test runner can be
    pointed at directly.

    A changed file with no matching graph node (stale graph, unindexed
    language) is silently dropped by changed_seeds -- since that makes CI
    impact for that file undeterminable rather than genuinely zero, this
    warns on stderr (stdout/exit code are untouched, so piping is unaffected).
    """
    import sys
    from graphify.paths import is_ci_runnable_test_file

    all_changed = git_diff_changed_ranges(repo_root, base)
    seeds_by_file = changed_seeds(graph, repo_root, base)
    unindexed = sorted(set(all_changed) - set(seeds_by_file))
    if unindexed:
        print(
            f"warning: {len(unindexed)} changed file(s) not found in the graph "
            "(stale graph or unindexed language) -- CI impact may be incomplete: "
            + ", ".join(unindexed),
            file=sys.stderr,
        )

    relation_list = tuple(relations)
    test_files: set[str] = set()
    for file_path, seed_ids in seeds_by_file.items():
        if is_ci_runnable_test_file(file_path):
            test_files.add(file_path)
        for seed_id in seed_ids:
            for hit in affected_nodes(graph, seed_id, relations=relation_list, depth=depth):
                hit_file = graph.nodes[hit.node_id].get("source_file")
                if hit_file and is_ci_runnable_test_file(str(hit_file)):
                    test_files.add(str(hit_file))
    return sorted(test_files)


def format_ci_affected_tests(
    graph: nx.Graph,
    repo_root: Path,
    *,
    base: str | None = None,
    relations: Iterable[str] = DEFAULT_AFFECTED_RELATIONS,
    depth: int = 2,
    as_json: bool = False,
) -> str:
    """CI-consumable output: one test-file path per line (or a JSON array with
    as_json=True), no diagnostic prose -- meant to be piped into a test
    runner. `xargs -r` (skip on empty input) is GNU-only; on BSD/macOS xargs
    (no -r) an empty result still invokes the command with zero arguments,
    which for most test runners means "run everything". Prefer --json and
    checking for an empty list in the CI script, or guard with
    `[ -n "$(graphify affected --ci)" ] && graphify affected --ci | xargs pytest`
    for a portable shell one-liner."""
    tests = ci_affected_tests(graph, repo_root, base=base, relations=relations, depth=depth)
    if as_json:
        import json
        return json.dumps(tests)
    return "\n".join(tests)


def format_affected(
    graph: nx.Graph,
    query: str,
    *,
    relations: Iterable[str] = DEFAULT_AFFECTED_RELATIONS,
    depth: int = 2,
) -> str:
    relation_list = tuple(relations)
    seed = resolve_seed(graph, query)
    if seed is None:
        return f"No unique node match for {query}"

    hits = affected_nodes(graph, seed, relations=relation_list, depth=depth)
    lines = [
        f"Affected nodes for {_node_label(graph, seed)}",
        f"Relations: {', '.join(relation_list)}",
        f"Depth: {depth}",
    ]
    if not hits:
        lines.append("No affected nodes found.")
        return "\n".join(lines)

    for hit in hits:
        data = graph.nodes[hit.node_id]
        lines.append(
            f"- {_node_label(graph, hit.node_id)} [{hit.via_relation}] {_format_location(data)}"
        )
    return "\n".join(lines)


def load_graph(path: Path) -> nx.Graph:
    import json
    from networkx.readwrite import json_graph

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(
            f"Cannot read graph file {path}: {exc}. "
            "Re-run 'graphify extract' to regenerate it."
        ) from exc
    from graphify.multigraph_compat import require_multigraph_capabilities
    require_multigraph_capabilities()
    # Normalize the edge key: graphify's `extract` output uses "edges" while
    # networkx's node_link_data default is "links". Without this, an edges-keyed
    # graph.json raises an uncaught KeyError: 'links' here — every other loader
    # (__main__.py) already normalizes this (#738; same class as #1198).
    if "links" not in raw and "edges" in raw:
        raw = dict(raw, links=raw["edges"])
    # Force directed so stored caller→callee direction survives the round-trip;
    # mirrors serve.py and __main__.py (#1174, #2309).
    # Keep in-file markers when present (#2309): unconditionally
    # overwriting them with source/target would clobber the true
    # direction of a link persisted in flipped endpoint order.
    raw = dict(
        raw,
        links=[
            {
                **link,
                "_src": link.get("_src", link.get("source")),
                "_tgt": link.get("_tgt", link.get("target")),
            }
            for link in raw.get("links", [])
        ],
        directed=True,
        multigraph=True,
    )
    try:
        return json_graph.node_link_graph(raw, edges="links")
    except TypeError:
        return json_graph.node_link_graph(raw)
