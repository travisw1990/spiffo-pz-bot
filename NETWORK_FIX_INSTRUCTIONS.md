# Network Fix Instructions

**Issue:** Bot can't detect server status correctly when running in Docker on Unraid

**Root Cause:** Docker container using default bridge networking can't properly connect to external game port

**Solution:** Use `network_mode: host` to give container full network access (same as running locally)

---

## Quick Fix (Recommended)

### Option 1: Automated Script

1. **Copy the deployment script to Unraid:**
   - Via SMB: Copy `deploy_network_fix.sh` to `\\192.168.1.24\appdata\spiffo-bot\`
   - Or via SSH: `scp deploy_network_fix.sh root@192.168.1.24:/mnt/user/appdata/spiffo-bot/`

2. **SSH into Unraid:**
   ```bash
   ssh root@192.168.1.24
   ```

3. **Run the deployment script:**
   ```bash
   cd /mnt/user/appdata/spiffo-bot
   chmod +x deploy_network_fix.sh
   ./deploy_network_fix.sh
   ```

   The script will:
   - Stop the current container
   - Backup your existing docker-compose.yml
   - Update with `network_mode: host`
   - Restart the container
   - Show logs

4. **Test in Discord:**
   ```
   @Spiffo is the server online?
   ```

---

### Option 2: Manual Update

1. **SSH into Unraid:**
   ```bash
   ssh root@192.168.1.24
   cd /mnt/user/appdata/spiffo-bot
   ```

2. **Stop the container:**
   ```bash
   docker-compose down
   ```

3. **Edit docker-compose.yml:**
   ```bash
   nano docker-compose.yml
   ```

4. **Add `network_mode: host` after `restart: unless-stopped`:**
   ```yaml
   services:
     spiffo-bot:
       image: ghcr.io/travisw1990/spiffo-pz-bot:latest
       container_name: spiffo-pz-bot
       restart: unless-stopped

       # Add this line:
       network_mode: host

       env_file:
         - .env
   ```

5. **Save and exit:**
   - Press `Ctrl+X`
   - Press `Y`
   - Press `Enter`

6. **Start the container:**
   ```bash
   docker-compose up -d
   ```

7. **Check logs:**
   ```bash
   docker-compose logs -f
   ```

---

## Testing the Fix

### Test 1: From Inside Container

```bash
# On Unraid
docker exec spiffo-pz-bot python /app/test_docker_network.py
```

This will test:
- Game port connectivity (should be OPEN now)
- FTP port connectivity
- DNS resolution
- Container network info

### Test 2: In Discord

Ask Spiffo:
```
@Spiffo is the server online?
```

**Expected response:**
```
Server online (game port accessible, last log update: X minutes ago)
```

---

## What Changed

### Before (Bridge Network - Default)
- Container has isolated network stack
- Can reach some services but not others
- Port connectivity checks may fail even when server is online
- Works for FTP but not always for game port checks

### After (Host Network)
- Container uses Unraid's network stack directly
- Full network access, same as running bot locally
- All port checks work correctly
- Same behavior as before Docker deployment

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs
```

**Common issues:**
- Port conflict (another container using host networking)
- Invalid docker-compose.yml syntax

### Still Showing Offline

1. **Verify network mode:**
   ```bash
   docker inspect spiffo-pz-bot | grep NetworkMode
   ```
   Should show: `"NetworkMode": "host"`

2. **Test from container:**
   ```bash
   docker exec spiffo-pz-bot python -c "
   import socket
   sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   sock.settimeout(3)
   result = sock.connect_ex(('172.240.71.175', 27325))
   sock.close()
   print('Game port:', 'OPEN' if result == 0 else 'CLOSED')
   "
   ```

3. **Check if PZ server is actually running:**
   - Log into Indifferent Broccoli control panel
   - Verify server status
   - Try connecting with PZ game client

### Need to Rollback

If something goes wrong:
```bash
cd /mnt/user/appdata/spiffo-bot
docker-compose down
cp docker-compose.yml.backup.* docker-compose.yml
docker-compose up -d
```

---

## Why This Fix Works

**Docker Networking Modes:**

1. **Bridge (default):** Creates virtual network for container
   - Pros: Isolation, security
   - Cons: May have connectivity issues with external services

2. **Host:** Container uses host's network directly
   - Pros: Full network access, no translation needed
   - Cons: Less isolation (acceptable for trusted bot)

**For Spiffo:**
- Needs to connect to external PZ server (172.240.71.175:27325)
- Needs reliable port connectivity checks
- Host mode gives same network access as running locally
- This is why it worked before Docker but not after

---

## Security Considerations

**Is `network_mode: host` safe?**

✅ **Yes, for this use case:**
- Bot is not a public-facing service
- Only connects outbound to Discord, Claude API, and PZ server
- No incoming connections required
- Running on private Unraid server (not exposed to internet)
- Same security posture as running bot directly on Unraid

**Alternative (if concerned):**
- Use custom Docker network with proper routing
- Configure iptables rules for specific port access
- Use VPN/proxy for external connections

For home lab use, `network_mode: host` is the simplest and most reliable solution.

---

## Files Modified

- `docker-compose.unraid.yml` - Added `network_mode: host`
- `docker-compose.yml` - Added `network_mode: host`
- Created deployment script: `deploy_network_fix.sh`
- Created test script: `test_docker_network.py`

---

**Date:** 2025-11-08
**Issue:** Server status detection failing in Docker
**Solution:** Use host networking mode
**Status:** Ready to deploy
