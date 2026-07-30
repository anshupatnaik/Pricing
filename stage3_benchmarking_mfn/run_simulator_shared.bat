@echo off
REM ============================================================
REM  SL Revenue Simulator - SHARED launcher (work network / VPN)
REM  Binds to all interfaces so colleagues on the SAME corporate
REM  network / VPN can open it. Your machine must stay on & running.
REM  Token is read from dremio_connect\.env (do NOT set DREMIO_TOKEN).
REM ============================================================
cd /d "%~dp0"
echo Starting SL Revenue Simulator (shared)...
echo.
echo Share the "Network URL" printed below with colleagues on the
echo same corporate network / VPN (e.g. http://YOUR-IP:8602).
echo Local access: http://localhost:8602
echo Close this window to stop the app.
echo.
python -m streamlit run "%~dp0app\streamlit_app.py" --server.address 0.0.0.0 --server.port 8602
pause
