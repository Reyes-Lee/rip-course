@echo off
rem Double-click to run 01_check_serial (Windows). Logic lives in tools\01_check_serial.py.
chcp 65001 >nul
cd /d "%~dp0\.."
where uv >nul 2>nul
if errorlevel 1 (
  echo uv not found. Install uv first ^(see the course website^), then reopen this window.
  pause
  exit /b 1
)
uv run --project policy python tools\01_check_serial.py %*
