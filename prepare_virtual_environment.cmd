@echo off
cd /d %~dp0

IF NOT EXIST ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install build
pip install jinja2
pip install PySide6-Essentials
pip install PyOpenGL

echo Environment is ready!