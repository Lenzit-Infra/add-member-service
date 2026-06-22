# start_production.ps1
# Starts the API (no --reload) and the worker as background jobs. Run this
# manually, or drop a shortcut to it in the Windows Startup folder
# (shell:startup) so both processes come back automatically after a reboot.
#
# Uses the "lenzit" conda environment (not a project-local .venv). If it
# doesn't exist yet on this machine: conda create -n lenzit python=3.10
# then: conda activate lenzit && pip install -r backend\requirements.txt

$BackendDir = Split-Path -Parent $PSScriptRoot
$Python = "C:\ProgramData\anaconda3\envs\lenzit\python.exe"

if (-not (Test-Path $Python)) {
  Write-Error "Conda env 'lenzit' not found at $Python. Run: conda create -n lenzit python=3.10 && conda activate lenzit && pip install -r backend\requirements.txt"
  exit 1
}

Start-Process -FilePath $Python `
  -ArgumentList "-c", "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=4747, app_dir=r'$BackendDir')" `
  -WorkingDirectory $BackendDir -WindowStyle Hidden

Start-Process -FilePath $Python `
  -ArgumentList "scripts\run_worker.py" `
  -WorkingDirectory $BackendDir -WindowStyle Hidden

Write-Host "Backend API (port 4747) and worker started in the background, using conda env 'lenzit'."
Write-Host "Logs: backend\logs\api.log and backend\logs\worker.log (rotating, kept across restarts)."
Write-Host "Make sure the Cloudflare Tunnel service is also running (cloudflared service install)."
