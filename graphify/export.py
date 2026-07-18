# write graph to HTML, JSON, SVG, GraphML, Obsidian vault, and Neo4j Cypher
from __future__ import annotations
import hashlib
import html as _html
import json
import math
import os
import re
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path
import networkx as nx
from networkx.readwrite import json_graph
from graphify.security import sanitize_label
from graphify.analyze import _node_community_map
from graphify.build import edge_data


# Artifacts worth preserving across rebuilds (non-regenerable without LLM or curation).
_BACKUP_ARTIFACTS = [
    "graph.json",
    "GRAPH_REPORT.md",
    ".graphify_labels.json",
    ".graphify_analysis.json",
    "manifest.json",
    ".graphify_semantic_marker",
    "cost.json",
]


_DEFAULT_BACKUP_KEEP_DAYS = 14


def _prune_old_backups(out: Path, keep_days: int = _DEFAULT_BACKUP_KEEP_DAYS) -> None:
    """Delete dated backup dirs (YYYY-MM-DD, optionally _N suffixed) older than keep_days.

    Best-effort: a dir with an unparseable name or a failed rmtree is skipped,
    never raises. Runs on every backup_if_protected() call so retention stays
    bounded without needing a separate cleanup command.
    """
    try:
        keep_days = int(os.environ.get("GRAPHIFY_BACKUP_KEEP_DAYS", keep_days))
    except ValueError:
        keep_days = _DEFAULT_BACKUP_KEEP_DAYS
    cutoff = date.today().toordinal() - keep_days
    for child in out.iterdir():
        if not child.is_dir():
            continue
        date_part = child.name.split("_", 1)[0]
        try:
            dir_date = date.fromisoformat(date_part)
        except ValueError:
            continue
        if dir_date.toordinal() < cutoff:
            shutil.rmtree(child, ignore_errors=True)


def backup_if_protected(out_dir: Path) -> "Path | None":
    """Snapshot graph artifacts to a dated subfolder before an overwrite.

    Triggers when graph.json exists AND either:
    - .graphify_semantic_marker is present (graph cost real LLM tokens), or
    - .graphify_labels.json contains at least one non-default community label
      (graph has been curated by a human or skill).

    Returns the backup folder path, or None if no backup was taken.
    Never raises — backup failure prints a warning but never blocks the write.
    Set GRAPHIFY_NO_BACKUP=1 to disable. Set GRAPHIFY_BACKUP_KEEP_DAYS to change
    how many days of dated backups are retained (default 14).
    """
    if os.environ.get("GRAPHIFY_NO_BACKUP"):
        return None
    out = Path(out_dir)
    if not (out / "graph.json").exists():
        return None

    is_semantic = (out / ".graphify_semantic_marker").exists()
    is_curated = False
    labels_file = out / ".graphify_labels.json"
    if labels_file.exists():
        try:
            labels = json.loads(labels_file.read_text(encoding="utf-8"))
            is_curated = any(v != f"Community {k}" for k, v in labels.items())
        except Exception:
            pass

    if not is_semantic and not is_curated:
        return None

    reason = "+".join(filter(None, ["semantic" if is_semantic else "", "curated" if is_curated else ""]))
    _prune_old_backups(out)
    today = date.today().isoformat()
    backup_dir = out / today
    graph_src = out / "graph.json"

    # Skip re-copying if today's backup already has identical graph.json content.
    # If content differs (graph changed since the last backup today), overwrite
    # the backup in place — one folder per day, always the latest pre-overwrite state.
    if backup_dir.exists() and (backup_dir / "graph.json").exists():
        src_hash = hashlib.sha256(graph_src.read_bytes()).hexdigest()
        bak_hash = hashlib.sha256((backup_dir / "graph.json").read_bytes()).hexdigest()
        if src_hash == bak_hash:
            return backup_dir  # identical content, nothing to do

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        copied = 0
        for name in _BACKUP_ARTIFACTS:
            src = out / name
            if src.exists():
                try:
                    shutil.copy2(src, backup_dir / name)
                    copied += 1
                except Exception:
                    pass
        if copied:
            print(f"[graphify] backed up {reason} graph ({copied} files) -> {backup_dir.name}/")
        return backup_dir
    except Exception as exc:
        import sys
        print(f"[graphify] warning: backup failed ({exc}) - continuing with overwrite", file=sys.stderr)
        return None

def _strip_diacritics(text: str | None) -> str:
    import unicodedata
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _yaml_str(s: str) -> str:
    """Escape a value for safe embedding in a YAML double-quoted scalar (F-009).

    See `graphify.ingest._yaml_str` for the full rationale; duplicated here to
    avoid pulling the URL-fetching `ingest` module into export's dependency
    graph. Handles backslash, double-quote, all line breaks (\\n, \\r,
    U+2028, U+2029), tab, NUL, and other C0/DEL control characters that
    would otherwise let a hostile `source_file` / `community` / etc. break
    out of the YAML scalar and inject sibling keys.
    """
    if s is None:
        return ""
    out: list[str] = []
    for ch in str(s):
        cp = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\0":
            out.append("\\0")
        elif cp == 0x2028:
            out.append("\\L")
        elif cp == 0x2029:
            out.append("\\P")
        elif cp < 0x20 or cp == 0x7F:
            out.append(f"\\x{cp:02x}")
        else:
            out.append(ch)
    return "".join(out)


COMMUNITY_COLORS = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
]

MAX_NODES_FOR_VIZ = 5_000


def _viz_node_limit() -> int:
    """Return the effective viz node limit, honoring GRAPHIFY_VIZ_NODE_LIMIT env var.

    Falls back to MAX_NODES_FOR_VIZ when the env var is unset, empty, or non-integer.
    Set to 0 to disable HTML viz unconditionally (useful for CI runners).
    """
    import os
    raw = os.environ.get("GRAPHIFY_VIZ_NODE_LIMIT")
    if raw is None or not raw.strip():
        return MAX_NODES_FOR_VIZ
    try:
        return int(raw)
    except ValueError:
        return MAX_NODES_FOR_VIZ


def _html_styles() -> str:
    return """<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f1a; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; display: flex; height: 100vh; overflow: hidden; }
  #graph { flex: 1; }
  #graph-3d { flex: 1; display: none; }
  #sidebar { width: 280px; background: #1a1a2e; border-left: 1px solid #2a2a4e; display: flex; flex-direction: column; overflow: hidden; }
  #mode-toggle-wrap, #lens-toggle-wrap { padding: 12px; border-bottom: 1px solid #2a2a4e; display: flex; gap: 8px; }
  .toggle-btn { flex: 1; background: #0f0f1a; border: 1px solid #3a3a5e; color: #aaa; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; transition: all 0.2s ease; outline: none; font-weight: 500; text-align: center; }
  .toggle-btn:hover { border-color: #4E79A7; color: #fff; }
  .toggle-btn.active { background: #4E79A7; border-color: #4E79A7; color: #fff; box-shadow: 0 0 8px rgba(78, 121, 167, 0.4); }
  #search-wrap { padding: 12px; border-bottom: 1px solid #2a2a4e; }
  #search { width: 100%; background: #0f0f1a; border: 1px solid #3a3a5e; color: #e0e0e0; padding: 7px 10px; border-radius: 6px; font-size: 13px; outline: none; }
  #search:focus { border-color: #4E79A7; }
  #search-results { max-height: 140px; overflow-y: auto; padding: 4px 12px; border-bottom: 1px solid #2a2a4e; display: none; }
  .search-item { padding: 4px 6px; cursor: pointer; border-radius: 4px; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .search-item:hover { background: #2a2a4e; }
  #info-panel { padding: 14px; border-bottom: 1px solid #2a2a4e; min-height: 140px; }
  #info-panel h3 { font-size: 13px; color: #aaa; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
  #info-content { font-size: 13px; color: #ccc; line-height: 1.6; }
  #info-content .field { margin-bottom: 5px; }
  #info-content .field b { color: #e0e0e0; }
  #info-content .empty { color: #555; font-style: italic; }
  .neighbor-link { display: block; padding: 2px 6px; margin: 2px 0; border-radius: 3px; cursor: pointer; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-left: 3px solid #333; }
  .neighbor-link:hover { background: #2a2a4e; }
  #neighbors-list { max-height: 160px; overflow-y: auto; margin-top: 4px; }
  #legend-wrap { flex: 1; overflow-y: auto; padding: 12px; }
  #legend-wrap h3 { font-size: 13px; color: #aaa; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
  .legend-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; cursor: pointer; border-radius: 4px; font-size: 12px; }
  .legend-item:hover { background: #2a2a4e; padding-left: 4px; }
  .legend-item.dimmed { opacity: 0.35; }
  .legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .legend-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .legend-count { color: #666; font-size: 11px; }
  #stats { padding: 10px 14px; border-top: 1px solid #2a2a4e; font-size: 11px; color: #555; }
  #legend-controls { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 4px 0; }
  #legend-controls label { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; color: #aaa; user-select: none; }
  #legend-controls label:hover { color: #e0e0e0; }
  .legend-cb, #select-all-cb { appearance: none; -webkit-appearance: none; width: 14px; height: 14px; border: 1.5px solid #3a3a5e; border-radius: 3px; background: #0f0f1a; cursor: pointer; position: relative; flex-shrink: 0; }
  .legend-cb:checked, #select-all-cb:checked { background: #4E79A7; border-color: #4E79A7; }
  .legend-cb:checked::after, #select-all-cb:checked::after { content: ''; position: absolute; left: 3.5px; top: 1px; width: 4px; height: 7px; border: solid #fff; border-width: 0 2px 2px 0; transform: rotate(45deg); }
  #select-all-cb:indeterminate { background: #4E79A7; border-color: #4E79A7; }
  #select-all-cb:indeterminate::after { content: ''; position: absolute; left: 2px; top: 5px; width: 8px; height: 2px; background: #fff; border: none; transform: none; }
  .collapsible-section h3 { font-size: 13px; color: #aaa; padding: 12px; border-bottom: 1px solid #2a2a4e; cursor: pointer; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; letter-spacing: 0.05em; user-select: none; }
  .collapsible-section h3:hover { background: #2a2a4e; color: #fff; }
  .slider-group { margin-bottom: 12px; }
  .slider-group label { display: block; font-size: 11px; color: #aaa; margin-bottom: 4px; }
  .slider-group label span { float: right; color: #fff; font-weight: bold; }
  .slider-group input[type="range"] { width: 100%; height: 4px; background: #3a3a5e; border-radius: 2px; outline: none; -webkit-appearance: none; cursor: pointer; }
  .slider-group input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 12px; height: 12px; border-radius: 50%; background: #4E79A7; transition: transform 0.1s; }
  .slider-group input[type="range"]::-webkit-slider-thumb:hover { transform: scale(1.2); }
  .checkbox-group { margin-top: 8px; font-size: 11px; color: #aaa; }
  .checkbox-group label { display: flex; align-items: center; gap: 6px; cursor: pointer; }
</style>"""


