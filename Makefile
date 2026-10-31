.PHONY: start dev preview test build version-check release-check

start: preview

dev:
	uv run graphify --version

preview:
	uv run graphify --help

test:
	uv run pytest tests/ -q

build:
	uv build

version-check:
	python3 scripts/check_version.py

release-check: version-check test build
