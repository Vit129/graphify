from __future__ import annotations

import networkx as nx
from graphify.bridges import resolve_cross_language_bridges
from graphify.build import build_from_json


def test_resolve_react_native_bridge():
    G = nx.DiGraph()
    # Native module in ObjC
    G.add_node(
        "native_mod",
        label="RCT_EXPORT_MODULE(AnalyticsModule)",
        source_file="ios/AnalyticsModule.m",
        file_type="code",
    )
    # JS Caller
    G.add_node(
        "js_fn",
        label="trackEvent() { NativeModules.AnalyticsModule.logEvent('click'); }",
        source_file="src/analytics.ts",
        file_type="function",
    )

    added = resolve_cross_language_bridges(G)
    assert added == 1
    assert G.has_edge("js_fn", "native_mod")
    edge = G.edges["js_fn", "native_mod"]
    assert edge["relation"] == "bridges_to"
    assert edge["context"] == "react_native_bridge"


def test_resolve_swift_objc_bridge():
    G = nx.DiGraph()
    # Swift class with @objc
    G.add_node(
        "swift_class",
        label="@objc class PaymentService",
        source_file="ios/PaymentService.swift",
        file_type="class",
    )
    # ObjC caller referencing PaymentService
    G.add_node(
        "objc_fn",
        label="PaymentService *service = [[PaymentService alloc] init];",
        source_file="ios/LegacyController.m",
        file_type="function",
    )

    added = resolve_cross_language_bridges(G)
    assert added == 1
    assert G.has_edge("objc_fn", "swift_class")
    edge = G.edges["objc_fn", "swift_class"]
    assert edge["relation"] == "bridges_to"
    assert edge["context"] == "objc_bridge"


def test_build_from_json_integrates_bridges():
    extraction = {
        "nodes": [
            {
                "id": "native_mod",
                "label": "RCT_EXPORT_MODULE(Biometrics)",
                "source_file": "ios/Biometrics.m",
                "file_type": "code",
            },
            {
                "id": "js_fn",
                "label": "authenticate() { const mod = requireNativeModule('Biometrics'); }",
                "source_file": "src/auth.ts",
                "file_type": "code",
            },
        ],
        "edges": [],
    }

    G = build_from_json(extraction, directed=True)
    assert G.has_edge("js_fn", "native_mod")
    assert G.edges["js_fn", "native_mod"]["relation"] == "bridges_to"
