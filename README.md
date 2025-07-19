# Discord Member Monitoring Bot

A comprehensive Discord bot with **dual monitoring capabilities** that tracks member joins across all Discord servers. Get instant notifications with detailed user information whenever someone joins your servers.

## 🌟 Features

### Core Functionality
- **Dual Monitoring System**:
  - **Bot Monitoring**: Real-time notifications when the bot is invited to servers
  - **User Monitoring**: Periodic checks of servers where you're a regular member (bot not invited)
- **Complete Coverage**: Monitor member joins across ALL your Discord servers
- **Auto-Discovery**: Automatically discovers and monitors servers you're a member of
- **Detailed User Information**: Username, display name, user ID, account age, avatar, verification status, and more
- **Cross-Server Tracking**: Monitor member joins across multiple servers simultaneously
- **Smart Filtering**: Filter notifications by account age, bot accounts, and more

### Advanced Features
- **Server Management**: Exclude/include specific servers from monitoring
- **Database Storage**: SQLite database for storing member join history
- **Statistics & Reports**: Detailed statistics and member join reports
- **CLI Management**: Command-line interface for bot management
- **Backup System**: Automatic database backups
- **Rate Limiting**: Respects Discord API limits

### Notification Options
- **Discord DM**: Direct messages to your Discord account (default)
- **Multiple Formats**: Basic or detailed notification formats
- **Instant Alerts**: Real-time notifications as members join
- **Summary Reports**: Daily/weekly summary reports (planned)

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Discord account
- Discord bot token (we'll help you create one)

### Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd discord-member-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the setup wizard**
   ```bash
   python setup.py
   ```
   This will guide you through:
   - Creating necessary directories
   - Configuring your Discord bot token
   - Setting up your user ID for notifications
   - Choosing notification preferences

4. **Create your Discord bot** (if you haven't already)
   - Follow the detailed guide in [`DISCORD_BOT_SETUP_GUIDE.md`](DISCORD_BOT_SETUP_GUIDE.md)
   - **Important**: Enable "SERVER MEMBERS INTENT" in your bot settings

5. **Set up User Monitoring** (optional but recommended)
   - Follow the guide in [`USER_TOKEN_SETUP_GUIDE.md`](USER_TOKEN_SETUP_GUIDE.md)
   - This enables monitoring of servers where you're a member but the bot isn't invited
   - Provides complete coverage of all your Discord servers

6. **Start the bot**
   ```bash
   python main.py
   ```

## 📖 Usage

### Starting the Bot
```bash
python main.py
```

The bot will:
- Connect to Discord
- Discover all servers you're a member of
- Start monitoring for new member joins
- Send you a startup notification

### Command Line Interface
```bash
python cli.py
```

Available CLI commands:
- `status` - Show bot status and statistics
- `servers` - List all monitored servers
- `stats` - Show detailed statistics
- `recent [hours]` - Show recent member joins
- `exclude <server_id>` - Exclude a server from monitoring
- `include <server_id>` - Include a previously excluded server
- `config` - Show current configuration
- `backup` - Create database backup
- `cleanup [days]` - Clean old database records
- `help` - Show help information

### Example CLI Usage
```bash
# Show recent joins from last 48 hours
python cli.py recent 48

# Exclude a server from monitoring
python cli.py exclude 123456789

# Show bot statistics
python cli.py stats
```

## ⚙️ Configuration

The bot is configured through [`config.yaml`](config.yaml). Key settings include:

### Discord Settings
```yaml
discord:
  token: "YOUR_BOT_TOKEN_HERE"
  user_id: "YOUR_USER_ID_HERE"

# User Token for User Monitoring (optional)
user_token: "YOUR_USER_TOKEN_HERE"

# User Monitoring Settings
user_monitoring:
  enabled: true
  check_interval_minutes: 5  # How often to check for new members
```

### Notification Settings
```yaml
notifications:
  method: "discord_dm"  # discord_dm, email, webhook
  frequency: "instant"  # instant, hourly, daily
  detailed_format: true
```

### Server Monitoring
```yaml
servers:
  monitor_all: true
  excluded_servers: []  # List of server IDs to exclude
  auto_discover: true
  max_servers: 100
```

### Filtering Options
```yaml
filters:
  minimum_account_age_days: 0  # 0 = no filter
  ignore_bots: true
```

## 📊 Notification Examples

### Detailed Format (Default)

**Bot Monitoring (Real-time):**
```
🤖 New Member Joined (Bot Monitoring)

Server: My Discord Server (ID: 123456789)

Username: NewUser#1234
Display Name: New User
User ID: 987654321
Account Age: 2 years, 3 months, and 15 days
Created: 2022-01-15 14:30 UTC
Joined Server: 2024-12-07 18:45 UTC

Status: ✅ Verified | 🔸 New Account

Avatar: https://cdn.discordapp.com/avatars/...

Roles: Member

────────────────────────────────────────
Monitored by Discord Member Tracker
```

**User Monitoring (Periodic checks):**
```
👤 New Member Joined (User Monitoring)

Server: Another Discord Server (ID: 987654321)

Username: AnotherUser#5678
Display Name: Another User
User ID: 123456789
Account Age: 1 year, 2 months, and 5 days
Created: 2023-10-02 09:15 UTC
Joined Server: 2024-12-07 18:50 UTC

Status: ✅ Verified

Avatar: https://cdn.discordapp.com/avatars/...

────────────────────────────────────────
Monitored by Discord Member Tracker
```

### Basic Format
```
🤖 New Member Joined (Bot Monitoring)
User: NewUser#1234 (ID: 987654321)
Server: My Discord Server
```

```
👤 New Member Joined (User Monitoring)
User: AnotherUser#5678 (ID: 123456789)
Server: Another Discord Server
```

## 🗄️ Database

The bot uses SQLite to store:
- Server information and statistics
- Member join history
- Notification tracking
- Configuration data

Database files are stored in the `data/` directory.

## 📁 Project Structure

```
discord-member-bot/
├── main.py                 # Main bot entry point
├── cli.py                  # CLI entry point
├── setup.py               # Setup wizard
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── DISCORD_BOT_SETUP_GUIDE.md  # Bot setup guide
├── USER_TOKEN_SETUP_GUIDE.md   # User monitoring setup guide
├── src/                  # Source code
│   ├── discord_bot.py    # Main bot class
│   ├── config_manager.py # Configuration management
│   ├── database_manager.py # Database operations
│   ├── user_formatter.py # User data formatting
│   ├── notification_manager.py # Notification handling
│   ├── server_manager.py # Server discovery and management
│   ├── user_client.py    # User monitoring client
│   └── cli_manager.py    # CLI interface
├── data/                 # Database files
├── logs/                 # Log files
└── backups/             # Database backups
```

## 🔧 Troubleshooting

### Common Issues

**Bot not receiving member join events:**
- Ensure "SERVER MEMBERS INTENT" is enabled in Discord Developer Portal
- Check that the bot has proper permissions in the server
- Verify the bot is actually in the servers you want to monitor

**Configuration errors:**
- Run `python setup.py` to reconfigure
- Check `config.yaml` for correct token and user ID format
- Ensure your Discord user ID is correct (enable Developer Mode to copy it)

**Database issues:**
- Check that the `data/` directory exists and is writable
- Use `python cli.py backup` to create backups before troubleshooting
- Use `python cli.py cleanup` to clean old records if database is large

**Notification not working:**
- Verify your Discord user ID is correct
- Check that you can receive DMs (privacy settings)
- Use `python cli.py test` for testing information

**User monitoring not working:**
- Check that `user_token` is set correctly in config.yaml
- Verify your user token is valid (see USER_TOKEN_SETUP_GUIDE.md)
- Ensure `user_monitoring.enabled` is set to `true`
- Check logs for "User monitoring initialized successfully" message
- Verify you're actually a member of the servers you want to monitor

### Logging

Logs are stored in `logs/bot.log`. Check this file for detailed error information.

### Getting Help

1. Check the logs in `logs/bot.log`
2. Use `python cli.py status` to check bot status
3. Verify your configuration with `python cli.py config`
4. Review the Discord bot setup guide

## 🔒 Security & Privacy

- **Token Security**: Never share your bot token publicly
- **Data Privacy**: All data is stored locally in SQLite database
- **API Compliance**: Bot respects Discord's API rate limits and ToS
- **Minimal Permissions**: Bot only requests necessary permissions

## 📋 Requirements

### System Requirements
- Python 3.8+
- 50MB+ free disk space
- Internet connection
- Discord account

### Python Dependencies
- discord.py >= 2.3.0
- python-dotenv >= 1.0.0
- aiofiles >= 23.0.0
- aiosqlite >= 0.19.0
- aiohttp >= 3.8.0
- pyyaml >= 6.0
- colorama >= 0.4.6

## 🚨 Important Notes

### Discord Terms of Service
- This bot complies with Discord's Terms of Service
- Only monitors servers where you're a legitimate member
- Does not perform any automated actions beyond monitoring
- Respects Discord's API rate limits

### Bot Permissions
The bot needs these permissions in Discord servers:
- View Channels
- Read Message History
- Send Messages (for notifications)

### Server Members Intent
**Critical**: You must enable "SERVER MEMBERS INTENT" in your Discord bot settings, or the bot won't receive member join events.

## 🔄 Updates & Maintenance

### Regular Maintenance
- Use `python cli.py cleanup` to clean old database records
- Use `python cli.py backup` to create database backups
- Monitor `logs/bot.log` for any issues

### Updating the Bot
1. Backup your database and configuration
2. Update the code files
3. Install any new requirements: `pip install -r requirements.txt`
4. Restart the bot

## 📈 Performance

### Scalability
- Tested with 50+ servers simultaneously
- Efficient SQLite database with proper indexing
- Memory usage typically under 100MB
- Handles high-activity servers with rate limiting

### Optimization Tips
- Use server exclusion for very high-activity servers if needed
- Regular database cleanup to maintain performance
- Monitor logs for any rate limiting warnings

## 🤝 Contributing

This is a personal monitoring tool, but suggestions and improvements are welcome:

1. Check existing issues and documentation
2. Test your changes thoroughly
3. Follow the existing code style
4. Update documentation as needed

## 📄 License

This project is for personal use. Please respect Discord's Terms of Service and API guidelines when using this bot.

---

**Happy Monitoring!** 🎉

For additional help, check the [`DISCORD_BOT_SETUP_GUIDE.md`](DISCORD_BOT_SETUP_GUIDE.md) for bot setup or [`USER_TOKEN_SETUP_GUIDE.md`](USER_TOKEN_SETUP_GUIDE.md) for user monitoring setup. Review the configuration in [`config.yaml`](config.yaml).