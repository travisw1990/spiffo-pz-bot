# Spiffo - Project Zomboid Discord Bot 🧟

AI-powered Discord bot for managing Project Zomboid multiplayer servers using natural language commands.

![Status](https://img.shields.io/badge/status-production%20ready-green)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

### 🤖 Natural Language Interface
- Mention `@Spiffo` in Discord or DM directly
- Powered by Claude AI (Anthropic)
- Conversational understanding of commands

### 🎮 Server Management
- Check server online/offline status
- View and search server logs
- Monitor player connections and activity
- Get server configuration details

### ⚙️ Configuration Management
- Read and update server settings (pzserver.ini)
- Manage sandbox gameplay settings (SandboxVars.lua)
- Configure max players, PVP, passwords, and more

### 🔧 Mod Management
- List installed mods
- Add mods by Steam Workshop ID
- Remove mods from server
- View available backups

### 📚 Knowledge Base
- Curated Project Zomboid wiki knowledge (20+ articles)
- Semantic search using ChromaDB vector database
- Answer gameplay questions about mechanics, strategies, tips
- Live wiki fallback for comprehensive coverage

### 📊 Player Statistics & Analytics
- **Lifetime vs Per-Life Tracking** - Separate current life and all-time stats
- **Survival Streak System** - Complete history of each player's lives
- **10 Leaderboard Categories:**
  - Zombies killed, Distance traveled, Buildings placed, Items crafted
  - Total playtime, Longest life (survival record)
  - Current life duration (who's alive longest right now)
  - Kill/death ratio, Most deaths (hall of shame)
- Automatic stat tracking from server logs
- Playstyle profiling (Combat Fighter, Explorer, Builder, etc.)

## Tech Stack

- **Language:** Python 3.10+
- **AI:** Claude API (Anthropic)
- **Discord:** discord.py
- **Vector Database:** ChromaDB + sentence-transformers
- **Server Access:** FTP (RCON optional)

## Quick Start

### Prerequisites
- Python 3.10 or higher
- Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- Anthropic API key ([Anthropic Console](https://console.anthropic.com/))
- Project Zomboid server with FTP access

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/travisw1990/spiffo-pz-bot.git
cd spiffo-pz-bot
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Build knowledge base** (one-time setup)
```bash
python build_curated_knowledge.py
```

6. **Run the bot**
```bash
python main.py
```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Update and restart
docker-compose pull && docker-compose up -d
```

### Manual Docker Build

```bash
docker build -t spiffo-bot .
docker run -d --env-file .env --name spiffo-bot spiffo-bot
```

## Usage Examples

### Basic Commands
```
@Spiffo is the server online?
@Spiffo show me the last 100 log lines
@Spiffo search logs for "error"
@Spiffo who's been playing today?
@Spiffo what mods are installed?
```

### Configuration Changes
```
@Spiffo change max players to 16
@Spiffo set the welcome message to [text]
@Spiffo disable MultiHitZombies
@Spiffo set zombie speed to 3
```

### Mod Management
```
@Spiffo add workshop mod 2169435993
@Spiffo remove mod 2169435993
@Spiffo list all mods
```

### Gameplay Knowledge
```
@Spiffo what's the best strategy for early game survival?
@Spiffo how do zombie migrations work?
@Spiffo explain the different zombie speed settings
@Spiffo how does farming work?
```

### Player Statistics
```
@Spiffo show me PlayerName's stats
@Spiffo who has killed the most zombies?
@Spiffo show me the distance traveled leaderboard
@Spiffo who's been alive the longest right now?
@Spiffo show me the kill/death ratio leaderboard
```

## Configuration

See `.env.example` for all available configuration options.

**Required:**
- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `FTP_HOST`, `FTP_USER`, `FTP_PASSWORD` - Server FTP credentials

**Optional:**
- `RCON_HOST`, `RCON_PORT`, `RCON_PASSWORD` - RCON access (if available)
- Server path overrides (defaults work for Indifferent Broccoli hosting)

## Project Structure

```
spiffo-pz-bot/
├── ai/                      # Claude AI integration
│   └── claude_agent.py
├── analytics/               # Player statistics
│   ├── player_stats.py
│   └── log_parser.py
├── bot/                     # Discord bot
│   └── discord_client.py
├── knowledge/               # Knowledge base system
│   ├── rag_manager.py
│   ├── wiki_scraper.py
│   └── curated_knowledge.json
├── server/                  # Server management
│   ├── ftp_client.py
│   └── controller.py
├── utils/                   # Utilities
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── Dockerfile              # Docker build
└── docker-compose.yml      # Docker Compose config
```

## Limitations

- **RCON Access:** Some hosting providers (like Indifferent Broccoli) don't expose RCON ports externally
  - Server restart must be done via hosting provider's tools
  - Real-time in-game commands not available without RCON
- **FTP Only:** All management done through FTP file access
- **Log Parsing:** Player stats based on what's logged by the game (some events may not be captured)

## Contributing

Contributions welcome! Feel free to:
- Report bugs via GitHub Issues
- Suggest features via GitHub Issues
- Submit pull requests

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with [Claude AI](https://www.anthropic.com/claude) by Anthropic
- Project Zomboid by The Indie Stone
- Community wiki: [pzwiki.net](https://pzwiki.net/)

## Support

For issues or questions:
- Open a GitHub Issue
- Check the [Project Zomboid Wiki](https://pzwiki.net/)
- Review the documentation in the repo

---

**Note:** This bot requires server access via FTP. Ensure you have proper permissions before deploying.
