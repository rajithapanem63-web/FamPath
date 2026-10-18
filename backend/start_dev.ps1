# FamPath Backend — Local Dev Startup Script
# Run from: c:\Users\jakat\OneDrive\Desktop\rajitha\backend\
# Usage: .\start_dev.ps1

$ErrorActionPreference = "Stop"

Write-Host "Starting FamPath backend..." -ForegroundColor Cyan

# Set environment variables
$env:FAMPATH_DB_URL = "sqlite+aiosqlite:///./fampath_dev.db"
$env:FAMPATH_SECRET_KEY = "dev-secret-key-fampath-local-only"
$env:FAMPATH_ENCRYPTION_KEY = "0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b"
$env:FAMPATH_APP_ENV = "development"
$env:FAMPATH_DEBUG = "true"
$env:FAMPATH_LLM_PROVIDER = "mock"
$env:FAMPATH_REDIS_URL = "redis://localhost:6379/0"
$env:FAMPATH_CORS_ORIGINS = '["http://localhost:3000","http://localhost:3001","http://localhost:3002","http://127.0.0.1:3000","http://127.0.0.1:3001","http://127.0.0.1:3002"]'
$env:FAMPATH_LOG_LEVEL = "INFO"

Write-Host "Environment set" -ForegroundColor Green
Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Yellow
Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""

# Activate venv and start uvicorn
& ".\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000 --reload
