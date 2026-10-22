"""Tests for graphify.lsp_resolve using a tiny fake LSP server (no pyright needed)."""

from __future__ import annotations

import json
import shlex
import shutil
import sys
import textwrap
from pathlib import Path

import pytest

from graphify import lsp_resolve as L

FAKE_SERVER = textwrap.dedent(
    '''
    import json, sys, time
    cfg = json.load(open(sys.argv[1]))
    inp, out = sys.stdin.buffer, sys.stdout.buffer

    def read():
        n = None
        while True:
            line = inp.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            if line.lower().startswith(b"content-length:"):
                n = int(line.split(b":")[1])
        return json.loads(inp.read(n))

    def send(m):
        b = json.dumps(m).encode()
        out.write(b"Content-Length: %d\\r\\n\\r\\n" % len(b) + b)
        out.flush()

    calls = 0
    while True:
        m = read()
        if m is None:
            break
        meth = m.get("method")
        if meth == "initialize":
            send({"jsonrpc": "2.0", "id": m["id"], "result": {"capabilities": {}}})
        elif meth == "textDocument/definition":
            calls += 1
            if cfg.get("crash_after") is not None and calls > cfg["crash_after"]:
                sys.exit(1)
            if cfg.get("hang_after") is not None and calls > cfg["hang_after"]:
                time.sleep(60)
            p = m["params"]["position"]
            with open(cfg["log"], "a") as f:
                f.write(json.dumps([p["line"], p["character"]]) + "\\n")
            ans = cfg["answers"].get("%d:%d" % (p["line"], p["character"]))
            send({"jsonrpc": "2.0", "id": m["id"], "result": ans})
        elif meth == "shutdown":
            send({"jsonrpc": "2.0", "id": m["id"], "result": None})
        elif meth == "exit":
            break
    '''
)

APP = "def helper():\n    pass\n\n\ndef other():\n    pass\n\n\ndef main():\n    helper()\n    helper()\n"
# lines: helper=1, other=5, main=9, call sites L10/L11 (column 4)


def _node(nid, label, loc, f="app.py"):
    return {"id": nid, "label": label, "file_type": "code", "source_file": f, "source_location": loc}


def _edge(tgt, loc, **kw):
    e = {"source": "main", "target": tgt, "relation": "calls", "confidence": "INFERRED",
         "confidence_score": 0.8, "source_file": "app.py", "source_location": loc, "weight": 1.0}
    e.update(kw)
    return e


def _loc(root: Path, f: str, line0: int):
    return {"uri": (root / f).resolve().as_uri(), "range": {"start": {"line": line0, "character": 4}, "end": {"line": line0, "character": 10}}}


@pytest.fixture
def proj(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "app.py").write_text(APP)
    (tmp_path / "fake_server.py").write_text(FAKE_SERVER)
    return root


def _graph(root, edges):
    data = {"directed": True, "multigraph": True, "graph": {}, "hyperedges": [],
            "nodes": [_node("app", "app.py", "L1"), _node("helper", "helper()", "L1"),
                      _node("other", "other()", "L5"), _node("main", "main()", "L9")],
            "links": edges}
    gp = root.parent / "graph.json"
    gp.write_text(json.dumps(data))
    return gp


def _server(tmp_path, answers, **extra):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"answers": answers, "log": str(tmp_path / "log.txt"), **extra}))
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(tmp_path / 'fake_server.py'))} {shlex.quote(str(cfg))}"


def _run(proj, gp, server, **kw):
    return L.run(gp, proj, server=server, timeout=kw.pop("timeout", 5), **kw)


