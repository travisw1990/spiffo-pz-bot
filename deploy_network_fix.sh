#!/bin/bash

# Deployment script for network fix
# Run this on your Unraid server to update the bot with network_mode: host

echo "==========================================="
echo "Spiffo Bot - Network Fix Deployment"
echo "==========================================="
echo ""

# Navigate to app directory
cd /mnt/user/appdata/spiffo-bot || exit 1

echo "[Step 1] Stopping current container..."
docker-compose down

echo ""
echo "[Step 2] Backing up current docker-compose.yml..."
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)

echo ""
echo "[Step 3] Updating docker-compose.yml with network_mode: host..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  spiffo-bot:
    # Pull pre-built image from GitHub Container Registry
    image: ghcr.io/travisw1990/spiffo-pz-bot:latest
    container_name: spiffo-pz-bot
    restart: unless-stopped

    # Use host networking for full network access (fixes port connectivity issues)
    network_mode: host

    # Environment variables from .env file
    env_file:
      - .env

    # Persist data on Unraid array
    volumes:
      # Knowledge base (built on first run)
      - /mnt/user/appdata/spiffo-bot/knowledge_base:/app/knowledge_base
      # Player statistics
      - /mnt/user/appdata/spiffo-bot/player_stats.json:/app/player_stats.json
      # Bot logs
      - /mnt/user/appdata/spiffo-bot/logs:/app/logs

    # Logging configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

    # Health check (optional but recommended)
    healthcheck:
      test: ["CMD-SHELL", "pgrep -f python || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF

echo "✓ docker-compose.yml updated"

echo ""
echo "[Step 4] Starting container with new network configuration..."
docker-compose up -d

echo ""
echo "[Step 5] Waiting for container to start..."
sleep 5

echo ""
echo "[Step 6] Checking container status..."
docker-compose ps

echo ""
echo "[Step 7] Viewing recent logs (Ctrl+C to exit)..."
echo "==========================================="
docker-compose logs -f --tail=50
