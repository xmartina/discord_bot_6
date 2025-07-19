@echo off
echo Discord Bot AWS Compatibility Startup (Windows)
echo =============================================
echo.

echo Setting UTF-8 encoding environment...
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
chcp 65001 >nul 2>&1

echo Checking if Git Bash or WSL is available...
where bash >nul 2>&1
if %errorlevel% equ 0 (
    echo Found Bash - Running AWS startup script...
    bash start_bot_aws.sh
    goto :end
)

echo Bash not found - Running Windows equivalent...
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org/downloads/
    pause
    exit /b 1
)

echo Python found! Continuing setup...
echo Current directory: %CD%

echo Checking for main.py...
if not exist "main.py" (
    echo ERROR: main.py not found in current directory
    echo Please run this script from the Discord bot folder
    pause
    exit /b 1
)

echo Checking virtual environment...
if not exist "venv" (
    echo ERROR: Virtual environment not found
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Checking configuration...
if not exist "config.yaml" (
    echo WARNING: config.yaml not found
    if exist "config_template_windows.yaml" (
        echo Creating config.yaml from template...
        copy "config_template_windows.yaml" "config.yaml"
        echo Please edit config.yaml with your Discord tokens before running again
        pause
        exit /b 1
    ) else (
        echo ERROR: No config template found
        pause
        exit /b 1
    )
)

echo Creating necessary directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

echo.
echo ========================================
echo Starting Discord Bot...
echo ========================================
echo.
echo UTF-8 Encoding: ENABLED
echo Rate Limiting: ENABLED (2 second delays)
echo AWS Compatibility: ENABLED
echo.
echo Logs will be saved to: logs\bot.log
echo To stop the bot, press Ctrl+C
echo.

python main.py

:end
echo.
echo ========================================
echo Bot stopped.
echo ========================================
echo.
if exist "logs\bot.log" (
    echo Check logs\bot.log for details
) else (
    echo No log file found - check console output above
)
echo.
pause
