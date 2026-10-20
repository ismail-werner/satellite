@echo off
cd /d "%~dp0"
start "satellite" python sat.py
timeout /t 1 >nul
start "ground" python ground.py
timeout /t 2 >nul
start http://localhost:8000
