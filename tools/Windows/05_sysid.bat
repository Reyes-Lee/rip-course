@echo off
rem Double-click to run 05_sysid (Windows). Logic lives in tools\_lib\05_sysid.py.
chcp 65001 >nul
rem Python prints UTF-8 even when the output goes to a file (otherwise cp950 crashes on symbols).
set PYTHONUTF8=1
cd /d "%~dp0\..\.."
rem uv installs to %USERPROFILE%\.local\bin; add it in case this window has not picked up the new PATH yet.
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
  echo uv not found. Install uv first ^(see the course website^), then reopen this window.
  pause
  exit /b 1
)
uv run --project policy python tools\_lib\05_sysid.py %*
rem Exit code 3 = the tool already waited for Enter. Any other error (uv failed, crash) keeps the window open.
set RC=%ERRORLEVEL%
if not %RC%==0 if not %RC%==3 pause
exit /b %RC%
