@echo off
echo Checking Discord Bot Status
echo =========================
echo.

echo Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Installing required packages if needed...
pip install psutil > nul 2>&1

echo Running status check...
echo.
python check_bot_status.py

echo.
echo =========================
echo Status check complete
echo =========================
echo.
pause 