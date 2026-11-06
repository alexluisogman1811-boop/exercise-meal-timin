@echo off
REM Double-click to make a PUBLIC link (https://....trycloudflare.com) that friends can open.
REM Works only while this window stays open and the computer is on. The link changes each time.
cd /d "%~dp0"
chcp 65001 >nul

if not exist ".venv\Scripts\python.exe" (
    echo First run: installing the app...
    py -m venv .venv || python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
)
if not exist ".streamlit\secrets.toml" copy ".streamlit\secrets.toml.example" ".streamlit\secrets.toml" >nul

if not exist "tools\cloudflared\cloudflared.exe" (
    echo Downloading Cloudflare Tunnel from Cloudflare's GitHub...
    mkdir "tools\cloudflared" 2>nul
    curl -L -o "tools\cloudflared\cloudflared.exe" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
)

echo Starting the app in a second window...
start "Meal timing app" ".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless true

echo.
echo ===============================================================
echo  Look below for a line with  https://....trycloudflare.com
echo  Copy that link and send it to your friends.
echo  Keep this window open. Close it to stop sharing.
echo ===============================================================
echo.
"tools\cloudflared\cloudflared.exe" tunnel --no-autoupdate --url http://localhost:8501
pause
