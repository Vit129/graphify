from __future__ import annotations

from pathlib import Path
from graphify.extract import extract_python, extract_js


def test_extract_fastapi_and_flask_routes(tmp_path):
    py_file = tmp_path / "app.py"
    py_file.write_text(
        """
from fastapi import FastAPI, APIRouter
from flask import Flask

app = FastAPI()
router = APIRouter()
flask_app = Flask(__name__)

@app.get("/users")
def list_users():
    return []

@router.post("/items")
async def create_item():
    return {}

@flask_app.route("/auth/login", methods=["GET", "POST"])
def login_view():
    return "ok"
""",
        encoding="utf-8",
    )

    result = extract_python(py_file)
    node_labels = {n["label"]: n for n in result.get("nodes", [])}

    assert "GET /users" in node_labels
    assert node_labels["GET /users"]["file_type"] == "route"

    assert "POST /items" in node_labels
    assert "GET /auth/login" in node_labels
    assert "POST /auth/login" in node_labels

    edges = [(e["source"], e["target"], e["relation"]) for e in result.get("edges", [])]
    # Check that route node connects to handler function with 'handles' relation
    get_users_rid = node_labels["GET /users"]["id"]
    handles_edges = [e for e in edges if e[0] == get_users_rid and e[2] == "handles"]
    assert len(handles_edges) == 1


def test_extract_django_urls(tmp_path):
    urls_file = tmp_path / "urls.py"
    urls_file.write_text(
        """
from django.urls import path
from . import views

urlpatterns = [
    path('api/v1/profile/', views.profile_detail),
]

def profile_detail(request):
    pass
""",
        encoding="utf-8",
    )

    result = extract_python(urls_file)
    node_labels = {n["label"]: n for n in result.get("nodes", [])}

    assert "ROUTE /api/v1/profile/" in node_labels
    assert node_labels["ROUTE /api/v1/profile/"]["file_type"] == "route"

    # Regression: fn_nodes used to filter on file_type == "function"/kind ==
    # "function", but real Python function nodes carry file_type "code" in
    # this codebase -- fn_nodes was always empty, so `handles` never formed
    # even for this same-file case (#p20-review finding 8, root cause).
    route_id = node_labels["ROUTE /api/v1/profile/"]["id"]
    handler_id = node_labels["profile_detail()"]["id"]
    edges = [(e["source"], e["target"], e["relation"]) for e in result.get("edges", [])]
    assert (route_id, handler_id, "handles") in edges


def test_django_route_handler_resolves_across_files(tmp_path):
    """Regression: Django's own convention (from . import views; path(...,
    views.user_list)) puts the route in urls.py and the real handler in a
    separate views.py -- extract_python_routes can only see its own file's
    nodes, so this never resolved. build_from_json now runs
    resolve_django_route_handlers once the whole graph is assembled, when
    cross-file lookup is finally possible (#p20-review finding 8)."""
    from graphify.build import build_from_json

    views_file = tmp_path / "views.py"
    views_file.write_text("def user_list(request):\n    return []\n", encoding="utf-8")
    urls_file = tmp_path / "urls.py"
    urls_file.write_text(
        "from django.urls import path\n"
        "from . import views\n"
        "\n"
        "urlpatterns = [\n"
        "    path('users/', views.user_list),\n"
        "]\n",
        encoding="utf-8",
    )

    extraction = {"nodes": [], "edges": []}
    for f in (views_file, urls_file):
        r = extract_python(f)
        extraction["nodes"].extend(r.get("nodes", []))
        extraction["edges"].extend(r.get("edges", []))

    G = build_from_json(extraction, directed=True, root=str(tmp_path))

    handles = [(u, v) for u, v, d in G.edges(data=True) if d.get("relation") == "handles"]
    assert len(handles) == 1
    route_nid, handler_nid = handles[0]
    assert G.nodes[route_nid]["label"] == "ROUTE /users/"
    assert G.nodes[handler_nid]["label"] == "user_list()"
    # The pending-handler marker must never leak into the persisted graph.
    assert all("_django_pending_handler" not in d for _, d in G.nodes(data=True))


