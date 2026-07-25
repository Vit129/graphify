# Plan: P13 — Lazy-Loaded 3D Force Graph Option (Additive, Opt-In)

We need to add a "3D View" visualization option to the graphify HTML output. This design should follow the "Don't force, make it opt-in" philosophy from `codeflow`, keeping a single static HTML file with no extra build steps, Python changes, or generation flags.

---

## 1. Research & Analysis of Existing Visualizers

We cloned and analyzed two candidates to inform this design:

### A. braedonsaunders/codeflow (3,648★)
- **Metaphor/Architecture:** Static 2D force simulation by default (SVG/d3), with a toggle for 3D View using WebGL/Three.js via `3d-force-graph` library.
- **Key Pattern:** It includes `<script src="https://unpkg.com/3d-force-graph" defer></script>` in the page head but doesn't initialize it until the user toggles `graphConfig.vizType === 'graph3d'`. When activated, it spawns `ForceGraph3D({controlType: 'orbit'})(container)` using the exact same node/link schema.
- **Why this fits graphify:** Since graphify exports a single standalone HTML file (`graphify/export.py`), we can bundle both view modes in that one file. To be even more lightweight and not hit the network for unneeded resources, we should **lazy-load** the `3d-force-graph` library script only when the user first clicks "3D View".

### B. MaibornWolff/codecharta (formerly cree.js)
- **Metaphor/Architecture:** The "Code City" metaphor. Every folder is a city block, every file is a building. Dimensions (width/height/depth) and color represent metrics like LOC, complexity, and churn.
- **Why it is out-of-scope for now:** Extremely beautiful, but requires rich metrics data (cyclomatic complexity, commit churn, LOC analysis) to make the building heights and colors meaningful. It has its own complex file parser and visualization studio. This is significantly more complex than a standard force-directed layout and requires generate-time options.

---

## 2. Design Goals

- **Additive & Zero Overhead at Generate Time:** No python-side options or changes to the graph generation pipeline. The generated HTML remains a single self-contained file.
- **Lazy Network Load:** Do NOT load the `3d-force-graph` script from the CDN on page load. Load it dynamically when the "3D View" toggle is clicked. If a user never clicks it, they never download the library.
- **Shared Data & State:** Use the exact same `RAW_NODES`, `RAW_EDGES`, and community datasets. If a node is selected or filtered in the sidebar, both 2D and 3D views should reflect this selection/filter state seamlessly.
- **Dark Mode Aesthetics:** Ensure the 3D canvas integrates beautifully with graphify's dark cyberpunk theme (cyberpunk/slate colors, glowing nodes, translucent edges).

---

## 3. Detailed Implementation Tasks

### Step 1: Update UI Layout & CSS (`graphify/export.py`)
- Add a `#graph-3d` container hidden by default (`display: none; width: 100%; height: 100%`) alongside `#graph`.
- In the sidebar header or next to the search wrap, add a "Switch to 3D View" button/toggle.
- Add CSS styling for the toggle button (cyberpunk slate button with hover glow).

### Step 2: Dynamic Script Loader (`graphify/export.py`)
- Write a Javascript helper `loadScript(url, callback)` that injects a `<script>` tag and triggers a callback when loaded.
- Point to the latest stable CDN: `https://unpkg.com/3d-force-graph@1.73.3/dist/3d-force-graph.min.js`.

### Step 3: 3D Force Graph Initialization
- When toggling to 3D:
  - If the library is not yet loaded, load it.
  - Hide `#graph` (vis.js container), show `#graph-3d`.
  - Create the `ForceGraph3D` instance on `#graph-3d`.
  - Supply the data by mapping `RAW_NODES` and `RAW_EDGES` to 3D properties.
  - Setup node color mapping using the vis.js community color logic.
  - Scale node size based on degree or member count (like in 2D).
  - Setup directional arrows on links.

### Step 4: Sync Interactive State (Click/Search/Filters)
- **Node Clicks:** Attach `onNodeClick` handler to focus on the clicked node, highlight it, and trigger the existing `showInfo(nodeId)` sidebar update.
- **Search Focus:** If a user searches and clicks a node in the search results, focus the 3D camera onto that node position using `graph.cameraPosition({ x, y, z }, lookAt, duration)`.
- **Community Filters:** When checkboxes are toggled, sync filtered nodes to the 3D graph (using `.graphData({ nodes: activeNodes, links: activeLinks })`).
- **Toggle Back:** Allow toggling back to 2D view by hiding `#graph-3d` and showing `#graph`.

---

## 4. Verification & Validation Plan

1. **Build & Syntax Verification:** Compile Python and ensure no lint errors.
2. **Visual Inspection:**
   - Run graphify on an existing project (e.g. `graphify update .`) to generate a new `graph.html`.
   - Open `graph.html` in Chrome.
   - Verify 2D works as normal, network tab does NOT show `3d-force-graph` download.
   - Click "3D View", verify script loads, 3D canvas initializes, and renders the nodes.
   - Test toggle back to 2D.
3. **Interactivity Check:**
   - Click a node in 3D: verify sidebar info updates.
   - Filter a community: verify nodes in 3D are added/removed.
   - Search a node: verify focus changes.
