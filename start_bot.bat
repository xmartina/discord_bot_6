@echo off
echo Starting Discord Bot
echo ====================
echo.

echo Checking if virtual environment exists...
if not exist "venv\Scripts\activate.bat" (
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
    echo ERROR: config.yaml not found
    echo Please make sure config.yaml exists and is configured with your Discord tokens
    pause
    exit /b 1
)

echo Creating necessary directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

echo.
echo ========================================
echo Discord Bot is starting...
echo ========================================
echo.
echo The bot will monitor Discord servers for new members
echo Press Ctrl+C to stop the bot
echo.
echo Bot logs will be saved to logs\bot.log
echo.

python main.py
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Bot stopped with an error!
    echo ========================================
    echo.
    echo Check logs\bot.log for error details
    echo If this is the first run, make sure:
    echo - Discord tokens are correctly configured in config.yaml
    echo - You have internet connectivity
    echo - The bot has proper permissions
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Bot stopped normally
echo ========================================
echo.
pause