def test_django_route_handler_ambiguous_name_resolves_by_proximity():
    """Two Django apps each with their own views.py defining the same view
    name must resolve to the app's own handler, not an arbitrary one --
    ambiguity is broken by path proximity to the referencing urls.py, the
    same tie-break rule cross-file call resolution already uses.

    Exercises resolve_django_route_handlers directly against a hand-built
    graph rather than through extract_python/build_from_json -- two files
    named "views.py" with byte-identical content hits an unrelated,
    pre-existing id-collision bug in build_from_json's own id assembly
    (reproducible with zero routes.py code involved), which isn't what this
    test is about."""
    import networkx as nx
    from graphify.routes import resolve_django_route_handlers

    G = nx.DiGraph()
    G.add_node("route", label="ROUTE /", file_type="route", source_file="app_a/urls.py",
               _django_pending_handler="index")
    G.add_node("a_index", label="index()", file_type="code", source_file="app_a/views.py")
    G.add_node("b_index", label="index()", file_type="code", source_file="app_b/views.py")

    added = resolve_django_route_handlers(G)
    assert added == 1
    assert G.has_edge("route", "a_index")
    assert not G.has_edge("route", "b_index")


def test_extract_express_and_nestjs_routes(tmp_path):
    js_file = tmp_path / "server.ts"
    js_file.write_text(
        """
import express from 'express';
const app = express();
const router = express.Router();

function getUserHandler(req, res) {}
app.get('/api/users', getUserHandler);
router.delete('/api/items/:id', deleteItemHandler);

@Controller('products')
export class ProductController {
    @Get(':id')
    getProduct() {}

    @Post('create')
    createProduct() {}
}
""",
        encoding="utf-8",
    )

    result = extract_js(js_file)
    node_labels = {n["label"]: n for n in result.get("nodes", [])}

    assert "GET /api/users" in node_labels
    assert "DELETE /api/items/:id" in node_labels
    assert "GET /products/:id" in node_labels
    assert "POST /products/create" in node_labels


def test_extract_nextjs_app_router(tmp_path):
    route_file = tmp_path / "app" / "api" / "auth" / "route.ts"
    route_file.parent.mkdir(parents=True)
    route_file.write_text(
        """
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    return NextResponse.json({ ok: true });
}

export async function POST(request: Request) {
    return NextResponse.json({ created: true });
}
""",
        encoding="utf-8",
    )

    result = extract_js(route_file)
    node_labels = {n["label"]: n for n in result.get("nodes", [])}

    assert "GET /api/auth" in node_labels
    assert "POST /api/auth" in node_labels


def test_route_ids_do_not_collide_across_same_named_files(tmp_path):
    """Regression: _make_route_id used to key on path.stem, so two same-
    filename route files in different directories (a routine monorepo shape)
    collided into one route node, silently merging both services' `handles`
    edges onto it (#p20-review finding 3)."""
    svc_a = tmp_path / "svcA"
    svc_a.mkdir()
    svc_b = tmp_path / "svcB"
    svc_b.mkdir()
    source = (
        "const express = require('express');\n"
        "const app = express();\n"
        "app.get('/users', handler);\n"
    )
    file_a = svc_a / "routes.js"
    file_a.write_text(source, encoding="utf-8")
    file_b = svc_b / "routes.js"
    file_b.write_text(source, encoding="utf-8")

    result_a = extract_js(file_a)
    result_b = extract_js(file_b)

    route_id_a = next(n["id"] for n in result_a["nodes"] if n["label"] == "GET /users")
    route_id_b = next(n["id"] for n in result_b["nodes"] if n["label"] == "GET /users")
    assert route_id_a != route_id_b


def test_extract_express_inline_arrow_and_function_handlers(tmp_path):
    """Regression: an inline handler ((req, res) => ... or function(req, res)
    {...}) failed the handler-argument regex entirely, so the route was never
    extracted at all -- not just missing its `handles` edge. This is the most
    common Express idiom (#p20-review finding 7)."""
    js_file = tmp_path / "server.js"
    js_file.write_text(
        """
const express = require('express');
const app = express();

function listUsers(req, res) { res.json([]); }

app.get('/health', (req, res) => { res.send('ok'); });
app.post('/webhook', function (req, res) { res.sendStatus(200); });
app.get('/users', listUsers);
""",
        encoding="utf-8",
    )

    result = extract_js(js_file)
    node_labels = {n["label"]: n for n in result.get("nodes", [])}

    assert "GET /health" in node_labels
    assert "POST /webhook" in node_labels
    assert "GET /users" in node_labels

    edges = [(e["source"], e["target"], e["relation"]) for e in result.get("edges", [])]
    users_rid = node_labels["GET /users"]["id"]
    assert any(e[0] == users_rid and e[2] == "handles" for e in edges)
