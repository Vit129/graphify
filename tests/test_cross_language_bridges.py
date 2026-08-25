from __future__ import annotations

from pathlib import Path

import networkx as nx

from graphify.bridges import resolve_cross_language_bridges
from graphify.build import build_from_json
from graphify.extract import extract_js, extract_objc, extract_swift


def _merge(*extractions: dict) -> dict:
    nodes: list = []
    edges: list = []
    for extraction in extractions:
        nodes.extend(extraction.get("nodes", []))
        edges.extend(extraction.get("edges", []))
    return {"nodes": nodes, "edges": edges}


def test_resolve_react_native_bridge_from_real_extractors(tmp_path: Path):
    """Regression: the old implementation matched RCT_EXPORT_MODULE/NativeModules
    against node *labels*, but real extracted labels are bare symbol names
    ("AnalyticsModule", "trackEvent()") that never contain that source text --
    it silently produced zero edges against any real extractor. This drives
    extract_objc/extract_js for real, not hand-fabricated labels."""
    objc_file = tmp_path / "AnalyticsModule.m"
    objc_file.write_text(
        "#import \"AnalyticsModule.h\"\n"
        "@implementation AnalyticsModule\n"
        "RCT_EXPORT_MODULE(AnalyticsModule)\n"
        "RCT_EXPORT_METHOD(logEvent:(NSString *)name)\n"
        "{\n"
        "}\n"
        "@end\n",
        encoding="utf-8",
    )
    ts_file = tmp_path / "analytics.ts"
    ts_file.write_text(
        "export function trackEvent() {\n"
        "    NativeModules.AnalyticsModule.logEvent('click');\n"
        "}\n",
        encoding="utf-8",
    )

    extraction = _merge(extract_objc(objc_file), extract_js(ts_file))
    G = build_from_json(extraction, directed=True, root=str(tmp_path))

    bridge_edges = [
        (u, v) for u, v, d in G.edges(data=True) if d.get("relation") == "bridges_to"
    ]
    assert bridge_edges, "expected at least one bridges_to edge from a real RN call site"
    assert any(d.get("context") == "react_native_bridge" for _, _, d in G.edges(data=True))


def test_resolve_swift_objc_bridge_from_real_extractors(tmp_path: Path):
    """Regression: same failure class as above for the Swift<->ObjC side --
    @objc lives in the real source text, never in an extracted node label."""
    swift_file = tmp_path / "PaymentService.swift"
    swift_file.write_text(
        "import Foundation\n"
        "@objc class PaymentService: NSObject {\n"
        "    @objc func charge() {}\n"
        "}\n",
        encoding="utf-8",
    )
    objc_file = tmp_path / "LegacyController.m"
    objc_file.write_text(
        "#import \"Bridging-Header.h\"\n"
        "void run(void) {\n"
        "    PaymentService *service = [[PaymentService alloc] init];\n"
        "    [service charge];\n"
        "}\n",
        encoding="utf-8",
    )

    extraction = _merge(extract_swift(swift_file), extract_objc(objc_file))
    G = build_from_json(extraction, directed=True, root=str(tmp_path))

    bridge_edges = [
        (u, v, d) for u, v, d in G.edges(data=True) if d.get("relation") == "bridges_to"
    ]
    assert bridge_edges, "expected at least one bridges_to edge from a real ObjC call site"
    assert any(d.get("context") == "objc_bridge" for _, _, d in bridge_edges)


def test_resolve_cross_language_bridges_no_source_on_disk_is_a_noop():
    """When source files can't be read from disk (no root, relative paths that
    don't resolve), the resolver must degrade to zero edges, not crash --
    mirrors how a stale/incomplete project_path is handled elsewhere."""
    G = nx.DiGraph()
    G.add_node("a", label="AnalyticsModule", source_file="ios/AnalyticsModule.m", source_location="L1")
    G.add_node("b", label="trackEvent()", source_file="src/analytics.ts", source_location="L1")

    added = resolve_cross_language_bridges(G)
    assert added == 0


def test_build_from_json_integrates_bridges_end_to_end(tmp_path: Path):
    """build_from_json wires resolve_cross_language_bridges with the same
    root it resolves every other source_file against, so a real project
    build (not just a hand-built extraction dict) gets working bridge edges."""
    objc_file = tmp_path / "Biometrics.m"
    objc_file.write_text(
        "RCT_EXPORT_MODULE(Biometrics)\n"
        "RCT_EXPORT_METHOD(authenticate:(NSString *)reason)\n"
        "{\n"
        "}\n",
        encoding="utf-8",
    )
    ts_file = tmp_path / "auth.ts"
    ts_file.write_text(
        "export function authenticate() {\n"
        "    const mod = requireNativeModule('Biometrics');\n"
        "    return mod;\n"
        "}\n",
        encoding="utf-8",
    )

    extraction = _merge(extract_objc(objc_file), extract_js(ts_file))
    G = build_from_json(extraction, directed=True, root=str(tmp_path))

    assert any(d.get("relation") == "bridges_to" for _, _, d in G.edges(data=True))


def test_bridge_and_django_resolution_failure_logs_warning_without_aborting(tmp_path: Path, monkeypatch, capsys):
    def broken_bridges(*args, **kwargs):
        raise RuntimeError("simulated bridge resolution error")

    def broken_django(*args, **kwargs):
        raise RuntimeError("simulated django resolution error")

    monkeypatch.setattr("graphify.bridges.resolve_cross_language_bridges", broken_bridges)
    monkeypatch.setattr("graphify.routes.resolve_django_route_handlers", broken_django)

    extraction = {"nodes": [{"id": "a", "label": "A"}], "edges": []}
    G = build_from_json(extraction, directed=True, root=str(tmp_path))
    assert G.has_node("a")

    captured = capsys.readouterr()
    assert "[graphify] Cross-language bridge resolution failed: simulated bridge resolution error" in captured.err
    assert "[graphify] Django route handler resolution failed: simulated django resolution error" in captured.err

