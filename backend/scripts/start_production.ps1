# start_production.ps1
# Starts the API, the worker, and the Cloudflare Tunnel as background
# processes. Run this manually, or drop a shortcut to it in the Windows
# Startup folder (shell:startup) so all three come back automatically after
# a reboot/login.
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

$BackendDir = Split-Path -Parent $PSScriptRoot
$Python = "C:\ProgramData\anaconda3\envs\lenzit\python.exe"
$Cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"

if (-not (Test-Path $Python)) {
  Write-Error "Conda env 'lenzit' not found at $Python. Run: conda create -n lenzit python=3.10 && conda activate lenzit && pip install -r backend\requirements.txt"
  exit 1
}

New-Item -ItemType Directory -Force -Path (Join-Path $BackendDir "logs") | Out-Null

Start-Process -FilePath $Python `
  -ArgumentList "-c", "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=4747, app_dir=r'$BackendDir')" `
  -WorkingDirectory $BackendDir -WindowStyle Hidden

Start-Process -FilePath $Python `
  -ArgumentList "scripts\run_worker.py" `
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

Write-Host "Backend API (port 4747), worker, and Cloudflare Tunnel started in the background, using conda env 'lenzit'."
Write-Host "Logs: backend\logs\api.log, worker.log, and cloudflared.log (rotating, kept across restarts)."
