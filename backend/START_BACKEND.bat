@echo off
cd /d "%~dp0"
set FAMPATH_DB_URL=sqlite+aiosqlite:///./fampath_dev.db
set FAMPATH_SECRET_KEY=dev-secret-key-fampath-local-only
set FAMPATH_ENCRYPTION_KEY=0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b
set FAMPATH_APP_ENV=development
set FAMPATH_LLM_PROVIDER=mock
set FAMPATH_REDIS_URL=redis://localhost:6379/0
set FAMPATH_CORS_ORIGINS=["http://localhost:3000"]
set FAMPATH_LOG_LEVEL=INFO
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
pause