def _hyperedge_script(hyperedges_json: str) -> str:
    return f"""<script>
// Render hyperedges as shaded regions
const hyperedges = {hyperedges_json};
// afterDrawing passes ctx already transformed to network coordinate space.
// Draw node positions raw — no manual pan/zoom/DPR math needed.
network.on('afterDrawing', function(ctx) {{
    hyperedges.forEach(h => {{
        const positions = h.nodes
            .map(nid => network.getPositions([nid])[nid])
            .filter(p => p !== undefined);
        if (positions.length < 2) return;
        ctx.save();
        ctx.globalAlpha = 0.12;
        ctx.fillStyle = '#6366f1';
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 2;
        ctx.beginPath();
        // Centroid and expanded hull in network coordinates
        const cx = positions.reduce((s, p) => s + p.x, 0) / positions.length;
        const cy = positions.reduce((s, p) => s + p.y, 0) / positions.length;
        const expanded = positions.map(p => ({{
            x: cx + (p.x - cx) * 1.15,
            y: cy + (p.y - cy) * 1.15
        }}));
        ctx.moveTo(expanded[0].x, expanded[0].y);
        expanded.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
        ctx.closePath();
        ctx.fill();
        ctx.globalAlpha = 0.4;
        ctx.stroke();
        // Label
        ctx.globalAlpha = 0.8;
        ctx.fillStyle = '#4f46e5';
        ctx.font = 'bold 11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(h.label, cx, cy - 5);
        ctx.restore();
    }});
}});
</script>"""


