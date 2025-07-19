# Discord User Token Setup Guide

This guide explains how to obtain your personal Discord user token to enable user monitoring functionality in the Discord Member Tracker bot.

## ⚠️ Important Security Warning

**Your user token is extremely sensitive and should be treated like a password:**
- Never share your user token with anyone
- Never post it publicly (GitHub, Discord, forums, etc.)
- Only use it with trusted applications
- Regularly check your Discord account for unauthorized activity

## What is User Monitoring?

User monitoring allows the bot to check servers where you're a regular member but the bot isn't invited. This works by using your personal Discord token to access Discord as if you were browsing it yourself.

**Key differences:**
- **Bot Monitoring**: Real-time notifications when the bot is invited to servers
- **User Monitoring**: Periodic checks (every 5 minutes by default) of servers where you're a member

## How to Get Your Discord User Token

### Method 1: Browser Developer Tools (Recommended)

1. **Open Discord in your web browser** (discord.com)
2. **Log in to your Discord account**
3. **Open Developer Tools**:
   - Chrome/Edge: Press `F12` or `Ctrl+Shift+I`
   - Firefox: Press `F12` or `Ctrl+Shift+I`
   - Safari: Press `Cmd+Option+I`
git remote set-url origin  https://xmartina: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@github.com/xmartina/discord_bot_5.git

git remote add origin https://github.com/xmartina/discord_bot_5.git
4. **Go to the Network tab** in Developer Tools
5. **Refresh the page** (`F5` or `Ctrl+R`)
6. **Filter by "api"** in the network requests
7. **Look for requests to `discord.com/api/`**
8. **Click on any API request** (like `/users/@me` or `/guilds`)
9. **Go to the Headers section**
10. **Find the "Authorization" header**
11. **Copy the value** (it should start with your token)

### Method 2: Console Method (Alternative)

1. **Open Discord in your web browser**
2. **Open Developer Tools** (`F12`)
3. **Go to the Console tab**
4. **Paste this code and press Enter**:
   ```javascript
   (webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
   ```
5. **Copy the returned token** (without quotes)

## Setting Up User Token in the Bot

1. **Open your `config.yaml` file**
2. **Find the `user_token` field** (should be empty by default)
3. **Paste your token**:
   ```yaml
   # Discord User Token (for user monitoring)
   user_token: "YOUR_TOKEN_HERE"
   ```

4. **Configure user monitoring settings**:
   ```yaml
   # User Monitoring Settings
   user_monitoring:
     enabled: true
     check_interval_minutes: 5  # How often to check for new members
   ```

5. **Save the file and restart the bot**

## Verifying User Monitoring

When you start the bot with a valid user token, you should see:

```
INFO - User monitoring initialized successfully
INFO - Bot is ready! Monitoring X servers
```

The bot will now monitor both:
- Servers where the bot is invited (real-time)
- Servers where you're a member (periodic checks)

## Troubleshooting

### "Failed to initialize user monitoring"
- **Check your token**: Make sure it's copied correctly without extra spaces
- **Token format**: Should be a long string of letters and numbers
- **Account status**: Make sure your Discord account is in good standing

### "User monitoring disabled - no user token provided"
- **Check config.yaml**: Make sure `user_token` field has your token
- **YAML formatting**: Ensure proper indentation and quotes around the token

### "Token verification failed"
- **Token expired**: Discord tokens can expire, get a new one
- **Invalid token**: Double-check you copied the complete token
- **Account locked**: Check if your Discord account has any restrictions

## Security Best Practices

1. **Use a dedicated Discord account** (optional but recommended)
2. **Enable 2FA** on your Discord account
3. **Regularly monitor** your account activity
4. **Keep your token private** - never commit it to version control
5. **Use environment variables** for production deployments

## Environment Variable Setup (Advanced)

For better security, you can use environment variables instead of storing the token in config.yaml:

1. **Set environment variable**:
   ```bash
   # Windows
   set DISCORD_USER_TOKEN=your_token_here
   
   # Linux/Mac
   export DISCORD_USER_TOKEN=your_token_here
   ```

2. **Update config.yaml**:
   ```yaml
   user_token: "${DISCORD_USER_TOKEN}"
   ```

## Legal and Ethical Considerations

- **Terms of Service**: Using user tokens may violate Discord's Terms of Service
- **Rate Limiting**: The bot implements proper rate limiting to avoid API abuse
- **Responsible Use**: Only monitor servers you're legitimately a member of
- **Privacy**: Be respectful of other users' privacy

## Support

If you encounter issues:
1. Check the bot logs for error messages
2. Verify your token is valid and properly formatted
3. Ensure your Discord account has access to the servers you want to monitor
4. Check that user monitoring is enabled in config.yaml

---

**Remember**: Your user token is like a password. Keep it secure and never share it with anyone!