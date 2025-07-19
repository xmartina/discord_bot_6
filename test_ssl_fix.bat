@echo off
echo Testing SSL Fix for Discord Bot
echo ==============================
echo.

echo Activating virtual environment...
call venv\Scripts\activate

echo Running SSL fix test...
python test_ssl_fix.py

echo.
echo If the test was successful, you can now run the bot with start_bot.bat
echo.
pause 