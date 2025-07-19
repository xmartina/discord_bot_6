# Discord Bot Windows Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Download and Extract
1. Download the Discord_bot folder to your computer
2. Extract it to a location like `C:\Discord_bot`
3. Open the folder in Windows Explorer

### Step 2: Run Setup
1. **Right-click** on `setup_windows.bat`
2. Select **"Run as administrator"**
3. Wait for the installation to complete

### Step 3: Configure Tokens
1. Open `config.yaml` with Notepad
2. Replace the following values:
   ```yaml
   discord:
     token: "YOUR_BOT_TOKEN_HERE"
     user_id: "YOUR_USER_ID_HERE"
     user_token: "YOUR_USER_TOKEN_HERE"
   ```

### Step 4: Test and Run
1. Double-click `test_bot.bat` to verify setup
2. Double-click `start_bot.bat` to start the bot
3. Check Discord for startup notification

---

## 🔑 Getting Your Discord Tokens

### Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" or select existing one
3. Go to "Bot" section on the left
4. Click "Reset Token" and copy the new token
5. Paste it in `config.yaml` replacing `YOUR_BOT_TOKEN_HERE`

### User Token
1. Open Discord in your web browser (not the app)
2. Press `F12` to open Developer Tools
3. Go to "Network" tab
4. Refresh the page (`F5`)
5. Look for any request to `discord.com/api`
6. Click on it and find "Authorization" in Request Headers
7. Copy the value (starts with "MTc..." or similar)
8. Paste it in `config.yaml` replacing `YOUR_USER_TOKEN_HERE`

### Your User ID
1. In Discord, go to Settings (gear icon)
2. Go to "Advanced" and enable "Developer Mode"
3. Close settings and right-click on your username
4. Select "Copy ID"
5. Paste it in `config.yaml` replacing `YOUR_USER_ID_HERE`

---

## 📁 File Structure

```
Discord_bot/
├── setup_windows.bat     ← Run this first
├── test_bot.bat          ← Test your setup
├── start_bot.bat         ← Start the bot
├── stop_bot.bat          ← Stop the bot
├── config.yaml           ← Your configuration
├── main.py               ← Bot main file
├── requirements.txt      ← Python dependencies
├── venv/                 ← Virtual environment (created automatically)
├── data/                 ← Database files
├── logs/                 ← Log files
└── backups/              ← Database backups
```

---

## 🎯 Usage Instructions

### Starting the Bot
- **Double-click** `start_bot.bat`
- A command window will open showing bot status
- You'll receive a Discord DM when bot starts
- **Keep the window open** - closing it stops the bot

### Stopping the Bot
- **Press `Ctrl + C`** in the bot window
- Or double-click `stop_bot.bat`
- Or close the command window

### Testing the Bot
- **Double-click** `test_bot.bat`
- Verifies all systems are working
- Run this after making configuration changes

### Viewing Logs
- Check `logs\bot.log` for detailed information
- Open with Notepad or any text editor
- Useful for troubleshooting issues

---

## 🔧 Common Issues & Solutions

