# Going live: lenzit.ir

This covers the one-time manual steps — everything else (CI build/deploy, backend code) is already wired up.

## 1. Frontend — GitHub Pages (auto-deploys on every push to `main`)

1. **Enable Pages on the repo**: GitHub → `Lenzit-Infra/add-member-service` → Settings → Pages → under "Build and deployment", set **Source: GitHub Actions**. (One-time click — `.github/workflows/deploy-frontend.yml` does the rest.)
2. **DNS**: at whoever manages DNS for `lenzit.ir`, add these 4 `A` records for the apex (`@`):
   ```
   185.199.108.153
   185.199.109.153
   185.199.110.153
   185.199.111.153
   ```
   (If you'd rather use `www.lenzit.ir`, add a `CNAME` record `www` → `lenzit-infra.github.io` instead, and update `frontend/public/CNAME` to match.)
3. Push to `main` (touching anything under `frontend/`) and the Actions tab will show the deploy running. First propagation can take a few minutes to a few hours for DNS, plus GitHub auto-provisions an HTTPS cert once the domain resolves.

## 2. Backend — self-hosted via Cloudflare Tunnel

**Prerequisite**: `lenzit.ir` needs to be on Cloudflare's nameservers (Cloudflare Tunnel's DNS routing only works for zones it manages). If it isn't yet, add the site in the Cloudflare dashboard first and update your registrar's nameservers.

On the machine that will run the backend (this one, kept on):

```powershell
winget install --id Cloudflare.cloudflared
cloudflared tunnel login          # opens a browser — authorize the lenzit.ir zone
cloudflared tunnel create lenzit-backend     # prints a TUNNEL_ID, writes ~/.cloudflared/<TUNNEL_ID>.json
cloudflared tunnel route dns lenzit-backend api.lenzit.ir
```

Edit `backend/cloudflared-config.yml` and replace both `<TUNNEL_ID>` placeholders with the ID printed above. Then:

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
1. Use a Gmail account, turn on 2-Step Verification.
2. Create an App Password: https://myaccount.google.com/apppasswords
3. Set in `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=youraccount@gmail.com
   SMTP_PASSWORD=<the 16-character app password>
   SMTP_FROM=youraccount@gmail.com
   ```

## 4. Start the backend for real

```powershell
backend\scripts\start_production.ps1
```

Put a shortcut to this script in `shell:startup` (Win+R → `shell:startup`) so the API + worker relaunch automatically after a reboot — the Cloudflare Tunnel service (step 2) already auto-starts on its own.

## 5. First login

Once `api.lenzit.ir` and `lenzit.ir` are both live: open the site, click **"Claim admin account"**, enter the email you put in `ADMIN_EMAILS`, and follow the link sent to that inbox to set your username/password.
