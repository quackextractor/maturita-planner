@echo off
set VENV_DIR=venv

if not exist %VENV_DIR% (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
    call %VENV_DIR%\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
) else (
    echo Virtual environment found. Activating...
    call %VENV_DIR%\Scripts\activate
)

echo Setting up pre-commit hooks...
pre-commit install

echo Starting Planner App...
python main.py

call %VENV_DIR%\Scripts\deactivate
pause
