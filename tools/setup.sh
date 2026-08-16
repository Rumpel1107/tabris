#!/usr/bin/env bash
set -euo pipefail

# The venv lives outside the repo on purpose: it hardcodes absolute paths, so one
# created inside a shared project directory breaks for every other environment.
VENV="${TABRIS_VENV:-$HOME/.venvs/tabris}"

cd "$(dirname "$0")/.."

# --- Preconditions: fail before creating anything ---
# First candidate that both exists and meets the minimum version wins, so an
# older python3 earlier on PATH does not block a newer one installed elsewhere.
find_python() {
    local candidate path
    for candidate in "$@"; do
        path=$(command -v "$candidate" 2>/dev/null) || continue
        "$path" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)' 2>/dev/null || continue
        echo "$path"
        return 0
    done
    return 1
}

if [ -n "${PYTHON:-}" ]; then
    CANDIDATES=("$PYTHON")
else
    CANDIDATES=(python3 python3.14 python3.13 "$HOME"/.local/share/uv/python/*/bin/python3)
fi

if ! PYTHON=$(find_python "${CANDIDATES[@]}"); then
    echo "ERROR: no Python 3.13+ found." >&2
    echo "       Tried: ${CANDIDATES[*]}" >&2
    echo "       (audioop-lts, pulled in by discord.py, does not build below 3.13)" >&2
    echo "       Install Python 3.13+ or set PYTHON=/path/to/python3" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import venv' 2>/dev/null; then
    echo "ERROR: the 'venv' module is missing from $PYTHON" >&2
    echo "       On Debian/Ubuntu: sudo apt install python3-venv" >&2
    exit 1
fi

# --- Environment ---
if [ -x "$VENV/bin/python" ]; then
    echo "Reusing virtualenv at $VENV"
else
    echo "Creating virtualenv at $VENV (using $PYTHON)"
    "$PYTHON" -m venv "$VENV"
fi

"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install -r requirements.txt

# --- Secrets ---
if [ ! -f .env ]; then
    cp .env.example .env
    ENV_CREATED=1
fi

# Permissions are OS-level and never survive a copy, so reapply them every run.
chmod 600 .env
mkdir -p data
chmod 600 data/*.db* data/*_client_id 2>/dev/null || true

# --- Verify ---
"$VENV/bin/python" -m pytest -q

echo
echo "Ready — Python $("$VENV/bin/python" -c 'import platform; print(platform.python_version())') at $VENV"
echo "Run tests with:  $VENV/bin/python -m pytest"

if [ "${ENV_CREATED:-0}" = "1" ]; then
    echo
    echo "NOTE: .env was created from .env.example — add your API keys before running Tabris."
fi
