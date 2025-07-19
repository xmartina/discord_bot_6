@echo off
echo Stopping Discord Bot
echo ====================
echo.

echo Looking for Discord Bot process...
wmic process where "name='python.exe' and commandline like '%%main.py%%'" get processid 2>nul | findstr /r "[0-9]" > temp_pid.txt

set /p BOT_PID=<temp_pid.txt
del temp_pid.txt

if "%BOT_PID%"=="" (
    echo No Discord Bot process found running
    echo Bot may already be stopped
    pause
    exit /b 0
)

echo Found Discord Bot process (PID: %BOT_PID%). Attempting to stop...
echo.

echo Method 1: Attempting graceful shutdown...
taskkill /PID %BOT_PID% 2>nul
timeout /t 3 /nobreak >nul

echo Checking if bot is still running...
wmic process where "processid=%BOT_PID%" get name 2>nul | find "python.exe" >nul
if %errorlevel% neq 0 (
    echo Bot has been gracefully stopped
) else (
    echo Method 2: Force stopping Discord Bot process...
    taskkill /f /PID %BOT_PID% 2>nul
    if %errorlevel% equ 0 (
        echo Successfully stopped Discord Bot process
    ) else (
        echo Failed to stop Discord Bot process
        echo You may need to stop it manually
    )
)

echo.
echo Checking for any remaining Discord Bot processes...
wmic process where "name='python.exe' and commandline like '%%main.py%%'" get processid 2>nul | findstr /r "[0-9]" > temp_remaining.txt
set /p REMAINING=<temp_remaining.txt
del temp_remaining.txt

if "%REMAINING%"=="" (
    echo All Discord Bot processes have been stopped
) else (
    echo Warning: Some Discord Bot processes may still be running
    echo If needed, open Task Manager to stop them manually
)

echo.
echo ========================================
echo Stop operation completed
echo ========================================
echo.
pause
