@echo off
REM Double-click to start the app. First run installs everything (needs internet, ~2 min).
cd /d "%~dp0"
chcp 65001 >nul

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv .venv || python -m venv .venv
    if errorlevel 1 (
        echo Python not found. Install Python 3.11+ from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo Installing packages...
    ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
)

if not exist ".streamlit\secrets.toml" (
    copy ".streamlit\secrets.toml.example" ".streamlit\secrets.toml" >nul
    echo Created .streamlit\secrets.toml - change admin_password before real use.
)

echo Opening http://localhost:8501 ...
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless false
pause
