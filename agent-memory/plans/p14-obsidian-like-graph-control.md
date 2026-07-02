# P14: Obsidian-like Graph Control & Automation

This plan designs and implements Obsidian-like graph interaction features in `graphify`. The target is to make graph generation, visualization, and parameter tuning effortless and highly interactive.

---

## 1. Goals
*   **Auto-Open Browser on Build:** Open the generated `graph.html` automatically in the user's default browser after successful CLI commands (`update`, `extract`, `cluster-only`), unless `--no-open` is supplied.
*   **Live Update (Auto-Reload):** Automatically reload open browser tabs displaying `graph.html` on macOS when a new build completes, avoiding the need for manual refreshes.
*   **Interactive Control Panel:** Embed a collapsible settings panel in `graph.html` allowing real-time adjustment of graph physics and styling parameters via sliders.

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
