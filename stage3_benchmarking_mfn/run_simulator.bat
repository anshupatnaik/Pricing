@echo off
REM ============================================================
REM  SL Revenue Simulator - one-click launcher
REM  Double-click this file, or run it from any terminal.
REM  The Dremio token is read from dremio_connect\.env
REM  (do NOT set a DREMIO_TOKEN environment variable).
REM ============================================================
cd /d "%~dp0"
echo Starting SL Revenue Simulator...
echo A browser tab will open at http://localhost:8600
echo (Close this window to stop the app.)
python -m streamlit run "%~dp0app\streamlit_app.py" --server.port 8600
pause
