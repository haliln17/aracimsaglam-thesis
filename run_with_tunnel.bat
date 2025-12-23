@echo off
echo ===================================================
echo 🌍 AracimSaglam Global Access Launcher
echo ===================================================

:: Check if cloudflared is installed
set EXE=cloudflared
if exist cloudflared.exe (
    set EXE=.\cloudflared.exe
    goto :Found
)

where cloudflared >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ cloudflared is not installed or not in PATH.
    echo Please install it from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
    echo.
    echo After installing, restart this script.
    pause
    exit /b
)

:Found

echo.
echo 1. Starting Flask App...
start "AracimSaglam Server" python run_app.py

echo.
echo 2. Waiting for server to initialize...
timeout /t 10 >nul

echo.
echo 3. Starting Cloudflare Tunnel...
echo ---------------------------------------------------
echo 🔗 Your PUBLIC URL will appear below (look for *.trycloudflare.com)
echo ---------------------------------------------------
echo.
%EXE% tunnel --url http://127.0.0.1:5000

pause
