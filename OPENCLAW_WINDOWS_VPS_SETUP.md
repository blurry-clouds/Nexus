# OpenClaw + Codex/Claude Agent Swarm on Windows + VPS + Tailscale

This guide gives a **production-minded, step-by-step setup** for a solo founder running an orchestrated coding swarm from Windows, with a Linux VPS as always-on execution infrastructure and Tailscale as the private network.

---

## 0) Target Architecture (what you are building)

You will operate a **two-tier AI system**:

- **Control Plane (Windows machine)**
  - Obsidian vault (business context)
  - OpenClaw orchestrator ("Zoe")
  - Discord alerts (using your existing bot token)
  - Optional manual intervention via SSH/tmux

- **Execution Plane (Linux VPS)**
  - One worktree + tmux session per task
  - Codex and/or Claude Code agents running in isolated branches
  - GitHub PR automation and CI checks
  - Deterministic monitor script polling task state

- **Private Connectivity (Tailscale)**
  - Windows and VPS connected over WireGuard mesh
  - SSH and service access only over tailnet IPs
  - No public SSH exposure required

---

## 1) Prerequisites and Accounts

## 1.1 Hardware/OS
- Windows 11 (preferred), with WSL2 enabled.
- 1 Linux VPS (Ubuntu 22.04/24.04 LTS).
- Optional second VPS later for scaling (review/test split).

## 1.2 Required Accounts
- GitHub (repo + Actions enabled).
- Tailscale account.
- Discord bot token + target server/channel.
- OpenAI/Codex access.
- Anthropic Claude Code access.
- Optional Gemini code review access.

## 1.3 Required Tools
On **Windows**:
- Git for Windows
- VS Code (optional)
- Obsidian
- Tailscale client
- PowerShell 7+

On **VPS**:
- git, gh CLI, tmux, jq, Node.js + pnpm (or your stack equivalent), Docker (optional), Tailscale, cron.

---

## 2) Provision and Harden the VPS First

## 2.1 Create VPS
- Recommended starter size: 4 vCPU / 8 GB RAM / 120 GB SSD.
- Region near your users or CI provider.

## 2.2 Baseline hardening
Run as root once:

```bash
apt update && apt upgrade -y
apt install -y ufw fail2ban unattended-upgrades
adduser swarm
usermod -aG sudo swarm
```

Then configure:
- Disable password SSH login.
- Disable root SSH login.
- Enable unattended upgrades.

## 2.3 Install core runtime packages
As `swarm` user:

```bash
sudo apt install -y git gh tmux jq ripgrep build-essential curl ca-certificates
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g pnpm
```

(If your project is Python/Rust/Go, add those runtimes too.)

---

## 3) Build the Private Network with Tailscale

## 3.1 Install on VPS

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh --hostname openclaw-vps
```

## 3.2 Install on Windows
- Install Tailscale desktop app.
- Sign in to same tailnet.
- Approve both devices in Tailscale admin.

## 3.3 Lock down SSH to tailnet only
- In cloud firewall: close port 22 to public internet.
- Keep Tailscale SSH enabled.
- Verify from Windows:

```powershell
ssh swarm@openclaw-vps
```

(Or use tailnet IP directly.)

---

## 4) Repository + Branching + Worktree Strategy

## 4.1 Clone repo on VPS

```bash
mkdir -p ~/repos ~/worktrees ~/.clawdbot ~/logs
cd ~/repos
git clone git@github.com:YOURORG/YOURREPO.git app
cd app
pnpm install
```

## 4.2 Define branch conventions
Use deterministic names:
- Feature: `feat/<ticket-or-short-name>`
- Fix: `fix/<ticket-or-short-name>`
- Chore: `chore/<short-name>`

## 4.3 Worktree convention
Per task:
- Worktree path: `~/worktrees/<task-id>`
- tmux session: `agent-<task-id>`
- Registry entry: `~/.clawdbot/active-tasks.json`

---

## 5) Install and Configure Coding Agents on VPS

## 5.1 Secrets strategy
Store all tokens in `~/.config/swarm/.env` (chmod 600):
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GITHUB_TOKEN` (repo scope)
- `DISCORD_BOT_TOKEN`
- `DISCORD_CHANNEL_ID`

Never place secrets in prompts or committed files.

## 5.2 Wrapper scripts
Create wrappers so orchestrator calls one command shape.

