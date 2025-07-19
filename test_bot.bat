@echo off
echo Testing Discord Bot
echo ==================
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
    echo Please make sure config.yaml exists in the current directory
    pause
    exit /b 1
)

echo Running bot tests...
echo.
python test_monitoring.py
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Tests failed! Check the output above.
    echo ========================================
    echo.
    echo Common issues:
    echo - Invalid Discord tokens in config.yaml
    echo - Network connectivity problems
    echo - Missing user permissions
    echo.
    echo Check logs\bot.log for more details
    pause
    exit /b 1
)

echo.
echo ========================================
echo All tests passed! The bot is ready to run.
echo ========================================
echo.
echo You can now run start_bot.bat to start the Discord bot
echo.
pause
