@echo off
REM Quick start batch file for running shorts generator

echo.
echo ========================================================
echo YouTube Shorts Generator - Quick Start
echo ========================================================
echo.

REM Change to project directory
cd /d "C:\Users\basit\Music\sports video"

REM Activate virtual environment and run
powershell -ExecutionPolicy Bypass -Command "& {.\.venv\Scripts\Activate.ps1; python sports_shorts_pipeline.py --count 15}"

pause
