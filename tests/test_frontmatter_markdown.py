from pathlib import Path
import pytest
from graphify.extract import extract_markdown, extract


def test_markdown_frontmatter_title_override(tmp_path: Path):
    """[TS-MD-001] When frontmatter specifies a title, the document node label should use it."""
    doc = tmp_path / "adr-005.md"
    doc.write_text(
        "---\n"
        "title: \"ADR-005: Event-Driven Processing\"\n"
        "status: accepted\n"
        "---\n"
        "# Section 1\n"
        "Details here.\n",
        encoding="utf-8",
    )
    res = extract_markdown(doc)
    doc_node = next(n for n in res["nodes"] if n["source_file"] == str(doc) and "Section 1" not in n["label"])
    assert doc_node["label"] == "ADR-005: Event-Driven Processing"


def test_markdown_frontmatter_authors_and_tags(tmp_path: Path):
    """[TS-MD-002, TS-MD-003] Frontmatter authors and tags should emit person/concept nodes and edges."""
    doc = tmp_path / "spec.md"
    doc.write_text(
        "---\n"
        "title: Specification\n"
        "authors:\n"
        "  - Alice\n"
        "  - Bob\n"
        "tags:\n"
        "  - architecture\n"
        "  - security\n"
        "---\n"
        "# Overview\n",
        encoding="utf-8",
    )
    res = extract_markdown(doc)
    labels = {n["label"] for n in res["nodes"]}
    assert "Alice" in labels
    assert "Bob" in labels
    assert "architecture" in labels
    assert "security" in labels

    # Check node types
    alice_node = next(n for n in res["nodes"] if n["label"] == "Alice")
    assert alice_node["file_type"] == "concept"
    arch_node = next(n for n in res["nodes"] if n["label"] == "architecture")
    assert arch_node["file_type"] == "concept"

    # Schema validation must pass
    from graphify.validate import validate_extraction
    assert validate_extraction(res) == []

    # Check edges
    authored_edges = [e for e in res["edges"] if e["relation"] == "authored"]
    assert len(authored_edges) == 2

    tagged_edges = [e for e in res["edges"] if e["relation"] == "tagged"]
    assert len(tagged_edges) == 2


def test_markdown_frontmatter_superseded_by_direction(tmp_path: Path):
    """[TS-MD-004B] Frontmatter superseded_by should have the replacing document as source."""
    adr1 = tmp_path / "old.md"
    adr1.write_text(
        "---\n"
        "title: Old Architecture\n"
        "superseded_by: [\"./new.md\"]\n"
        "---\n"
        "# Old\n",
        encoding="utf-8",
    )
    adr2 = tmp_path / "new.md"
    adr2.write_text("# New\n", encoding="utf-8")

    res = extract([adr1, adr2], cache_root=tmp_path, parallel=False)
    supersedes_edges = [e for e in res["edges"] if e["relation"] == "supersedes"]
    assert len(supersedes_edges) == 1
    new_node = next(n for n in res["nodes"] if n["label"] == "new.md")
    old_node = next(n for n in res["nodes"] if n["label"] == "Old Architecture")
    # new supersedes old
    assert supersedes_edges[0]["source"] == new_node["id"]
    assert supersedes_edges[0]["target"] == old_node["id"]


def test_markdown_frontmatter_supersedes_link(tmp_path: Path):
    """[TS-MD-004] Frontmatter supersedes field should link to the target document node."""
    adr1 = tmp_path / "adr-001.md"
    adr1.write_text("# ADR 001\nOld way.\n", encoding="utf-8")

    adr2 = tmp_path / "adr-002.md"
    adr2.write_text(
        "---\n"
        "title: ADR 002\n"
        "supersedes: [\"./adr-001.md\"]\n"
        "---\n"
        "# ADR 002\nNew way.\n",
        encoding="utf-8",
    )

    res = extract([adr1, adr2], cache_root=tmp_path, parallel=False)
    supersedes_edges = [e for e in res["edges"] if e["relation"] == "supersedes"]
    assert len(supersedes_edges) == 1

    adr2_node = next(n for n in res["nodes"] if n["label"] == "ADR 002")
    adr1_node = next(n for n in res["nodes"] if n["label"] == "adr-001.md" or "ADR 001" in n["label"])

    assert supersedes_edges[0]["source"] == adr2_node["id"]
    assert supersedes_edges[0]["target"] == adr1_node["id"]


def test_markdown_without_frontmatter_unchanged(tmp_path: Path):
    """[TS-MD-005] Markdown without frontmatter continues to parse headings and links as usual."""
    doc = tmp_path / "plain.md"
    doc.write_text("# Heading 1\n## Heading 2\nBody text\n", encoding="utf-8")
    res = extract_markdown(doc)
    doc_node = next(n for n in res["nodes"] if n["source_file"] == str(doc) and "Heading" not in n["label"])
    assert doc_node["label"] == "plain.md"
    assert any(n["label"] == "Heading 1" for n in res["nodes"])
    assert any(n["label"] == "Heading 2" for n in res["nodes"])


def test_markdown_malformed_frontmatter_safe(tmp_path: Path):
    """[TS-MD-006] Malformed frontmatter does not raise and parses the rest of the document."""
    doc = tmp_path / "broken.md"
    doc.write_text(
        "---\n"
        "invalid: [yaml: broken\n"
        "---\n"
        "# Still Parsed\n",
        encoding="utf-8",
    )
    res = extract_markdown(doc)
    assert any(n["label"] == "Still Parsed" for n in res["nodes"])


def test_export_html_supersedes_styling(tmp_path: Path):
    """[TS-MD-007] to_html applies distinct dashed styling and orange color to supersedes edges."""
    import networkx as nx
    from graphify.export import to_html
    G = nx.Graph()
    G.add_node("adr1", label="ADR 001", file_type="document")
    G.add_node("adr2", label="ADR 002", file_type="document")
    G.add_edge("adr2", "adr1", relation="supersedes", confidence="EXTRACTED", _src="adr2", _tgt="adr1")
    out_file = tmp_path / "graph.html"
    to_html(G, {0: ["adr1", "adr2"]}, str(out_file))
    html_content = out_file.read_text(encoding="utf-8")
    assert '"dashes": true' in html_content.lower()
    assert "#d19a66" in html_content
