#!/usr/bin/env bash
# Portable launcher for the GIGA PHONE AI worker.
set -euo pipefail

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -f "config/settings.local.json" ]; then
    printf 'Missing config/settings.local.json. Run the platform setup script first.\n' >&2
    exit 1
fi

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON_BIN" ]; then
    printf 'Python was not found. Run the platform setup script again.\n' >&2
    exit 1
fi

exec "$PYTHON_BIN" main.py
