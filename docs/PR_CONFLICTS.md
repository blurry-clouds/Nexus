# PR Conflict Resolution Playbook (NEXUS)

If GitHub says your PR has conflicts, use this exact flow locally.

## 1) Ensure `origin` points to your repo

```bash
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/blurry-clouds/Nexus.git
git remote -v
```

## 2) Fetch latest branches

```bash
git fetch origin --prune
```

## 3) Rebase your working branch on top of `origin/main`

```bash
git checkout work
git rebase origin/main
```

If conflicts appear:

```bash
# inspect conflicted files
git status

# edit files to resolve <<<<<<< / ======= / >>>>>>> markers
# then mark resolved
git add <file1> <file2>

# continue
git rebase --continue
```

If you need to stop and retry:

```bash
git rebase --abort
```

## 4) Push updated branch

```bash
git push --force-with-lease origin work
```

---

## Conflict policy for this repo

1. Prefer keeping **latest functional code path** over placeholder scaffolds.
2. Preserve DB schema compatibility with `database/migrations/001_init.sql`.
3. Keep provider routing options (`anthropic`, `puter_js`, `openai_compatible`).
4. If both sides changed `README.md`, keep operational steps + security notes from both.

---

## Typical hotspots in this project

- `README.md` (high churn due roadmap updates)
- `config.py` and `.env.example` (new flags added frequently)
- `brain/decision_engine.py` and `cogs/moderation.py` (active implementation area)

---

## After conflict resolution: sanity checks

```bash
python -m compileall .
```

If Docker is available:

```bash
docker compose config
docker compose up --build -d
docker compose logs -f nexus-bot
```

---

## Security reminder

If a Discord token was ever pasted publicly, rotate it immediately in Discord Developer Portal and update `.env`.
