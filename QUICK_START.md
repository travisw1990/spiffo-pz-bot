# Quick Start Guide

## What You Have

A fully functional AI-powered Discord bot for managing your Project Zomboid server! 🎮🤖

## What It Can Do

✅ **Natural Language Commands**
- "Is the server online?"
- "Show me the last 100 log lines"
- "Search logs for errors"
- "Who's been playing today?"
- "Show me recent chat messages"
- "What mods are installed?"
- "Change max players to 16"

✅ **Smart Features**
- AI understands context and intent
- Searches and analyzes logs
- Monitors player activity
- Manages server configuration
- Lists mods and backups

## Setup Steps

### 1. Get Your Discord Server ID (Optional)

If you want to limit the bot to specific servers:

1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click your server → Copy ID
3. Add to `.env`: `DISCORD_GUILD_ID=your_server_id`

### 2. Invite Bot to Discord

The bot needs to be invited to your Discord server. Run this once to get the invite link:

```python
# Get your bot's client ID from: https://discord.com/developers/applications
# Then use this URL (replace YOUR_CLIENT_ID):
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2048&scope=bot
```

**Permissions needed:** Send Messages, Read Messages

### 3. Start the Bot

```bash
# Activate virtual environment (if not already)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the bot
python main.py
```

You should see:
```
Starting Project Zomboid Discord Bot...
FTP Host: 172.240.71.175:21
FTP User: zpTRCxlfpTqX
--------------------------------------------------
Bot logged in as YourBotName
Bot is in 1 guilds
```

## How to Use

### Mention the Bot

In Discord, @ mention your bot and ask it anything:

```
@YourBot is the server online?
@YourBot show me recent errors
@YourBot who played yesterday?
```

### DM the Bot

You can also DM the bot directly (no @mention needed):

```
show me chat logs
what mods are installed?
```

## Example Conversations

```
You: @PZBot is the server up?
Bot: Yes! Server online (last activity: 2 minutes ago)

You: @PZBot show me the last 50 log lines
Bot: [Bot displays last 50 lines from server console]

You: @PZBot search for "error"
Bot: Found 3 matches:
- LOG: ERROR in module X
- LOG: ERROR: Connection timeout
- ...

You: @PZBot who's been playing?
Bot: Recent player activity:
- Player "Travis" connected at 14:23
- Player "Sarah" disconnected at 15:45
```

## Important Limitations

🚫 **What the bot CANNOT do:**
- Restart the server (use IB's bot: `/restart`)
- Kick/ban players in real-time
- Send in-game announcements
- Execute RCON commands

💡 **Why?** The RCON port isn't exposed externally by Indifferent Broccoli. The bot uses FTP access instead, which still gives you tons of functionality!

## Troubleshooting

### Bot doesn't respond
- Make sure you @mentioned the bot
- Check the bot is online in Discord
- Check the console for errors

### "Could not read logs" error
- FTP credentials might be wrong
- Server might be down
- Check `.env` file has correct FTP info

### Bot keeps disconnecting
- Check your internet connection
- Verify Discord token is correct
- Check for errors in console

## Configuration

Edit `.env` file to change settings:

```bash
# Discord
DISCORD_BOT_TOKEN=your_token_here

# Server Paths (already configured)
PZ_LOGS_PATH=/server-data/Logs
PZ_CONFIG_PATH=/server-data/Server
```

## Next Steps

1. **Test it!** Try asking the bot various questions
2. **Customize**: Add more features in `ai/claude_agent.py`
3. **Share with team**: Invite coworkers to your Discord server
4. **Set permissions**: Use Discord roles to limit who can use certain commands

## Need Help?

Check `CLAUDE.md` for full documentation and architecture details.

---

**Have fun managing your Project Zomboid server! 🧟‍♂️**
