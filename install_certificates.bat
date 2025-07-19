@echo off
echo Installing SSL Certificates for Discord Bot
echo ==========================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing certifi package...
pip install certifi

echo Running certificate installation script...
python install_certificates.py

echo.
echo Certificate installation completed.
echo Now you can run the Discord bot with start_bot.bat
echo.
pause 