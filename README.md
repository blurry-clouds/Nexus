# NEXUS (Current State + Go-Live Plan)

NEXUS is an autonomous Discord agent scaffold with Dockerized runtime services and a provider-routed AI client.

## Current architecture in code

Implemented now:

- Discord runtime (`main.py`) with cog wiring and slash sync
- Event router seed (`cogs/events.py`) + rolling last-10-message channel context cache
- Decision engine (`brain/decision_engine.py`) for AI task orchestration
- `/nexus ask` command path that invokes the decision engine and provider client
- AI provider routing (`brain/claude_client.py`):
  - `anthropic`
  - `puter_js`
  - `openai_compatible`
- Worker stack scaffolding (Celery/beat + Redis)
- Data layer placeholders for upcoming SQLAlchemy models and queries

## Services included

- `nexus-bot` (Discord runtime)
- `celery-worker` (background jobs)
- `celery-beat` (scheduled jobs)
- `postgres` (PostgreSQL 16)
- `redis` (cache + task broker)

## Quick start (local or VPS)

1. Copy env template:

   ```bash
   cp .env.example .env
   ```

2. Fill required values in `.env`:
   - `SERVER_NAME`
   - `DISCORD_TOKEN`
   - AI provider mode (choose one):
     - `AI_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`
     - `AI_PROVIDER=puter_js`
     - `AI_PROVIDER=openai_compatible` + `AI_BASE_URL` + `OPENAI_COMPATIBLE_API_KEY`
   - `TWITCH_CLIENT_ID`
   - `TWITCH_CLIENT_SECRET`

3. Build and start:

   ```bash
   docker compose up --build -d
   ```

4. Tail logs:

   ```bash
   docker compose logs -f nexus-bot
   ```

## Go-live readiness checklist (top-to-bottom comb)

### 1) Core runtime (now)
- [x] Bot process starts with structured JSON logging.
- [x] `/nexus ask` is wired to AI provider via decision engine.
- [x] Recent channel context (last 10 messages) is supplied to AI.

### 2) Must build next (before production autonomy)
- [ ] SQLAlchemy models + Alembic migrations for `users`, `mod_log`, `memory`, `autonomous_posts`, `server_events`.
- [ ] Query layer for user profile load/update, moderation logs, memory writes.
- [ ] Moderation pipeline: pre-screen -> Claude JSON decision -> confidence gate -> action executor.
- [ ] Staff override loop (`✅` approve / `❌` override) + strictness recalibration.
- [ ] Celery beat schedules for web awareness and autonomous behaviors.
- [ ] Scrapers (RSS + BeautifulSoup + Playwright) with dedupe hashes in Redis.

### 3) Hardening required
- [ ] Rate limiting + retry/backoff for AI and external APIs.
- [ ] Circuit breaker for provider failures (fallback strategy).
- [ ] Startup health checks for DB/Redis/AI provider.
- [ ] Secrets rotation plan and backup/restore drill.

### 4) VPS deployment finalization
- [ ] Install Docker + Compose plugin on Ubuntu 24.04.
- [ ] Create systemd unit to auto-start compose stack on reboot.
- [ ] Add daily PostgreSQL backup job to `/var/backups/nexus/`.
- [ ] Enforce firewall: only port 22 inbound.

## Provider strategy guidance

For moderation-critical enforcement (`warn/mute/kick/ban`), keep official Anthropic as primary.
Use Puter/openai-compatible as secondary if you need cost/availability flexibility.
Run laptop Ollama as auxiliary analysis only (not single source of moderation truth).

## Security notes

- Do **not** expose Postgres/Redis ports publicly.
- Keep only SSH (22) open.
- Store secrets in `.env` or secret manager.
