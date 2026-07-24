"""Tests for the YAML extractor (P2). YAML previously had no extractor at
all — .yaml/.yml files were invisible to the graph (0 nodes, confirmed on a
real Home-Assistant repo during P2's investigation). See
agent-memory/plans/p2-yaml-extraction.md.
"""
from graphify.extractors.yaml_ import extract_yaml


def test_extract_yaml_top_level_key_produces_node(tmp_path):
    f = tmp_path / "config.yaml"
    f.write_text("automation:\n  - alias: Turn on lights\n")
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "automation" in labels


def test_extract_yaml_list_item_uses_alias_as_label(tmp_path):
    f = tmp_path / "automations.yaml"
    f.write_text(
        "automation:\n"
        "  - alias: Turn on lights\n"
        "    trigger:\n"
        "      platform: state\n"
        "  - alias: Living room AC timer\n"
        "    id: living_room_ac_timer\n"
    )
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "Turn on lights" in labels
    assert "Living room AC timer" in labels


def test_extract_yaml_list_item_without_label_key_falls_back_to_position(tmp_path):
    f = tmp_path / "no_alias.yaml"
    f.write_text("items:\n  - foo: bar\n  - baz: qux\n")
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "items[0]" in labels
    assert "items[1]" in labels


def test_extract_yaml_nested_mapping_key_uses_name_field(tmp_path):
    """Home Assistant's timer: entity_id: {name: ...} shape — a mapping
    (not a list) under a top-level key, each sub-key a named entity.
    """
    f = tmp_path / "timers.yaml"
    f.write_text(
        "timer:\n"
        "  living_room_ac_cleanup:\n"
        '    name: "Living Room AC Cleanup"\n'
        "    icon: mdi:fan-clock\n"
    )
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "Living Room AC Cleanup" in labels


def test_extract_yaml_nested_mapping_key_without_name_falls_back_to_key(tmp_path):
    f = tmp_path / "scripts.yaml"
    f.write_text("script:\n  another_script:\n    sequence:\n      - delay: 5\n")
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "another_script" in labels


def test_extract_yaml_edges_connect_file_to_top_level_to_items(tmp_path):
    f = tmp_path / "chain.yaml"
    f.write_text("automation:\n  - alias: Test automation\n")
    result = extract_yaml(f)
    by_label = {n["label"]: n["id"] for n in result["nodes"]}
    file_id = by_label["chain.yaml"]
    auto_id = by_label["automation"]
    item_id = by_label["Test automation"]
    relations = {(e["source"], e["target"]) for e in result["edges"]}
    assert (file_id, auto_id) in relations
    assert (auto_id, item_id) in relations


def test_extract_yaml_empty_file_produces_only_file_node(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    result = extract_yaml(f)
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["label"] == "empty.yaml"
    assert result.get("error") is None


def test_extract_yaml_multi_document_extracts_both_documents(tmp_path):
    """`---`-separated multi-document YAML (the shape Kubernetes manifests
    commonly use to bundle multiple resources in one file) must extract every
    document, not just the first. Regression test for the bug found while
    designing K8s Resource-node typing (agent-memory/plans/iac-http-linking/).
    """
    f = tmp_path / "multi.yaml"
    f.write_text("first_key: 1\n---\nsecond_key: 2\n")
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "first_key" in labels
    assert "second_key" in labels


def test_extract_yaml_multi_document_with_shared_keys_does_not_collide(tmp_path):
    """Kubernetes manifests routinely repeat `apiVersion`/`kind`/`spec` across
    documents in the same file - both documents' nodes must exist
    independently, not collapse into one shared node."""
    f = tmp_path / "k8s.yaml"
    f.write_text("kind: Deployment\nspec:\n  replicas: 1\n---\nkind: Service\nspec:\n  port: 80\n")
    result = extract_yaml(f)
    kind_nodes = [n for n in result["nodes"] if n["label"] == "kind"]
    spec_nodes = [n for n in result["nodes"] if n["label"] == "spec"]
    assert len(kind_nodes) == 2
    assert len(spec_nodes) == 2
    assert kind_nodes[0]["id"] != kind_nodes[1]["id"]
    assert spec_nodes[0]["id"] != spec_nodes[1]["id"]
    # each document's spec sub-key (replicas vs port) must exist, proving the
    # second document's nested content was extracted too, not just its top key
    labels = [n["label"] for n in result["nodes"]]
    assert "replicas" in labels
    assert "port" in labels


def test_extract_yaml_k8s_manifest_gets_typed_resource_node(tmp_path):
    """apiVersion + kind at top level -> additive Resource node, alongside
    the existing generic per-key nodes (not replacing them)."""
    f = tmp_path / "deployment.yaml"
    f.write_text(
        "apiVersion: apps/v1\n"
        "kind: Deployment\n"
        "metadata:\n"
        "  name: my-app\n"
    )
    result = extract_yaml(f)
    resource_nodes = [n for n in result["nodes"] if n.get("type") == "resource"]
    assert len(resource_nodes) == 1
    assert resource_nodes[0]["label"] == "Deployment my-app"
    assert resource_nodes[0]["metadata"]["kind"] == "Deployment"
    assert resource_nodes[0]["metadata"]["api_version"] == "apps/v1"
    # generic per-key nodes must still exist (additive, not replaced)
    labels = [n["label"] for n in result["nodes"]]
    assert "apiVersion" in labels
    assert "kind" in labels
    assert "metadata" in labels


def test_extract_yaml_non_k8s_yaml_gets_no_resource_node(tmp_path):
    f = tmp_path / "config.yaml"
    f.write_text("automation:\n  - alias: Turn on lights\n")
    result = extract_yaml(f)
    resource_nodes = [n for n in result["nodes"] if n.get("type") == "resource"]
    assert resource_nodes == []


def test_extract_yaml_multi_doc_k8s_gets_one_resource_node_per_document(tmp_path):
    f = tmp_path / "bundle.yaml"
    f.write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: web\n"
        "---\n"
        "apiVersion: v1\nkind: Service\nmetadata:\n  name: web-svc\n"
    )
    result = extract_yaml(f)
    resource_nodes = [n for n in result["nodes"] if n.get("type") == "resource"]
    assert len(resource_nodes) == 2
    labels = {n["label"] for n in resource_nodes}
    assert labels == {"Deployment web", "Service web-svc"}


def test_extract_yaml_dispatches_from_extract_module(tmp_path):
    """.yaml/.yml must actually be wired into the main dispatch table, not
    just exist as a standalone function nobody calls."""
    from graphify.extract import extract

    f = tmp_path / "wired.yaml"
    f.write_text("key: value\n")
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert "wired.yaml" in labels
