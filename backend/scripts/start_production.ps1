# start_production.ps1
# Starts the API (no --reload) and the worker as background jobs. Run this
# manually, or drop a shortcut to it in the Windows Startup folder
# (shell:startup) so both processes come back automatically after a reboot.

$BackendDir = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"

Start-Process -FilePath $Python `
  -ArgumentList "-c", "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=4747, app_dir=r'$BackendDir')" `
  -WorkingDirectory $BackendDir -WindowStyle Hidden

Start-Process -FilePath $Python `
  -ArgumentList "scripts\run_worker.py" `
  -WorkingDirectory $BackendDir -WindowStyle Hidden

Write-Host "Backend API (port 4747) and worker started in the background."
Write-Host "Make sure the Cloudflare Tunnel service is also running (cloudflared service install)."
