# Repo Recovery Status (recovery/full-sync)

This branch was created to provide a single branch containing all local implementation work that may be missing from GitHub due to PR conflicts.

## Live GitHub verification

Attempted to verify live remote state with:

- `git ls-remote --heads origin`

In this execution environment, GitHub access failed with:

- `CONNECT tunnel failed, response 403`

So this branch is prepared from the complete local history available here.

## Included implementation scope

- Provider-routed Claude client (`anthropic`, `puter_js`, `openai_compatible`)
- Ask path with decision engine and channel context cache
- Async PostgreSQL models/session/query layer + init + SQL bootstrap
- Baseline autonomous moderation pipeline with confidence gating and mod-log persistence
- PR conflict-resolution playbook
- VPS deployment runbook and security notes

## How to use this branch

1. Push branch:
   ```bash
   git push -u origin recovery/full-sync
   ```
2. Open PR from `recovery/full-sync` -> `main`.
3. If GitHub reports conflicts, follow `docs/PR_CONFLICTS.md`.
4. After merge, rotate Discord token if previously exposed.

## Recommended follow-up

- Implement mod reaction override learning (`✅/❌` => `mod_override=true` updates)
- Add scraper + Celery schedules
- Complete remaining slash commands
