"""Tests for the Dockerfile extractor (Feature 1, IaC indexing). Dockerfile
previously had no extractor and no classification path at all - see
agent-memory/plans/iac-http-linking/design.md.
"""
from graphify.extractors.dockerfile import extract_dockerfile


def test_extract_dockerfile_single_stage_produces_stage_and_external_image_node(tmp_path):
    f = tmp_path / "Dockerfile"
    f.write_text("FROM python:3.11\n")
    result = extract_dockerfile(f)
    stage_nodes = [n for n in result["nodes"] if n.get("type") == "stage"]
    assert len(stage_nodes) == 1
    assert stage_nodes[0]["label"] == "stage[0]"
    labels = [n["label"] for n in result["nodes"]]
    assert "python:3.11" in labels
    relations = {(e["source"], e["target"], e["relation"]) for e in result["edges"]}
    image_id = next(n["id"] for n in result["nodes"] if n["label"] == "python:3.11")
    assert (stage_nodes[0]["id"], image_id, "depends_on") in relations


def test_extract_dockerfile_multi_stage_with_copy_from_links_stages(tmp_path):
    f = tmp_path / "Dockerfile"
    f.write_text(
        "FROM node AS build\n"
        "RUN npm run build\n"
        "FROM nginx\n"
        "COPY --from=build /app/dist /usr/share/nginx/html\n"
    )
    result = extract_dockerfile(f)
    stage_nodes = [n for n in result["nodes"] if n.get("type") == "stage"]
    assert len(stage_nodes) == 2
    build_stage = next(n for n in stage_nodes if n["label"] == "build")
    final_stage = next(n for n in stage_nodes if n["label"] == "stage[1]")
    labels = [n["label"] for n in result["nodes"]]
    assert "node" in labels
    assert "nginx" in labels
    relations = {(e["source"], e["target"]) for e in result["edges"]}
    # final stage COPY --from=build must link to the named build stage node,
    # not to a separate external "build" image node
    assert (final_stage["id"], build_stage["id"]) in relations


def test_extract_dockerfile_copy_from_positional_index(tmp_path):
    f = tmp_path / "Dockerfile"
    f.write_text("FROM golang\nFROM alpine\nCOPY --from=0 /bin/app /bin/app\n")
    result = extract_dockerfile(f)
    stage_nodes = sorted(
        (n for n in result["nodes"] if n.get("type") == "stage"),
        key=lambda n: n["source_location"],
    )
    relations = {(e["source"], e["target"]) for e in result["edges"]}
    assert (stage_nodes[1]["id"], stage_nodes[0]["id"]) in relations


def test_extract_dockerfile_dispatches_from_extract_module(tmp_path):
    """A bare `Dockerfile` (no suffix) must actually reach this extractor via
    the main dispatch pipeline, not just work as a standalone function."""
    from graphify.extract import extract

    f = tmp_path / "Dockerfile"
    f.write_text("FROM alpine\n")
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert "stage[0]" in labels