def test_confirmed(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10")])
    s = _run(proj, gp, _server(tmp_path, {"9:4": _loc(proj, "app.py", 0)}))
    assert (s.examined, s.confirmed) == (1, 1)
    e = json.loads(gp.read_text())["links"][0]
    assert e["confidence"] == "EXTRACTED" and e["confidence_score"] == 1.0 and e["resolved_by"] == "lsp"
    assert e["weight"] == 1.0 and e["target"] == "helper"


def test_retargeted_keeps_attributes(proj, tmp_path):
    gp = _graph(proj, [_edge("other", "L10", context="call")])
    # `other` label does not appear on the line -> skipped; use a label that does
    data = json.loads(gp.read_text())
    data["nodes"][2]["label"] = "helper()"  # a same-named decoy node at L5
    gp.write_text(json.dumps(data))
    s = _run(proj, gp, _server(tmp_path, {"9:4": _loc(proj, "app.py", 0)}))
    assert s.retargeted == 1
    e = json.loads(gp.read_text())["links"][0]
    assert e["target"] == "helper" and e["context"] == "call" and e["resolved_by"] == "lsp"


def test_retarget_respects_src_tgt(proj, tmp_path):
    ed = _edge("other", "L10", _src="main", _tgt="other")
    ed["source"], ed["target"] = "other", "main"  # stored flipped; _src/_tgt are authoritative
    data_edges = [ed]
    gp = _graph(proj, data_edges)
    data = json.loads(gp.read_text())
    data["nodes"][2]["label"] = "helper()"
    gp.write_text(json.dumps(data))
    s = _run(proj, gp, _server(tmp_path, {"9:4": _loc(proj, "app.py", 0)}))
    assert s.retargeted == 1
    e = json.loads(gp.read_text())["links"][0]
    assert (e["_src"], e["_tgt"]) == ("main", "helper") and e["source"] == "helper" and e["target"] == "main"


def test_unresolved_leaves_edge_untouched(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10")])
    before = gp.read_text()
    s = _run(proj, gp, _server(tmp_path, {}))  # null result
    assert s.unresolved == 1 and s.confirmed == 0
    assert gp.read_text() == before


def test_definition_with_no_matching_node_is_unresolved(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10")])
    s = _run(proj, gp, _server(tmp_path, {"9:4": _loc(proj, "app.py", 2)}))  # line 3 has no node
    assert s.unresolved == 1


def test_external_definition(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10")])
    before = gp.read_text()
    outside = {"uri": (tmp_path / "elsewhere.py").as_uri(), "range": {"start": {"line": 0, "character": 0}}}
    s = _run(proj, gp, _server(tmp_path, {"9:4": outside}))
    assert s.external == 1
    assert gp.read_text() == before


def test_non_file_uri_is_external(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10")])
    weird = {"uri": "http://evil.example/x.py", "range": {"start": {"line": 0, "character": 0}}}
    assert _run(proj, gp, _server(tmp_path, {"9:4": weird})).external == 1


def test_crash_keeps_results_so_far(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10"), _edge("helper", "L11")])
    srv = _server(tmp_path, {"9:4": _loc(proj, "app.py", 0), "10:4": _loc(proj, "app.py", 0)}, crash_after=1)
    s = _run(proj, gp, srv)
    assert s.confirmed == 1 and ("exited" in s.aborted or "lost" in s.aborted)
    assert s.skipped == 1
    links = json.loads(gp.read_text())["links"]
    assert [e.get("resolved_by") for e in links] == ["lsp", None]


def test_timeout_stops_cleanly(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10"), _edge("helper", "L11")])
    srv = _server(tmp_path, {"9:4": _loc(proj, "app.py", 0)}, hang_after=1)
    s = _run(proj, gp, srv, timeout=1)
    assert s.confirmed == 1 and "timed out" in s.aborted and s.skipped == 1


def test_column_location():
    assert L.find_column("    x = helper(1)", "helper") == 8
    assert L.find_column("    self.helper()", "helper") == 9
    assert L.find_column("    helper(helper)", "helper") == 4  # only one is a call
    assert L.find_column("    helper(); helper()", "helper") is None  # ambiguous
    assert L.find_column("    my_helper()", "helper") is None  # not a whole word
    assert L.find_column("    foo(helper)", "helper", "indirect_call") == 8
    assert L.callee_name("Foo.bar()") == "bar" and L.callee_name(".bar()") == "bar"


def test_ambiguous_line_is_skipped(proj, tmp_path):
    (proj / "app.py").write_text(APP.replace("    helper()\n    helper()\n", "    helper(); helper()\n"))
    gp = _graph(proj, [_edge("helper", "L10")])
    s = _run(proj, gp, _server(tmp_path, {}))
    assert s.skipped == 1 and s.examined == 0
    assert not (tmp_path / "log.txt").exists()


def test_dry_run_does_not_write(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10")])
    before = gp.read_text()
    s = _run(proj, gp, _server(tmp_path, {"9:4": _loc(proj, "app.py", 0)}), dry_run=True)
    assert s.confirmed == 1
    assert gp.read_text() == before


def test_extracted_edges_and_other_relations_not_examined(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10", confidence="EXTRACTED"), _edge("helper", "L11", relation="imports")])
    s = _run(proj, gp, _server(tmp_path, {}))
    assert s.examined == 0 and s.skipped == 0


def test_max_edges(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10"), _edge("helper", "L11")])
    s = _run(proj, gp, _server(tmp_path, {"9:4": _loc(proj, "app.py", 0)}), max_edges=1)
    assert s.examined == 1 and s.skipped == 1


def test_source_file_escaping_root_is_skipped(proj, tmp_path):
    (tmp_path / "secret.py").write_text("helper()\n")
    gp = _graph(proj, [_edge("helper", "L1", source_file="../secret.py")])
    s = _run(proj, gp, _server(tmp_path, {}))
    assert s.skipped == 1 and s.examined == 0


def test_missing_server_message(proj, tmp_path):
    gp = _graph(proj, [_edge("helper", "L10")])
    with pytest.raises(L.LspError, match="not found on PATH"):
        L.run(gp, proj, server="definitely-not-a-real-lsp-binary --stdio")


def test_cli_missing_server_no_traceback(proj, tmp_path):
    import subprocess
    gp = _graph(proj, [_edge("helper", "L10")])
    r = subprocess.run(
        [sys.executable, "-m", "graphify", "lsp-resolve", "--graph", str(gp), "--root", str(proj),
         "--server", "definitely-not-a-real-lsp-binary"],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 1 and "error:" in r.stderr and "Traceback" not in r.stderr


@pytest.mark.skipif(shutil.which("pyright-langserver") is None, reason="pyright-langserver not installed")
def test_real_pyright(tmp_path):
    root = tmp_path / "p"
    root.mkdir()
    (root / "lib.py").write_text("class Box:\n    def open(self):\n        return 1\n")
    (root / "app.py").write_text(
        "from lib import Box\n\n\ndef run():\n    b = Box()\n    return b.open()\n"
    )
    nodes = [_node("lib", "lib.py", "L1", "lib.py"), _node("box", "Box", "L1", "lib.py"),
             _node("box_open", ".open()", "L2", "lib.py"), _node("run", "run()", "L4", "app.py"),
             _node("wrong_open", ".open()", "L1", "app.py")]
    edges = [{"source": "run", "target": "wrong_open", "relation": "calls", "confidence": "INFERRED",
              "confidence_score": 0.8, "source_file": "app.py", "source_location": "L6"}]
    gp = tmp_path / "graph.json"
    gp.write_text(json.dumps({"nodes": nodes, "links": edges}))
    s = L.run(gp, root, timeout=30)
    assert s.retargeted == 1, s
    e = json.loads(gp.read_text())["links"][0]
    assert e["target"] == "box_open" and e["confidence"] == "EXTRACTED" and e["resolved_by"] == "lsp"
