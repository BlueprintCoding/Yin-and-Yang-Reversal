@echo off
SET VENV_DIR="venv"

IF NOT EXIST %VENV_DIR% (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
    echo Environment created.
)

echo Activating environment...
CALL %VENV_DIR%\Scripts\activate.bat

echo Checking for package installations...
pip install pygame

echo Launching script...
python yyr.py

pause
