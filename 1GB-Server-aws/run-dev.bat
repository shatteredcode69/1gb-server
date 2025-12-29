@echo off
title 1GB Server Challenge - Muhammad Abbas
color 0A

cls
echo.
echo ============================================================
echo.
echo       1GB SERVER CHALLENGE
echo       By Muhammad Abbas
echo.
echo ============================================================
echo.
echo  Loading environment...
timeout /t 1 /nobreak >nul

call venv\Scripts\activate.bat

echo  Environment activated!
echo.
echo  Starting Flask server...
echo.

python dev-server.py

pause
