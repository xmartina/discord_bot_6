@echo off
echo Discord Bot Restart Utility
echo =========================
echo.

echo Checking if bot is running...
tasklist /FI "IMAGENAME eq python.exe" | find "python.exe" > nul
if %errorlevel% equ 0 (
    echo Bot process found. Stopping bot...
    call stop_bot.bat
    timeout /t 5 /nobreak > nul
) else (
    echo No bot process found.
)

echo Starting bot...
start "" cmd /c start_bot.bat

echo.
echo Bot has been restarted in a new window.
echo You can close this window.
echo.
pause 