`~/.codex-agent/run-agent.sh`:
- Accepts task id, model, effort, and prompt file.
- Exports env.
- Launches codex CLI with consistent flags.
- Writes full logs to `~/logs/<task-id>.log`.

`~/.claude-agent/run-agent.sh`:
- Similar pattern for Claude Code.

## 5.3 tmux launch pattern
Example launch:

```bash
tmux new-session -d -s "agent-feat-template" \
  -c "$HOME/worktrees/feat-template" \
  "$HOME/.codex-agent/run-agent.sh feat-template gpt-5.3-codex high /tmp/prompts/feat-template.md"
```

---

## 6) OpenClaw Orchestrator Design (Zoe)

Treat OpenClaw as a **state machine**, not a chat bot.

## 6.1 Input layers
1. Obsidian notes (meeting notes, requirements, constraints)
2. Product history (decisions, failures, architecture notes)
3. Operational context (open PRs, blocked tasks, CI failures)

## 6.2 Task lifecycle states
- `scoped`
- `spawned`
- `coding`
- `pr_open`
- `ci_running`
- `review_running`
- `ready_for_human`
- `merged` or `needs_retry`

## 6.3 JSON registry schema (`~/.clawdbot/active-tasks.json`)
Include at minimum:
- task id
- branch
- worktree
- tmux session
- agent type/model
- start timestamp
- retries
- PR URL
- CI state
- reviewer states
- final summary

---

## 7) Monitoring Loop (deterministic, token-efficient)

Create `~/.clawdbot/check-agents.sh` and run every 10 min by cron.

Checks to perform:
1. tmux session exists?
2. branch pushed?
3. PR exists for branch?
4. CI status via `gh pr checks`.
5. Review gates passed (Codex/Claude/Gemini labels or checks).
6. Retry rules (max 3) for recoverable failures.
7. Discord alert only on action-required events.

Cron entry example:

```bash
*/10 * * * * /home/swarm/.clawdbot/check-agents.sh >> /home/swarm/logs/check-agents-cron.log 2>&1
```

---

## 8) GitHub PR and Definition of Done (DoD)

A task is complete only if all are true:
1. PR created.
2. Branch up-to-date with `main`.
3. CI green (lint, types, unit, integration/e2e).
4. AI review gates passed.
5. Screenshot attached for UI-impacting changes.
6. Release notes/changelog entry prepared (if your process requires it).

Implement these as required GitHub status checks so this is machine-enforced.

---

## 9) Discord Notification Pipeline (use your existing bot token)

