@echo off
echo.
echo  E-shop Backend Startup
echo  ========================
call venv\Scripts\activate.bat

echo  [0/3] Freeing port 8000...
powershell -NoProfile -Command "$p = netstat -aon | Select-String ':8000 '; if ($p) { $p | ForEach-Object { $pid_ = ($_ -replace '.*\s(\d+)$','$1').Trim(); taskkill /PID $pid_ /F 2>$null } }"
timeout /t 1 /nobreak >nul

echo  [1/3] Ensuring database exists...
venv\Scripts\python.exe create_db.py
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Could not connect to PostgreSQL.
    echo  Check DATABASE_URL in .env ^(password / host / db name^)
    echo.
    pause
    exit /b 1
)

echo  [2/3] Clearing stale Python processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo  [3/3] Starting API server...
venv\Scripts\python.exe run.py
