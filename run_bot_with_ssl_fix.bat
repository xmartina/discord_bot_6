@echo off
echo Starting Discord Bot with SSL Fix
echo ==============================
echo.

echo Activating virtual environment...
call venv\Scripts\activate

echo Setting up SSL environment...
set PYTHONHTTPSVERIFY=0
set PYTHONWARNINGS=ignore:Unverified HTTPS request

echo Running Discord Bot...
python main.py

echo.
echo Bot has stopped. Check logs for details.
echo.
pause 