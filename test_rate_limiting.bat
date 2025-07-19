@echo off
echo Discord Bot Rate Limiting Test
echo =============================
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
echo Starting Rate Limiting Test...
echo ========================================
echo.
echo This test will:
echo 1. Check your user token validity
echo 2. Test API rate limiting
echo 3. Verify guild access permissions
echo 4. Test member data retrieval
echo.
echo Results will be saved to: logs/rate_limit_test.log
echo.

python test_rate_limiting.py

echo.
echo ========================================
echo Test completed!
echo ========================================
echo.
echo Check logs/rate_limit_test.log for detailed results
echo.
pause
