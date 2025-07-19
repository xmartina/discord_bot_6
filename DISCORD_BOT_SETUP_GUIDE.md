# Discord Bot Setup Guide

## Step 1: Create a Discord Application

1. Go to the Discord Developer Portal: https://discord.com/developers/applications
2. Click "New Application" button (top right)
3. Enter a name for your application (e.g., "Server Monitor Bot")
4. Click "Create"

## Step 2: Create a Bot

1. In your application dashboard, click on "Bot" in the left sidebar
2. Click "Add Bot" button
3. Click "Yes, do it!" to confirm
4. Your bot is now created!

## Step 3: Get Your Bot Token

1. In the Bot section, you'll see a "Token" section
2. Click "Copy" to copy your bot token
3. **IMPORTANT**: Keep this token secret! Never share it publicly

## Step 4: Configure Bot Permissions

1. Still in the Bot section, scroll down to "Privileged Gateway Intents"
2. Enable the following intents:
   - ✅ **SERVER MEMBERS INTENT** (Required for member join events)
   - ✅ **MESSAGE CONTENT INTENT** (Optional, for message monitoring)
   - ✅ **PRESENCE INTENT** (Optional, for user status tracking)

## Step 5: Generate Invite Link

1. Go to "OAuth2" → "URL Generator" in the left sidebar
2. Under "Scopes", select:
   - ✅ `bot`
3. Under "Bot Permissions", select:
   - ✅ `View Channels`
   - ✅ `Read Message History`
   - ✅ `Send Messages` (for notifications)
   - ✅ `Use Slash Commands` (optional)
4. Copy the generated URL at the bottom

## Step 6: Add Bot to Your Servers

1. Open the generated URL in your browser
2. Select the server you want to add the bot to
3. Click "Authorize"
4. Complete the captcha if prompted

**Note**: You'll need to repeat this for each server you want to monitor, or ask server admins to add your bot.

## Important Security Notes

- Never share your bot token publicly
- Store it securely (we'll create a secure config file)
- If your token is compromised, regenerate it immediately in the Developer Portal

## Next Steps

Once you have your bot token:
1. Copy the token
2. Add the bot to all servers you want to monitor
3. Provide me with the token so I can configure the monitoring bot

---

**Ready to proceed?** Once you've completed these steps and have your bot token, let me know and I'll continue with the setup!


Server Details
Application ID
1392085717122813952

Public Key
1e3ffd1979a6eb7a7ed4d0aaecd1957484275a87e9cf99548e263695e72eb5ad

Bot Token
MTM5MjA4NTcxNzEyMjgxMzk1Mg.GrC4O9.jarzVZBAkWJSKKTsuBOmVZ1z9_wC1it3eGa_No

bot OAuth2 generated link
https://discord.com/oauth2/authorize?client_id=1392085717122813952&permissions=2147552256&integration_type=0&scope=bot

server to work with
server ID
1389524220156837958

my user Id
1371624094860312608