def _html_script(nodes_json: str, edges_json: str, legend_json: str) -> str:
    return f"""<script>
const RAW_NODES = {nodes_json};
const RAW_EDGES = {edges_json};
const LEGEND = {legend_json};

// HTML-escape helper — prevents XSS when injecting graph data into innerHTML
function esc(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}}

// Build vis datasets
const nodesDS = new vis.DataSet(RAW_NODES.map(n => ({{
  id: n.id, label: n.label, color: n.color, size: n.size,
  font: n.font, title: n.title,
  _community: n.community, _community_name: n.community_name,
  _source_file: n.source_file, _file_type: n.file_type, _degree: n.degree,
}})));

const edgesDS = new vis.DataSet(RAW_EDGES.map((e, i) => ({{
  id: i, from: e.from, to: e.to,
  label: '',
  title: e.title,
  dashes: e.dashes,
  width: e.width,
  color: e.color,
  arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
}})));

const container = document.getElementById('graph');
const network = new vis.Network(container, {{ nodes: nodesDS, edges: edgesDS }}, {{
  physics: {{
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {{
      gravitationalConstant: -60,
      centralGravity: 0.005,
      springLength: 120,
      springConstant: 0.08,
      damping: 0.4,
      avoidOverlap: 0.8,
    }},
    stabilization: {{ iterations: 200, fit: true }},
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 100,
    hideEdgesOnDrag: true,
    navigationButtons: false,
    keyboard: false,
  }},
  nodes: {{ shape: 'dot', borderWidth: 1.5 }},
  edges: {{ smooth: {{ type: 'continuous', roundness: 0.2 }}, selectionWidth: 3 }},
}});

network.once('stabilizationIterationsDone', () => {{
  network.setOptions({{ physics: {{ enabled: false }} }});
}});

function showInfo(nodeId) {{
  const n = nodesDS.get(nodeId);
  if (!n) return;
  const neighborIds = network.getConnectedNodes(nodeId);
  const neighborItems = neighborIds.map(nid => {{
    const nb = nodesDS.get(nid);
    const color = nb ? nb.color.background : '#555';
    return `<span class="neighbor-link" style="border-left-color:${{esc(color)}}" onclick="focusNode(${{JSON.stringify(nid)}})">${{esc(nb ? nb.label : nid)}}</span>`;
  }}).join('');
  document.getElementById('info-content').innerHTML = `
    <div class="field"><b>${{esc(n.label)}}</b></div>
    <div class="field">Type: ${{esc(n._file_type || 'unknown')}}</div>
    <div class="field">Community: ${{esc(n._community_name)}}</div>
    <div class="field">Source: ${{esc(n._source_file || '-')}}</div>
    <div class="field">Degree: ${{n._degree}}</div>
    ${{neighborIds.length ? `<div class="field" style="margin-top:8px;color:#aaa;font-size:11px">Neighbors (${{neighborIds.length}})</div><div id="neighbors-list">${{neighborItems}}</div>` : ''}}
  `;
}}

function focusNode(nodeId) {{
  const is3D = document.getElementById('graph-3d').style.display !== 'none';
  if (is3D && graph3DInstance) {{
    const node3d = graph3DInstance.graphData().nodes.find(n => n.id === nodeId);
    if (node3d) {{
      const distance = 80;
      const distRatio = 1 + distance/Math.hypot(node3d.x || 0, node3d.y || 0, node3d.z || 0);
      graph3DInstance.cameraPosition(
        {{ x: (node3d.x || 0) * distRatio, y: (node3d.y || 0) * distRatio, z: (node3d.z || 0) * distRatio }},
        node3d,
        1000
      );
    }}
  }} else {{
    network.focus(nodeId, {{ scale: 1.4, animation: true }});
    network.selectNodes([nodeId]);
  }}
  showInfo(nodeId);
}}

// Track hovered node — hover detection is more reliable than click params
let hoveredNodeId = null;
network.on('hoverNode', params => {{
  hoveredNodeId = params.node;
  container.style.cursor = 'pointer';
}});
network.on('blurNode', () => {{
  hoveredNodeId = null;
  container.style.cursor = 'default';
}});
container.addEventListener('click', () => {{
  if (hoveredNodeId !== null) {{
    showInfo(hoveredNodeId);
    network.selectNodes([hoveredNodeId]);
  }}
}});
network.on('click', params => {{
  if (params.nodes.length > 0) {{
    showInfo(params.nodes[0]);
  }} else if (hoveredNodeId === null) {{
    document.getElementById('info-content').innerHTML = '<span class="empty">Click a node to inspect it</span>';
  }}
}});

const searchInput = document.getElementById('search');
const searchResults = document.getElementById('search-results');
searchInput.addEventListener('input', () => {{
  const q = searchInput.value.toLowerCase().trim();
  searchResults.innerHTML = '';
  if (!q) {{ searchResults.style.display = 'none'; return; }}
  const matches = RAW_NODES.filter(n => n.label.toLowerCase().includes(q)).slice(0, 20);
  if (!matches.length) {{ searchResults.style.display = 'none'; return; }}
  searchResults.style.display = 'block';
  matches.forEach(n => {{
    const el = document.createElement('div');
    el.className = 'search-item';
    el.textContent = n.label;
    el.style.borderLeft = `3px solid ${{n.color.background}}`;
    el.style.paddingLeft = '8px';
    el.onclick = () => {{
      focusNode(n.id);
      searchResults.style.display = 'none';
      searchInput.value = '';
    }};
    searchResults.appendChild(el);
  }});
}});
document.addEventListener('click', e => {{
  if (!searchResults.contains(e.target) && e.target !== searchInput)
    searchResults.style.display = 'none';
}});

// View lens: 'community' (default, unchanged behavior) groups/colors by the
// inferred Leiden community. 'file' and 'deps' are additive alternatives that
// group/color by real code structure (source_file, and file-to-file
// calls/imports/references/extends edges) instead of an inferred cluster —
// computed lazily here in the browser from data already embedded above, so
// building/updating the graph (`extract`, `update`, `cluster-only`) does no
// extra work and graph.html isn't any bigger than before.
let currentLens = 'community'; // 'community' | 'file' | 'deps' | 'calls'
const hiddenCommunities = new Set();
const hiddenFiles = new Set();
// Real relation vocabulary measured across Python/YAML, Swift, and JS/TS corpora (2026-07-04):
// excludes structural/containment relations (contains, method, defines, case_of)
// and doc-explains-code (rationale_for), which aren't call/dependency structure.
// Shared by the 'deps' (file-collapsed) and 'calls' (per-symbol) lenses.
const REL_WHITELIST = new Set(['calls', 'imports', 'imports_from', 'references', 'inherits', 'implements', 'indirect_call', 're_exports', 'uses', 'embeds']);
let depNodesCache = null;
let depEdgesCache = null;

const selectAllCb = document.getElementById('select-all-cb');
const legendEl = document.getElementById('legend');
const legendTitleEl = document.getElementById('legend-title');

const _fileColorCache = {{}};
function colorForFile(f) {{
  if (!_fileColorCache[f]) {{
    let hash = 0;
    for (let i = 0; i < f.length; i++) hash = (hash * 31 + f.charCodeAt(i)) | 0;
    _fileColorCache[f] = `hsl(${{Math.abs(hash) % 360}}, 55%, 55%)`;
  }}
  return _fileColorCache[f];
}}

function isNodeHidden(n) {{
  if (currentLens === 'calls' && (n.file_type || n._file_type) !== 'code') return true;
  if (currentLens === 'file' || currentLens === 'calls') return hiddenFiles.has(n.source_file || n._source_file || '(none)');
  return hiddenCommunities.has(n.community !== undefined ? n.community : n._community);
}}

function nodeDisplayColor(n) {{
  if (currentLens === 'file' || currentLens === 'calls') return colorForFile(n.source_file || n._source_file || '(none)');
  return n.color.background;
}}

function updateSelectAllState(total, hidden) {{
  selectAllCb.checked = hidden === 0;
  selectAllCb.indeterminate = hidden > 0 && hidden < total;
}}

function applyVisibility() {{
  if (currentLens === 'deps') {{
    const updates = depNodesCache.map(n => ({{ id: n.id, hidden: hiddenFiles.has(n._source_file) }}));
    nodesDS.update(updates);
    return; // collapsed file graph has no 3D view to keep in sync
  }}
  const updates = RAW_NODES.map(n => ({{ id: n.id, hidden: isNodeHidden(n) }}));
  nodesDS.update(updates);
  update3DGraphData();
}}

function toggleAllGroups(hide) {{
  document.querySelectorAll('.legend-item').forEach(item => {{
    hide ? item.classList.add('dimmed') : item.classList.remove('dimmed');
  }});
  document.querySelectorAll('.legend-cb').forEach(cb => {{ cb.checked = !hide; }});
  if (currentLens === 'community') {{
    LEGEND.forEach(c => {{ if (hide) hiddenCommunities.add(c.cid); else hiddenCommunities.delete(c.cid); }});
  }} else {{
    const files = new Set(RAW_NODES.map(n => n.source_file || '(none)'));
    files.forEach(f => {{ if (hide) hiddenFiles.add(f); else hiddenFiles.delete(f); }});
  }}
  applyVisibility();
  const total = currentLens === 'community' ? LEGEND.length : new Set(RAW_NODES.map(n => n.source_file || '(none)')).size;
  const hidden = currentLens === 'community' ? hiddenCommunities.size : hiddenFiles.size;
  updateSelectAllState(total, hidden);
}}

function renderCommunityLegend() {{
  legendTitleEl.textContent = 'Communities';
  legendEl.innerHTML = '';
  LEGEND.forEach(c => {{
    const item = document.createElement('div');
    item.className = 'legend-item' + (hiddenCommunities.has(c.cid) ? ' dimmed' : '');
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.className = 'legend-cb';
    cb.checked = !hiddenCommunities.has(c.cid);
    cb.addEventListener('change', (e) => {{
      e.stopPropagation();
      if (cb.checked) {{ hiddenCommunities.delete(c.cid); item.classList.remove('dimmed'); }}
      else {{ hiddenCommunities.add(c.cid); item.classList.add('dimmed'); }}
      applyVisibility();
      updateSelectAllState(LEGEND.length, hiddenCommunities.size);
    }});
    item.innerHTML = `<div class="legend-dot" style="background:${{c.color}}"></div>
      <span class="legend-label">${{c.label}}</span>
      <span class="legend-count">${{c.count}}</span>`;
    item.prepend(cb);
    item.onclick = (e) => {{ if (e.target === cb) return; cb.checked = !cb.checked; cb.dispatchEvent(new Event('change')); }};
    legendEl.appendChild(item);
  }});
  updateSelectAllState(LEGEND.length, hiddenCommunities.size);
}}

function renderFileLegend() {{
  legendTitleEl.textContent = currentLens === 'deps' ? 'Files' : 'Files (color)';
  legendEl.innerHTML = '';
  const counts = {{}};
  RAW_NODES.forEach(n => {{ const f = n.source_file || '(none)'; counts[f] = (counts[f] || 0) + 1; }});
  const files = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  files.forEach(f => {{
    const color = colorForFile(f);
    const item = document.createElement('div');
    item.className = 'legend-item' + (hiddenFiles.has(f) ? ' dimmed' : '');
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.className = 'legend-cb';
    cb.checked = !hiddenFiles.has(f);
    cb.addEventListener('change', (e) => {{
      e.stopPropagation();
      if (cb.checked) {{ hiddenFiles.delete(f); item.classList.remove('dimmed'); }}
      else {{ hiddenFiles.add(f); item.classList.add('dimmed'); }}
      applyVisibility();
      updateSelectAllState(files.length, hiddenFiles.size);
    }});
    item.innerHTML = `<div class="legend-dot" style="background:${{color}}"></div>
      <span class="legend-label" title="${{esc(f)}}">${{esc(f)}}</span>
      <span class="legend-count">${{counts[f]}}</span>`;
    item.prepend(cb);
    item.onclick = (e) => {{ if (e.target === cb) return; cb.checked = !cb.checked; cb.dispatchEvent(new Event('change')); }};
    legendEl.appendChild(item);
  }});
  updateSelectAllState(files.length, hiddenFiles.size);
}}

function renderLegend() {{
  if (currentLens === 'community') renderCommunityLegend();
  else renderFileLegend();
}}

// Collapse RAW_NODES/RAW_EDGES to one node per file, with an edge between
// file A and file B for each calls/imports/references/extends/implements/uses
// relation crossing between them. Same-file edges are skipped (already shown
// by the file/community lenses). Computed once, lazily, on first use.
function buildFileDependencyGraph() {{
  const nodeToFile = {{}};
  const fileCounts = {{}};
  RAW_NODES.forEach(n => {{
    const f = n.source_file || '(none)';
    nodeToFile[n.id] = f;
    fileCounts[f] = (fileCounts[f] || 0) + 1;
  }});
  const edgeAgg = {{}};
  RAW_EDGES.forEach(e => {{
    const fa = nodeToFile[e.from], fb = nodeToFile[e.to];
    if (!fa || !fb || fa === fb) return;
    const rel = (e.label || '').toLowerCase();
    if (!REL_WHITELIST.has(rel)) return;
    const key = fa + '\\u0001' + fb;
    edgeAgg[key] = (edgeAgg[key] || 0) + 1;
  }});
  const maxCount = Math.max(1, ...Object.values(fileCounts));
  depNodesCache = Object.keys(fileCounts).map(f => {{
    const c = colorForFile(f);
    return {{
      id: 'file::' + f,
      label: f.split('/').pop() || f,
      title: esc(f),
      color: {{ background: c, border: c, highlight: {{ background: '#fff', border: c }} }},
      size: 10 + 25 * (fileCounts[f] / maxCount),
      font: {{ size: 12, color: '#fff' }},
      _community: -1, _community_name: 'n/a', _source_file: f, _file_type: 'file', _degree: fileCounts[f],
    }};
  }});
  depEdgesCache = Object.entries(edgeAgg).map(([key, count], i) => {{
    const [fa, fb] = key.split('\\u0001');
    return {{
      id: 'dep' + i, from: 'file::' + fa, to: 'file::' + fb,
      label: '', title: `${{count}} cross-file reference(s)`,
      width: Math.min(6, 1 + Math.log2(count + 1)), dashes: false,
      color: {{ opacity: 0.5 }},
      arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
    }};
  }});
}}

function switchLens(lens) {{
  if (lens === currentLens) return;
  document.querySelectorAll('.lens-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('lens-btn-' + lens).classList.add('active');

  const btn3d = document.getElementById('btn-3d');
  if (lens === 'deps') {{
    btn3d.disabled = true;
    btn3d.title = 'Not available in Dependencies view';
    if (document.getElementById('graph-3d').style.display !== 'none') switchMode('2d');
  }} else {{
    btn3d.disabled = false;
    btn3d.title = '';
  }}

  currentLens = lens;

  if (lens === 'deps') {{
    if (!depNodesCache) buildFileDependencyGraph();
    nodesDS.clear();
    nodesDS.add(depNodesCache);
    edgesDS.clear();
    edgesDS.add(depEdgesCache);
  }} else {{
    nodesDS.clear();
    nodesDS.add(RAW_NODES.map(n => ({{
      id: n.id, label: n.label,
      color: (lens === 'file' || lens === 'calls')
        ? {{ background: colorForFile(n.source_file || '(none)'), border: colorForFile(n.source_file || '(none)'), highlight: {{ background: '#fff', border: colorForFile(n.source_file || '(none)') }} }}
        : n.color,
      size: n.size, font: n.font, title: n.title,
      _community: n.community, _community_name: n.community_name,
      _source_file: n.source_file, _file_type: n.file_type, _degree: n.degree,
      hidden: isNodeHidden(n),
    }})));
    edgesDS.clear();
    edgesDS.add(RAW_EDGES.filter(e => lens !== 'calls' || REL_WHITELIST.has((e.label || '').toLowerCase())).map((e, i) => ({{
      id: i, from: e.from, to: e.to, label: '', title: e.title,
      dashes: e.dashes, width: e.width, color: e.color,
      arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
    }})));
    if (graph3DInstance) update3DGraphData();
  }}

  renderLegend();
  network.setOptions({{ physics: {{ enabled: true }} }});
  network.once('stabilizationIterationsDone', () => network.setOptions({{ physics: {{ enabled: false }} }}));
}}

renderLegend();

let graph3DInstance = null;
let scriptLoaded = false;

function loadScript(url, callback) {{
  const script = document.createElement('script');
  script.type = 'text/javascript';
  script.src = url;
  script.onload = callback;
  script.onerror = () => {{
    alert('Failed to load 3D Force Graph library from CDN.');
    switchMode('2d');
  }};
  document.head.appendChild(script);
}}

function toggleSection(id) {{
  var el = document.getElementById(id);
  var arrow = document.getElementById('settings-arrow');
  if (el.style.display === 'none') {{
    el.style.display = 'block';
    arrow.textContent = '▼';
  }} else {{
    el.style.display = 'none';
    arrow.textContent = '▶';
  }}
}}

function updatePhysics2D() {{
  const rep = parseInt(document.getElementById('slide-repulsion').value);
  const dist = parseInt(document.getElementById('slide-distance').value);
  document.getElementById('val-repulsion').textContent = rep;
  document.getElementById('val-distance').textContent = dist;
  network.setOptions({{
    physics: {{
      forceAtlas2Based: {{
        gravitationalConstant: rep,
        springLength: dist
      }}
    }}
  }});
}}

function updateDisplay2D() {{
  const sizeMult = parseFloat(document.getElementById('slide-size').value);
  const thickMult = parseFloat(document.getElementById('slide-thickness').value);
  const showLabels = document.getElementById('check-labels').checked;
  document.getElementById('val-size').textContent = sizeMult.toFixed(1);
  document.getElementById('val-thickness').textContent = thickMult.toFixed(1);

  network.setOptions({{
    nodes: {{
      scaling: {{
        customScalingFunction: (min, max, total, value) => value * sizeMult
      }}
    }},
    edges: {{
      width: thickMult
    }}
  }});
  
  const updatedNodes = RAW_NODES.map(n => {{
    const maxDeg = Math.max(...RAW_NODES.map(x => x.degree || 1));
    let fontSz = 0;
    if (showLabels) {{
      fontSz = (n.degree >= maxDeg * 0.15) ? 12 : 0;
    }}
    return {{
      id: n.id,
      size: n.size * sizeMult,
      font: {{ size: fontSz }}
    }};
  }});
  nodesDS.update(updatedNodes);
}}

function updatePhysics3D() {{
  if (!graph3DInstance) return;
  const rep = parseInt(document.getElementById('slide-repulsion-3d').value);
  const dist = parseInt(document.getElementById('slide-distance-3d').value);
  document.getElementById('val-repulsion-3d').textContent = rep;
  document.getElementById('val-distance-3d').textContent = dist;
  
  graph3DInstance.d3Force('charge').strength(rep);
  graph3DInstance.d3Force('link').distance(dist);
  graph3DInstance.numDimensions(3); 
}}

function updateDisplay3D() {{
  if (!graph3DInstance) return;
  const sizeMult = parseFloat(document.getElementById('slide-size-3d').value);
  const particles = parseInt(document.getElementById('slide-particles-3d').value);
  const speed = parseFloat(document.getElementById('slide-speed-3d').value);
  
  document.getElementById('val-size-3d').textContent = sizeMult.toFixed(1);
  document.getElementById('val-particles-3d').textContent = particles;
  document.getElementById('val-speed-3d').textContent = speed.toFixed(1);
  
  graph3DInstance
    .nodeVal(node => node.val * sizeMult)
    .linkDirectionalParticles(particles)
    .linkDirectionalParticleSpeed(particles > 0 ? speed * 0.005 : 0);
}}

function switchMode(mode) {{
  const graph2d = document.getElementById('graph');
  const graph3d = document.getElementById('graph-3d');
  const btn2d = document.getElementById('btn-2d');
  const btn3d = document.getElementById('btn-3d');
  
  if (mode === '2d') {{
    graph3d.style.display = 'none';
    graph2d.style.display = 'block';
    btn3d.classList.remove('active');
    btn2d.classList.add('active');
    document.getElementById('settings-2d').style.display = 'block';
    document.getElementById('settings-3d').style.display = 'none';
  }} else if (mode === '3d') {{
    btn2d.classList.remove('active');
    btn3d.classList.add('active');
    
    if (!scriptLoaded) {{
      const originalText = btn3d.textContent;
      btn3d.textContent = 'Loading 3D...';
      btn3d.disabled = true;
      loadScript('https://unpkg.com/3d-force-graph@1.73.3/dist/3d-force-graph.min.js', () => {{
        scriptLoaded = true;
        btn3d.textContent = originalText;
        btn3d.disabled = false;
        graph2d.style.display = 'none';
        graph3d.style.display = 'block';
        document.getElementById('settings-2d').style.display = 'none';
        document.getElementById('settings-3d').style.display = 'block';
        init3DGraph();
      }});
    }} else {{
      graph2d.style.display = 'none';
      graph3d.style.display = 'block';
      document.getElementById('settings-2d').style.display = 'none';
      document.getElementById('settings-3d').style.display = 'block';
      if (graph3DInstance) {{
        graph3DInstance.resumeAnimation();
      }}
    }}
  }}
}}

function init3DGraph() {{
  const container = document.getElementById('graph-3d');
  const activeNodes = RAW_NODES.filter(n => !isNodeHidden(n));
  const activeNodeIds = new Set(activeNodes.map(n => n.id));
  const activeEdges = RAW_EDGES.filter(e => activeNodeIds.has(e.from) && activeNodeIds.has(e.to)
    && (currentLens !== 'calls' || REL_WHITELIST.has((e.label || '').toLowerCase())));

  const gData = {{
    nodes: activeNodes.map(n => ({{
      id: n.id,
      label: n.label,
      color: nodeDisplayColor(n),
      val: n.size,
      community: n.community,
      community_name: n.community_name,
      source_file: n.source_file,
      file_type: n.file_type,
      degree: n.degree
    }})),
    links: activeEdges.map((e, idx) => ({{
      id: idx,
      source: e.from,
      target: e.to,
      label: e.label,
      title: e.title,
      color: e.color ? `rgba(255,255,255,${{e.color.opacity || 0.4}})` : 'rgba(255,255,255,0.4)',
      width: e.width || 1
    }}))
  }};

  const sizeMult = parseFloat(document.getElementById('slide-size-3d').value);
  const rep = parseInt(document.getElementById('slide-repulsion-3d').value);
  const dist = parseInt(document.getElementById('slide-distance-3d').value);
  const particles = parseInt(document.getElementById('slide-particles-3d').value);
  const speed = parseFloat(document.getElementById('slide-speed-3d').value);

  graph3DInstance = ForceGraph3D({{ controlType: 'orbit' }})(container)
    .backgroundColor('#0f0f1a')
    .graphData(gData)
    .nodeLabel(node => `<div style="padding: 6px; background: rgba(26,26,46,0.9); border: 1px solid #3a3a5e; border-radius: 4px; color: #fff; font-family: sans-serif; font-size: 12px;"><b>${{esc(node.label)}}</b><br/>Type: ${{esc(node.file_type || 'unknown')}}<br/>Community: ${{esc(node.community_name)}}</div>`)
    .nodeColor(node => node.color)
    .nodeVal(node => node.val * sizeMult)
    .linkWidth(link => link.width)
    .linkColor(link => link.color)
    .linkOpacity(0.4)
    .linkDirectionalArrowLength(3.5)
    .linkDirectionalArrowRelPos(1)
    .linkDirectionalParticles(particles)
    .linkDirectionalParticleSpeed(particles > 0 ? speed * 0.005 : 0)
    .onNodeClick(node => {{
      const distance = 80;
      const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
      graph3DInstance.cameraPosition(
        {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }},
        node,
        1000
      );
      showInfo(node.id);
    }});

  // Apply physics slider settings on first init
  graph3DInstance.d3Force('charge').strength(rep);
  graph3DInstance.d3Force('link').distance(dist);
}}

function update3DGraphData() {{
  if (!graph3DInstance) return;
  const activeNodes = RAW_NODES.filter(n => !isNodeHidden(n));
  const activeNodeIds = new Set(activeNodes.map(n => n.id));
  const activeEdges = RAW_EDGES.filter(e => activeNodeIds.has(e.from) && activeNodeIds.has(e.to)
    && (currentLens !== 'calls' || REL_WHITELIST.has((e.label || '').toLowerCase())));

  graph3DInstance.graphData({{
    nodes: activeNodes.map(n => ({{
      id: n.id,
      label: n.label,
      color: nodeDisplayColor(n),
      val: n.size,
      community: n.community,
      community_name: n.community_name,
      source_file: n.source_file,
      file_type: n.file_type,
      degree: n.degree
    }})),
    links: activeEdges.map((e, idx) => ({{
      id: idx,
      source: e.from,
      target: e.to,
      label: e.label,
      title: e.title,
      color: e.color ? `rgba(255,255,255,${{e.color.opacity || 0.4}})` : 'rgba(255,255,255,0.4)',
      width: e.width || 1
    }}))
  }});
}}

</script>"""


