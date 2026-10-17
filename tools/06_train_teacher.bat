@echo off
rem Double-click to run 06_train_teacher (Windows). Logic lives in tools\06_train_teacher.py.
chcp 65001 >nul
cd /d "%~dp0\.."
where uv >nul 2>nul
if errorlevel 1 (
  echo uv not found. Install uv first ^(see the course website^), then reopen this window.
  pause
  exit /b 1
)
uv run --project policy python tools\06_train_teacher.py %*
