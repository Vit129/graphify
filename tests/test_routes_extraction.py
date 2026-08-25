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
