"""`graphify ingest-scip` — CLI wiring for graphify/scip_ingest.py's
ingest_scip_json (previously implemented but never exposed on the CLI)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable

_SAMPLE_DOC = {
    "documents": [
        {
            "relative_path": "src/main.py",
            "language": "python",
            "symbols": [
                {
                    "symbol": "python/main.py:MainClass#",
                    "kind": "class",
                    "display_name": "MainClass",
                    "documentation": ["The main class"],
                    "relationships": [],
                    "occurrences": [
                        {"range": [5, 0, 5, 9], "symbol": "python/main.py:MainClass#"}
                    ],
                }
            ],
        }
    ]
}


def _run(args, cwd):
    return subprocess.run([PYTHON, "-m", "graphify"] + args, cwd=cwd,
                          capture_output=True, text=True)


def test_ingest_scip_writes_nodes_and_edges_to_default_out(tmp_path):
    scip_path = tmp_path / "index.scip.json"
    scip_path.write_text(json.dumps(_SAMPLE_DOC))

    r = _run(["ingest-scip", str(scip_path)], tmp_path)

    assert r.returncode == 0, r.stderr
    out = tmp_path / "graphify-out" / "scip-ingested.json"
    assert out.exists()
    data = json.loads(out.read_text())
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["label"] == "MainClass"
    assert "Ingested: 1 nodes, 0 edges" in r.stdout
    assert "merge-semantic" in r.stdout


def test_ingest_scip_respects_out_flag(tmp_path):
    scip_path = tmp_path / "index.scip.json"
    scip_path.write_text(json.dumps(_SAMPLE_DOC))
    out_path = tmp_path / "custom-out.json"

    r = _run(["ingest-scip", str(scip_path), "--out", str(out_path)], tmp_path)

    assert r.returncode == 0, r.stderr
    assert out_path.exists()


def test_ingest_scip_missing_file_exits_nonzero(tmp_path):
    r = _run(["ingest-scip", str(tmp_path / "nope.json")], tmp_path)
    assert r.returncode != 0
    assert "not found" in r.stderr


def test_ingest_scip_invalid_json_exits_nonzero(tmp_path):
    scip_path = tmp_path / "bad.json"
    scip_path.write_text("{not valid json")

    r = _run(["ingest-scip", str(scip_path)], tmp_path)

    assert r.returncode != 0
    assert "not valid JSON" in r.stderr


def test_ingest_scip_no_args_shows_usage(tmp_path):
    r = _run(["ingest-scip"], tmp_path)
    assert r.returncode != 0
    assert "Usage: graphify ingest-scip" in r.stderr


def test_ingest_scip_then_merge_semantic_combines_with_existing_extraction(tmp_path):
    """The documented workflow: ingest, then feed the result into the
    existing merge-semantic combinator (no new merge logic needed)."""
    scip_path = tmp_path / "index.scip.json"
    scip_path.write_text(json.dumps(_SAMPLE_DOC))
    ingested_path = tmp_path / "graphify-out" / "scip-ingested.json"

    r1 = _run(["ingest-scip", str(scip_path)], tmp_path)
    assert r1.returncode == 0, r1.stderr

    existing_path = tmp_path / "existing.json"
    existing_path.write_text(json.dumps({
        "nodes": [{"id": "n_existing", "label": "Existing"}],
        "edges": [],
        "hyperedges": [],
    }))
    merged_path = tmp_path / "merged.json"

    r2 = _run([
        "merge-semantic", "--cached", str(existing_path),
        "--new", str(ingested_path), "--out", str(merged_path),
    ], tmp_path)

    assert r2.returncode == 0, r2.stderr
    merged = json.loads(merged_path.read_text())
    labels = {n["label"] for n in merged["nodes"]}
    assert labels == {"Existing", "MainClass"}
