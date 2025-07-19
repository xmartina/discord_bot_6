@echo off
echo Enhanced Detection Test for Discord Bot
echo =======================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and make sure it's in your PATH
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
    echo ERROR: config.yaml not found
    echo Please create and configure config.yaml first
    pause
    exit /b 1
)

echo Creating logs directory...
if not exist "logs" mkdir logs

echo.
echo ========================================
echo Starting Enhanced Detection Test...
echo ========================================
echo.
echo This test will check:
echo 1. Activity-based detection methods
echo 2. Real username vs generic detection
echo 3. Message scanning capabilities
echo 4. Overall bot detection success rate
echo.
echo The test will help identify if your bot is:
echo - Getting real usernames (GOOD)
echo - Getting "New Member(s) Online" messages (NEEDS FIX)
echo.
echo Results will be saved to: logs/enhanced_detection_test.log
echo.

python test_enhanced_detection.py

echo.
echo ========================================
echo Enhanced Detection Test Completed!
echo ========================================
echo.
echo Check the output above for:
echo - Success rate of real username detection
echo - Which detection methods are working best
echo - Recommendations for your bot setup
echo.
echo If success rate is low, the bot has been updated to
echo prioritize activity-based detection over count-based.
echo.
pause
