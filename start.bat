@echo off
echo.
echo ============================================================
echo   AI Motor Claim Estimator — Starting All Servers
echo ============================================================
echo.

:: Start Python FastAPI backend in a new window
echo [1/2] Starting Python backend (FastAPI) on http://localhost:8000 ...
start "Python Backend - FastAPI" cmd /k "cd /d "%~dp0" && uvicorn api:app --reload --port 8000"

:: Wait 2 seconds for backend to initialize
timeout /t 2 /nobreak >nul

:: Start React frontend in a new window
echo [2/2] Starting React frontend (Vite) on http://localhost:5173 ...
start "React Frontend - Vite" cmd /k "cd /d "%~dp0claim-analyzer-ai-main" && powershell -ExecutionPolicy Bypass -Command "npm run dev""

echo.
echo ============================================================
echo   Both servers are starting in separate windows:
echo   Backend  ---^>  http://localhost:8000
echo   Frontend ---^>  http://localhost:5173
echo   API Docs ---^>  http://localhost:8000/docs
echo ============================================================
echo.
pause
