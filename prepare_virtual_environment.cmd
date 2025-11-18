@echo off
cd /d %~dp0

IF NOT EXIST ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python pip install --upgrade pip
pip install jinja2
pip install PySide6
pip install PyOpenGL

echo Environment is ready!
pause
