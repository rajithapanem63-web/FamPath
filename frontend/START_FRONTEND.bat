@echo off
cd /d "%~dp0"
set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
pause
