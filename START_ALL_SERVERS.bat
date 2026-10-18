@echo off
echo ========================================
echo   FAMPATH - Starting All Servers
echo ========================================
echo.
echo Starting Backend Server (Port 8000)...
start "FamPath Backend" cmd /k "cd backend && START_BACKEND.bat"
timeout /t 3 /nobreak >nul
echo.
echo Starting Frontend Server (Port 3000)...
start "FamPath Frontend" cmd /k "cd frontend && START_FRONTEND.bat"
echo.
echo ========================================
echo   Both servers are starting!
echo ========================================
echo.
echo Backend will be on: http://localhost:8000
echo Frontend will be on: http://localhost:3000
echo.
echo Wait 10-15 seconds, then open:
echo   http://localhost:3000
echo.
echo Press any key to exit this launcher...
echo (The server windows will stay open)
pause >nul
