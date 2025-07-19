# Discord Bot Windows Setup Guide

## Prerequisites

### 1. Install Python 3.8 or higher
- Download from [python.org](https://www.python.org/downloads/)
- During installation, **check "Add Python to PATH"**
- Verify installation: Open Command Prompt and run:
  ```cmd
  python --version
  ```

### 2. Install Git (Optional but recommended)
- Download from [git-scm.com](https://git-scm.com/download/win)
- Or download the project as ZIP file

## Quick Setup (Automated)

### Option 1: Using Batch Script (Recommended)

1. **Download/Extract** the Discord_bot folder to your desired location
2. **Open Command Prompt as Administrator**
3. **Navigate** to the Discord_bot directory:
   ```cmd
   cd C:\path\to\Discord_bot
   ```
4. **Run the setup script**:
   ```cmd
   setup_windows.bat
   ```

### Option 2: Manual Setup

Follow the detailed instructions below if you prefer manual setup or the batch script doesn't work.

## Manual Setup Instructions

### Step 1: Open Command Prompt
- Press `Win + R`, type `cmd`, press Enter
- Or search "Command Prompt" in Start menu

### Step 2: Navigate to Bot Directory
```cmd
cd C:\path\to\Discord_bot
```
Replace `C:\path\to\Discord_bot` with the actual path where you extracted the bot files.

### Step 3: Create Virtual Environment
```cmd
python -m venv venv
```

### Step 4: Activate Virtual Environment
```cmd
venv\Scripts\activate
```
You should see `(venv)` at the beginning of your command prompt.

### Step 5: Install Dependencies
```cmd
pip install -r requirements.txt
```

### Step 6: Configure the Bot
1. Open `config.yaml` in a text editor (Notepad, VS Code, etc.)
2. Update the following fields:
   ```yaml
   discord:
     token: "YOUR_BOT_TOKEN_HERE"
     user_id: "YOUR_DISCORD_USER_ID_HERE"
     user_token: "YOUR_DISCORD_USER_TOKEN_HERE"
   ```

### Step 7: Test the Setup
```cmd
python test_monitoring.py
```

### Step 8: Run the Bot
```cmd
python main.py
```

## Getting Your Discord Tokens

### Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select existing one
3. Go to "Bot" section
4. Click "Reset Token" and copy the token
5. **Keep this token secret!**

### User Token (For monitoring uninvited servers)
1. Open Discord in your web browser
2. Press `F12` to open Developer Tools
3. Go to "Network" tab
4. Refresh the page
5. Look for any request to Discord API
6. Check request headers for "Authorization" header
7. Copy the token (starts with "MTc..." or similar)
8. **Keep this token secret and never share it!**

### Your User ID
1. In Discord, go to User Settings (gear icon)
2. Go to "Advanced" and enable "Developer Mode"
3. Right-click on your username and select "Copy ID"

## Batch Scripts for Easy Management

### Create `setup_windows.bat`
Create a file named `setup_windows.bat` in the Discord_bot directory with this content:

```batch
@echo off
echo Discord Bot Windows Setup
echo ========================

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org/downloads/
    pause
    exit /b 1
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

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Creating directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

echo Setup complete!
echo.
echo Next steps:
echo 1. Edit config.yaml with your Discord tokens
echo 2. Run test_bot.bat to test the setup
echo 3. Run start_bot.bat to start the bot
echo.
pause
```

### Create `test_bot.bat`
Create a file named `test_bot.bat` in the Discord_bot directory:

```batch
@echo off
echo Testing Discord Bot
echo ==================

call venv\Scripts\activate
echo Running tests...
python test_monitoring.py
if %errorlevel% neq 0 (
    echo.
    echo Tests failed! Check the output above.
    pause
    exit /b 1
)

echo.
echo All tests passed! The bot is ready to run.
pause
```

### Create `start_bot.bat`
Create a file named `start_bot.bat` in the Discord_bot directory:

```batch
@echo off
echo Starting Discord Bot
echo ====================

call venv\Scripts\activate
echo Bot is starting...
python main.py
pause
```

### Create `stop_bot.bat`
Create a file named `stop_bot.bat` in the Discord_bot directory:

```batch
@echo off
echo Stopping Discord Bot
echo ====================

taskkill /f /im python.exe
echo Bot stopped.
pause
```

## Running the Bot

### First Time Setup
1. Run `setup_windows.bat` as Administrator
2. Edit `config.yaml` with your tokens
3. Run `test_bot.bat` to verify everything works
4. Run `start_bot.bat` to start the bot

### Daily Usage
- **Start Bot**: Double-click `start_bot.bat`
- **Stop Bot**: Press `Ctrl+C` in the command window or run `stop_bot.bat`
- **Test Bot**: Run `test_bot.bat` if you make changes

## Troubleshooting

### Common Issues

#### "Python is not recognized"
- Reinstall Python and check "Add Python to PATH" during installation
- Or manually add Python to PATH in System Environment Variables

#### "pip is not recognized"
- Python wasn't properly installed
- Try: `python -m pip install -r requirements.txt`

#### "Access denied" errors
- Run Command Prompt as Administrator
- Check if antivirus is blocking the files

#### "Module not found" errors
- Make sure virtual environment is activated: `venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

#### Bot doesn't start
- Check `config.yaml` for correct token format
- Verify tokens are valid and not expired
- Check `logs\bot.log` for error messages

### Getting Help

1. **Check Logs**: Look in `logs\bot.log` for error messages
2. **Run Tests**: Use `test_bot.bat` to diagnose issues
3. **Verify Config**: Double-check `config.yaml` settings
4. **Check Network**: Ensure internet connection is working

## Configuration Tips

### Performance Settings
For Windows systems, you might want to adjust these settings in `config.yaml`:

```yaml
user_monitoring:
  check_interval: 300  # 5 minutes (increase if CPU usage is high)

performance:
  rate_limit_buffer: 1.5  # Increase if getting rate limited
  memory_limit_mb: 256   # Decrease if running low on RAM
```

### Startup with Windows
To start the bot automatically when Windows starts:

1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `start_bot.bat` in the startup folder

## Security Notes

### Protecting Your Tokens
- Never share your bot token or user token
- Don't commit `config.yaml` to version control
- Consider using environment variables for production

### Windows Defender
- Add the Discord_bot folder to Windows Defender exclusions
- This prevents antivirus from interfering with the bot

## Advanced Usage

### Running as Windows Service
For advanced users who want the bot to run as a Windows service:

1. Install `python-windows-service`:
   ```cmd
   pip install pywin32
   ```

2. Create a service wrapper (advanced topic)

### Monitoring Multiple Accounts
- Create separate folders for each Discord account
- Use different `config.yaml` files for each setup
- Run multiple instances with different batch files

## Support

If you encounter issues:
1. Check the logs in `logs\bot.log`
2. Run the test script to identify problems
3. Verify your Discord tokens are correct
4. Ensure you have proper permissions in Discord servers

The bot should now properly monitor Discord servers where you're a member, regardless of whether the bot was formally invited to those servers!