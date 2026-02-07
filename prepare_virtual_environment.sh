#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install build
pip install jinja2
pip install PySide6-Essentials
pip install PyOpenGL

echo "Environment is ready!"
