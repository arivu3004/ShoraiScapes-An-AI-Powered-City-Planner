# Run Flask with Waitress WSGI Server
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Starting Flask with Waitress WSGI Server..." -ForegroundColor Green
Write-Host ""
Write-Host "Visit: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""

python -m waitress --host=0.0.0.0 --port=5000 wsgi:app
