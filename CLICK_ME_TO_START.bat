@echo off
title FamPath Launcher
color 0A
cls

echo.
echo  ================================================
echo    FAMPATH - Starting Development Servers
echo  ================================================
echo.
echo  This will open 2 windows:
echo   [1] Backend  (Port 8000)
echo   [2] Frontend (Port 3000)
echo.
echo  After they start, open: http://localhost:3000
echo  ================================================
echo.
pause

echo.
echo [1/2] Starting Backend Server...
cd /d "%~dp0backend"
start "FAMPATH BACKEND [PORT 8000]" cmd /k "START_BACKEND.bat"

timeout /t 5 /nobreak >nul

echo [2/2] Starting Frontend Server...
cd /d "%~dp0frontend"
start "FAMPATH FRONTEND [PORT 3000]" cmd /k "START_FRONTEND.bat"

echo.
echo ================================================
echo  SERVERS ARE STARTING!
echo ================================================
echo.
echo  Two new windows opened:
echo   - FAMPATH BACKEND [PORT 8000]
echo   - FAMPATH FRONTEND [PORT 3000]
echo.
echo  Wait 15-20 seconds for them to start, then:
echo.
echo  Open your browser to:
echo    http://localhost:3000
echo.
echo ================================================
echo.
echo Press any key to close this launcher window...
echo (The server windows will stay open)
pause >nul