_CONFIDENCE_SCORE_DEFAULTS = {"EXTRACTED": 1.0, "INFERRED": 0.5, "AMBIGUOUS": 0.2}


def attach_hyperedges(G: nx.Graph, hyperedges: list) -> None:
    """Store hyperedges in the graph's metadata dict."""
    existing = G.graph.get("hyperedges", [])
    seen_ids = {h["id"] for h in existing}
    for h in hyperedges:
        if h.get("id") and h["id"] not in seen_ids:
            existing.append(h)
            seen_ids.add(h["id"])
    G.graph["hyperedges"] = existing


def _git_head() -> str | None:
    """Return the current git HEAD commit hash, or None if not in a git repo."""
    import subprocess as _sp
    try:
        r = _sp.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=3)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def to_json(G: nx.Graph, communities: dict[int, list[str]], output_path: str, *, force: bool = False, built_at_commit: str | None = None, community_labels: dict[int, str] | None = None) -> bool:
    # Safety check: refuse to silently shrink an existing graph (#479)
    existing_path = Path(output_path)
    if not force and existing_path.exists():
        try:
            from graphify.security import check_graph_file_size_cap
            check_graph_file_size_cap(existing_path)
            existing_data = json.loads(existing_path.read_text(encoding="utf-8"))
            existing_n = len(existing_data.get("nodes", []))
            new_n = G.number_of_nodes()
            if new_n < existing_n:
                import sys as _sys
                print(
                    f"[graphify] WARNING: new graph has {new_n} nodes but existing "
                    f"graph.json has {existing_n} (net -{existing_n - new_n}). "
                    f"Refusing to overwrite. Possible causes: missing chunk files from "
                    f"a previous session, or fuzzy dedup collapsed same-named symbols "
                    f"across files during an --update on an already-current graph. "
                    f"Run a full rebuild (/graphify .) to be safe, or pass force=True "
                    f"only if you have verified the reduction is legitimate.",
                    file=_sys.stderr,
                )
                return False
        except Exception:
            pass  # unreadable existing file — proceed with write

    node_community = _node_community_map(communities)
    _labels: dict[int, str] = {int(k): v for k, v in (community_labels or {}).items()}
    try:
        data = json_graph.node_link_data(G, edges="links")
    except TypeError:
        data = json_graph.node_link_data(G)
    for node in data["nodes"]:
        cid = node_community.get(node["id"])
        node["community"] = cid
        if cid is not None and _labels:
            node["community_name"] = _labels.get(cid, f"Community {cid}")
        node["norm_label"] = _strip_diacritics(node.get("label", "")).lower()
    for link in data["links"]:
        if "confidence_score" not in link:
            conf = link.get("confidence", "EXTRACTED")
            link["confidence_score"] = _CONFIDENCE_SCORE_DEFAULTS.get(conf, 1.0)
        # Restore original edge direction. Undirected NetworkX storage may
        # canonicalize endpoint order, flipping `calls` and other directional
        # edges in graph.json. The build path stashes the true endpoints in
        # _src/_tgt for exactly this purpose (#563).
        true_src = link.pop("_src", None)
        true_tgt = link.pop("_tgt", None)
        if true_src is not None and true_tgt is not None:
            link["source"] = true_src
            link["target"] = true_tgt
    data["hyperedges"] = getattr(G, "graph", {}).get("hyperedges", [])
    commit = built_at_commit if built_at_commit is not None else _git_head()
    if commit:
        data["built_at_commit"] = commit
    with open(output_path, "w", encoding="utf-8") as f:  # nosec
        json.dump(data, f, indent=2)
    return True


