@echo off
REM ApplyPilot Quick Scan Launcher
REM ===============================
REM Double-click to run full job scan!

echo.
echo ========================================
echo   ApplyPilot - Job Search System
echo ========================================
echo.
echo Starting full scan...
echo This will take 20-30 minutes.
echo.

cd /d %~dp0

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set UTF-8 encoding
set PYTHONIOENCODING=utf-8

REM Run scan
python scripts\run_full_scan.py

echo.
echo ========================================
echo   Scan Complete!
echo ========================================
echo.
echo Check reports\latest.txt for results
echo.

pause
