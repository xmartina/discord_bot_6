@echo off
echo Starting Discord Bot with SSL Fix
echo ==============================
echo.

echo Activating virtual environment...
call venv\Scripts\activate

echo Setting up SSL environment...
set SSL_CERT_FILE=%CD%\venv\Lib\site-packages\certifi\cacert.pem
set REQUESTS_CA_BUNDLE=%CD%\venv\Lib\site-packages\certifi\cacert.pem
set PYTHONHTTPSVERIFY=0

echo Running Discord Bot...
python main.py

echo.
echo Bot has stopped. Check logs for details.
echo.
pause 