### "Python is not recognized"
**Problem**: Python not installed or not in PATH
**Solution**: 
1. Download Python from [python.org](https://python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart command prompt and try again

### "The bot token is invalid"
**Problem**: Wrong or expired bot token
**Solution**: 
1. Go to Discord Developer Portal
2. Reset your bot token
3. Update `config.yaml` with new token

### "Access denied" errors
**Problem**: Insufficient permissions
**Solution**: 
1. Right-click on batch files
2. Select "Run as administrator"
3. Or disable Windows Defender temporarily

### Bot starts but no notifications
**Problem**: Configuration issues
**Solution**: 
1. Verify your user ID is correct
2. Check if DMs are enabled in Discord settings
3. Make sure bot is in at least one server

### "Module not found" errors
**Problem**: Dependencies not installed
**Solution**: 
1. Delete `venv` folder
2. Run `setup_windows.bat` again
3. Make sure you have internet connection

---

## 🎮 What the Bot Does

### Bot Monitoring (🤖)
- Monitors servers where your bot is invited
- Gets full member details and real-time join events
- Provides complete user information

### User Monitoring (👤)
- Monitors servers where you're a member but bot isn't invited
- Uses your user account to detect new members
- Provides limited but useful information

### Notifications
- Sends Discord DMs when new members join
- Shows monitoring source (Bot vs User)
- Includes user details, account age, and server info

---

## ⚙️ Configuration Options

### Basic Settings (in config.yaml)
```yaml
# How often to check for new members (seconds)
user_monitoring:
  check_interval: 300  # 5 minutes

# Notification settings
notifications:
  method: "discord_dm"    # Where to send notifications
  frequency: "instant"    # When to send them
  detailed_format: true   # Include full user details

# Filter settings
filters:
  ignore_bots: true              # Don't notify for bots
  minimum_account_age_days: 0    # Minimum account age
```

### Performance Settings
```yaml
# Adjust for your system
performance:
  rate_limit_buffer: 1.0    # Delay between API calls
  memory_limit_mb: 512      # Memory usage limit
  
# Logging
logging:
  level: "INFO"             # DEBUG for troubleshooting
  file: "logs/bot.log"      # Log file location
```

---

## 🔒 Security Notes

### Keep Your Tokens Safe
- **Never share** your bot token or user token
- **Don't post** them in Discord or online
- **Regenerate** tokens if compromised

### User Token Warning
- Your user token gives **full access** to your Discord account
- The bot only uses it to monitor servers
- **Keep it secure** and never share it

### Windows Defender
- May flag Python files as suspicious
- Add Discord_bot folder to exclusions if needed
- This is normal for Python applications

---

## 📊 Monitoring Multiple Servers

### Server Types
- **Bot-invited servers**: Full monitoring with complete data
- **User-member servers**: Limited monitoring with basic data
- **Excluded servers**: Listed in config, not monitored

### Expected Behavior
- Bot discovers all servers automatically
- Shows monitoring method in logs
- Handles inaccessible servers gracefully

### Example Log Output
```
INFO - Found 9 guilds where user is a member
INFO - No member count available for Server_Name, trying alternative monitoring methods
INFO - Detected potential new member through channel activity in Server_Name
INFO - Processing user monitoring join: username in Server_Name
INFO - Notification sent for username in Server_Name (via user monitoring)
```

---

## 🆘 Getting Help

### Check These First
1. **Log file**: `logs\bot.log` contains error details
2. **Test script**: Run `test_bot.bat` to diagnose issues
3. **Configuration**: Verify tokens and settings in `config.yaml`

### Common Log Messages
- `✅ Bot is ready!` - Everything working
- `❌ Failed to initialize user monitoring` - Check user token
- `⚠️ Rate limited` - Increase rate_limit_buffer in config
- `🔍 No member count available` - Normal for uninvited servers

### When to Restart
- After changing configuration
- If bot stops responding
- When Discord updates cause issues

---

## 🔄 Maintenance

### Regular Tasks
- **Check logs** weekly for any issues
- **Update tokens** if they expire
- **Backup configuration** before making changes

### Updates
- Download new version when available
- Run `setup_windows.bat` again
- Restore your `config.yaml` settings

### Performance Monitoring
- Watch memory usage in Task Manager
- Monitor network activity
- Check log file size (rotates automatically)

---

## 📱 Advanced Features

### Startup with Windows
1. Press `Win + R`, type `shell:startup`
2. Create shortcut to `start_bot.bat`
3. Bot will start automatically with Windows

### Multiple Accounts
- Create separate folders for each Discord account
- Use different configuration files
- Run multiple bots simultaneously

### Custom Notifications
- Edit notification templates in code
- Add webhook support for other services
- Customize message formats

---

## ✅ Success Checklist

Before considering setup complete:
- [ ] Python installed and in PATH
- [ ] Virtual environment created
- [ ] Dependencies installed successfully
- [ ] config.yaml configured with your tokens
- [ ] Test script passes all checks
- [ ] Bot starts without errors
- [ ] Startup notification received in Discord
- [ ] Log file shows servers being monitored
- [ ] Bot detects new members (test in a server)

---

**🎉 Congratulations! Your Discord Member Monitoring Bot is now running and monitoring both invited and uninvited servers on Windows!**

For detailed technical information, see `IMPROVEMENTS_DOCUMENTATION.md`
