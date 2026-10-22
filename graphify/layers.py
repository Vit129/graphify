"""Architecture-layer heuristic: group files by well-known directory names.

No LLM. A path belongs to the first layer (in LAYER_RULES order) that has a
directory segment equal to one of its names, singular or plural. Unmatched
paths fall into "Core".
"""
from __future__ import annotations

from collections import Counter, defaultdict

import networkx as nx

LAYER_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("API", "HTTP endpoints, route handlers, controllers", ("route", "controller", "handler", "endpoint", "api")),
    ("Service", "Business logic and application services", ("service", "usecase", "use-case", "business")),
    ("Data", "Models, database access, persistence", ("model", "entity", "schema", "database", "db", "migration", "repository", "repo")),
    ("UI", "User interface components and views", ("component", "view", "page", "screen", "layout", "widget", "ui")),
    ("Middleware", "Request/response middleware and interceptors", ("middleware", "interceptor", "guard", "filter", "pipe")),
    ("External", "Third-party integrations, SDKs, adapters", ("client", "integration", "external", "sdk", "vendor", "adapter")),
    ("Background", "Workers, jobs, queues, schedulers", ("worker", "job", "queue", "cron", "consumer", "processor", "scheduler", "background")),
    ("Utility", "Shared helpers and common libraries", ("util", "helper", "lib", "common", "shared")),
    ("Test", "Tests and test utilities", ("test", "spec", "__test__", "__spec__", "__tests__", "__specs__")),
    ("Config", "Configuration and environment settings", ("config", "setting", "env")),
]
LAYER_COLORS = {
    "API": "#4e9bff", "Service": "#43c478", "Data": "#f0a04b", "UI": "#e86fb0",
    "Middleware": "#9b7bf0", "External": "#2fc6c0", "Background": "#e6cf4f",
    "Utility": "#9aa3b2", "Test": "#6c7a96", "Config": "#b9835a", "Core": "#7fb7e6",
}
_DESCRIPTIONS = {name: desc for name, desc, _ in LAYER_RULES}
_DESCRIPTIONS["Core"] = "Core application code (no layer-style directory name)"


def layer_of_path(path: str) -> str:
    segments = path.replace("\\", "/").lower().split("/")[:-1]
    for name, _, words in LAYER_RULES:
        for seg in segments:
            if any(seg == w or seg == w + "s" for w in words):
                return name
    return "Core"


def detect_layers(G: nx.Graph) -> list[dict]:
    """Return [{name, description, node_count, files}] for layers that have nodes, largest first."""
    counts: Counter = Counter()
    files: dict[str, Counter] = defaultdict(Counter)
    for _, data in G.nodes(data=True):
        src = data.get("source_file")
        if not src:
            continue
        layer = layer_of_path(src)
        counts[layer] += 1
        files[layer][src] += 1
    return [
        {
            "name": name,
            "description": _DESCRIPTIONS[name],
            "node_count": n,
            "files": [f for f, _ in files[name].most_common(5)],
        }
        for name, n in counts.most_common()
    ]
