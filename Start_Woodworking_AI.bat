@echo off
title Woodworking AI Server
color 0A
cls
echo ===================================================
echo           WOODWORKING AI SERVER LAUNCHER           
echo ===================================================
echo.
echo Starting Flask Server on http://127.0.0.1:5000...
echo.

cd /d "%~dp0"

start "" "http://127.0.0.1:5000"

".\venv\Scripts\python.exe" app.py

pause
