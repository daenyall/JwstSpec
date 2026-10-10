#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAIN="$(git -C "$ROOT" worktree list --porcelain | sed -n '1s/^worktree //p')"

verify_backend() {
    local py="$ROOT/backend/.venv/bin/python"

    if [[ "$ROOT" != "$MAIN" ]] &&
       cmp -s "$ROOT/backend/requirements.txt" "$MAIN/backend/requirements.txt" &&
       [[ -x "$MAIN/backend/.venv/bin/python" ]] &&
       "$MAIN/backend/.venv/bin/python" -c 'import pytest, numpy, astropy, astroquery, fastapi, pandas, requests, uvicorn' 2>/dev/null; then
        echo "Reusing existing Python environment for testing"
        py="$MAIN/backend/.venv/bin/python"
    elif [[ ! -x "$py" ]]; then
        echo "Creating isolated Python environment"
        python3 -m venv "$ROOT/backend/.venv"
        "$py" -m pip install -r "$ROOT/backend/requirements.txt" pytest
    fi

    echo "Running backend tests"
    (cd "$ROOT/backend" && "$py" -m pytest tests -q)
}

verify_frontend() {
    if [[ ! -x "$ROOT/frontend/node_modules/.bin/eslint" ]]; then
        echo "Installing frontend dependencies"
        (cd "$ROOT/frontend" && npm ci)
    fi

    echo "Running ESLint and TypeScript"
    (
        cd "$ROOT/frontend"
        npm run lint
        ./node_modules/.bin/tsc --noEmit --incremental false
    )
}

case "${1:-all}" in
    backend) verify_backend ;;
    frontend) verify_frontend ;;
    all)
        verify_backend
        verify_frontend
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all]" >&2
        exit 2
        ;;
esac
