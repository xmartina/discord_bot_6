# Manual Windows Setup Guide

## When Automated Setup Fails

If the automated setup scripts don't work, follow these manual steps to set up the Discord bot on Windows.

## Prerequisites Check

Before starting, ensure you have:
- Windows 10/11
- Administrator privileges
- Internet connection
- All bot files extracted to a folder (e.g., `C:\Discord_bot`)

## Step 1: Install Python

### Download and Install Python
1. Go to [https://python.org/downloads/](https://python.org/downloads/)
2. Download Python 3.8 or higher
3. **IMPORTANT**: During installation, check "Add Python to PATH"
4. Complete the installation

### Verify Python Installation
1. Press `Win + R`, type `cmd`, press Enter
2. Type: `python --version`
3. You should see something like "Python 3.x.x"
4. If not, reinstall Python and ensure "Add to PATH" is checked

## Step 2: Navigate to Bot Directory

### Open Command Prompt
1. Press `Win + R`, type `cmd`, press Enter
2. Navigate to your bot folder:
   ```cmd
   cd C:\path\to\Discord_bot
   ```
   (Replace with your actual path)

### Verify You're in the Right Directory
Type `dir` and you should see these files:
- main.py
- config.yaml
- requirements.txt
- src folder

## Step 3: Create Requirements File (If Missing)

If you get "requirements.txt not found" error:

1. Create a new text file called `requirements.txt`
2. Open it with Notepad
3. Paste this content:
   ```
   discord.py>=2.3.0
   python-dotenv>=1.0.0
   PyYAML>=6.0
   aiofiles>=23.0.0
   aiosqlite>=0.19.0
   aiohttp>=3.8.0
   colorama>=0.4.6
   typing-extensions>=4.0.0
   ```
4. Save the file

## Step 4: Create Virtual Environment

In the command prompt (make sure you're in the Discord_bot directory):

1. Create virtual environment:
   ```cmd
   python -m venv venv
   ```

2. Activate virtual environment:
   ```cmd
   venv\Scripts\activate
   ```

3. You should see `(venv)` at the beginning of your prompt

## Step 5: Install Dependencies

With the virtual environment activated:

1. Upgrade pip:
   ```cmd
   python -m pip install --upgrade pip
   ```

2. Install requirements:
   ```cmd
   pip install -r requirements.txt
   ```

If you get errors:
- Check your internet connection
- Try: `pip install discord.py aiohttp aiofiles aiosqlite PyYAML python-dotenv colorama`

## Step 6: Create Necessary Directories

Create these folders if they don't exist:
```cmd
mkdir data
mkdir logs
mkdir backups
```

## Step 7: Configure the Bot

### Create/Edit config.yaml
1. Open `config.yaml` with Notepad
2. If it doesn't exist, create it with this content:
   ```yaml
   discord:
     token: "YOUR_BOT_TOKEN_HERE"
     user_id: "YOUR_USER_ID_HERE"
     user_token: "YOUR_USER_TOKEN_HERE"

   notifications:
     method: "discord_dm"
     frequency: "instant"
     detailed_format: true

   user_monitoring:
     enabled: true
     check_interval: 300
     monitor_user_servers: true
     combine_with_bot_monitoring: true

   servers:
     monitor_all: true
     excluded_servers: []
     auto_discover: true
     max_servers: 100

   filters:
     minimum_account_age_days: 0
     ignore_bots: true
     ignore_system_messages: true

   database:
     type: "sqlite"
     path: "data/member_joins.db"
     backup_enabled: true
     backup_interval_hours: 24

   logging:
     level: "INFO"
     file: "logs/bot.log"
     max_file_size_mb: 10
     backup_count: 5

   performance:
     rate_limit_buffer: 1.0
     batch_size: 50
     memory_limit_mb: 512

   timezone: "UTC"
   ```

### Get Your Discord Tokens

#### Bot Token:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select existing one
3. Go to "Bot" section → Reset Token → Copy token
4. Replace "YOUR_BOT_TOKEN_HERE" in config.yaml

#### User Token:
1. Open Discord in web browser (Chrome/Firefox)
2. Press F12 → Network tab → Refresh page
3. Find any Discord API request
4. Look for "Authorization" in request headers
5. Copy the token value (starts with "MTc..." or similar)
6. Replace "YOUR_USER_TOKEN_HERE" in config.yaml

#### Your User ID:
1. In Discord: Settings → Advanced → Enable Developer Mode
2. Right-click your username → Copy ID
3. Replace "YOUR_USER_ID_HERE" in config.yaml

## Step 8: Test the Setup

With virtual environment still activated:

1. Test imports:
   ```cmd
   python -c "import discord; print('Discord.py installed successfully')"
   ```

2. Test bot configuration:
   ```cmd
   python test_monitoring.py
   ```

## Step 9: Run the Bot

Start the bot:
```cmd
python main.py
```

You should see:
- Bot login messages
- Server discovery
- User monitoring initialization
- "Bot is ready!" message

## Troubleshooting Common Issues

### "Python is not recognized"
- Reinstall Python with "Add to PATH" checked
- Restart command prompt
- Or use full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python3x\python.exe`

### "No module named 'discord'"
- Make sure virtual environment is activated: `venv\Scripts\activate`
- Reinstall: `pip install discord.py`

### "Access denied"
- Run command prompt as administrator
- Check if antivirus is blocking files

### "Config file not found"
- Make sure config.yaml exists in the Discord_bot directory
- Check file name spelling and extension

### "Invalid token"
- Regenerate bot token in Discord Developer Portal
- Get fresh user token from browser
- Make sure no extra spaces in config.yaml

### "No servers found"
- Verify user token is correct
- Make sure you're a member of Discord servers
- Check if user monitoring is enabled in config

## Creating Batch Files for Easy Use

Create these .bat files in your Discord_bot directory:

### start_bot.bat:
```batch
@echo off
call venv\Scripts\activate
python main.py
pause
```

### test_bot.bat:
```batch
@echo off
call venv\Scripts\activate
python test_monitoring.py
pause
```

### stop_bot.bat:
```batch
@echo off
taskkill /f /im python.exe
echo Bot stopped
pause
```

## Verification Checklist

Before considering setup complete:
- [ ] Python installed and in PATH
- [ ] Virtual environment created and working
- [ ] All dependencies installed without errors
- [ ] config.yaml exists with your tokens
- [ ] Test script runs successfully
- [ ] Bot starts without errors
- [ ] Startup notification received in Discord

## Getting Help

If you're still having issues:

1. Run the diagnostic script: `diagnose_setup.bat`
2. Check `logs\bot.log` for error details
3. Verify all tokens are correct and not expired
4. Make sure you have internet connectivity
5. Try running command prompt as administrator

## Security Notes

- Keep your tokens private and secure
- Never share your user token (gives full Discord account access)
- Add Discord_bot folder to Windows Defender exclusions if needed
- The bot only monitors public server information

Your Discord bot should now be working and monitoring both invited and uninvited servers!