def prune_dangling_edges(graph_data: dict) -> tuple[dict, int]:
    """Remove edges whose source or target node is not in the node set.

    Returns the cleaned graph_data dict and the number of pruned edges.
    """
    node_ids = {n["id"] for n in graph_data["nodes"]}
    links_key = "links" if "links" in graph_data else "edges"
    before = len(graph_data[links_key])
    graph_data[links_key] = [
        e for e in graph_data[links_key]
        if e["source"] in node_ids and e["target"] in node_ids
    ]
    return graph_data, before - len(graph_data[links_key])


def _cypher_escape(s: str) -> str:
    """Escape a string for safe embedding in a Cypher single-quoted literal.

    Handles all characters that could prematurely terminate the literal or
    inject control sequences:
      - `\\` and `'` (literal terminators)
      - newlines/CRs (would break the per-line statement framing)
      - NUL/control bytes (defensive — Neo4j errors on raw NULs)

    Also strips any leading/trailing whitespace that would let an attacker
    break the `;`-terminated statement boundary used by `cypher-shell`.
    Closing `}` and `)` are NOT special inside a single-quoted Cypher string,
    so escaping the quote and backslash correctly is sufficient (a `}` inside
    a properly-closed `'...'` literal is just a character) — but we previously
    missed `\\n` / `\\r` which DO let a payload break out of the statement
    line and inject a fresh MATCH/DELETE on the following line. See F-008.
    """
    # First normalise: drop NUL and other C0 control chars except tab.
    s = "".join(ch for ch in s if ch >= " " or ch == "\t")
    return (
        s.replace("\\", "\\\\")
         .replace("'", "\\'")
         .replace("\n", "\\n")
         .replace("\r", "\\r")
    )


