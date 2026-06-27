# start_production.ps1
# Starts Xray-core (Telegram proxy), the API, the worker, and the Cloudflare
# Tunnel as background processes. Run this manually, or drop a shortcut to it
# in the Windows Startup folder (shell:startup) so everything comes back
# automatically after a reboot/login.
#
# Uses the "lenzit" conda environment (not a project-local .venv). If it
# doesn't exist yet on this machine: conda create -n lenzit python=3.10
# then: conda activate lenzit && pip install -r backend\requirements.txt
#
# The Cloudflare Tunnel is started as a plain background process here
# rather than via "cloudflared service install" — on this machine the
# Windows service wrapper silently failed to load its config (no tunnel
# connection was ever attempted), while running it directly works reliably.
# It's also pinned to --protocol http2 because this network blocks outbound
# QUIC/UDP (port 7844); without that flag it spends ~60s retrying QUIC.
#
# Xray-core: this network also blocks direct outbound connections to
# Telegram's own servers, so every Telethon connection (agent onboarding, the
# worker) routes through a local Xray-core instance instead. It's managed by
# scripts/proxy_supervisor.py, which refetches TELEGRAM_PROXY_SUBSCRIPTION_URL
# (or falls back to the static TELEGRAM_PROXIES list) every
# TELEGRAM_PROXY_REFRESH_MINUTES, regenerates xray-config.json, and restarts
# xray-core only when the list actually changed or it died.

$BackendDir = Split-Path -Parent $PSScriptRoot
$Python = "C:\ProgramData\anaconda3\envs\lenzit\python.exe"
$Cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"

if (-not (Test-Path $Python)) {
  Write-Error "Conda env 'lenzit' not found at $Python. Run: conda create -n lenzit python=3.10 && conda activate lenzit && pip install -r backend\requirements.txt"
  exit 1
}

New-Item -ItemType Directory -Force -Path (Join-Path $BackendDir "logs") | Out-Null

Start-Process -FilePath $Python `
  -ArgumentList "scripts\proxy_supervisor.py" `
  -WorkingDirectory $BackendDir -WindowStyle Hidden
Start-Sleep -Seconds 3  # give it a moment to fetch the subscription and bind the local SOCKS5 port before Telethon needs it

Start-Process -FilePath $Python `
  -ArgumentList "scripts\run_api.py" `
  -WorkingDirectory $BackendDir -WindowStyle Hidden

Start-Process -FilePath $Python `
  -ArgumentList "scripts\run_worker.py" `
  -WorkingDirectory $BackendDir -WindowStyle Hidden

# Polls /health from outside the API process and DMs the owner via a Telegram
# bot on any ok<->degraded/down transition. No-op if ALERT_BOT_TOKEN/ALERT_CHAT_ID
# aren't set in .env.
Start-Process -FilePath $Python `
  -ArgumentList "scripts\health_watchdog.py" `
  -WorkingDirectory $BackendDir -WindowStyle Hidden

if (Test-Path $Cloudflared) {
  Start-Process -FilePath $Cloudflared `
    -ArgumentList "tunnel", "--protocol", "http2", "--config", "cloudflared-config.yml", "run" `
    -WorkingDirectory $BackendDir -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $BackendDir "logs\cloudflared.log") `
    -RedirectStandardError (Join-Path $BackendDir "logs\cloudflared.err.log")
} else {
  Write-Warning "cloudflared.exe not found at $Cloudflared — api.lenzit.ir will not be reachable until it's installed."
}

Write-Host "Proxy supervisor (xray-core), backend API (port 4747), worker, health watchdog, and Cloudflare Tunnel started in the background, using conda env 'lenzit'."
Write-Host "Logs: backend\logs\api.log, worker.log, xray_supervisor.log, xray.log, watchdog.log, and cloudflared.log (rotating, kept across restarts)."
