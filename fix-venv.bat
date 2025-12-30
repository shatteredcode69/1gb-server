@echo off
title Fix Virtual Environment - 1GB Server Challenge
color 0C

echo ========================================
echo  Fixing Virtual Environment
echo ========================================
echo.

cd /d %~dp0

echo [1/4] Removing corrupted venv...
if exist venv (
    rmdir /s /q venv
    echo      Done!
) else (
    echo      No venv folder found!
)
echo.

timeout /t 2 /nobreak >nul

echo [2/4] Creating fresh virtual environment...
python -m venv venv
echo      Done!
echo.

timeout /t 2 /nobreak >nul

echo [3/4] Activating environment...
call venv\Scripts\activate.bat
echo      Done!
echo.

timeout /t 2 /nobreak >nul

echo [4/4] Installing dependencies...
pip install -r app\requirements.txt
echo      Done!
echo.

echo ========================================
echo  Virtual Environment Fixed!
echo ========================================
echo.
echo You can now run: python dev-server.py
echo.
pause