# Restrict identifier-position values (labels and relationship types are NOT
# quoted in Cypher and so cannot be safely escaped — they must be allowlisted).
_CYPHER_IDENT_RE = re.compile(r"[^A-Za-z0-9_]")


def _cypher_label(raw: str, fallback: str) -> str:
    """Sanitise a value used in identifier position (node label / rel type).

    Cypher does not provide a way to escape `:Foo` label syntax, so we must
    strip everything except `[A-Za-z0-9_]` and require the result to start
    with a letter; otherwise we fall back to a safe constant.
    """
    cleaned = _CYPHER_IDENT_RE.sub("", raw or "")
    if not cleaned or not cleaned[0].isalpha():
        return fallback
    return cleaned


def to_cypher(G: nx.Graph, output_path: str) -> None:
    lines = ["// Neo4j Cypher import - generated by /graphify", ""]
    for node_id, data in G.nodes(data=True):
        label = _cypher_escape(data.get("label", node_id))
        node_id_esc = _cypher_escape(node_id)
        ftype = _cypher_label(
            (data.get("file_type", "unknown") or "unknown").capitalize(),
            "Entity",
        )
        lines.append(f"MERGE (n:{ftype} {{id: '{node_id_esc}', label: '{label}'}});")
    lines.append("")
    for u, v, data in G.edges(data=True):
        rel = _cypher_label(
            (data.get("relation", "RELATES_TO") or "RELATES_TO").upper(),
            "RELATES_TO",
        )
        conf = _cypher_escape(data.get("confidence", "EXTRACTED"))
        u_esc = _cypher_escape(u)
        v_esc = _cypher_escape(v)
        lines.append(
            f"MATCH (a {{id: '{u_esc}'}}), (b {{id: '{v_esc}'}}) "
            f"MERGE (a)-[:{rel} {{confidence: '{conf}'}}]->(b);"
        )
    with open(output_path, "w", encoding="utf-8") as f:  # nosec
        f.write("\n".join(lines))


def to_html(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_path: str,
    community_labels: dict[int, str] | None = None,
    member_counts: dict[int, int] | None = None,
    node_limit: int | None = None,
    learning_overlay: dict | None = None,
) -> None:
    """Generate an interactive vis.js HTML visualization of the graph.

    Features: node size by degree, click-to-inspect panel, search box,
    community filter, physics clustering by community, confidence-styled edges.
    Raises ValueError if graph exceeds MAX_NODES_FOR_VIZ.

    If member_counts is provided (aggregated community view), node sizes are
    based on community member counts rather than graph degree.

    If node_limit is set and the graph exceeds it, automatically builds an
    aggregated community-level meta-graph instead of raising ValueError.
    """
    limit = node_limit if node_limit is not None else _viz_node_limit()
    if G.number_of_nodes() > limit:
        if node_limit is not None:
            # Build aggregated community meta-graph
            from collections import Counter as _Counter
            import networkx as _nx
            print(f"Graph has {G.number_of_nodes()} nodes (above {limit} limit). Building aggregated community view...")
            node_to_community = {nid: cid for cid, members in communities.items() for nid in members}
            meta = _nx.Graph()
            for cid, members in communities.items():
                meta.add_node(str(cid), label=(community_labels or {}).get(cid, f"Community {cid}"))
            edge_counts = _Counter()
            for u, v in G.edges():
                cu, cv = node_to_community.get(u), node_to_community.get(v)
                if cu is not None and cv is not None and cu != cv:
                    edge_counts[(min(cu, cv), max(cu, cv))] += 1
            for (cu, cv), w in edge_counts.items():
                meta.add_edge(str(cu), str(cv), weight=w,
                              relation=f"{w} cross-community edges", confidence="AGGREGATED")
            if meta.number_of_nodes() <= 1:
                print("Single community - aggregated view not useful. Skipping graph.html.")
                return
            meta_communities = {cid: [str(cid)] for cid in communities}
            mc = {cid: len(members) for cid, members in communities.items()}
            # Remap hyperedges from semantic node IDs to community IDs
            raw_hyperedges = G.graph.get("hyperedges", [])
            if raw_hyperedges:
                remapped = []
                for he in raw_hyperedges:
                    he_members = he.get("nodes", [])
                    comm_ids, seen = [], set()
                    for nid in he_members:
                        c = node_to_community.get(nid)
                        if c is None:
                            continue
                        s = str(c)
                        if s in seen:
                            continue
                        seen.add(s)
                        comm_ids.append(s)
                    if len(comm_ids) < 2:
                        continue
                    remapped.append({
                        "id": he.get("id", ""),
                        "label": he.get("label") or he.get("relation", "").replace("_", " "),
                        "nodes": comm_ids,
                    })
                meta.graph["hyperedges"] = remapped
            to_html(meta, meta_communities, output_path,
                    community_labels=community_labels, member_counts=mc)
            print(f"graph.html written (aggregated: {meta.number_of_nodes()} community nodes, {meta.number_of_edges()} cross-community edges)")
            print("Tip: run `graphify export wiki` for full node-level detail.")
            return
        raise ValueError(
            f"Graph has {G.number_of_nodes()} nodes - too large for HTML viz "
            f"(limit: {limit}). Use --no-viz, raise GRAPHIFY_VIZ_NODE_LIMIT, "
            f"or reduce input size."
        )

    node_community = _node_community_map(communities)
    degree = dict(G.degree())
    max_deg = max(degree.values(), default=1) or 1
    max_mc = (max(member_counts.values(), default=1) or 1) if member_counts else 1

    # Work-memory overlay (derived sidecar). When not passed explicitly, load it
    # best-effort from the sibling .graphify_learning.json next to the output
    # graph.html (which lives beside graph.json). Empty/missing => no learning
    # fields, so the un-annotated render is byte-identical to pre-feature.
    if learning_overlay is None:
        learning_overlay = {}
        try:
            from graphify.reflect import load_learning_overlay as _llo
            learning_overlay = _llo(Path(output_path))
        except Exception:
            learning_overlay = {}
    # Status -> ring color. preferred=green, contested=amber. Tentative gets no
    # ring (it's not yet trustworthy enough to highlight in the map).
    _RING = {"preferred": "#22c55e", "contested": "#f59e0b"}

    # Build nodes list for vis.js
    vis_nodes = []
    for node_id, data in G.nodes(data=True):
        cid = node_community.get(node_id, 0)
        color = COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
        label = sanitize_label(data.get("label", node_id))
        deg = degree.get(node_id, 1)
        if member_counts:
            mc = member_counts.get(cid, 1)
            size = 10 + 30 * (mc / max_mc)
            font_size = 12
        else:
            size = 10 + 30 * (deg / max_deg)
            # Only show label for high-degree nodes by default; others show on hover
            font_size = 12 if deg >= max_deg * 0.15 else 0
        node = {
            "id": node_id,
            "label": label,
            "color": {"background": color, "border": color, "highlight": {"background": "#ffffff", "border": color}},
            "size": round(size, 1),
            "font": {"size": font_size, "color": "#ffffff"},
            "title": _html.escape(label),
            "community": cid,
            "community_name": sanitize_label((community_labels or {}).get(cid, f"Community {cid}")),
            "source_file": sanitize_label(str(data.get("source_file") or "")),
            "file_type": data.get("file_type", ""),
            "degree": deg,
        }
        # Conditional learning fields — only present for annotated nodes, so
        # un-annotated output keeps the exact pre-feature node dict shape.
        entry = learning_overlay.get(str(node_id)) if learning_overlay else None
        if entry:
            status = sanitize_label(str(entry.get("status", "")))
            stale = bool(entry.get("stale"))
            node["learning_status"] = status
            node["learning_stale"] = stale
            ring = _RING.get(status)
            if ring:
                # Status-colored ring via the border; stale => desaturated +
                # dashed (vis.js supports per-node `shapeProperties.borderDashes`).
                if stale:
                    ring = "#9ca3af"
                    node["shapeProperties"] = {"borderDashes": [4, 4]}
                node["borderWidth"] = 3
                node["color"] = {
                    "background": color, "border": ring,
                    "highlight": {"background": "#ffffff", "border": ring},
                }
            # Lesson line appended to the hover title.
            if status == "contested":
                lesson = f"Lesson: contested (useful {entry.get('uses', 0)} / dead-end {entry.get('neg', 0)})"
            elif status == "preferred":
                lesson = f"Lesson: preferred source ({entry.get('uses', 0)} useful, score={entry.get('score', 0)})"
            else:
                lesson = f"Lesson: {status} ({entry.get('uses', 0)} useful)"
            if stale:
                lesson += " [code changed — re-verify]"
            node["title"] = _html.escape(label) + "\n" + _html.escape(sanitize_label(lesson))
        vis_nodes.append(node)

    # Build edges list. Restore original edge direction from _src/_tgt
    # (stashed by build.py for exactly this reason): undirected NetworkX
    # canonicalizes endpoint order, which would otherwise flip the arrow
    # for `calls` and `rationale_for` in the rendered graph (#563).
    vis_edges = []
    for u, v, data in G.edges(data=True):
        confidence = data.get("confidence", "EXTRACTED")
        relation = data.get("relation", "")
        true_src = data.get("_src", u)
        true_tgt = data.get("_tgt", v)
        vis_edges.append({
            "from": true_src,
            "to": true_tgt,
            "label": relation,
            "title": _html.escape(f"{relation} [{confidence}]"),
            "dashes": confidence != "EXTRACTED",
            "width": 2 if confidence == "EXTRACTED" else 1,
            "color": {"opacity": 0.7 if confidence == "EXTRACTED" else 0.35},
            "confidence": confidence,
        })

    # Build community legend data
    legend_data = []
    for cid in sorted((community_labels or {}).keys()):
        color = COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
        lbl = _html.escape(sanitize_label((community_labels or {}).get(cid, f"Community {cid}")))
        n = member_counts.get(cid, len(communities.get(cid, []))) if member_counts else len(communities.get(cid, []))
        legend_data.append({"cid": cid, "color": color, "label": lbl, "count": n})

    # Escape </script> sequences so embedded JSON cannot break out of the script tag
    def _js_safe(obj) -> str:
        return json.dumps(obj).replace("</", "<\\/")

    nodes_json = _js_safe(vis_nodes)
    edges_json = _js_safe(vis_edges)
    legend_json = _js_safe(legend_data)
    hyperedges_json = _js_safe(getattr(G, "graph", {}).get("hyperedges", []))
    title = _html.escape(sanitize_label(str(output_path)))
    stats = f"{G.number_of_nodes()} nodes &middot; {G.number_of_edges()} edges &middot; {len(communities)} communities"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>graphify - {title}</title>
