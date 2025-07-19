@echo off
echo.
echo ====================================
echo Enhanced Discord Bot Monitoring Test
echo ====================================
echo.

:: Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found. Using system Python.
)

echo.
echo Choose test mode:
echo 1. Run test suite (quick verification)
echo 2. Run live monitoring (5 minutes)
echo 3. Run live monitoring (custom duration)
echo 4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running test suite...
    echo ========================
    python test_enhanced_monitoring.py
    goto :end
)

if "%choice%"=="2" (
    echo.
    echo Running live monitoring for 5 minutes...
    echo ========================================
    echo This will test real-time detection - try joining Abu Cartel now!
    echo.
    python test_enhanced_monitoring.py live 5
    goto :end
)

if "%choice%"=="3" (
    set /p duration="Enter duration in minutes: "
    echo.
    echo Running live monitoring for %duration% minutes...
    echo =============================================
    echo This will test real-time detection - try joining Abu Cartel now!
    echo.
    python test_enhanced_monitoring.py live %duration%
    goto :end
)

if "%choice%"=="4" (
    echo Exiting...
    goto :end
)

echo Invalid choice. Please run the script again.

:end
echo.
echo Test completed. Check the logs for detailed results.
echo Log file: logs\enhanced_monitoring_test.log
echo.
pause
