#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

# Ensure XWayland (xcb) is used on Linux for desktop window positioning
if [ -z "$QT_QPA_PLATFORM" ] && [ -n "$DISPLAY" ]; then
    export QT_QPA_PLATFORM=xcb
fi

echo "Starting 2D Desktop Avatar..."
exec .venv/bin/python3 main.py "$@"
