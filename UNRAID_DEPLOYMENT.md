# Spiffo Bot - Unraid Deployment Guide

Complete guide for deploying Spiffo to your Unraid server (SEVRO).

---

## Prerequisites

- Unraid server running (SEVRO at 192.168.1.24)
- SSH access to Unraid
- Docker and Docker Compose installed on Unraid
- Your `.env` file with credentials

---

## Deployment Steps

### Step 1: Create Application Directory

SSH into your Unraid server and create the app directory:

```bash
mkdir -p /mnt/user/appdata/spiffo-bot/logs
cd /mnt/user/appdata/spiffo-bot
```

### Step 2: Transfer Files to Unraid

You have **three options** to get your files onto Unraid:

#### Option A: SMB Share (Easiest - Windows)

1. Open File Explorer on Windows
2. Navigate to: `\\192.168.1.24\appdata\spiffo-bot\`
3. Copy these files from your local project:
   - `.env` (your credentials file)
   - `docker-compose.unraid.yml` (rename to `docker-compose.yml`)

#### Option B: Direct Creation via SSH

**Create the .env file:**
```bash
cd /mnt/user/appdata/spiffo-bot
nano .env
```

Paste your environment variables, then press `Ctrl+X`, `Y`, `Enter` to save.

**Create docker-compose.yml:**
```bash
nano docker-compose.yml
```

Copy the contents from `docker-compose.unraid.yml` in your project, then save.

#### Option C: SCP/SFTP (Advanced)

```bash
# From your local machine
scp .env root@192.168.1.24:/mnt/user/appdata/spiffo-bot/
scp docker-compose.unraid.yml root@192.168.1.24:/mnt/user/appdata/spiffo-bot/docker-compose.yml
```

### Step 3: Authenticate with GitHub Container Registry

On Unraid, log in to GitHub Container Registry (one-time setup):

```bash
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u travisw1990 --password-stdin
```

**Note:** Replace `YOUR_GITHUB_TOKEN` with your actual token (starts with `ghp_`)

You should see: `Login Succeeded`

### Step 4: Create Placeholder Files

Create empty files that Docker will mount:

```bash
cd /mnt/user/appdata/spiffo-bot
touch player_stats.json
echo "{}" > player_stats.json
mkdir -p knowledge_base
```

### Step 5: Pull and Start the Container

```bash
cd /mnt/user/appdata/spiffo-bot
docker-compose pull
docker-compose up -d
```

**Expected output:**
```
Pulling spiffo-bot ... done
Creating spiffo-pz-bot ... done
```

### Step 6: Verify It's Running

Check container status:
```bash
docker-compose ps
```

You should see:
```
NAME            STATUS          PORTS
spiffo-pz-bot   Up 10 seconds
```

### Step 7: View Logs

Watch the bot start up:
```bash
docker-compose logs -f
```

**Look for:**
- "Initializing knowledge base..."
- "Knowledge base loaded: X chunks from ~Y pages"
- "Starting Project Zomboid Discord Bot..."
- "Logged in as Spiffo#XXXX"

Press `Ctrl+C` to exit logs (bot keeps running).

### Step 8: Test in Discord

Go to your Discord server and test:
```
@Spiffo are you online?
```

---

## Managing the Bot

### View Logs
```bash
cd /mnt/user/appdata/spiffo-bot
docker-compose logs -f
```

### Restart Bot
```bash
cd /mnt/user/appdata/spiffo-bot
docker-compose restart
```

### Stop Bot
```bash
cd /mnt/user/appdata/spiffo-bot
docker-compose down
```

### Start Bot
```bash
cd /mnt/user/appdata/spiffo-bot
docker-compose up -d
```

### Update to Latest Version

When you push new code to GitHub:

```bash
cd /mnt/user/appdata/spiffo-bot
docker-compose pull      # Pull latest image
docker-compose up -d     # Restart with new version
```

Or use the update script (see below).

---

## Automated Updates

### Create Update Script

Create a simple update script for convenience:

```bash
nano /mnt/user/appdata/spiffo-bot/update.sh
```

Paste this:
```bash
#!/bin/bash
cd /mnt/user/appdata/spiffo-bot
echo "Pulling latest Spiffo bot image..."
docker-compose pull
echo "Restarting bot with new version..."
docker-compose up -d
echo "Update complete! Viewing logs..."
docker-compose logs --tail=50
```

Make it executable:
```bash
chmod +x /mnt/user/appdata/spiffo-bot/update.sh
```

**To update in the future:**
```bash
/mnt/user/appdata/spiffo-bot/update.sh
```

---

## Troubleshooting

### Bot Not Starting

**Check logs:**
```bash
docker-compose logs
```

**Common issues:**
- Missing environment variables in `.env`
- Invalid Discord token
- Invalid Anthropic API key
- FTP credentials incorrect

### Container Keeps Restarting

```bash
docker-compose logs --tail=100
```

Look for error messages about missing credentials or connection failures.

### Knowledge Base Not Loading

The knowledge base builds on first run. If empty:

```bash
# SSH into the container
docker exec -it spiffo-pz-bot /bin/bash

# Manually build knowledge base
cd /app
python build_curated_knowledge.py

# Exit container
exit
```

Then restart:
```bash
docker-compose restart
```

### Update Not Working

If `docker-compose pull` doesn't get the latest:

```bash
# Force remove old image
docker image rm ghcr.io/travisw1990/spiffo-pz-bot:latest

# Pull fresh
docker-compose pull
docker-compose up -d
```

### Check Container Resource Usage

```bash
docker stats spiffo-pz-bot
```

Shows CPU, memory, and network usage.

---

## File Locations on Unraid

```
/mnt/user/appdata/spiffo-bot/
├── .env                    # Your credentials (never commit!)
├── docker-compose.yml      # Container configuration
├── player_stats.json       # Player statistics (auto-generated)
├── knowledge_base/         # Vector database (auto-generated)
├── logs/                   # Bot logs
└── update.sh              # Update script
```

---

## Auto-Start on Unraid Boot

Docker Compose containers with `restart: unless-stopped` will automatically start when Unraid boots.

To verify:
```bash
docker inspect spiffo-pz-bot | grep RestartPolicy -A 3
```

Should show:
```json
"RestartPolicy": {
    "Name": "unless-stopped"
}
```

---

## Security Notes

- ✅ `.env` file stays on Unraid only (not in GitHub)
- ✅ Keep your GitHub token secure
- ✅ FTP/Discord/Anthropic credentials never leave Unraid
- ✅ Docker logs rotate automatically (max 10MB, 3 files)

---

## Monitoring

### Discord Notifications (Future Enhancement)

Consider adding a monitoring service that pings Discord if the bot goes down:
- Uptime Kuma (runs on Unraid)
- Healthchecks.io (cloud service)

### Unraid Dashboard

The container will show up in the Unraid Docker tab. You can:
- See if it's running
- View basic stats
- Stop/start/restart via UI

---

## Need Help?

**Check GitHub Issues:**
https://github.com/travisw1990/spiffo-pz-bot/issues

**Common commands reference:**
```bash
# View logs
docker-compose logs -f

# Restart bot
docker-compose restart

# Update bot
docker-compose pull && docker-compose up -d

# Check status
docker-compose ps

# Stop bot
docker-compose down
```

---

**Deployment Date:** 2025-11-07
**Server:** SEVRO (192.168.1.24)
**Container Name:** spiffo-pz-bot
**Image:** ghcr.io/travisw1990/spiffo-pz-bot:latest
