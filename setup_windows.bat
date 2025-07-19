@echo off
echo Discord Bot Multi-Platform Setup (Windows/Linux Compatible)
echo ===========================================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    echo For AWS/Linux servers, use: sudo apt-get install python3 python3-pip python3-venv
    pause
    exit /b 1
)

echo Python found! Continuing setup...
echo.

echo Checking current directory...
echo Current directory: %CD%
if not exist "main.py" (
    echo ERROR: main.py not found in current directory
    echo Please make sure you are running this script from the Discord_bot folder
    echo The folder should contain: main.py, config.yaml, src folder, etc.
    pause
    exit /b 1
)

echo Checking for requirements.txt...
if not exist "requirements.txt" (
    echo requirements.txt not found. Creating it...
    echo discord.py^>=2.3.0 > requirements.txt
    echo python-dotenv^>=1.0.0 >> requirements.txt
    echo aiofiles^>=23.0.0 >> requirements.txt
    echo aiosqlite^>=0.19.0 >> requirements.txt
    echo aiohttp^>=3.8.0 >> requirements.txt
    echo pyyaml^>=6.0 >> requirements.txt
    echo colorama^>=0.4.6 >> requirements.txt
    echo Created requirements.txt
)

echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
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

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Check your internet connection and try again
    echo.
    echo For SSL issues on AWS/Linux, try:
    echo pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
    pause
    exit /b 1
)

echo Installing additional SSL/Unicode fixes...
pip install certifi --upgrade
pip install charset-normalizer --upgrade

echo Creating necessary directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

echo Checking for config.yaml...
if not exist "config.yaml" (
    echo config.yaml not found. Creating from template...
    if exist "config_template_windows.yaml" (
        copy "config_template_windows.yaml" "config.yaml"
        echo Created config.yaml from template
    ) else (
        echo No template found. You'll need to create config.yaml manually.
    )
)

echo.
echo Applying Unicode/Encoding fixes for AWS compatibility...
echo.
echo # Set Unicode environment variables > set_encoding.bat
echo set PYTHONIOENCODING=utf-8 >> set_encoding.bat
echo set PYTHONUTF8=1 >> set_encoding.bat
echo chcp 65001 >> set_encoding.bat

echo Creating AWS-compatible startup script...
echo #!/bin/bash > start_bot_aws.sh
echo export PYTHONIOENCODING=utf-8 >> start_bot_aws.sh
echo export PYTHONUTF8=1 >> start_bot_aws.sh
echo cd "$(dirname "$0")" >> start_bot_aws.sh
echo source venv/bin/activate 2>/dev/null ^|^| source venv/Scripts/activate >> start_bot_aws.sh
echo python main.py >> start_bot_aws.sh
chmod +x start_bot_aws.sh 2>nul

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo IMPORTANT: Rate limiting and Unicode fixes applied!
echo.
echo Next steps:
echo 1. Edit config.yaml with your Discord tokens:
echo    - Bot token (from Discord Developer Portal)
echo    - User token (from Discord web app)
echo    - Your Discord user ID
echo.
echo 2. For Windows: Run test_bot.bat to test the setup
echo 3. For AWS/Linux: Run ./start_bot_aws.sh or bash start_bot_aws.sh
echo 4. For Windows with AWS compatibility: Run start_bot_aws.bat
echo 5. For regular Windows: Run start_bot.bat to start the bot
echo.
echo DEBUGGING TOOLS AVAILABLE:
echo - test_rate_limiting.bat - Test API rate limits and token validity
echo - test_enhanced_detection.bat - Test username detection improvements
echo - start_bot_aws.sh - AWS/Linux compatible startup script
echo - start_bot_aws.bat - Windows batch file with AWS compatibility
echo - logs/rate_limit_test.log - Rate limiting test results
echo - logs/enhanced_detection_test.log - Detection method test results
echo.
echo FIXES APPLIED:
echo - RATE LIMITING: Bot now includes 1.5-second delays between API calls
echo - UNICODE FIXES: Log encoding errors should be resolved
echo - ENHANCED DETECTION: Bot prioritizes activity-based detection for real usernames
echo - MESSAGE SCANNING: Bot scans recent messages to find actual user details
echo - DETECTION PRIORITY: Activity methods run before count-based fallbacks
echo - AWS COMPATIBILITY: Created start_bot_aws.sh for Linux servers
echo.
echo TROUBLESHOOTING:
echo - If you see "New Member(s) Online" instead of usernames:
echo   1. Run test_enhanced_detection.bat to check detection methods
echo   2. Run test_rate_limiting.bat to verify API access
echo   3. Bot now prioritizes activity-based detection automatically
echo - For AWS servers, use start_bot_aws.sh or start_bot_aws.bat
echo - For Unicode errors on Windows, use start_bot_aws.bat
echo - Check logs/bot.log for detailed error information
echo - Bot will now prefer real usernames from messages over generic counts
echo.
echo For help getting tokens, see WINDOWS_SETUP_GUIDE.md
echo.
pause
