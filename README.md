# NEXUS (Step 3: Moderation Pipeline + DB + Go-Live)

NEXUS is an autonomous Discord governance agent scaffold. This repo now includes:

- Dockerized runtime stack
- provider-routed Claude client
- working `/nexus ask` decision path
- PostgreSQL data models and async query layer
- baseline autonomous moderation flow

## Implemented architecture status

### Runtime flow (implemented)

`Discord Event -> Event Router -> Decision Engine -> Claude Client -> Discord Response/Action`

- Event router captures rolling message context (last 10 per channel)
- Decision engine builds structured ask/moderation prompts
- Claude provider route executes and returns answer/decision

### Database layer (implemented)

- SQLAlchemy models for:
  - `users`
  - `mod_log`
  - `memory`
  - `autonomous_posts`
  - `server_events`
- Async engine/session
- Basic query helpers:
  - get/create user
  - user memory upsert/load
  - moderation log insert
- App startup table initialization (`create_all`)
- SQL bootstrap file: `database/migrations/001_init.sql`

### Moderation layer (implemented baseline)

- Reads all messages in accessible guild channels
- Local suspicious pre-screen with `better-profanity` + custom flagged words
- For flagged messages: sends full moderation context to Claude
- Requires structured decision JSON:
  - `action`: `warn|mute|kick|ban|ignore`
  - `confidence`: `0-100`
  - `reason`
  - `duration_minutes`
- Confidence gate:
  - `< MOD_CONFIDENCE_THRESHOLD`: escalates to staff log channel
  - `>= threshold`: executes action and logs to DB
- Posts staff embed for each escalation/action with `✅` / `❌` reaction controls

## Quick start

1. Copy env template:

```bash
cp .env.example .env
```

2. Fill required values:
- `SERVER_NAME`
- `DISCORD_TOKEN`
- AI provider config (`AI_PROVIDER` + matching keys)
- `STAFF_LOG_CHANNEL_ID`
- `MUTE_ROLE_ID`
- `MOD_CONFIDENCE_THRESHOLD`
- `SERVER_RULES_TEXT`
- `CUSTOM_FLAGGED_WORDS` (JSON array)
- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`

3. Start stack:

```bash
docker compose up --build -d
```

4. Verify bot logs:

```bash
docker compose logs -f nexus-bot
```

---

## CRITICAL Security note (token safety)

If your Discord token has ever been pasted into chat or exposed publicly, rotate it immediately:

1. Discord Developer Portal -> Bot -> **Reset Token**
2. Replace `DISCORD_TOKEN` in `.env`
3. Restart stack:

```bash
docker compose up -d --force-recreate nexus-bot
```

---

## Fresh Ubuntu 24.04 VPS bring-up (your case)

### 1) Base packages + Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg ufw
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

Logout/login once after group change.

### 2) Firewall (SSH only inbound)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw --force enable
sudo ufw status
```

### 3) Deploy app

```bash
cd /opt
sudo git clone https://github.com/blurry-clouds/Nexus.git nexus
sudo chown -R $USER:$USER /opt/nexus
cd /opt/nexus
cp .env.example .env
nano .env
docker compose up --build -d
docker compose ps
```

### 4) Auto-start on reboot (systemd)

Create `/etc/systemd/system/nexus-compose.service`:

```ini
[Unit]
Description=NEXUS Docker Compose Stack
After=network-online.target docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/nexus
RemainAfterExit=yes
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nexus-compose
sudo systemctl start nexus-compose
sudo systemctl status nexus-compose
```

### 5) Daily Postgres backup

```bash
sudo mkdir -p /var/backups/nexus
sudo chown -R $USER:$USER /var/backups/nexus
crontab -e
```

Add:

```cron
15 3 * * * cd /opt/nexus && /usr/bin/docker compose exec -T postgres pg_dump -U nexus nexus | gzip > /var/backups/nexus/nexus_$(date +\%F).sql.gz
```

---

## Immediate next build steps

1. Implement staff override learning from reactions (persist `mod_override=true`, strictness calibration)
2. Add Redis-based rate limits + anti-spam guardrails
3. Add Celery beat schedule map for patch/news/esports/twitch
4. Implement scraper modules + relevance gating + dedupe hashes
5. Implement autonomous daily/weekly posts + quiet-server triggers
6. Complete slash commands: `/nexus patch`, `/nexus stats`, `/nexus schedule`, `/nexus playing`, `/nexus remember`


## PR conflict help

If GitHub reports merge conflicts for your PR, follow `docs/PR_CONFLICTS.md` for a step-by-step rebase and resolution workflow.
