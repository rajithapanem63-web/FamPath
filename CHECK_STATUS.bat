@echo off
echo ========================================
echo   FAMPATH - Server Status Check
echo ========================================
echo.
echo Checking Backend (Port 8000)...
netstat -ano | findstr ":8000" >nul
if %errorlevel%==0 (
    echo [OK] Backend is RUNNING on port 8000
) else (
    echo [FAIL] Backend is NOT running
)
echo.
echo Checking Frontend (Port 3000)...
netstat -ano | findstr ":3000" >nul
if %errorlevel%==0 (
    echo [OK] Frontend is RUNNING on port 3000
) else (
    echo [FAIL] Frontend is NOT running
)
echo.
echo ========================================
echo If both say FAIL, run: START_ALL_SERVERS.bat
echo ========================================
echo.
pause