<script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"
        integrity="sha384-Ux6phic9PEHJ38YtrijhkzyJ8yQlH8i/+buBR8s3mAZOJrP1gwyvAcIYl3GWtpX1"
        crossorigin="anonymous"></script>
{_html_styles()}
</head>
<body>
<div id="graph"></div>
<div id="graph-3d"></div>
<div id="sidebar">
  <div id="mode-toggle-wrap">
    <button id="btn-2d" class="toggle-btn active" onclick="switchMode('2d')">2D View</button>
    <button id="btn-3d" class="toggle-btn" onclick="switchMode('3d')">3D View</button>
  </div>
  <div id="lens-toggle-wrap">
    <button id="lens-btn-community" class="toggle-btn active lens-btn" onclick="switchLens('community')" title="Group/color by inferred community">Community</button>
    <button id="lens-btn-file" class="toggle-btn lens-btn" onclick="switchLens('file')" title="Group/color by source file">File</button>
    <button id="lens-btn-deps" class="toggle-btn lens-btn" onclick="switchLens('deps')" title="Collapse to one node per file, edges = calls/imports/references/extends between files">Dependencies</button>
    <button id="lens-btn-calls" class="toggle-btn lens-btn" onclick="switchLens('calls')" title="Code symbols only (functions/classes/methods) — hides concept/rationale/document nodes, edges = real calls/imports/references between symbols">Calls</button>
  </div>
  <div id="search-wrap">
    <input id="search" type="text" placeholder="Search nodes..." autocomplete="off">
    <div id="search-results"></div>
  </div>
  <div id="info-panel">
    <h3>Node Info</h3>
    <div id="info-content"><span class="empty">Click a node to inspect it</span></div>
  </div>
  <div id="settings-wrap" class="collapsible-section">
    <h3 onclick="toggleSection('settings-content')">⚙️ Settings <span id="settings-arrow">▶</span></h3>
    <div id="settings-content" style="display: none; padding: 12px; border-bottom: 1px solid #2a2a4e; overflow-y: auto; max-height: 250px;">
      <!-- 2D settings group -->
      <div id="settings-2d">
        <div class="slider-group">
          <label>Node Repulsion: <span id="val-repulsion">-60</span></label>
          <input type="range" id="slide-repulsion" min="-300" max="-10" value="-60" oninput="updatePhysics2D()">
        </div>
        <div class="slider-group">
          <label>Link Distance: <span id="val-distance">120</span></label>
          <input type="range" id="slide-distance" min="30" max="300" value="120" oninput="updatePhysics2D()">
        </div>
        <div class="slider-group">
          <label>Node Size Mult: <span id="val-size">1.0</span></label>
          <input type="range" id="slide-size" min="0.2" max="3.0" step="0.1" value="1.0" oninput="updateDisplay2D()">
        </div>
        <div class="slider-group">
          <label>Link Thickness: <span id="val-thickness">1.0</span></label>
          <input type="range" id="slide-thickness" min="0.2" max="3.0" step="0.1" value="1.0" oninput="updateDisplay2D()">
        </div>
        <div class="checkbox-group">
          <label><input type="checkbox" id="check-labels" checked onchange="updateDisplay2D()"> Show Labels</label>
        </div>
      </div>
      <!-- 3D settings group -->
      <div id="settings-3d" style="display: none;">
        <div class="slider-group">
          <label>Node Scale: <span id="val-size-3d">1.0</span></label>
          <input type="range" id="slide-size-3d" min="0.2" max="3.0" step="0.1" value="1.0" oninput="updateDisplay3D()">
        </div>
        <div class="slider-group">
          <label>Repulsion (3D): <span id="val-repulsion-3d">-150</span></label>
          <input type="range" id="slide-repulsion-3d" min="-1000" max="-10" value="-150" oninput="updatePhysics3D()">
        </div>
        <div class="slider-group">
          <label>Link Distance (3D): <span id="val-distance-3d">50</span></label>
          <input type="range" id="slide-distance-3d" min="10" max="250" value="50" oninput="updatePhysics3D()">
        </div>
        <div class="slider-group">
          <label>Particles Count: <span id="val-particles-3d">0</span></label>
          <input type="range" id="slide-particles-3d" min="0" max="6" value="0" oninput="updateDisplay3D()">
        </div>
        <div class="slider-group">
          <label>Particle Speed: <span id="val-speed-3d">1.0</span></label>
          <input type="range" id="slide-speed-3d" min="0.1" max="3.0" step="0.1" value="1.0" oninput="updateDisplay3D()">
        </div>
      </div>
    </div>
  </div>
  <div id="legend-wrap">
    <h3 id="legend-title">Communities</h3>
    <div id="legend-controls">
      <label><input type="checkbox" id="select-all-cb" checked onchange="toggleAllGroups(!this.checked)">Select All</label>
    </div>
    <div id="legend"></div>
  </div>
  <div id="stats">{stats}</div>
</div>
{_html_script(nodes_json, edges_json, legend_json)}
{_hyperedge_script(hyperedges_json)}
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")  # nosec


# Keep backward-compatible alias - skill.md calls generate_html
generate_html = to_html


