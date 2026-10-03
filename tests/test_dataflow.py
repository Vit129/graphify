"""graphify flow: where does a Python function's parameter flow? (name-based, flow-insensitive
inside a function; crosses functions through the graph's `calls` edges.)"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from networkx.readwrite import json_graph

import graphify.__main__ as mainmod
from graphify import serve as servemod
from graphify.build import build_from_json
from graphify.dataflow import FlowError, format_flow, trace_flow
from graphify.extract import extract

WEB = (
    "import subprocess\n"
    "import store\n"
    "\n"
    "def handle(user_text, mode):\n"
    "    cmd = build(user_text)\n"
    "    run(cmd)\n"
    "    return mode\n"
    "\n"
    "def build(text):\n"
    "    return f'echo {text}'\n"
    "\n"
    "def run(command):\n"
    "    subprocess.run(command, shell=True)\n"
    "    store.save(command)\n"
)
STORE = "def save(value):\n    return value\n"


def _project(tmp_path: Path, files: dict[str, str] | None = None):
    files = files or {"web.py": WEB, "store.py": STORE}
    paths = []
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
        paths.append(tmp_path / name)
    result = extract(paths, cache_root=tmp_path)
    G = build_from_json(result, directed=True, root=tmp_path)
    out = tmp_path / "graphify-out"
    out.mkdir(exist_ok=True)
    gp = out / "graph.json"
    gp.write_text(json.dumps(json_graph.node_link_data(G, edges="links")), encoding="utf-8")
    return G, gp


def _calls(res) -> list[str]:
    """Flatten every step's callee in the flow tree."""
    out: list[str] = []

    def walk(steps):
        for s in steps:
            out.append(s["call"])
            walk(s["next"])

    walk(res["steps"])
    return out


def test_param_flows_through_helpers_to_the_sink(tmp_path: Path):
    G, _ = _project(tmp_path)
    res = trace_flow(G, "handle()", tmp_path, param="user_text")
    calls = _calls(res)
    assert "build" in calls and "run" in calls and "subprocess.run" in calls and "store.save" in calls
    assert res["param"] == "user_text"


def test_sink_filter_keeps_only_paths_that_reach_the_sink(tmp_path: Path):
    G, _ = _project(tmp_path)
    res = trace_flow(G, "handle()", tmp_path, param="user_text", to=r"subprocess\.")
    calls = _calls(res)
    assert "subprocess.run" in calls and "store.save" not in calls
    assert res["reaches_sink"] is True


def test_param_that_only_reaches_the_return_has_no_sink(tmp_path: Path):
    G, _ = _project(tmp_path)
    res = trace_flow(G, "handle()", tmp_path, param="mode", to=r"subprocess\.")
    assert res["reaches_sink"] is False and res["steps"] == [] and res["returned"] is True


def test_keyword_arguments_map_to_parameters(tmp_path: Path):
    src = "import subprocess\n\ndef a(x):\n    b(value=x)\n\ndef b(value):\n    subprocess.run(value)\n"
    G, _ = _project(tmp_path, {"k.py": src})
    assert "subprocess.run" in _calls(trace_flow(G, "a()", tmp_path, param="x"))


def test_method_self_is_skipped_when_mapping_positional_args(tmp_path: Path):
    src = (
        "import subprocess\n\nclass S:\n    def go(self, x):\n        self.run(x)\n\n"
        "    def run(self, cmd):\n        subprocess.run(cmd)\n"
    )
    G, _ = _project(tmp_path, {"m.py": src})
    assert "subprocess.run" in _calls(trace_flow(G, ".go()", tmp_path, param="x"))


def test_taint_follows_assignments_containers_and_fstrings(tmp_path: Path):
    src = (
        "import os\n\ndef f(a):\n    b = [a, 1]\n    c = {'k': b}\n    d = f'{c}!'\n"
        "    e, g = d, 2\n    os.system(e)\n"
    )
    G, _ = _project(tmp_path, {"t.py": src})
    assert "os.system" in _calls(trace_flow(G, "f()", tmp_path, param="a"))


def test_untainted_arguments_are_not_reported(tmp_path: Path):
    src = "import os\n\ndef f(a):\n    b = 'constant'\n    os.system(b)\n"
    G, _ = _project(tmp_path, {"u.py": src})
    assert _calls(trace_flow(G, "f()", tmp_path, param="a")) == []


def test_recursion_terminates(tmp_path: Path):
    src = "def f(x):\n    return g(x)\n\ndef g(y):\n    return f(y)\n"
    G, _ = _project(tmp_path, {"r.py": src})
    assert trace_flow(G, "f()", tmp_path, param="x")["steps"]  # finite, no hang


def test_depth_limit_stops_the_walk(tmp_path: Path):
    G, _ = _project(tmp_path)
    shallow = trace_flow(G, "handle()", tmp_path, param="user_text", depth=1)
    assert "subprocess.run" not in _calls(shallow)


def test_unknown_param_lists_the_real_ones(tmp_path: Path):
    G, _ = _project(tmp_path)
    with pytest.raises(FlowError, match="user_text, mode"):
        trace_flow(G, "handle()", tmp_path, param="nope")


def test_default_param_is_every_parameter_except_self_and_cls(tmp_path: Path):
    G, _ = _project(tmp_path)
    res = trace_flow(G, "handle()", tmp_path)
    assert set(res["params"]) == {"user_text", "mode"}


def test_non_python_node_is_refused(tmp_path: Path):
    G, _ = _project(tmp_path)
    G.add_node("js", label="doIt()", source_file="x.js", source_location="L1", end_line=2)
    (tmp_path / "x.js").write_text("function doIt(a) {\n}\n", encoding="utf-8")
    with pytest.raises(FlowError, match="Python"):
        trace_flow(G, "doIt()", tmp_path)


def test_format_flow_renders_a_readable_tree(tmp_path: Path):
    G, _ = _project(tmp_path)
    text = format_flow(trace_flow(G, "handle()", tmp_path, param="user_text", to=r"subprocess\."))
    assert "handle()" in text and "subprocess.run" in text and "web.py:13" in text
    assert "REACHES SINK" in text


def test_cli_flow(tmp_path: Path, monkeypatch, capsys):
    _, gp = _project(tmp_path)
    monkeypatch.setattr(sys, "argv", ["graphify", "flow", "handle()", "--param", "user_text", "--to", "subprocess", "--graph", str(gp)])
    mainmod.main()
    assert "subprocess.run" in capsys.readouterr().out


def test_cli_flow_error_exits_nonzero(tmp_path: Path, monkeypatch, capsys):
    _, gp = _project(tmp_path)
    monkeypatch.setattr(sys, "argv", ["graphify", "flow", "handle()", "--param", "nope", "--graph", str(gp)])
    with pytest.raises(SystemExit) as exc:
        mainmod.main()
    assert exc.value.code == 1 and "user_text" in capsys.readouterr().err


def test_mcp_trace_flow(tmp_path: Path):
    G, gp = _project(tmp_path)
    out = servemod._tool_trace_flow_text(G, {"node": "handle()", "param": "user_text", "to": "subprocess"}, gp)
    assert "subprocess.run" in out
    assert servemod._tool_trace_flow_text(G, {"node": "handle()", "param": "zzz"}, gp).startswith("Error:")
    assert 'name="trace_flow"' in Path(servemod.__file__).read_text(encoding="utf-8")
