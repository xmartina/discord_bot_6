@echo off
echo Discord Bot Setup Diagnostics
echo ============================
echo.

echo [1/8] Checking current directory...
echo Current directory: %CD%
echo.

echo [2/8] Checking for required files...
set MISSING_FILES=0

if exist "main.py" (
    echo ✓ main.py found
) else (
    echo ✗ main.py MISSING
    set /a MISSING_FILES+=1
)

if exist "config.yaml" (
    echo ✓ config.yaml found
) else (
    echo ✗ config.yaml MISSING
    set /a MISSING_FILES+=1
)

if exist "requirements.txt" (
    echo ✓ requirements.txt found
) else (
    echo ✗ requirements.txt MISSING
    set /a MISSING_FILES+=1
)

if exist "src" (
    echo ✓ src folder found
) else (
    echo ✗ src folder MISSING
    set /a MISSING_FILES+=1
)

echo.

echo [3/8] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo ✓ %%i
) else (
    echo ✗ Python not found or not in PATH
    echo   Please install Python from https://python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during installation
)
echo.

echo [4/8] Checking pip installation...
python -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python -m pip --version 2^>^&1') do echo ✓ %%i
) else (
    echo ✗ pip not found
)
echo.

echo [5/8] Checking virtual environment...
if exist "venv" (
    echo ✓ venv folder exists
    if exist "venv\Scripts\python.exe" (
        echo ✓ Virtual environment appears complete
    ) else (
        echo ✗ Virtual environment incomplete
    )
) else (
    echo ✗ Virtual environment not found
)
echo.

echo [6/8] Checking internet connectivity...
ping -n 1 google.com >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Internet connection available
) else (
    echo ✗ No internet connection (may affect package installation)
)
echo.

echo [7/8] Checking file permissions...
echo test > test_write.tmp 2>nul
if exist "test_write.tmp" (
    echo ✓ Write permissions OK
    del test_write.tmp
) else (
    echo ✗ No write permissions - try running as administrator
)
echo.

echo [8/8] Checking Windows version...
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo ✓ Windows version: %VERSION%
echo.

echo ============================
echo DIAGNOSTIC SUMMARY
echo ============================

if %MISSING_FILES% equ 0 (
    echo ✓ All required files present
) else (
    echo ✗ %MISSING_FILES% required files missing
    echo   Make sure you're in the correct Discord_bot directory
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python installation OK
) else (
    echo ✗ Python installation issue
    echo   SOLUTION: Install Python from https://python.org/downloads/
    echo             Check "Add Python to PATH" during installation
)

if exist "venv\Scripts\python.exe" (
    echo ✓ Virtual environment OK
) else (
    echo ✗ Virtual environment missing or incomplete
    echo   SOLUTION: Delete venv folder and run setup_windows.bat again
)

ping -n 1 google.com >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Internet connectivity OK
) else (
    echo ✗ Internet connectivity issue
    echo   SOLUTION: Check your internet connection
)

echo.
echo RECOMMENDED ACTIONS:
echo.

if %MISSING_FILES% gtr 0 (
    echo 1. Navigate to the correct Discord_bot directory
    echo    The directory should contain: main.py, config.yaml, src folder, etc.
    echo.
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 2. Install Python:
    echo    - Download from https://python.org/downloads/
    echo    - Check "Add Python to PATH" during installation
    echo    - Restart command prompt after installation
    echo.
)

if exist "venv" (
    if not exist "venv\Scripts\python.exe" (
        echo 3. Fix virtual environment:
        echo    - Delete the venv folder
        echo    - Run setup_windows.bat again
        echo.
    )
) else (
    echo 3. Create virtual environment:
    echo    - Run setup_windows.bat
    echo.
)

if not exist "config.yaml" (
    echo 4. Configure the bot:
    echo    - Edit config.yaml with your Discord tokens
    echo    - See WINDOWS_SETUP_GUIDE.md for help getting tokens
    echo.
)

echo 5. After fixing issues, run setup_windows.bat again
echo.

echo Press any key to continue...
pause >nul
