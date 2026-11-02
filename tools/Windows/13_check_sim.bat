@echo off
rem Double-click to run 13_check_sim (Windows). Logic lives in tools\_lib\13_check_sim.py.
chcp 65001 >nul
cd /d "%~dp0\..\.."
rem uv installs to %USERPROFILE%\.local\bin; add it in case this window has not picked up the new PATH yet.
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
  echo uv not found. Install uv first ^(see the course website^), then reopen this window.
  pause
  exit /b 1
)
uv run --project policy python tools\_lib\13_check_sim.py %*
