"""Tests for the Kustomize overlay extractor (Feature 1, IaC indexing) - see
agent-memory/plans/iac-http-linking/design.md. Resolution of `imports` edges
requires the corpus-wide `_resolve_kustomize_imports` pass, so these tests go
through the real `extract()` pipeline, not `extract_kustomization()` alone.
"""
from graphify.extract import extract
from graphify.extractors.kustomization import extract_kustomization


def test_extract_kustomization_produces_module_node(tmp_path):
    f = tmp_path / "kustomization.yaml"
    f.write_text("resources:\n  - deployment.yaml\n")
    result = extract_kustomization(f)
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["type"] == "module"
    assert result["nodes"][0]["metadata"]["kind"] == "kustomize_overlay"


def test_extract_kustomization_dispatches_from_extract_module(tmp_path):
    f = tmp_path / "kustomization.yaml"
    f.write_text("resources:\n  - deployment.yaml\n")
    result = extract([str(f)])
    module_nodes = [n for n in result["nodes"] if n.get("type") == "module"]
    assert len(module_nodes) == 1


def test_extract_kustomization_imports_edge_resolves_to_target_file(tmp_path):
    kustom = tmp_path / "kustomization.yaml"
    kustom.write_text("resources:\n  - deployment.yaml\n  - service.yaml\n")
    deployment = tmp_path / "deployment.yaml"
    deployment.write_text("apiVersion: apps/v1\nkind: Deployment\n")
    service = tmp_path / "service.yaml"
    service.write_text("apiVersion: v1\nkind: Service\n")

    result = extract([str(kustom), str(deployment), str(service)])
    module_nid = next(n["id"] for n in result["nodes"] if n.get("type") == "module")
    # source_file may get shortened to a basename for deeply-nested paths
    # (extract()'s own post-processing) - match by basename, same tolerance
    # the resolver itself uses.
    deployment_file_nid = next(
        n["id"] for n in result["nodes"]
        if n["source_file"].endswith(deployment.name) and n["source_location"] == "L1"
    )
    service_file_nid = next(
        n["id"] for n in result["nodes"]
        if n["source_file"].endswith(service.name) and n["source_location"] == "L1"
    )
    import_edges = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "imports"}
    assert (module_nid, deployment_file_nid) in import_edges
    assert (module_nid, service_file_nid) in import_edges


def test_extract_kustomization_missing_target_produces_no_dangling_edge(tmp_path):
    """A `resources:` entry pointing at a file not in the corpus (excluded,
    renamed, outside the scan root) must be skipped, not produce a dangling
    edge to a node that doesn't exist."""
    kustom = tmp_path / "kustomization.yaml"
    kustom.write_text("resources:\n  - missing.yaml\n")
    result = extract([str(kustom)])
    import_edges = [e for e in result["edges"] if e["relation"] == "imports"]
    assert import_edges == []
