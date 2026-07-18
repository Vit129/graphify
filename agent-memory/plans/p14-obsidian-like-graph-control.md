# P14: Obsidian-like Graph Control & Automation

Status: **Done** — all 4 goals shipped (structural view mode 2026-07-04 per its own note below; auto-open/
live-reload/interactive settings panel landed in `e4e4f9c feat: implement Obsidian-like control panel,
auto-open browser, and live reload` and `d79b6fb feat: add lazy-loaded 3D force graph view option to HTML
export`). This doc was never updated when that work landed — verified live in `graphify/__main__.py`
(`--no-open`, `webbrowser.open`, `osascript` Chrome/Safari reload) and `graphify/export.py`
(`#settings-2d`/`#settings-3d` panels with `gravitationalConstant`/`springLength` sliders) during the
2026-07-18 session, corrected here rather than left stale.

This plan designs and implements Obsidian-like graph interaction features in `graphify`. The target is to make graph generation, visualization, and parameter tuning effortless and highly interactive.

---

## 1. Goals
*   **Auto-Open Browser on Build:** Open the generated `graph.html` automatically in the user's default browser after successful CLI commands (`update`, `extract`, `cluster-only`), unless `--no-open` is supplied.
*   **Live Update (Auto-Reload):** Automatically reload open browser tabs displaying `graph.html` on macOS when a new build completes, avoiding the need for manual refreshes.
*   **Interactive Control Panel:** Embed a collapsible settings panel in `graph.html` allowing real-time adjustment of graph physics and styling parameters via sliders.
*   **Structural (non-community) View Mode** — **DONE (2026-07-04)**. Added a second lens toggle (`Community` / `File` / `Dependencies`) in `graph.html`'s sidebar, entirely client-side in `_html_script` — no new Python-side computation, so `extract`/`update`/`cluster-only` do no extra work and `graph.html`'s embedded payload is the same size as before:
    *   **File** — recolors every node by `source_file` (deterministic hash → HSL) instead of Leiden community; legend switches to a per-file list (sorted by node count) with the same show/hide checkboxes.
    *   **Dependencies** — collapses to one node per file; edge between file A and file B if any underlying symbol-level edge crossing between them has `relation` in the real vocabulary measured across 3 corpora (Python/YAML, Swift, JS/TS): `calls, imports, imports_from, references, inherits, implements, indirect_call, re_exports, uses, embeds` — deliberately excludes containment/doc relations (`contains, method, defines, case_of, rationale_for`), which aren't file-to-file coupling. Computed lazily in the browser on first click, then cached. This is the same shape of information `graphify export callflow-html` already produces as a separate static Mermaid page — this surfaces it as an interactive lens inside `graph.html` itself.
    *   **Dropped from the original design**: a `type`-based class/struct containment anchor. Checked real data first — `type` is essentially unpopulated (10,130/10,135 nodes have no `type` in the graphify repo's own graph; same story in harness-terminal, My-Investment-Port, Home-Assistant) — so a "class" mode would silently do nothing on ~100% of real nodes. Not implemented rather than shipping something that doesn't work.
    *   3D view is disabled while in Dependencies mode (button grayed out with a tooltip) — the collapsed file-graph isn't wired into the 3D renderer; Community/File both work in 2D and 3D.
    *   Verified: full test suite (2967 passed, 28 skipped, no regressions) + a demo built from Home-Assistant's real committed `graph.json` (read-only — nothing in that repo was touched) sent to the user to click through directly, since sandboxed browser control wasn't available to self-screenshot.

---

## 2. Technical Design

### A. Real-Time Settings UI in `graph.html`
*   Add a settings toggle button (`#settings-btn`) and a collapsible panel (`#settings-panel`) inside the sidebar or as a floating widget.
*   Create a Settings Panel containing:
    *   **2D Settings (vis.js):**
        *   Repulsion Strength (gravitationalConstant)
        *   Link Distance (springLength)
        *   Node Size multiplier
        *   Link Thickness
        *   Show Labels (Toggle font size)
        *   Show Arrows (Toggle arrow visibility)
    *   **3D Settings (3d-force-graph):**
        *   Node Size / Scale
        *   Repulsion Strength (d3Force('charge').strength)
        *   Link Distance (d3Force('link').distance)
        *   Directional Particles (count & speed sliders)
        *   Show Labels (Toggle text sprites)
*   Write event listeners in JavaScript to map slider changes to `network.setOptions` (for 2D) and `Graph3D` property setters (for 3D).

### B. Auto-Open & Live Reload in Python CLI
*   Add `--no-open` to arguments parsing in `__main__.py` under commands `update`, `extract`, and `cluster-only`.
*   After successful output write of `graph.html`, check `no_open`. If false, trigger `webbrowser.open(html_path.absolute().as_uri())`.
*   Implement a macOS-specific `osascript` subprocess that reloads any browser tab matching `graphify-out/graph.html` to achieve instant live refresh.

---

## 3. Implementation Steps

1.  **Modify `graphify/export.py`:**
    *   Inject Control Panel HTML/CSS in `to_html` and `_html_styles`.
    *   Map settings values to vis.js and 3d-force-graph physics configurations in `_html_script`.
2.  **Modify `graphify/__main__.py`:**
    *   Parse `--no-open` flag.
    *   Implement browser opening and AppleScript reload triggers.
3.  **Validate:**
    *   Run tests (`pytest`) in the `graphify` workspace.
    *   Test generation in `/Users/supavit.cho/Git/Personal/My-Investment-Port`.
    *   Test generation in `/Users/supavit.cho/Git/Personal/harness-terminal`.
