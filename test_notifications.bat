@echo off
echo Testing Discord Bot Notifications
echo =================================
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
    echo Please make sure config.yaml exists and is configured
    pause
    exit /b 1
)

echo.
echo ========================================
echo Running Notification Tests...
echo ========================================
echo.
echo This will test:
echo - Discord DM sending functionality
echo - User monitoring notifications
echo - Database duplicate prevention
echo - Message formatting
echo.
echo The bot will send test messages to verify everything works.
echo Check your Discord DMs during the test.
echo.

python test_notifications.py
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Notification tests failed!
    echo ========================================
    echo.
    echo Common issues:
    echo - Invalid Discord tokens in config.yaml
    echo - DMs disabled in Discord settings
    echo - Bot not properly configured
    echo - Network connectivity problems
    echo.
    echo Check logs for more details
    pause
    exit /b 1
)

echo.
echo ========================================
echo All notification tests passed!
echo ========================================
echo.
echo If you received test messages in Discord, the notification system is working.
echo If not, check:
echo 1. Your Discord user ID is correct in config.yaml
echo 2. DMs are enabled in your Discord privacy settings
echo 3. The bot has proper permissions
echo.
echo You can now run start_bot.bat to start monitoring
echo.
pause
