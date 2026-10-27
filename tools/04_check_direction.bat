@echo off
rem Double-click to run 04_check_direction (Windows). Logic lives in tools\04_check_direction.py.
chcp 65001 >nul
cd /d "%~dp0\.."
where uv >nul 2>nul
if errorlevel 1 (
  echo uv not found. Install uv first ^(see the course website^), then reopen this window.
  pause
  exit /b 1
)
uv run --project policy python tools\04_check_direction.py %*
