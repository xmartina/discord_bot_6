# Discord Bot Operation Guide

This guide provides instructions on how to properly run and manage the Discord Member Monitoring Bot.

## Prerequisites

- Windows operating system
- Python 3.8 or higher
- Discord bot token and user token configured in `config.yaml`

## Running the Bot

Follow these steps to run the bot properly:

1. **Test the Bot First**
   Always run the test script before starting the bot to ensure everything is configured correctly:
   ```
   .\test_bot.bat
   ```
   This will check your configuration, database, and Discord connectivity.

2. **Start the Bot**
   If the tests pass successfully, start the bot:
   ```
   .\start_bot.bat
   ```
   The bot will run in a command prompt window. Keep this window open to keep the bot running.

3. **Check Bot Status**
   To verify that the bot is running properly:
   ```
   .\check_bot_status.bat
   ```
   This will provide a detailed status report about the bot's operation.

4. **Stop the Bot**
   To stop the bot gracefully:
   ```
   .\stop_bot.bat
   ```
   This will attempt to stop the bot process without killing other Python processes.

5. **Restart the Bot**
   If you need to restart the bot:
   ```
   .\restart_bot.bat
   ```
   This will stop any running bot processes and start a new instance.

## Troubleshooting

If you encounter issues with the bot:

1. Check the log file at `logs/bot.log` for error messages
2. Ensure your Discord tokens in `config.yaml` are valid and have not expired
3. Verify that your internet connection is stable
4. Check that the bot has proper permissions in your Discord servers

## Database Backups

The bot automatically creates backups of the database in the `backups` directory. These backups can be used to restore data if needed.

## Configuration

The bot's behavior can be customized by editing the `config.yaml` file. Important settings include:

- `discord.token`: Your Discord bot token
- `discord.user_token`: Your personal Discord user token for monitoring servers where the bot isn't invited
- `notifications.method`: How notifications are delivered (discord_dm, email, webhook)
- `filters.minimum_account_age_days`: Filter out accounts newer than this many days
- `user_monitoring.check_interval`: How often to check for new members (in seconds)

## Advanced Usage

For advanced usage and customization, refer to the following documentation:

- `WINDOWS_SETUP_GUIDE.md`: Detailed setup instructions
- `USER_TOKEN_SETUP_GUIDE.md`: How to obtain and configure your user token
- `SSL_FIX_README.md`: Information about SSL certificate fixes

## Support

If you need additional help, please refer to the documentation files in the project directory or contact the bot developer. 