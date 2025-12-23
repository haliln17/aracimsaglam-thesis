@echo off
title AracimSaglam - Baslatiliyor...
cls
echo ================================================
echo          ARACIMSAGLAM BASLATILIYOR
echo ================================================
echo.
echo [*] Server baslatiliyor...
cd /d "%~dp0"
start "" http://127.0.0.1:5000
python run_app.py
pause