def push_to_neo4j(
    G: nx.Graph,
    uri: str,
    user: str,
    password: str,
    communities: dict[int, list[str]] | None = None,
) -> dict[str, int]:
    """Push graph directly to a running Neo4j instance via the Python driver.

    Requires: pip install neo4j

    Uses MERGE so re-running is safe - nodes and edges are upserted, not duplicated.
    Returns a dict with counts of nodes and edges pushed.
    """
    try:
        from neo4j import GraphDatabase
    except ImportError as e:
        raise ImportError(
            "neo4j driver not installed. Run: pip install neo4j"
        ) from e

    node_community = _node_community_map(communities) if communities else {}

    def _safe_rel(relation: str) -> str:
        return re.sub(r"[^A-Z0-9_]", "_", relation.upper().replace(" ", "_").replace("-", "_")) or "RELATED_TO"

    def _safe_label(label: str) -> str:
        """Sanitize a Neo4j node label to prevent Cypher injection."""
        sanitized = re.sub(r"[^A-Za-z0-9_]", "", label)
        return sanitized if sanitized else "Entity"

    driver = GraphDatabase.driver(uri, auth=(user, password))
    nodes_pushed = 0
    edges_pushed = 0

    with driver.session() as session:
        for node_id, data in G.nodes(data=True):
            props = {
                k: v for k, v in data.items()
                if isinstance(v, (str, int, float, bool)) and not k.startswith("_")
            }
            props["id"] = node_id
            cid = node_community.get(node_id)
            if cid is not None:
                props["community"] = cid
            ftype = _safe_label(data.get("file_type", "Entity").capitalize())
            session.run(
                f"MERGE (n:{ftype} {{id: $id}}) SET n += $props",
                id=node_id,
                props=props,
            )
            nodes_pushed += 1

        for u, v, data in G.edges(data=True):
            rel = _safe_rel(data.get("relation", "RELATED_TO"))
            props = {
                k: v for k, v in data.items()
                if isinstance(v, (str, int, float, bool)) and not k.startswith("_")
            }
            session.run(
                f"MATCH (a {{id: $src}}), (b {{id: $tgt}}) "
                f"MERGE (a)-[r:{rel}]->(b) SET r += $props",
                src=u,
                tgt=v,
                props=props,
            )
            edges_pushed += 1

    driver.close()
    return {"nodes": nodes_pushed, "edges": edges_pushed}


def push_to_falkordb(
    G: nx.Graph,
    uri: str,
    user: str | None = None,
    password: str | None = None,
    communities: dict[int, list[str]] | None = None,
    graph_name: str = "graphify",
) -> dict[str, int]:
    """Push graph directly to a running FalkorDB instance via the Python SDK.

    Requires: pip install falkordb

    FalkorDB is OpenCypher-compatible, so the MERGE/SET upsert queries are
    identical to push_to_neo4j. Differences from the Neo4j path:
      - connects with FalkorDB(host, port, username, password) instead of a bolt
        driver; only the host/port are read from the URI, so the scheme is
        informational - "falkordb://localhost:6379", "redis://localhost:6379"
        and a bare "localhost:6379" are all equivalent (default port 6379).
      - a named graph is selected via db.select_graph(graph_name) (default
        "graphify"); FalkorDB keys each graph by name in the same instance.
      - queries run via graph.query(cypher, params) - there is no session object.
      - auth is optional (FalkorDB runs without credentials by default), so user
        and password may be None.
      - no APOC: the Neo4j path does not use APOC either, so nothing to port.

    Uses MERGE so re-running is safe - nodes and edges are upserted, not
    duplicated. Returns a dict with counts of nodes and edges pushed.
    """
    try:
        from falkordb import FalkorDB
    except ImportError as e:
        raise ImportError(
            "falkordb SDK not installed. Run: pip install falkordb"
        ) from e

    from urllib.parse import urlparse

    node_community = _node_community_map(communities) if communities else {}

    def _safe_rel(relation: str) -> str:
        return re.sub(r"[^A-Z0-9_]", "_", relation.upper().replace(" ", "_").replace("-", "_")) or "RELATED_TO"

    def _safe_label(label: str) -> str:
        """Sanitize a FalkorDB node label to prevent Cypher injection."""
        sanitized = re.sub(r"[^A-Za-z0-9_]", "", label)
        return sanitized if sanitized else "Entity"

    parsed = urlparse(uri if "://" in uri else f"redis://{uri}")
    # FalkorDB auth is optional. Only send credentials when a password is
    # provided; otherwise connect anonymously and ignore any bolt-style default
    # username (e.g. Neo4j's "neo4j"), which FalkorDB rejects as an unknown ACL
    # user. Credentials embedded in the URI take precedence over the args.
    connect_user = parsed.username or (user if password else None)
    connect_password = parsed.password or (password or None)
    db = FalkorDB(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        username=connect_user,
        password=connect_password,
    )
    graph = db.select_graph(graph_name)
    nodes_pushed = 0
    edges_pushed = 0

    for node_id, data in G.nodes(data=True):
        props = {
            k: v for k, v in data.items()
            if isinstance(v, (str, int, float, bool)) and not k.startswith("_")
        }
        props["id"] = node_id
        cid = node_community.get(node_id)
        if cid is not None:
            props["community"] = cid
        ftype = _safe_label(data.get("file_type", "Entity").capitalize())
        graph.query(
            f"MERGE (n:{ftype} {{id: $id}}) SET n += $props",
            {"id": node_id, "props": props},
        )
        nodes_pushed += 1

    for u, v, data in G.edges(data=True):
        rel = _safe_rel(data.get("relation", "RELATED_TO"))
        props = {
            k: v for k, v in data.items()
            if isinstance(v, (str, int, float, bool)) and not k.startswith("_")
        }
        graph.query(
            f"MATCH (a {{id: $src}}), (b {{id: $tgt}}) "
            f"MERGE (a)-[r:{rel}]->(b) SET r += $props",
            {"src": u, "tgt": v, "props": props},
        )
        edges_pushed += 1

    return {"nodes": nodes_pushed, "edges": edges_pushed}


def to_graphml(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_path: str,
) -> None:
    """Export graph as GraphML - opens in Gephi, yEd, and any GraphML-compatible tool.

    Community IDs are written as a node attribute so Gephi can colour by community.
    Edge confidence (EXTRACTED/INFERRED/AMBIGUOUS) is preserved as an edge attribute.
    """
    H = G.copy()
    node_community = _node_community_map(communities)
    for node_id in H.nodes():
        H.nodes[node_id]["community"] = node_community.get(node_id, -1)
    # Drop internal markers (e.g. the AST-provenance "_origin" tag, #1116, and
    # the "_src"/"_tgt" direction markers) — they are persistence/runtime details,
    # not graph data, and should not leak into the exported file.
    for _, attrs in H.nodes(data=True):
        for k in [k for k in attrs if k.startswith("_")]:
            del attrs[k]
    for _, _, attrs in H.edges(data=True):
        for k in [k for k in attrs if k.startswith("_")]:
            del attrs[k]
    # nx.write_graphml raises ValueError on None attribute values; replace with "".
    for node_id in H.nodes():
        for key, val in list(H.nodes[node_id].items()):
            if val is None:
                H.nodes[node_id][key] = ""
    for u, v in H.edges():
        for key, val in list(H.edges[u, v].items()):
            if val is None:
                H.edges[u, v][key] = ""
    nx.write_graphml(H, output_path)


def to_svg(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_path: str,
    community_labels: dict[int, str] | None = None,
    figsize: tuple[int, int] = (20, 14),
) -> None:
    """Export graph as an SVG file using matplotlib + spring layout.

    Lightweight and embeddable - works in Obsidian notes, Notion, GitHub READMEs,
    and any markdown renderer. No JavaScript required.

    Node size scales with degree. Community colors match the HTML output.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError as e:
        raise ImportError("matplotlib not installed. Run: pip install matplotlib") from e

    node_community = _node_community_map(communities)

    fig, ax = plt.subplots(figsize=figsize, facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.axis("off")

    pos = nx.spring_layout(G, seed=42, k=2.0 / (G.number_of_nodes() ** 0.5 + 1))

    degree = dict(G.degree())
    max_deg = max(degree.values(), default=1) or 1

    node_colors = [COMMUNITY_COLORS[node_community.get(n, 0) % len(COMMUNITY_COLORS)] for n in G.nodes()]
    node_sizes = [300 + 1200 * (degree.get(n, 1) / max_deg) for n in G.nodes()]

    # Draw edges - dashed for non-EXTRACTED
    for u, v, data in G.edges(data=True):
        conf = data.get("confidence", "EXTRACTED")
        style = "solid" if conf == "EXTRACTED" else "dashed"
        alpha = 0.6 if conf == "EXTRACTED" else 0.3
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        ax.plot([x0, x1], [y0, y1], color="#aaaaaa", linewidth=0.8,
                linestyle=style, alpha=alpha, zorder=1)

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=node_sizes, alpha=0.9)
    nx.draw_networkx_labels(G, pos, ax=ax,
                            labels={n: G.nodes[n].get("label", n) for n in G.nodes()},
                            font_size=7, font_color="white")

    # Legend
    if community_labels:
        patches = [
            mpatches.Patch(
                color=COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)],
                label=f"{label} ({len(communities.get(cid, []))})",
            )
            for cid, label in sorted(community_labels.items())
        ]
        ax.legend(handles=patches, loc="upper left", framealpha=0.7,
                  facecolor="#2a2a4e", labelcolor="white", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, format="svg", bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
