"""End-to-end over real stdio: the MCP server must start, list every tool (building the tool
schemas is code that only runs on tools/list) and answer calls. A unit test that only greps the
source for tool names cannot catch a schema that raises when it is built."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from networkx.readwrite import json_graph

from graphify.build import build_from_json
from graphify.extract import extract

pytest.importorskip("mcp", reason="the MCP server needs the optional `mcp` extra")

EXPECTED_NEW_TOOLS = {
    "search_text", "get_snippet", "trace_flow",
    "replace_symbol_body", "insert_after_symbol", "rename_symbol", "safe_delete_symbol",
}


def _project(tmp_path: Path) -> Path:
    (tmp_path / "state.py").write_text("def load():\n    return 'needle'\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("import state\n\ndef run():\n    return state.load()\n", encoding="utf-8")
    result = extract([tmp_path / "state.py", tmp_path / "app.py"], cache_root=tmp_path)
    G = build_from_json(result, directed=True, root=tmp_path)
    out = tmp_path / "graphify-out"
    out.mkdir(exist_ok=True)
    gp = out / "graph.json"
    gp.write_text(json.dumps(json_graph.node_link_data(G, edges="links")), encoding="utf-8")
    return gp


class _Client:
    def __init__(self, gp: Path):
        self.p = subprocess.Popen(
            [sys.executable, "-m", "graphify.serve", "--graph", str(gp)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=gp.parent.parent,
        )
        self._id = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            assert line, f"server exited: {self.p.stderr.read()[:500]}"
            msg = json.loads(line)
            if msg.get("id") == self._id:
                return msg

    def notify(self, method: str) -> None:
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.p.stdin.flush()

    def close(self) -> None:
        self.p.terminate()
        self.p.wait(timeout=10)


def _started(tmp_path: Path) -> _Client:
    c = _Client(_project(tmp_path))
    c.call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}})
    c.notify("notifications/initialized")
    return c


def test_tools_list_builds_every_tool_schema(tmp_path: Path):
    c = _started(tmp_path)
    try:
        msg = c.call("tools/list")
        assert "error" not in msg, msg
        tools = {t["name"]: t for t in msg["result"]["tools"]}
        assert EXPECTED_NEW_TOOLS <= set(tools)
        assert all(isinstance(t["inputSchema"], dict) and t["inputSchema"]["type"] == "object" for t in tools.values())
        apply_prop = tools["rename_symbol"]["inputSchema"]["properties"]["apply"]
        assert apply_prop["default"] is False  # writes are opt-in
    finally:
        c.close()


def test_calls_over_stdio_search_and_dry_run_edit(tmp_path: Path):
    c = _started(tmp_path)
    try:
        hit = c.call("tools/call", {"name": "search_text", "arguments": {"pattern": "needle"}})
        assert "state.py:2:" in hit["result"]["content"][0]["text"]
        dry = c.call("tools/call", {"name": "rename_symbol", "arguments": {"node": "load()", "new_name": "fetch"}})
        assert "Dry run" in dry["result"]["content"][0]["text"]
        assert "def load()" in (tmp_path / "state.py").read_text(encoding="utf-8")  # nothing written
    finally:
        c.close()
