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

`cloudflared` is already installed on this machine (`C:\Program Files (x86)\cloudflared\cloudflared.exe`). The remaining steps need *your* Cloudflare account/browser, so run these yourself in a PowerShell window on this PC:

**Prerequisite**: `lenzit.ir` needs to be on Cloudflare's nameservers (Cloudflare Tunnel's DNS routing only works for zones it manages). If it isn't yet: Cloudflare dashboard → Add a site → `lenzit.ir` → follow its instructions to update nameservers at your registrar.

```powershell
cloudflared tunnel login          # opens a browser — log into Cloudflare and authorize the lenzit.ir zone
cloudflared tunnel create lenzit-backend     # prints a TUNNEL_ID, writes %USERPROFILE%\.cloudflared\<TUNNEL_ID>.json
cloudflared tunnel route dns lenzit-backend api.lenzit.ir
```

Tell me the `TUNNEL_ID` it prints and I'll fill in `backend/cloudflared-config.yml` and install the service for you. Or do it yourself:

```powershell
cloudflared service install --config backend\cloudflared-config.yml
```

This installs the tunnel as a Windows service so `https://api.lenzit.ir` stays up across reboots (as long as this PC is on).

## 3. Backend `.env` — production values

`backend/.env` already has a working `JWT_SECRET_KEY` and `ADMIN_EMAILS` for local dev. Before going live, update:

```
FRONTEND_URL=https://lenzit.ir
CORS_ORIGINS=https://lenzit.ir,https://www.lenzit.ir
COOKIE_DOMAIN=.lenzit.ir
COOKIE_SECURE=true
```

And fill in SMTP so claim-admin/forgot-password emails actually send (free option — no paid API):
1. Use a Gmail account, turn on 2-Step Verification (required for App Passwords): https://myaccount.google.com/security
2. Create an App Password: https://myaccount.google.com/apppasswords — sign in, name it anything (e.g. "Lenzit Dashboard"), copy the 16-character password it shows you (only shown once).
3. Set in `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=youraccount@gmail.com
   SMTP_PASSWORD=<the 16-character app password, no spaces>
   SMTP_FROM=youraccount@gmail.com
   ```
4. Restart the backend. Until this is filled in, claim/reset links are printed to `backend/logs/api.log` instead of emailed — still fully usable for testing.

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

Put a shortcut to this script in `shell:startup` (Win+R → `shell:startup`) so the API + worker relaunch automatically after a reboot — the Cloudflare Tunnel service (step 2) already auto-starts on its own.

## 5. Logs

Every process writes a rotating log file (5MB × 5 backups) in addition to whatever's on screen, so nothing is lost after a crash or a closed terminal:
- `backend/logs/api.log` — the API server (requests, startup, unhandled exceptions with full traceback).
- `backend/logs/worker.log` — the background worker (every batch it processes, agent selection, flood-waits, auto-pauses, and any error with full traceback).

These aren't committed to git (gitignored) and aren't deleted on restart — open them anytime to see exactly what happened, in order, with timestamps.

## 6. First login

Once `api.lenzit.ir` and `lenzit.ir` are both live: open the site, click **"Claim admin account"**, enter one of the emails in the admin allowlist (Settings → Admin Access once you're logged in, or initially whatever's in `.env`'s `ADMIN_EMAILS`), and follow the link sent to that inbox (or printed in `api.log` if SMTP isn't set up yet) to set your username/password.
