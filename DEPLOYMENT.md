# Going live: lenzit.ir

This covers the one-time manual steps — everything else (CI build/deploy, backend code) is already wired up.

## 1. Frontend — GitHub Pages (auto-deploys on push to `main`, gated)

1. **Enable Pages on the repo**: GitHub → `Lenzit-Infra/add-member-service` → Settings → Pages → under "Build and deployment", set **Source: GitHub Actions**. (One-time click — `.github/workflows/publish.yml` does the rest.)
2. **The deploy gate**: a push to `main` only actually deploys if BOTH are true:
   - Repo Settings → Secrets and variables → Actions → **Variables** → `DEPLOY_ENABLED` = `true` (already set).
   - The commit message contains `[deploy]`.
   Otherwise the workflow run shows up in the Actions tab but skips itself (no-op) — this is intentional, so not every push goes live automatically. You can also trigger a deploy manually anytime from the Actions tab → "Publish frontend to lenzit.ir" → **Run workflow**, no tag needed for that path.
3. **DNS**: at whoever manages DNS for `lenzit.ir` (Cloudflare, once you move nameservers there — see step 2 below), add these 4 `A` records for the apex (`@`), set to **DNS only / not proxied**:
   ```
   185.199.108.153
   185.199.109.153
   185.199.110.153
   185.199.111.153
   ```
   (If you'd rather use `www.lenzit.ir`, add a `CNAME` record `www` → `lenzit-infra.github.io` instead, and update `frontend/public/CNAME` to match.)
4. **Reading the deploy log**: GitHub → repo → **Actions** tab → click the run → click the `build` or `deploy` job → each step expands with full output. Logs are kept for 90 days and are downloadable as a zip from the run page (⚙️ icon, top right of the run).

## 2. Backend — self-hosted via Cloudflare Tunnel

Done — `lenzit.ir` is on Cloudflare's nameservers, tunnel `lenzit-backend` is created, `api.lenzit.ir` routes to it, and `backend/cloudflared-config.yml` has the real tunnel ID filled in.

One thing specific to this network: outbound QUIC/UDP (port 7844) is blocked, so the config pins `protocol: http2` — without it, cloudflared spends ~60s retrying QUIC before giving up.

Also: `cloudflared service install` (the Windows-service route) silently failed to load its config on this machine — the service started but never attempted a tunnel connection, with nothing useful in the Event Log. Rather than fight that, the tunnel runs as a plain background process, same as the API and worker — `start_production.ps1` (step 4 below) starts all three together. If `cloudflared.exe` isn't found, reinstall it:
```powershell
winget install --id Cloudflare.cloudflared -e --source winget
```

## 3. Backend `.env` — production values

`backend/.env` already has a working `JWT_SECRET_KEY` and `ADMIN_EMAILS` for local dev. Before going live, update:

```
FRONTEND_URL=https://lenzit.ir
CORS_ORIGINS=https://lenzit.ir,https://www.lenzit.ir
COOKIE_DOMAIN=.lenzit.ir
COOKIE_SECURE=true
```

SMTP (email) is optional — skip it entirely and use `scripts/manage_users.py` (step 6) instead. If you want it later anyway: fill in `SMTP_HOST`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM` in `.env` with any standard SMTP provider's credentials (Gmail App Password, Zoho Mail, etc.) and restart the backend. Until then, claim/reset links just get printed to `backend/logs/api.log` instead of emailed.

## 4. Start the backend for real

Backend runs in the **`lenzit` conda environment** (not a project-local `.venv`). One-time setup if the env isn't already populated:
```powershell
conda activate lenzit
pip install -r backend\requirements.txt
```

Then:
```powershell
backend\scripts\start_production.ps1
```

Put a shortcut to this script in `shell:startup` (Win+R → `shell:startup`) so the API, worker, and Cloudflare Tunnel all relaunch automatically after a reboot/login.

## 5. Logs

Every process writes a rotating log file (5MB × 5 backups) in addition to whatever's on screen, so nothing is lost after a crash or a closed terminal:
- `backend/logs/api.log` — the API server (requests, startup, unhandled exceptions with full traceback).
- `backend/logs/worker.log` — the background worker (every batch it processes, agent selection, flood-waits, auto-pauses, and any error with full traceback).
- `backend/logs/cloudflared.log` / `cloudflared.err.log` — the tunnel's own connection log.

These aren't committed to git (gitignored) and aren't deleted on restart — open them anytime to see exactly what happened, in order, with timestamps.

## 6. First login (no email needed)

```powershell
conda activate lenzit
cd backend
python scripts/manage_users.py create myusername my@email.com mypassword123
```

That creates an admin account directly in the database — log in with it right away, no claim link / email needed at all. To recover later if you forget the password:
```powershell
python scripts/manage_users.py reset-password myusername newpassword123
```
`python scripts/manage_users.py list` shows every existing account.

(The email-based "Claim admin account" flow on the login page still works too, once SMTP is configured — but it's no longer required to get in.)