## 9.1 Bot setup (one-time)
1. Go to [Discord Developer Portal](https://discord.com/developers/applications).
2. Open your existing bot application.
3. In **Bot** section, copy/reset your token if needed.
4. In **Privileged Gateway Intents**, enable only what you need (none required for pure outbound webhook-style messaging).
5. Invite bot to your server with minimum permissions:
   - View Channels
   - Send Messages
   - Embed Links (optional for rich formatting)
6. In Discord, enable Developer Mode and copy:
   - Server ID (optional)
   - Channel ID (required for notifications)

Save in `.env`:

```bash
DISCORD_BOT_TOKEN=...
DISCORD_CHANNEL_ID=123456789012345678
```

## 9.2 Minimal notifier script on VPS
Create `~/.clawdbot/notify-discord.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

source ~/.config/swarm/.env
MSG="${1:-Swarm update}"

curl -sS -X POST "https://discord.com/api/v10/channels/${DISCORD_CHANNEL_ID}/messages" \
  -H "Authorization: Bot ${DISCORD_BOT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg content "$MSG" '{content: $content}')" >/dev/null
```

Then:

```bash
chmod +x ~/.clawdbot/notify-discord.sh
~/.clawdbot/notify-discord.sh "✅ OpenClaw notifier test from VPS"
```

## 9.3 Notification events
Send concise structured messages:
- task started
- PR opened
- CI failed (with failing job)
- review failed (critical-only summary)
- PR ready to merge
- retry exhausted

Keep alert text action-oriented and include links:
- PR URL
- workflow run URL
- tmux/log reference

## 9.4 Suggested message format
Keep each Discord message short and machine-parseable:

```text
[swarm][ready_for_human] task=feat-template pr=#341
repo=yourorg/yourrepo branch=feat/template
ci=pass codex=pass claude=pass gemini=pass
https://github.com/yourorg/yourrepo/pull/341
```

## 9.5 Hook monitor script to Discord
In `~/.clawdbot/check-agents.sh`, replace/append notification calls like:

```bash
~/.clawdbot/notify-discord.sh "❌ CI failed for feat-template: lint"
~/.clawdbot/notify-discord.sh "✅ PR #341 ready for human review"
```

---

## 10) Windows Operator Workflow (daily routine)

1. Capture business inputs in Obsidian.
2. Ask Zoe to scope one or multiple tasks.
3. Zoe spawns agents on VPS (parallel).
4. Let monitor loop run unattended.
5. Watch Discord channel only when pinged for readiness/failure.
6. Perform final human review + merge.
7. Zoe writes outcome notes back to Obsidian memory.

This keeps your role at product/strategy level while code execution is automated.

---

## 11) Security and Access Segmentation (critical)

- Orchestrator has broader business context.
- Coding agents get least privilege:
  - repo write
  - no production DB write
  - no billing/admin secrets
- Production DB access should be read-only and only for orchestrator tools that require it.
- Separate API keys per component (orchestrator, codex worker, claude worker, reviewer).
- Rotate all keys monthly.

---

## 12) Reliability Patterns You Should Add Early

- Idempotent task spawn (don’t create duplicate worktrees for same task id).
- Dead-letter queue for permanently failed tasks.
- Retry backoff (e.g., 5m, 20m, 60m).
- Automatic stale rebase + rerun CI when conflict occurs.
- Log retention and compression.
- Daily health report sent to Discord at fixed hour.

---

## 13) Suggested 14-Day Rollout Plan

## Days 1–2: Foundation
- VPS provisioning, hardening, Tailscale, SSH.
- Repo clone, runtime install, GitHub CLI auth.

## Days 3–4: Agent execution
- Codex and Claude wrappers.
- tmux launch + per-task logs.
- Manual one-task dry run.

## Days 5–6: Registry + monitor
- Build JSON task store.
- Implement `check-agents.sh`.
- Add cron and Discord alerts.

## Days 7–8: PR automation and gates
- Auto PR creation.
- CI required checks.
- AI reviewer integration.

## Days 9–10: Context memory integration
- Obsidian ingestion pipeline.
- Prompt composer for task-specific context.

## Days 11–12: Failure handling
- Retry policy.
- Auto-respawn behavior.
- Dead-letter handling.

## Days 13–14: Production hardening
- Security audit.
- Key rotation process.
- Runbook and incident drills.

---

## 14) Practical Starter Command Templates

Create worktree:

```bash
git -C ~/repos/app fetch origin
git -C ~/repos/app worktree add ~/worktrees/feat-x -b feat/x origin/main
```

Spawn codex agent in tmux:

```bash
tmux new-session -d -s "agent-feat-x" \
  -c "$HOME/worktrees/feat-x" \
  "$HOME/.codex-agent/run-agent.sh feat-x gpt-5.3-codex high /tmp/prompts/feat-x.md"
```

Check PR CI:

```bash
gh pr checks <pr-number> --watch
```

Tail logs:

```bash
tmux capture-pane -pt agent-feat-x | tail -n 100
tail -f ~/logs/feat-x.log
```

---

## 15) Anti-Patterns to Avoid

- Giving coding agents unrestricted production credentials.
- Treating PR opened as "done".
- Polling LLMs directly for status instead of deterministic system checks.
- Running all tasks in one branch/session.
- Skipping screenshots for UI changes.
- No retry cap (can infinite-loop cost).

---

## 16) Minimum Viable Version (if you start this week)

If you want fast launch with minimal moving parts:
1. Tailscale + VPS + tmux.
2. Codex-only first (add Claude later).
3. One JSON registry + one monitor script.
4. GitHub Actions + required checks.
5. Discord “PR ready” + “CI failed” alerts.

Then add multi-agent orchestration and richer memory once stable.

---

## 17) Success Metrics to Track Weekly

- Tasks created vs merged.
- Median time: request → PR, PR → merge.
- CI pass rate on first attempt.
- Auto-retry resolution rate.
- Manual intervention rate.
- Token/tooling cost per merged PR.
- Production incidents linked to swarm changes.

These metrics tell you whether speed is actually improving delivery quality.
