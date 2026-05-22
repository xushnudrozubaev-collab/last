$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

function Stop-PortProcess {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        if ($connection.OwningProcess) {
            Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}

if (!(Test-Path $backend)) {
    throw "Backend papka topilmadi: $backend"
}

if (!(Test-Path $frontend)) {
    throw "Frontend papka topilmadi: $frontend"
}

if (!(Test-Path $python)) {
    Write-Host "Backend virtual environment yaratilmoqda..."
    Push-Location $backend
    python -m venv .venv
    Pop-Location
}

if (!(Test-Path (Join-Path $backend ".venv\Lib\site-packages\django"))) {
    Write-Host "Backend kutubxonalari o'rnatilmoqda..."
    Push-Location $backend
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
    Pop-Location
}

if (!(Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Frontend kutubxonalari o'rnatilmoqda..."
    Push-Location $frontend
    npm.cmd install
    Pop-Location
}

Write-Host "Backend migration tekshirilmoqda..."
Push-Location $backend
& $python manage.py migrate --noinput
Pop-Location

Stop-PortProcess -Port 8000
Stop-PortProcess -Port 5173

Write-Host "Backend ishga tushmoqda: http://127.0.0.1:8000"
$backendProcess = Start-Process `
    -FilePath $python `
    -ArgumentList "manage.py runserver 127.0.0.1:8000" `
    -WorkingDirectory $backend `
    -RedirectStandardOutput (Join-Path $backend "runserver.out.log") `
    -RedirectStandardError (Join-Path $backend "runserver.err.log") `
    -WindowStyle Hidden `
    -PassThru

Write-Host "Frontend ishga tushmoqda: http://127.0.0.1:5173"
$frontendProcess = Start-Process `
    -FilePath "npm.cmd" `
    -ArgumentList "run dev -- --host 127.0.0.1 --port 5173" `
    -WorkingDirectory $frontend `
    -RedirectStandardOutput (Join-Path $frontend "vite.out.log") `
    -RedirectStandardError (Join-Path $frontend "vite.err.log") `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Loyiha ishga tushdi."
Write-Host "Asosiy sayt: http://127.0.0.1:5173"
Write-Host "Backend API:  http://127.0.0.1:8000/api"
Write-Host "Admin panel:  http://127.0.0.1:8000/admin"
Write-Host ""
Write-Host "To'xtatish uchun:"
Write-Host "Stop-Process -Id $($backendProcess.Id),$($frontendProcess.Id)"
